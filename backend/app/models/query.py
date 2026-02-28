"""Query record database model for tracking RAG queries and responses."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON

from app.database import Base


class QueryRecord(Base):
    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    citations = Column(JSON, default=list)  # [{source, page, text, confidence}]
    confidence_score = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    agent_logs = Column(JSON, default=list)  # [{step, status, time, output}]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    from sqlalchemy.orm import relationship
    user = relationship("User", back_populates="queries")
