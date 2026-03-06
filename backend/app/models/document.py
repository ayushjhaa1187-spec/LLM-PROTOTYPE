"""Document database model for tracking processing and metadata.

Updated to match the security-hardened Requirements.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


import enum

class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AccessLevel(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"
    ADMIN_ONLY = "admin_only"

class SourceType(str, enum.Enum):
    USER_UPLOAD = "user_upload"
    REGULATION = "regulation"
    POLICY = "policy"
    EXTERNAL_DATASET = "external_dataset"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, txt, xml
    file_size = Column(Integer, nullable=False)  # bytes
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, failed
    chunk_count = Column(Integer, default=0)
    access_level = Column(String(20), default="public")  # public, private, admin_only
    
    # Metadata for RAG (Day 1 Secure Doc Handling)
    sha256 = Column(String(64), unique=True, nullable=True)
    metadata_json = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    
    source_type = Column(String(50), nullable=True)
    source_system = Column(String(50), nullable=True)
    part_number = Column(String(20), nullable=True)
    tags = Column(JSON, default=list)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
