"""Audit log database model for tracking all user actions."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, JSON

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # nullable for unauthenticated actions
    action = Column(String, nullable=False)  # LOGIN, UPLOAD, QUERY, etc.
    resource = Column(String, nullable=True)  # what was acted upon
    detail = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
