"""
Tests for the audit log — the foundation of Consent Guard's auditability.

These tests verify the append-only invariant: entries can be added,
read back in order, and the log file is never truncated or overwritten
during normal operation.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from models import Action, DarkPatternCategory, Decision, Flag
from audit_log import write_decision, read_log, clear_log


@pytest.fixture
def temp_log_path(tmp_path):
    """Provide a temporary log file path for each test."""
    return tmp_path / "test_audit.jsonl"


def _make_decision(
    message_id: str = "test-msg-1",
    action: Action = Action.SENT,
    category: DarkPatternCategory = None,
) -> Decision:
    """Helper to create a test Decision."""
    flags = []
    if category:
        flags.append(Flag(
            category=category,
            confidence=0.9,
            quoted_span="test span",
        ))

    return Decision(
        message_id=message_id,
        flags=flags,
        action=action,
    )


class TestAuditLogAppendOnly:
    """
    Verify that the audit log is append-only: new entries are added
    to the end, existing entries are never modified or removed.
    """

    def test_write_creates_file(self, temp_log_path: Path):
        """Writing to a non-existent log file creates it."""
        decision = _make_decision()
        write_decision(decision, log_path=temp_log_path)
        assert temp_log_path.exists()

    def test_write_appends_not_overwrites(self, temp_log_path: Path):
        """Each write adds a line; it never truncates previous lines."""
        d1 = _make_decision(message_id="msg-1", action=Action.SENT)
        d2 = _make_decision(message_id="msg-2", action=Action.HELD)

        write_decision(d1, log_path=temp_log_path)
        write_decision(d2, log_path=temp_log_path)

        lines = temp_log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        assert entry1["message_id"] == "msg-1"
        assert entry2["message_id"] == "msg-2"

    def test_read_returns_most_recent_first(self, temp_log_path: Path):
        """read_log returns entries in reverse chronological order."""
        for i in range(5):
            write_decision(
                _make_decision(message_id=f"msg-{i}"),
                log_path=temp_log_path
            )

        entries = read_log(log_path=temp_log_path)
        assert len(entries) == 5
        # Most recent (msg-4) should be first.
        assert entries[0]["message_id"] == "msg-4"
        assert entries[4]["message_id"] == "msg-0"

    def test_empty_log_returns_empty_list(self, temp_log_path: Path):
        """Reading a non-existent log returns an empty list, not an error."""
        entries = read_log(log_path=temp_log_path)
        assert entries == []

    def test_decision_fields_preserved(self, temp_log_path: Path):
        """All Decision fields survive the write→read roundtrip."""
        decision = _make_decision(
            message_id="round-trip-test",
            action=Action.HELD,
            category=DarkPatternCategory.FALSE_URGENCY,
        )
        write_decision(decision, log_path=temp_log_path)
        entries = read_log(log_path=temp_log_path)

        assert len(entries) == 1
        entry = entries[0]
        assert entry["message_id"] == "round-trip-test"
        assert entry["action"] == "held"
        assert len(entry["flags"]) == 1
        assert entry["flags"][0]["category"] == "false_urgency"
        assert entry["flags"][0]["confidence"] == 0.9
        assert entry["flags"][0]["quoted_span"] == "test span"

    def test_each_entry_is_valid_json(self, temp_log_path: Path):
        """Every line in the log file is a valid JSON object."""
        for i in range(10):
            write_decision(
                _make_decision(message_id=f"json-test-{i}"),
                log_path=temp_log_path
            )

        with open(temp_log_path) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    pytest.fail(f"Line {line_num} is not valid JSON: {line}")
