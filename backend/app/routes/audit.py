import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core import security
from app.utils.security import UserRole, require_role
from app.models.audit import AuditLog
from app.core.audit import AuditLogger

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    meta_data: Optional[dict]
    ip_address: Optional[str]
    previous_hash: Optional[str]
    entry_hash: Optional[str]
    signature: Optional[str]
    is_finalized: bool

    class Config:
        from_attributes = True

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: security.User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Access audit logs (Admin/Compliance Officer only)."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
        
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/reports/export")
def export_audit_report(
    action: Optional[str] = None,
    current_user: security.User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Export audit logs as CSV for compliance reporting."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
        
    logs = query.order_by(AuditLog.timestamp.desc()).limit(1000).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'User ID', 'Action', 'Resource', 'IP Address', 'Entry Hash', 'Signature'])
    
    for log in logs:
        writer.writerow([
            log.id, 
            log.timestamp.isoformat() if log.timestamp else "", 
            log.user_id, 
            log.action, 
            log.resource, 
            log.ip_address,
            log.entry_hash,
            log.signature
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=audit_report_{datetime.now().strftime('%Y%m%d')}.csv"
    return response


@router.get("/verify-chain")
def verify_audit_chain(
    limit: int = Query(100, ge=1, le=1000),
    current_user: security.User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Verify the cryptographic integrity of the audit log chain."""
    is_valid = AuditLogger.verify_chain(db, limit=limit)
    return {
        "status": "success" if is_valid else "failed",
        "message": "Audit chain is intact." if is_valid else "Audit chain integrity verification failed! Tampering detected."
    }
