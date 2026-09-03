from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    content = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 1:1 relationship
    decision = relationship("DecisionDB", back_populates="message", uselist=False, order_by="desc(DecisionDB.timestamp)")

class DecisionDB(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    message_id = Column(String, ForeignKey("messages.id"))
    action = Column(String, nullable=False)
    reviewer_id = Column(String, nullable=True)
    review_notes = Column(String, nullable=True)

    message = relationship("MessageDB", back_populates="decision")
    flags = relationship("FlagDB", back_populates="decision")

class FlagDB(Base):
    __tablename__ = "flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String, ForeignKey("decisions.id"))
    category = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    quoted_span = Column(String, nullable=False)
    cleared_by_allowlist = Column(Boolean, default=False)
    suggested_rewrite = Column(String, nullable=True)

    decision = relationship("DecisionDB", back_populates="flags")
