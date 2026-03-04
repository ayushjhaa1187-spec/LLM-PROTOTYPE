"""Document version tracking model for regulation change history."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    change_summary = Column(Text, nullable=True)
    changed_by = Column(String, ForeignKey("users.id"), nullable=True)
    file_hash = Column(String, nullable=True)  # SHA-256 of file contents
    metadata_json = Column(JSON, default=dict)  # Additional version metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    document = relationship("Document", back_populates="versions")
