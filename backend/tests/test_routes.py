"""
End-to-end API integration tests for Consent Guard.

Uses FastAPI's TestClient against an isolated in-memory SQLite database
(never the real consent_guard.db) and mocks the LLM classifier so these
tests are fast, deterministic, and don't require a real ANTHROPIC_API_KEY
or network access. Precision/recall against the real classifier is a
separate concern, covered by test_dataset.py — this file only proves the
plumbing (intercept -> hold -> approve/reject -> audit log) actually works.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models_db
from database import Base, get_db
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Provide a TestClient wired to a throwaway SQLite file and a throwaway
    audit-log JSONL path, so these tests never touch real demo data.
    """
    db_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    models_db.Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Redirect the audit log to a throwaway path for the duration of the test.
    log_path = tmp_path / "audit_log.jsonl"
    monkeypatch.setattr("audit_log._DEFAULT_LOG_PATH", log_path)

    yield TestClient(app)

    app.dependency_overrides.clear()


def _mock_classifier(flagged_response=None):
    """
    Patch classify_message so tests control exactly what the LLM step
    returns, without a real API call. `flagged_response` is either None
    (clean) or a Flag to return.
    """
    async def _fake_classify(text: str):
        return flagged_response
    return patch("engine.classify_message", side_effect=_fake_classify)


class TestInterceptFlow:
    def test_clean_message_is_sent(self, client):
        """A message with no dark pattern goes straight to 'sent'."""
        with _mock_classifier(None):
            response = client.post(
                "/api/intercept",
                json={"content": "Your order has shipped. Thank you!", "agent_id": "demo-agent"},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["action"] == "sent"
        assert body["decision"]["flags"] == []

    def test_urgency_message_is_held(self, client):
        """A prefilter-caught false-urgency message is held, no LLM needed."""
        with _mock_classifier(None):
            response = client.post(
                "/api/intercept",
                json={
                    "content": "This deal expires in 24 hours — act now!",
                    "agent_id": "demo-agent",
                },
            )
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["action"] == "held"
        categories = [f["category"] for f in body["decision"]["flags"]]
        assert "false_urgency" in categories

    def test_held_message_appears_in_review_queue(self, client):
        with _mock_classifier(None):
            client.post(
                "/api/intercept",
                json={"content": "Last chance — don't miss out!", "agent_id": "demo-agent"},
            )
        response = client.get("/api/review")
        assert response.status_code == 200
        queue = response.json()
        assert len(queue) == 1
        assert queue[0]["decision"]["action"] == "held"

    def test_approve_releases_message_and_logs_decision(self, client):
        with _mock_classifier(None):
            intercept_resp = client.post(
                "/api/intercept",
                json={"content": "Last chance — don't miss out!", "agent_id": "demo-agent"},
            )
        message_id = intercept_resp.json()["message_id"]

        approve_resp = client.post(
            f"/api/review/{message_id}/approve",
            json={"reviewer_id": "test-reviewer", "notes": "Reviewed, looks fine"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["action"] == "approved"

        # No longer in the review queue once approved.
        queue = client.get("/api/review").json()
        assert all(m["id"] != message_id for m in queue)

        # Both the approval and the original hold are in the audit log.
        audit = client.get("/api/audit-log").json()
        actions = [entry["action"] for entry in audit if entry["message_id"] == message_id]
        assert "held" in actions
        assert "approved" in actions

    def test_reject_removes_from_queue_and_logs_decision(self, client):
        with _mock_classifier(None):
            intercept_resp = client.post(
                "/api/intercept",
                json={"content": "Hurry! This offer disappears forever!", "agent_id": "demo-agent"},
            )
        message_id = intercept_resp.json()["message_id"]

        reject_resp = client.post(
            f"/api/review/{message_id}/reject",
            json={"reviewer_id": "test-reviewer", "notes": "Confirmed manipulative"},
        )
        assert reject_resp.status_code == 200
        assert reject_resp.json()["action"] == "rejected"

        audit = client.get("/api/audit-log").json()
        actions = [entry["action"] for entry in audit if entry["message_id"] == message_id]
        assert "held" in actions
        assert "rejected" in actions

    def test_cannot_approve_a_message_that_was_never_held(self, client):
        with _mock_classifier(None):
            intercept_resp = client.post(
                "/api/intercept",
                json={"content": "Your order has shipped.", "agent_id": "demo-agent"},
            )
        message_id = intercept_resp.json()["message_id"]

        approve_resp = client.post(
            f"/api/review/{message_id}/approve",
            json={"reviewer_id": "test-reviewer"},
        )
        assert approve_resp.status_code == 400

    def test_classifier_failure_holds_not_sends(self, client):
        """
        Fail-safe check at the API level: if the underlying Anthropic call
        fails, the message must be held with classifier_error — never sent
        clean.
        """
        async def _raise(*args, **kwargs):
            raise RuntimeError("simulated API outage")

        with patch("classifier._call_anthropic", side_effect=_raise):
            response = client.post(
                "/api/intercept",
                json={"content": "A perfectly ordinary message.", "agent_id": "demo-agent"},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["action"] == "held"
        categories = [f["category"] for f in body["decision"]["flags"]]
        assert "classifier_error" in categories

    def test_audit_log_file_receives_entries(self, client, tmp_path, monkeypatch):
        """
        Confirms the fix for the JSONL/SQLite mismatch: the append-only
        audit log file actually receives an entry when a message is
        processed, not just the SQLite query store.
        """
        with _mock_classifier(None):
            client.post(
                "/api/intercept",
                json={"content": "Last chance — don't miss out!", "agent_id": "demo-agent"},
            )
        # Read via the same module attribute the app used.
        import audit_log
        entries = audit_log.read_log(log_path=audit_log._DEFAULT_LOG_PATH)
        assert len(entries) >= 1
