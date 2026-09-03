from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models import (
    Action,
    Decision,
    Flag,
    InterceptRequest,
    Message,
    ReviewAction,
)
from engine import process_message
from crud import (
    create_message,
    create_decision,
    get_all_messages,
    get_review_queue,
    get_audit_log as read_audit_log,
    clear_db,
    get_message_by_id,
    get_latest_decision_for_message,
)
from database import get_db, SessionLocal
from event_manager import sse_manager
from audit_log import write_decision, clear_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/stream")
async def sse_stream():
    """Server-Sent Events endpoint for real-time frontend updates."""
    return StreamingResponse(sse_manager.subscribe(), media_type="text/event-stream")


@router.post("/intercept")
async def intercept_message(request: InterceptRequest, db: Session = Depends(get_db)) -> dict:
    message = Message(
        content=request.content,
        agent_id=request.agent_id,
    )

    # Persist the message payload immediately to SQLite
    create_message(db, message)

    # Process pipeline (which persists the Decision automatically),
    # passing this request's injected session through — see engine.py's
    # docstring for why process_message must never open its own.
    decision = await process_message(message, db)

    # Fire SSE broadcast
    sse_manager.publish({
        "event": "NEW_INTERCEPT",
        "message_id": message.id,
        "action": decision.action.value
    })

    return {
        "message_id": message.id,
        "content": message.content,
        "agent_id": message.agent_id,
        "timestamp": message.timestamp,
        "decision": decision.model_dump(),
    }


@router.get("/messages")
async def get_messages(db: Session = Depends(get_db)) -> list[dict]:
    return get_all_messages(db)


@router.get("/review")
async def get_review_queue_route(db: Session = Depends(get_db)) -> list[dict]:
    return get_review_queue(db)


@router.post("/review/{message_id}/approve")
async def approve_message(message_id: str, action: ReviewAction, db: Session = Depends(get_db)) -> dict:
    message_db = get_message_by_id(db, message_id)
    if not message_db:
        raise HTTPException(status_code=404, detail="Message not found")

    # Uses the latest-decision lookup, not the unreliable .decision
    # relationship — see get_latest_decision_for_message's docstring.
    latest_decision = get_latest_decision_for_message(db, message_id)
    if not latest_decision or latest_decision.action != "held":
        raise HTTPException(
            status_code=400,
            detail="Message is not currently held for review"
        )
        
    # Rehydrate the Pydantic flag objects from DB
    flags = [Flag(category=f.category, confidence=f.confidence, quoted_span=f.quoted_span, cleared_by_allowlist=f.cleared_by_allowlist, suggested_rewrite=f.suggested_rewrite) for f in latest_decision.flags]

    approval_decision = Decision(
        message_id=message_id,
        flags=flags, # Copy old flags
        action=Action.APPROVED,
        reviewer_id=action.reviewer_id,
        review_notes=action.notes,
    )

    # Write to the append-only audit trail BEFORE updating queryable state
    # or broadcasting — same ordering invariant as the intercept pipeline.
    write_decision(approval_decision)
    create_decision(db, approval_decision)
    
    # Broadcast to SSE
    sse_manager.publish({
        "event": "DECISION_UPDATED",
        "message_id": message_id,
        "action": Action.APPROVED.value
    })

    return {
        "message_id": message_id,
        "action": "approved",
        "decision": approval_decision.model_dump(),
    }


@router.post("/review/{message_id}/reject")
async def reject_message(message_id: str, action: ReviewAction, db: Session = Depends(get_db)) -> dict:
    message_db = get_message_by_id(db, message_id)
    if not message_db:
        raise HTTPException(status_code=404, detail="Message not found")

    latest_decision = get_latest_decision_for_message(db, message_id)
    if not latest_decision or latest_decision.action != "held":
        raise HTTPException(
            status_code=400,
            detail="Message is not currently held for review"
        )

    # Rehydrate the Pydantic flag objects from DB
    flags = [Flag(category=f.category, confidence=f.confidence, quoted_span=f.quoted_span, cleared_by_allowlist=f.cleared_by_allowlist, suggested_rewrite=f.suggested_rewrite) for f in latest_decision.flags]

    rejection_decision = Decision(
        message_id=message_id,
        flags=flags, 
        action=Action.REJECTED,
        reviewer_id=action.reviewer_id,
        review_notes=action.notes,
    )

    write_decision(rejection_decision)
    create_decision(db, rejection_decision)

    # Broadcast to SSE
    sse_manager.publish({
        "event": "DECISION_UPDATED",
        "message_id": message_id,
        "action": Action.REJECTED.value
    })

    return {
        "message_id": message_id,
        "action": "rejected",
        "decision": rejection_decision.model_dump(),
    }


@router.get("/audit-log")
async def get_audit_log_route(limit: int = 200, db: Session = Depends(get_db)) -> list[dict]:
    return read_audit_log(db, limit)


@router.post("/reset")
async def reset_state(db: Session = Depends(get_db)) -> dict:
    clear_db(db)
    clear_log()  # Keep the JSONL audit trail and SQLite state in sync on demo reset.
    # Broadcast reset
    sse_manager.publish({
        "event": "RESET_STATE",
    })
    return {"status": "reset"}
