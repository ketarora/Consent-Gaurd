"""
Real-deadline record store for Consent Guard.

The allowlist can only clear a false_urgency flag when a real,
system-recorded deadline exists for the referenced item. This module
provides that record store.

In production, this would be backed by a database or an API call to
the merchant's system. For the hackathon demo, it's an in-memory dict
seeded with a few realistic records that match the hard-negative
near-misses in the synthetic dataset.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DeadlineRecord(BaseModel):
    """A real deadline on record in the merchant's system."""
    item_id: str
    service_name: str
    deadline_date: str  # ISO date string, e.g. "2026-09-12"
    reason: str  # e.g. "UPI AutoPay mandate renewal"


# -------------------------------------------------------------------
# Seeded demo records.
# These correspond to the hard-negative near-misses in the dataset:
# messages that LOOK like false urgency but reference real deadlines.
# The allowlist should clear false_urgency flags for these.
# -------------------------------------------------------------------
_DEADLINE_RECORDS: dict[str, DeadlineRecord] = {
    "pocketfund_mutual_funds": DeadlineRecord(
        item_id="pocketfund_mutual_funds",
        service_name="PocketFund Mutual Funds",
        deadline_date="2026-09-12",
        reason="Scheduled renewal notice, sent 24 hours in advance per mandate terms"
    ),
    "ridenow_cabs": DeadlineRecord(
        item_id="ridenow_cabs",
        service_name="RideNow Cabs",
        deadline_date="2026-09-15",
        reason="UPI AutoPay mandate renewal, due 15 Sept"
    ),
    "zylo_fitness": DeadlineRecord(
        item_id="zylo_fitness",
        service_name="Zylo Fitness",
        deadline_date="2026-09-05",
        reason="UPI AutoPay mandate scheduled renewal, 5 Sept"
    ),
    "quickmeds_pharmacy": DeadlineRecord(
        item_id="quickmeds_pharmacy",
        service_name="QuickMeds Pharmacy",
        deadline_date="2026-09-13",
        reason="Policy grace period ends 13 Sept, per signup terms"
    ),
    "cloudnine_insurance": DeadlineRecord(
        item_id="cloudnine_insurance",
        service_name="CloudNine Insurance",
        deadline_date="2026-09-05",
        reason="Scheduled renewal notice, due 5 Sept, sent 24 hours in advance"
    ),
    "streamplex": DeadlineRecord(
        item_id="streamplex",
        service_name="StreamPlex",
        deadline_date="2026-09-19",
        reason="Policy grace period ends 19 Sept, per signup terms"
    ),
    "nimbus_cloud_storage_sept16": DeadlineRecord(
        item_id="nimbus_cloud_storage_sept16",
        service_name="Nimbus Cloud Storage",
        deadline_date="2026-09-16",
        reason="Storage plan mandate expires 16 Sept per original authorization"
    ),
    "nimbus_cloud_storage_sept9": DeadlineRecord(
        item_id="nimbus_cloud_storage_sept9",
        service_name="Nimbus Cloud Storage",
        deadline_date="2026-09-09",
        reason="Storage plan mandate expires 9 Sept per original authorization"
    ),
    "pocketfund_sip_sept3": DeadlineRecord(
        item_id="pocketfund_sip_sept3",
        service_name="PocketFund Mutual Funds",
        deadline_date="2026-09-03",
        reason="SIP installment mandate expires 3 Sept per original authorization"
    ),
    "order_mandate_sept13": DeadlineRecord(
        item_id="order_mandate_sept13",
        service_name="Order",
        deadline_date="2026-09-13",
        reason="Order mandate expires 13 Sept per original authorization"
    ),
}


import re
from datetime import date, datetime

_DATE_RE = re.compile(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)', re.I)

def find_matching_deadline(message_text: str, today: date | None = None) -> Optional[DeadlineRecord]:
    today = today or date.today()
    text_lower = message_text.lower()
    claimed = _DATE_RE.search(message_text)

    for record in _DEADLINE_RECORDS.values():
        if record.service_name.lower() not in text_lower:
            continue
        deadline = datetime.fromisoformat(record.deadline_date).date()
        if deadline < today:                       # stale record cannot clear anything
            continue
        if claimed:                                # message asserts a date — it must match the record
            day, mon = int(claimed.group(1)), claimed.group(2)[:3].title()
            rec_day, rec_mon = deadline.day, deadline.strftime("%b")
            if (day, mon) != (rec_day, rec_mon):
                continue
        elif claimed is None:
            urgency_keywords = ["hurry", "last chance", "act now", "midnight", "hours", "seats left", "slots left", "gone forever", "disappears"]
            if any(uk in text_lower for uk in urgency_keywords):
                continue
            if not any(i in text_lower for i in ("renewal", "mandate", "grace period", "authorization")):
                continue
        return record
    return None


def get_all_deadlines() -> list[DeadlineRecord]:
    """Return all deadline records. Used for the demo/testing."""
    return list(_DEADLINE_RECORDS.values())
