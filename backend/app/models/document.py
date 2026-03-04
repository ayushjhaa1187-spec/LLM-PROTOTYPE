"""Document database model for tracking processing and metadata.

Updated to match the security-hardened Requirements.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


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
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
