"""Audit log database model with cryptographic hash chaining.

Important for FAR/DFARS compliance and maintaining an immutable record of actions.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)  # nullable for unauthenticated actions
    action = Column(String, nullable=False)  # LOGIN, UPLOAD, QUERY, etc.
    resource = Column(String, nullable=True)  # what was acted upon
    metadata = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Security: Cryptographic integrity (Day 1 SEC-03)
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), unique=True)
    signature = Column(String(128))
    is_finalized = Column(Boolean, default=False)
