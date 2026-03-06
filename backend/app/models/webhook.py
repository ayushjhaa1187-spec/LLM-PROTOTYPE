"""Webhook definitions for external system integrations."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True) # nullable for system webhooks
    target_url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)  # List of event types like ["document.created", "query.resolved"]
    secret_key = Column(String(128))       # For HMAC signature
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
