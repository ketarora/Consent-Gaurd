from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models_db import MessageDB, DecisionDB, FlagDB
from models import Message, Decision, Flag, Action


def _parse_ts(iso_string: str) -> datetime:
    """
    Convert the Pydantic models' ISO-8601 timestamp strings into real
    Python datetime objects for SQLAlchemy's DateTime columns.

    Why this exists: Message.timestamp and Decision.timestamp are stored
    as strings on the Pydantic side (so they serialize cleanly to JSON
    for the API and the JSONL audit log), but SQLite's DateTime column
    type only accepts actual datetime objects — passing the raw string
    through raises a TypeError at insert time.
    """
    return datetime.fromisoformat(iso_string)


def create_message(db: Session, message: Message):
    db_msg = MessageDB(
        id=message.id,
        content=message.content,
        agent_id=message.agent_id,
        timestamp=_parse_ts(message.timestamp),
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

def create_decision(db: Session, decision: Decision):
    db_decision = DecisionDB(
        id=decision.id,
        timestamp=_parse_ts(decision.timestamp),
        message_id=decision.message_id,
        action=decision.action.value,
        reviewer_id=decision.reviewer_id,
        review_notes=decision.review_notes,
    )
    db.add(db_decision)
    db.commit()
    
    for flag in decision.flags:
        db_flag = FlagDB(
            decision_id=decision.id,
            category=flag.category.value,
            confidence=flag.confidence,
            quoted_span=flag.quoted_span,
            cleared_by_allowlist=flag.cleared_by_allowlist,
            suggested_rewrite=flag.suggested_rewrite,
        )
        db.add(db_flag)
        
    db.commit()
    return db_decision

def get_message_by_id(db: Session, msg_id: str):
    return db.query(MessageDB).filter(MessageDB.id == msg_id).first()


def get_latest_decision_for_message(db: Session, message_id: str) -> DecisionDB | None:
    """
    Return the MOST RECENT decision row for a message, not an arbitrary one.

    Why this exists: a message accumulates multiple Decision rows over its
    life — an initial 'held' decision from the pipeline, then a later
    'approved' or 'rejected' decision once a reviewer acts. MessageDB.decision
    was declared as a one-to-one relationship (uselist=False), which is
    wrong for this data shape — SQLAlchemy would non-deterministically
    return ONE of the matching rows, which meant an approved message could
    still appear to be 'held' depending on which row it happened to pick.
    Every place that needs "what's this message's current status" must go
    through this function, ordered explicitly by timestamp, not through
    the .decision relationship attribute.
    """
    return (
        db.query(DecisionDB)
        .filter(DecisionDB.message_id == message_id)
        .order_by(desc(DecisionDB.timestamp))
        .first()
    )


def _serialize_decision(d: DecisionDB) -> dict:
    flags = [
        {
            "category": f.category,
            "confidence": f.confidence,
            "quoted_span": f.quoted_span,
            "cleared_by_allowlist": f.cleared_by_allowlist,
            "suggested_rewrite": f.suggested_rewrite,
        }
        for f in d.flags
    ]
    return {
        "id": d.id,
        "timestamp": str(d.timestamp.isoformat()),
        "message_id": d.message_id,
        "action": d.action,
        "reviewer_id": d.reviewer_id,
        "review_notes": d.review_notes,
        "flags": flags,
    }


def get_all_messages(db: Session, limit: int = 200):
    msgs = db.query(MessageDB).order_by(desc(MessageDB.timestamp)).limit(limit).all()
    out = []
    for m in msgs:
        latest = get_latest_decision_for_message(db, m.id)
        out.append({
            "id": m.id,
            "content": m.content,
            "agent_id": m.agent_id,
            "timestamp": str(m.timestamp.isoformat()),
            "decision": _serialize_decision(latest) if latest else None,
        })
    return out


def get_review_queue(db: Session):
    """
    Messages whose LATEST decision is 'held' — not messages that were
    EVER held at some point in their history. A message approved after
    being held must not reappear here just because its old 'held' row
    still exists in the decisions table.
    """
    # Subquery: the most recent decision timestamp per message_id.
    latest_ts_subq = (
        db.query(
            DecisionDB.message_id,
            func.max(DecisionDB.timestamp).label("max_ts"),
        )
        .group_by(DecisionDB.message_id)
        .subquery()
    )

    latest_decisions = (
        db.query(DecisionDB)
        .join(
            latest_ts_subq,
            (DecisionDB.message_id == latest_ts_subq.c.message_id)
            & (DecisionDB.timestamp == latest_ts_subq.c.max_ts),
        )
        .filter(DecisionDB.action == "held")
        .all()
    )

    out = []
    for d in latest_decisions:
        m = db.query(MessageDB).filter(MessageDB.id == d.message_id).first()
        if m is None:
            continue
        out.append({
            "id": m.id,
            "content": m.content,
            "agent_id": m.agent_id,
            "timestamp": str(m.timestamp.isoformat()),
            "decision": _serialize_decision(d),
        })
    out.sort(key=lambda x: x["timestamp"], reverse=True)
    return out

def get_audit_log(db: Session, limit: int = 500):
    decisions = db.query(DecisionDB).order_by(desc(DecisionDB.timestamp)).limit(limit).all()
    out = []
    for d in decisions:
        flags = [{"category": f.category, "confidence": f.confidence, "quoted_span": f.quoted_span, "cleared_by_allowlist": f.cleared_by_allowlist, "suggested_rewrite": f.suggested_rewrite} for f in d.flags]
        out.append({
            "id": d.id,
            "timestamp": str(d.timestamp.isoformat()),
            "message_id": d.message_id,
            "action": d.action,
            "reviewer_id": d.reviewer_id,
            "review_notes": d.review_notes,
            "flags": flags
        })
    return out

def clear_db(db: Session):
    db.query(FlagDB).delete()
    db.query(DecisionDB).delete()
    db.query(MessageDB).delete()
    db.commit()
