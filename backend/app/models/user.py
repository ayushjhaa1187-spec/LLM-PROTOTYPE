"""User database model with role-based access control.

Updated to match the security-hardened requirements (SEC-02).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String(20), default="analyst", nullable=False)  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    token_revoked_at = Column(DateTime, nullable=True)

    # Relationships (lazy="dynamic" for large sets)
    documents = relationship("Document", back_populates="owner")
    queries = relationship("QueryRecord", back_populates="user")
