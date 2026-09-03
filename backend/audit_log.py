"""
Append-only audit log for Consent Guard.

Every classification decision — send, hold, approve, reject — is written
to this log BEFORE the corresponding side-effecting action occurs. That
ordering invariant is non-negotiable: if the system crashes between
logging and acting, we lose the action but keep the record. The reverse
(acting without recording) would make the system unauditable.

Implementation: JSON-lines file. Each line is a self-contained JSON
object representing one Decision. This is append-only at the application
level — we never seek backwards, never overwrite, never delete lines.
It is NOT cryptographically tamper-proof (that would be scope creep for
a hackathon demo), so we call it "append-only," not "immutable."
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Optional

from models import Decision

# Default path — can be overridden for testing.
_DEFAULT_LOG_PATH = Path(__file__).parent / "data" / "audit_log.jsonl"

# Thread lock to ensure atomic appends in a multi-request context.
_write_lock = threading.Lock()


def _ensure_log_dir(log_path: Path) -> None:
    """Create the log directory if it doesn't exist."""
    log_path.parent.mkdir(parents=True, exist_ok=True)


def write_decision(decision: Decision, log_path: Optional[Path] = None) -> None:
    """
    Append a decision to the audit log.

    Why this happens before any side-effect: if we crash after logging
    but before sending/holding, we have a record of intent. If we crash
    after acting but before logging, we have an unrecorded action —
    which is the one thing an audit tool must never allow.

    The file is opened in append mode ('a') — we never open in write
    mode ('w'), which would truncate existing entries.
    """
    path = log_path or _DEFAULT_LOG_PATH
    _ensure_log_dir(path)

    entry = decision.model_dump()

    with _write_lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def read_log(log_path: Optional[Path] = None, limit: int = 500) -> list[dict]:
    """
    Read the audit log, most-recent-first.

    Returns raw dicts, not Decision objects, because the log reader
    may be queried by the frontend which needs JSON-serializable data.
    """
    path = log_path or _DEFAULT_LOG_PATH

    if not path.exists():
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines — don't crash the reader
                    # because one entry got corrupted.
                    continue

    # Most recent first for the UI ledger.
    entries.reverse()
    return entries[:limit]


def clear_log(log_path: Optional[Path] = None) -> None:
    """
    Clear the audit log. ONLY used for testing and demo resets —
    never in production operation.

    Why this exists at all: during the hackathon demo, the presenter
    needs to reset state between runs. This is a deliberate escape
    hatch, not a normal operation.
    """
    path = log_path or _DEFAULT_LOG_PATH
    if path.exists():
        os.remove(path)
