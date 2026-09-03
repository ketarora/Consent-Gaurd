"""
Allowlist for Consent Guard.

The allowlist can ONLY clear false_urgency flags — and ONLY when a
matching real-deadline record exists in the deadline store. This is
the single most important safety invariant in the system:

    ┌─────────────────────────────────────────────────────────┐
    │  The allowlist NEVER clears confirm_shaming,            │
    │  forced_continuity, drip_pricing, or basket_sneaking.   │
    │  If you add a new category, it is NOT allowlisted       │
    │  unless you explicitly add it here AND justify why.     │
    └─────────────────────────────────────────────────────────┘

Why this restriction exists: false urgency is the one category where
a message can pattern-match as manipulative but actually be legitimate
(e.g., "Your renewal is due tomorrow" when there IS a renewal due
tomorrow). The other four categories describe structural manipulation
(pre-added cart items, hidden fees, guilt-tripped decline copy,
obstructed cancellation) that no allowlist entry can make legitimate.
"""

from __future__ import annotations

from typing import Optional

from deadline_store import find_matching_deadline
from models import DarkPatternCategory, Flag


def check_allowlist(flag: Flag, message_text: str) -> Flag:
    """
    Check a flag against the allowlist.

    SAFETY INVARIANT: This function will ONLY clear a flag if:
      1. The flag category is exactly FALSE_URGENCY, AND
      2. A matching real-deadline record exists in the deadline store.

    If either condition is false, the flag is returned unchanged.
    This is not a performance optimization — it's a correctness
    constraint. A bug here means a genuine dark pattern gets waved
    through to a customer.

    Returns:
        The original flag (unchanged if not clearable), or a new Flag
        with cleared_by_allowlist=True if both conditions are met.
    """
    # ── GUARD: only false_urgency is eligible for allowlist clearing ──
    # This guard is deliberately placed FIRST, before any deadline
    # lookup. Even if a deadline record exists, we refuse to clear
    # any category other than false_urgency.
    if flag.category != DarkPatternCategory.FALSE_URGENCY:
        return flag

    # ── Check for a matching real deadline ──
    deadline_record = find_matching_deadline(message_text)

    if deadline_record is not None:
        # A real deadline exists — this urgency reference is legitimate.
        return Flag(
            category=flag.category,
            confidence=flag.confidence,
            quoted_span=flag.quoted_span,
            cleared_by_allowlist=True,
        )

    # No matching deadline — the flag stands.
    return flag
