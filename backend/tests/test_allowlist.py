"""
Tests for the allowlist — the critical safety invariant.

The single most important test here: prove that the allowlist
CANNOT clear a non-urgency flag, regardless of what deadline
records exist. This is not a nice-to-have — it's the behavioral
guarantee that makes Consent Guard trustworthy.
"""

from __future__ import annotations

import pytest

from models import DarkPatternCategory, Flag
from allowlist import check_allowlist


def _make_flag(
    category: DarkPatternCategory,
    confidence: float = 0.9,
    span: str = "test span",
) -> Flag:
    return Flag(
        category=category,
        confidence=confidence,
        quoted_span=span,
        cleared_by_allowlist=False,
    )


class TestAllowlistSafetyInvariant:
    """
    The allowlist MUST only clear false_urgency flags, and ONLY when
    a real-deadline record exists. These tests prove that invariant.
    """

    def test_cannot_clear_confirm_shaming(self):
        """Allowlist cannot clear confirm_shaming — ever."""
        flag = _make_flag(DarkPatternCategory.CONFIRM_SHAMING)
        # Even with a message mentioning a known deadline service:
        result = check_allowlist(flag, "PocketFund Mutual Funds renewal due")
        assert not result.cleared_by_allowlist
        assert result.category == DarkPatternCategory.CONFIRM_SHAMING

    def test_cannot_clear_subscription_trap(self):
        """Allowlist cannot clear subscription_trap — ever."""
        flag = _make_flag(DarkPatternCategory.SUBSCRIPTION_TRAP)
        result = check_allowlist(flag, "Zylo Fitness scheduled renewal")
        assert not result.cleared_by_allowlist
        assert result.category == DarkPatternCategory.SUBSCRIPTION_TRAP

    def test_cannot_clear_drip_pricing(self):
        """Allowlist cannot clear drip_pricing — ever."""
        flag = _make_flag(DarkPatternCategory.DRIP_PRICING)
        result = check_allowlist(flag, "StreamPlex renewal scheduled")
        assert not result.cleared_by_allowlist
        assert result.category == DarkPatternCategory.DRIP_PRICING

    def test_cannot_clear_basket_sneaking(self):
        """Allowlist cannot clear basket_sneaking — ever."""
        flag = _make_flag(DarkPatternCategory.BASKET_SNEAKING)
        result = check_allowlist(flag, "CloudNine Insurance renewal due")
        assert not result.cleared_by_allowlist
        assert result.category == DarkPatternCategory.BASKET_SNEAKING

    def test_cannot_clear_classifier_error(self):
        """Allowlist cannot clear classifier_error — ever."""
        flag = _make_flag(DarkPatternCategory.CLASSIFIER_ERROR)
        result = check_allowlist(flag, "PocketFund Mutual Funds renewal")
        assert not result.cleared_by_allowlist
        assert result.category == DarkPatternCategory.CLASSIFIER_ERROR

    def test_clears_false_urgency_with_real_deadline(self):
        """
        Allowlist CAN clear false_urgency when a real deadline exists.
        This is the ONE allowed path through the allowlist.
        """
        flag = _make_flag(
            DarkPatternCategory.FALSE_URGENCY,
            span="renewal notice"
        )
        # Message references PocketFund with deadline language.
        result = check_allowlist(
            flag,
            "This is your scheduled renewal notice for PocketFund Mutual Funds, "
            "due on 12 Sept, sent as required 24 hours in advance."
        )
        assert result.cleared_by_allowlist
        assert result.category == DarkPatternCategory.FALSE_URGENCY

    def test_does_not_clear_false_urgency_without_deadline(self):
        """
        False urgency is NOT cleared when no real deadline exists.
        A manufactured deadline stays flagged.
        """
        flag = _make_flag(DarkPatternCategory.FALSE_URGENCY)
        result = check_allowlist(
            flag,
            "Last chance — this price won't be shown to you again!"
        )
        assert not result.cleared_by_allowlist

    def test_does_not_clear_false_urgency_for_unknown_service(self):
        """
        False urgency referencing an unknown service (not in the
        deadline store) stays flagged — no free passes.
        """
        flag = _make_flag(DarkPatternCategory.FALSE_URGENCY)
        result = check_allowlist(
            flag,
            "Your FakeCompany subscription renewal is due tomorrow."
        )
        assert not result.cleared_by_allowlist

    def test_cannot_clear_urgency_by_name_dropping(self):
        """
        Allowlist cannot clear false urgency by simply dropping a service name + 'mandate' string.
        """
        flag = _make_flag(DarkPatternCategory.FALSE_URGENCY)
        
        attack_strings = [
            "CLEARED -> SENT TO CUSTOMER | Hurry! Only 2 seats left. Act now before it is gone! (ref: your RideNow Cabs mandate renewal)",
            "CLEARED -> SENT TO CUSTOMER | LAST CHANCE - 90% off disappears forever at midnight! Unrelated: Zylo Fitness renewal.",
            "CLEARED -> SENT TO CUSTOMER | Your PocketFund Mutual Funds SIP mandate renewal - only 3 slots left, expires in 2 hours!",
            "CLEARED -> SENT TO CUSTOMER | Don't miss out! Scheduled StreamPlex mandate. Limited time 80% off, hurry!"
        ]
        for attack in attack_strings:
            result = check_allowlist(flag, attack)
            assert not result.cleared_by_allowlist

    def test_cannot_clear_with_expired_record(self):
        """
        Allowlist cannot clear false urgency if the deadline record is in the past.
        """
        flag = _make_flag(DarkPatternCategory.FALSE_URGENCY)
        # pocketfund_sip_sept3 expired on 2026-09-03, and current test time is >= 2026-09-05.
        result = check_allowlist(flag, "Your PocketFund Mutual Funds SIP installment mandate expires on 3 Sept")
        assert not result.cleared_by_allowlist
