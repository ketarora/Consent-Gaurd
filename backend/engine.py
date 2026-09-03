"""
Decision engine for Consent Guard.

Orchestrates the full detection pipeline:
    prefilter → allowlist → LLM classifier → threshold → audit log → action

The engine's single most important design constraint: the audit log
write happens BEFORE any side-effecting action (sending or holding).
If the system crashes between logging and acting, we lose the action
but keep the record. The reverse would make the system unauditable.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    Action,
    DarkPatternCategory,
    Decision,
    Flag,
    Message,
)
from crud import create_decision, create_message
from event_manager import sse_manager
from prefilter import run_prefilter
from allowlist import check_allowlist
from classifier import classify_message
from audit_log import write_decision

logger = logging.getLogger(__name__)

# Default confidence threshold for holding a message.
# At or above this threshold, the message is held for review.
# Below it, the message is sent through.
_DEFAULT_THRESHOLD = 0.75


def _get_threshold() -> float:
    """
    Read the confidence threshold from environment, falling back
    to 0.75 if not set.

    Why configurable: different merchants may have different risk
    tolerances. A conservative merchant might set 0.5 (hold more,
    miss less); a permissive one might set 0.9 (hold less, risk more).
    The default of 0.75 is a reasonable middle ground for the demo.
    """
    try:
        return float(os.environ.get("CONFIDENCE_THRESHOLD", str(_DEFAULT_THRESHOLD)))
    except ValueError:
        return _DEFAULT_THRESHOLD


async def process_message(message: Message, db: Session) -> Decision:
    """
    Run the full detection pipeline on a message and return a Decision.

    `db` is the caller's database session, injected via FastAPI's
    Depends(get_db) in routes.py. This function must NEVER open its own
    session from a global SessionLocal — doing so bypasses dependency
    injection entirely, silently writes to the real production database
    even when a test has overridden get_db with an isolated one, and
    makes this function untestable against anything but the live db file.

    Pipeline order matters:
    1. Rule-based prefilter (fast, catches obvious false_urgency)
    2. Allowlist check (only if prefilter flagged false_urgency)
    3. LLM classifier (for other categories + ambiguous urgency)
    4. Threshold check (hold if confidence ≥ threshold)
    5. Audit log write (BEFORE action — non-negotiable)
    6. Return decision
    """
    threshold = _get_threshold()
    all_flags: list[Flag] = []

    # ── Step 1: Rule-based pre-filter for false urgency ──
    prefilter_flag = run_prefilter(message.content)

    if prefilter_flag is not None:
        # ── Step 2: Allowlist check ──
        checked_flag = check_allowlist(prefilter_flag, message.content)

        if checked_flag.cleared_by_allowlist:
            # Real deadline confirmed — don't hold on this flag,
            # but still record that we checked it.
            all_flags.append(checked_flag)
            logger.info(
                f"Message {message.id}: false_urgency cleared by allowlist "
                f"(real deadline on record)"
            )
        else:
            # Urgency flag stands — no real deadline found.
            all_flags.append(checked_flag)

    # ── Step 3: LLM classifier ──
    # Runs on every message to catch non-urgency categories.
    # Also catches ambiguous urgency the prefilter can't resolve.
    classifier_flag = await classify_message(message.content)

    if classifier_flag is not None:
        # CRITICAL FIX: If the LLM independently flags false_urgency, it must ALSO
        # face the allowlist check, otherwise it neutralizes earlier clearances.
        if classifier_flag.category == DarkPatternCategory.FALSE_URGENCY:
            classifier_flag = check_allowlist(classifier_flag, message.content)

        # Don't double-flag the same category from prefilter + classifier.
        existing_active_categories = {f.category for f in all_flags if not f.cleared_by_allowlist}
        if classifier_flag.category not in existing_active_categories:
            all_flags.append(classifier_flag)

    # ── Step 4: Determine action ──
    # A message is held if ANY un-cleared flag meets the threshold.
    active_flags = [
        f for f in all_flags
        if not f.cleared_by_allowlist
    ]

    should_hold = any(
        f.confidence >= threshold or f.category == DarkPatternCategory.CLASSIFIER_ERROR
        for f in active_flags
    )

    action = Action.HELD if should_hold else Action.SENT

    # ── Step 5: Write to the audit log BEFORE any side-effecting action ──
    decision = Decision(
        message_id=message.id,
        flags=all_flags,
        action=action,
    )

    # The append-only JSONL audit trail is the record of intent described
    # in the README and design docs — it is written FIRST, before the
    # message becomes visible/actionable to a reviewer via the SQLite
    # query store or the SSE broadcast that follows in routes.py.
    write_decision(decision)

    # SQLite is the queryable application state the API/frontend reads
    # from (review queue, ledger, message history). Written immediately
    # after the JSONL audit trail, still before the SSE broadcast.
    # Uses the caller's injected session — never opens its own.
    create_decision(db, decision)

    # ── Step 6: Attach decision to message and return ──
    message.decision = decision
    return decision
