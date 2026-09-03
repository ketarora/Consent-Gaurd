import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Action, DarkPatternCategory, Decision, Flag, Message
from models_db import Base
from crud import create_message, create_decision, get_audit_log, get_all_messages

# Use an in-memory SQLite database for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def _make_pydantic_msg(msg_id: str) -> Message:
    return Message(
        id=msg_id,
        content="Test content",
        agent_id="test-agent",
    )

def _make_pydantic_decision(msg_id: str, action: Action, category: DarkPatternCategory = None) -> Decision:
    flags = []
    if category:
        flags.append(Flag(
            category=category,
            confidence=0.9,
            quoted_span="test span",
        ))

    return Decision(
        message_id=msg_id,
        flags=flags,
        action=action,
    )

def test_write_read_roundtrip(db_session):
    """Test inserting a message and a decision with flags, and reading it back."""
    # 1. Create a message
    msg = _make_pydantic_msg("msg-123")
    create_message(db_session, msg)

    # 2. Create decision
    dec = _make_pydantic_decision("msg-123", Action.HELD, DarkPatternCategory.FALSE_URGENCY)
    create_decision(db_session, dec)

    # 3. Read Audit log
    logs = get_audit_log(db_session)
    assert len(logs) == 1
    assert logs[0]["message_id"] == "msg-123"
    assert logs[0]["action"] == "held"
    assert len(logs[0]["flags"]) == 1
    assert logs[0]["flags"][0]["category"] == "false_urgency"
