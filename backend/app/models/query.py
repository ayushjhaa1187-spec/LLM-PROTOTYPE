"""Query record database model for tracking RAG queries.

Updated to match the security-hardened requirements (SEC-02).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class QueryRecord(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    citations = Column(JSON, default=list)  # [{source, citation, verified, confidence}]
    confidence_score = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    agent_logs = Column(JSON, default=list)  # [{agent, step, output}]
    
    # Metadata for RAG (Day 1 Citation Integrity)
    hallucination_detected = Column(Float, default=0.0)
    requires_review = Column(Float, default=0.0)
    
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="queries")
    conversation = relationship("Conversation", back_populates="messages")
