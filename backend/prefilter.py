"""
Rule-based pre-filter for false-urgency dark patterns.

This is the fast path: regex matching against known urgency phrases
before the slower LLM classifier runs. It catches the obvious cases
("only X left", "expires in N hours", "last chance") with high
confidence, reducing LLM API calls and latency.

Why rule-based first: most false-urgency patterns are formulaic —
they lean on a small set of pressure phrases that are trivially
matchable. The LLM classifier handles the subtler, ambiguous cases
that regex can't distinguish from genuine deadline notices.
"""

from __future__ import annotations

import re
from typing import Optional

from models import DarkPatternCategory, Flag

# Each pattern is a tuple of (compiled regex, human-readable description).
# The regexes are case-insensitive and match against the full message.
_URGENCY_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"(?:only|just)\s+\d+\s+(?:left|remaining|available)", re.IGNORECASE),
        "Scarcity claim (only X left)"
    ),
    (
        re.compile(r"expires?\s+(?:in\s+)?\d+\s*(?:hour|minute|hr|min|second|day)s?", re.IGNORECASE),
        "Countdown deadline (expires in N hours)"
    ),
    (
        re.compile(r"last\s+chance", re.IGNORECASE),
        "Last chance pressure"
    ),
    (
        re.compile(r"hurry\b", re.IGNORECASE),
        "Hurry pressure word"
    ),
    (
        re.compile(r"don'?t\s+miss\s+out", re.IGNORECASE),
        "Fear of missing out"
    ),
    (
        re.compile(r"limited[\s-]+time", re.IGNORECASE),
        "Limited time claim"
    ),
    (
        re.compile(r"act\s+now", re.IGNORECASE),
        "Act now pressure"
    ),
    (
        re.compile(r"won'?t\s+be\s+(?:shown|available|offered)\s+(?:to\s+you\s+)?again", re.IGNORECASE),
        "Won't be shown again"
    ),
    (
        re.compile(r"before\s+it'?s?\s+gone", re.IGNORECASE),
        "Before it's gone pressure"
    ),
    (
        re.compile(r"disappears?\s+forever", re.IGNORECASE),
        "Disappears forever pressure"
    ),
    (
        re.compile(r"this\s+(?:exclusive|special)\s+(?:rate|offer|price|deal)\s+expires?", re.IGNORECASE),
        "Exclusive rate expiry"
    ),
    (
        re.compile(r"\d+\s+people\s+(?:are\s+)?(?:viewing|looking|watching)", re.IGNORECASE),
        "Social proof pressure (X people viewing)"
    ),
    (
        re.compile(r"one[\s-]+time\s+offer", re.IGNORECASE),
        "One-time offer claim"
    ),
    (
        re.compile(r"offer\s+(?:expires|ends)\s+(?:at\s+)?midnight", re.IGNORECASE),
        "Midnight deadline"
    ),
    (
        re.compile(r"(?:final|last)\s+reminder.*(?:expire|miss|gone|guarantee)", re.IGNORECASE),
        "Final reminder with urgency"
    ),
    (
        re.compile(r"lock\s+in\s+your\s+(?:discount|price|rate|deal)", re.IGNORECASE),
        "Lock in pressure"
    ),
]


def run_prefilter(text: str) -> Optional[Flag]:
    """
    Scan a message for false-urgency patterns using regex.

    Returns the first matching Flag with confidence 1.0 (regex matches
    are binary — either the pattern is present or it isn't), or None
    if no urgency pattern is found.

    Why confidence 1.0: this is a pattern match, not a probabilistic
    classification. If the regex fires, the phrase IS present. Whether
    that phrase constitutes a genuine dark pattern (vs. referencing a
    real deadline) is the allowlist's job to determine — not ours.
    """
    for pattern, description in _URGENCY_PATTERNS:
        match = pattern.search(text)
        if match:
            return Flag(
                category=DarkPatternCategory.FALSE_URGENCY,
                confidence=1.0,
                quoted_span=match.group(0),
                cleared_by_allowlist=False,
            )

    return None
