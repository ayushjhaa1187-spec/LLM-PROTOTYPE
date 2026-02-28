"""Document database model with processing status tracking."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AccessLevel(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    ADMIN_ONLY = "admin_only"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)  # bytes
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.UPLOADED, nullable=False)
    chunk_count = Column(Integer, default=0)
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.PUBLIC, nullable=False)
    tags = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="documents")
