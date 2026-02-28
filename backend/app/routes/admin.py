"""Admin API routes: stats, user management, audit logs."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.document import Document
from app.models.query import QueryRecord
from app.models.audit import AuditLog
from app.services import vector_store
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _user_to_dict(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role.value if hasattr(u.role, "value") else u.role,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else "",
    }


@router.get("/stats")
def get_system_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """System-wide stats for the admin dashboard."""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    total_users = db.query(User).count()
    total_docs = db.query(Document).count()
    total_queries = db.query(QueryRecord).count()
    queries_today = db.query(QueryRecord).filter(QueryRecord.created_at >= day_ago).count()

    # Token cost calculation (GPT-4o-mini pricing: ~$0.15/1M input, ~$0.60/1M output)
    all_queries = db.query(QueryRecord).all()
    total_tokens = sum(q.tokens_used or 0 for q in all_queries)
    estimated_cost = round(total_tokens / 1_000_000 * 0.40, 2)  # blended avg

    avg_confidence = 0.0
    avg_response_time = 0
    if all_queries:
        avg_confidence = round(
            sum(q.confidence_score or 0 for q in all_queries) / len(all_queries), 3
        )
        avg_response_time = int(
            sum(q.processing_time_ms or 0 for q in all_queries) / len(all_queries)
        )

    vec_stats = vector_store.get_collection_stats()

    return {
        "total_users": total_users,
        "total_documents": total_docs,
        "total_queries": total_queries,
        "queries_today": queries_today,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
        "avg_confidence": avg_confidence,
        "avg_response_time_ms": avg_response_time,
        "vector_chunks": vec_stats["total_chunks"],
    }


@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return [_user_to_dict(u) for u in users]


class UpdateUserRoleRequest(BaseModel):
    role: str


@router.put("/users/{user_id}")
def update_user_role(
    user_id: str,
    body: UpdateUserRoleRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Update a user's role (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        new_role = UserRole(body.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
        )

    user.role = new_role
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="UPDATE_USER_ROLE",
        resource=user_id,
        detail=f"Changed role to {new_role.value}",
    ))
    db.commit()

    return _user_to_dict(user)


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Deactivate a user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="DEACTIVATE_USER",
        resource=user_id,
    ))
    db.commit()

    return {"detail": "User deactivated"}


@router.get("/audit-logs")
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get audit logs (filterable by action)."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource": log.resource,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        }
        for log in logs
    ]
