import hmac
import hashlib
import json
import logging
from typing import Dict, Any, List
import httpx
from sqlalchemy.orm import Session
from app.models.webhook import WebhookSubscription

logger = logging.getLogger(__name__)

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC SHA-256 signature for webhook payload."""
    sig = hmac.new(
        secret.encode("utf-8"), 
        payload.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest()
    return f"sha256={sig}"

async def dispatch_event(db: Session, event_type: str, payload_dict: Dict[str, Any]):
    """Dispatch an event asynchronously to all subscribed webhooks."""
    subs = db.query(WebhookSubscription).filter(WebhookSubscription.is_active == True).all()
    
    payload_str = json.dumps(payload_dict)
    
    async with httpx.AsyncClient() as client:
        for sub in subs:
            if "*" in sub.events or event_type in sub.events:
                headers = {"Content-Type": "application/json"}
                if sub.secret_key:
                    headers["X-Webhook-Signature"] = generate_signature(payload_str, sub.secret_key)
                
                try:
                    await client.post(sub.target_url, content=payload_str, headers=headers, timeout=5.0)
                except Exception as e:
                    logger.error(f"Failed to deliver webhook {event_type} to {sub.target_url}: {e}")
