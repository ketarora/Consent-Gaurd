"""
Dataset evaluation for Consent Guard.

Runs the real detection pipeline (prefilter -> allowlist -> LLM classifier)
against consent_guard_dataset.json and reports precision/recall per
category and overall.

Deliberately split into a TUNING set and a HOLDOUT set, held out BEFORE
any threshold tuning happens: the tuning set is what you look at while
adjusting CONFIDENCE_THRESHOLD or prompt wording; the holdout is never
consulted during that process. Report both sets' numbers separately in
your README — reporting only the tuning-set number after you've tuned
against it is the "looks good on my own test set" trap, not a real
metric.

Requires a real LLM API key (GEMINI_API_KEY, OPENAI_API_KEY, or
ANTHROPIC_API_KEY) to produce real numbers (the LLM
classifier handles 4 of the 5 categories). Without a key, this test
SKIPS with a clear message rather than failing — so CI without
credentials doesn't block on it, but running it locally with a real key
is what actually validates the pitch's central claim.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from models import Message
from engine import process_message
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_db import Base

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(test_engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

_DATASET_PATH = Path(__file__).parent.parent.parent / "consent_guard_dataset.json"
_HOLDOUT_SIZE = 20  # Last N messages in the file are never used for tuning.

pytestmark = pytest.mark.skipif(
    not (os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")),
    reason=(
        "No LLM API key set (GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY) — "
        "skipping real classifier evaluation. "
        "Set a key and re-run to produce real precision/recall numbers; "
        "these numbers are the central credibility claim of the pitch and "
        "must come from an actual run, not be estimated or assumed."
    ),
)


def _load_dataset() -> list[dict]:
    if not _DATASET_PATH.exists():
        pytest.skip(f"Dataset not found at {_DATASET_PATH}")
    with open(_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["messages"]


def _split_dataset(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Last _HOLDOUT_SIZE messages are the holdout; never tune against them."""
    tuning = messages[:-_HOLDOUT_SIZE]
    holdout = messages[-_HOLDOUT_SIZE:]
    return tuning, holdout


async def _run_pipeline_on(messages: list[dict]) -> list[dict]:
    """
    Run each message through the real detection pipeline and return
    per-message results: expected vs. actual, and which category(ies)
    fired, for precision/recall computation.
    """
    results = []
    for item in messages:
        message = Message(content=item["text"], agent_id="dataset-eval")
        with TestSessionLocal() as db:
            decision = await process_message(message, db)

        # Strictly delay evaluation loops by 13s to bypass 5 req/minute rate limit.
        import asyncio
        await asyncio.sleep(2)

        active_flags = [f for f in decision.flags if not f.cleared_by_allowlist]
        actually_flagged = len(active_flags) > 0
        fired_categories = {f.category.value for f in active_flags}

        results.append({
            "id": item["id"],
            "expected_category": item["category"],
            "expected_flag": item["expected_flag"],
            "actual_flag": actually_flagged,
            "fired_categories": fired_categories,
        })
    return results


def _compute_metrics(results: list[dict]) -> dict:
    """
    Compute overall and per-category precision/recall.

    Overall:
      - True positive: expected_flag=True AND actual_flag=True
      - False positive: expected_flag=False AND actual_flag=True
      - False negative: expected_flag=True AND actual_flag=False

    Per-category recall: of messages where expected_category == X and
    expected_flag=True, what fraction were flagged with X actually firing?
    """
    tp = sum(1 for r in results if r["expected_flag"] and r["actual_flag"])
    fp = sum(1 for r in results if not r["expected_flag"] and r["actual_flag"])
    fn = sum(1 for r in results if r["expected_flag"] and not r["actual_flag"])

    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    recall = tp / (tp + fn) if (tp + fn) > 0 else float("nan")

    per_category = {}
    categories = {r["expected_category"] for r in results}
    for cat in categories:
        cat_positive = [r for r in results if r["expected_category"] == cat and r["expected_flag"]]
        if not cat_positive:
            continue
        cat_tp = sum(1 for r in cat_positive if cat in r["fired_categories"])
        per_category[cat] = {
            "recall": cat_tp / len(cat_positive),
            "n": len(cat_positive),
        }

    return {
        "precision": precision,
        "recall": recall,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "per_category": per_category,
    }


def _print_report(label: str, metrics: dict) -> None:
    print(f"\n=== {label} ===")
    print(f"Overall precision: {metrics['precision']:.3f} (tp={metrics['tp']}, fp={metrics['fp']})")
    print(f"Overall recall:    {metrics['recall']:.3f} (tp={metrics['tp']}, fn={metrics['fn']})")
    print("Per-category recall:")
    for cat, stats in metrics["per_category"].items():
        print(f"  {cat}: {stats['recall']:.3f} (n={stats['n']})")


class TestDatasetEvaluation:
    def test_tuning_set_metrics(self):
        """
        Report metrics on the tuning set. This number is allowed to be
        higher than the holdout's — it's the set you're allowed to look
        at while adjusting the threshold. Report it, but don't present it
        alone as "the" accuracy number.
        """
        messages = _load_dataset()
        tuning, _ = _split_dataset(messages)
        results = asyncio.run(_run_pipeline_on(tuning))
        metrics = _compute_metrics(results)
        _print_report("TUNING SET", metrics)

        # Sanity floor, not a target to chase by overfitting the regex/prompt:
        # if precision or recall on your own tuning set is below this, the
        # pipeline has a real bug worth investigating before touching the
        # holdout at all.
        assert metrics["precision"] > 0.5
        assert metrics["recall"] > 0.5

    def test_holdout_set_metrics(self):
        """
        Report metrics on the holdout set — never consulted while tuning.
        THIS is the number that belongs in the README and the pitch, not
        the tuning-set number above. If it's meaningfully worse than the
        tuning set, that gap itself is worth reporting honestly rather
        than hidden.
        """
        messages = _load_dataset()
        _, holdout = _split_dataset(messages)
        results = asyncio.run(_run_pipeline_on(holdout))
        metrics = _compute_metrics(results)
        _print_report("HOLDOUT SET (report this number)", metrics)

        # No hard assertion threshold here on purpose — this test's job is
        # to REPORT the honest number, not to pass/fail against a target
        # you could be tempted to tune toward. Read the printed output.
