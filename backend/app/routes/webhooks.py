from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import secrets

from app.database import get_db
from app.core import security
from app.utils.security import UserRole, require_role
from app.models.webhook import WebhookSubscription

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

class WebhookCreate(BaseModel):
    target_url: str
    events: List[str]

class WebhookResponse(BaseModel):
    id: int
    target_url: str
    events: List[str]
    is_active: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=WebhookResponse)
def create_webhook(
    body: WebhookCreate,
    current_user: security.User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Register a new webhook subscription (Admin only)."""
    # Generate a strong secret key for HMAC signature
    secret_key = secrets.token_hex(32)
    
    sub = WebhookSubscription(
        user_id=current_user.id,
        target_url=body.target_url,
        events=body.events,
        secret_key=secret_key
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    # Return secret key ONLY once upon creation
    return {
        "id": sub.id,
        "target_url": sub.target_url,
        "events": sub.events,
        "is_active": sub.is_active,
        "secret_key": secret_key
    }

@router.get("/", response_model=List[WebhookResponse])
def list_webhooks(
    current_user: security.User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """List all active webhook subscriptions."""
    return db.query(WebhookSubscription).all()

@router.delete("/{sub_id}")
def delete_webhook(
    sub_id: int,
    current_user: security.User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a webhook subscription."""
    sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
        
    db.delete(sub)
    db.commit()
    return {"detail": "Webhook deleted successfully"}
