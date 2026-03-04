"""Immutable audit logging service with cryptographic integrity.

Ensures that every user action is logged with a hash chain and signature
for non-repudiation and compliance.
"""

import hashlib
import hmac
import json
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models.audit import AuditLog


class AuditLogger:
    """Service to create and verify cryptographically signed audit logs."""

    @staticmethod
    def log(
        db: Session,
        user_id: Optional[int],
        action: str,
        resource: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create a new signed audit log entry."""
        # Get the previous entry's hash for the chain
        last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_log.entry_hash if last_log else "0" * 64

        timestamp = datetime.utcnow()
        meta_json = json.dumps(metadata or {}, sort_keys=True)
        
        # Calculate entry hash
        raw_data = f"{user_id}:{action}:{resource}:{timestamp}:{meta_json}:{prev_hash}"
        entry_hash = hashlib.sha256(raw_data.encode()).hexdigest()
        
        # Create signature using secret key
        signature = hmac.new(
            settings.AUDIT_SECRET_KEY.encode(),
            entry_hash.encode(),
            hashlib.sha512
        ).hexdigest()
        
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            metadata=metadata or {},
            ip_address=ip_address,
            timestamp=timestamp,
            previous_hash=prev_hash,
            entry_hash=entry_hash,
            signature=signature,
            is_finalized=True
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def verify_chain(db: Session, limit: int = 100) -> bool:
        """Verify the integrity of recent audit logs."""
        logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
        # In reverse order (descending ID), so we check against previous
        for i in range(len(logs) - 1):
            if logs[i].previous_hash != logs[i+1].entry_hash:
                return False
        return True
