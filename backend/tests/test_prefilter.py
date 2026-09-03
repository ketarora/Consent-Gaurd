"""
Tests for the rule-based false-urgency pre-filter.
"""

from __future__ import annotations

import pytest

from models import DarkPatternCategory
from prefilter import run_prefilter


class TestPrefilterCatchesUrgency:
    """Verify that known false-urgency phrases are caught."""

    @pytest.mark.parametrize("text,description", [
        ("Only 3 left in stock — order now!", "Scarcity claim"),
        ("⏰ Hurry! Your deal expires in 2 hours", "Countdown + hurry"),
        ("Last chance to grab this offer!", "Last chance"),
        ("Don't miss out on this exclusive deal", "FOMO"),
        ("Limited-time offer, act now!", "Limited time + act now"),
        ("This price won't be shown to you again", "Won't be shown again"),
        ("Before it's gone forever!", "Before it's gone"),
        ("This exclusive rate expires at midnight", "Exclusive rate expiry"),
        ("6 people are viewing this offer right now", "Social proof"),
        ("One-time offer — disappears forever after today", "One-time + disappears"),
        ("Lock in your discount before it's gone!", "Lock in pressure"),
        ("Final reminder: this deal expires at midnight", "Final reminder"),
    ])
    def test_catches_urgency_pattern(self, text: str, description: str):
        """Pre-filter catches known urgency patterns."""
        flag = run_prefilter(text)
        assert flag is not None, f"Failed to catch: {description}"
        assert flag.category == DarkPatternCategory.FALSE_URGENCY
        assert flag.confidence == 1.0
        assert len(flag.quoted_span) > 0


class TestPrefilterPassesClean:
    """Verify that clean messages are not flagged."""

    @pytest.mark.parametrize("text,description", [
        ("Your order has been shipped.", "Normal order update"),
        ("Thank you for your purchase!", "Thank you message"),
        ("Your subscription will renew on March 1.", "Simple renewal notice"),
        ("Would you like to add gift wrapping?", "Optional add-on"),
        ("Final price: ₹599 (all taxes included).", "Upfront pricing"),
        ("Cancel anytime from Settings.", "Easy cancellation"),
    ])
    def test_passes_clean_message(self, text: str, description: str):
        """Pre-filter does not flag clean messages."""
        flag = run_prefilter(text)
        assert flag is None, f"False positive on: {description}"
