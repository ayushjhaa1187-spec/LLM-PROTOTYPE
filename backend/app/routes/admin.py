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


@router.post("/seed-datasets")
def trigger_seed_datasets(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Trigger background seeding of external procurement and GDP datasets."""
    import threading
    from scripts.seed_datasets import seed_datasets
    
    # Run in background to avoid timeout
    thread = threading.Thread(target=seed_datasets)
    thread.start()
    
    return {"detail": "Dataset seeding triggered in background"}


class SECIngestRequest(BaseModel):
    ticker: str

@router.post("/ingest/sec")
def ingest_sec_data(
    body: SECIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Download and process latest 10-K for a ticker."""
    import threading
    from app.services.ingestors import ingest_sec_10k
    
    thread = threading.Thread(target=ingest_sec_10k, args=(body.ticker, db, current_user.id))
    thread.start()
    return {"detail": f"SEC ingestion for {body.ticker} started"}


class HFIngestRequest(BaseModel):
    dataset_name: str
    limit: int = 50

@router.post("/ingest/hf")
def ingest_hf_data(
    body: HFIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Pull data from Hugging Face into the knowledge base."""
    import threading
    from app.services.ingestors import ingest_hf_dataset
    
    thread = threading.Thread(target=ingest_hf_dataset, args=(body.dataset_name, None, "train", body.limit, db, current_user.id))
    thread.start()
    return {"detail": f"Hugging Face ingestion for {body.dataset_name} started"}


class CourtListenerIngestRequest(BaseModel):
    query: str
    limit: int = 3

@router.post("/ingest/courtlistener")
def ingest_cl_data(
    body: CourtListenerIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Search and pull case law from CourtListener."""
    import threading
    from app.services.ingestors import ingest_courtlistener
    
    thread = threading.Thread(target=ingest_courtlistener, args=(body.query, db, current_user.id, body.limit))
    thread.start()
    return {"detail": f"CourtListener ingestion for '{body.query}' started"}

class KaggleIngestRequest(BaseModel):
    dataset_slug: str
    limit: int = 50

@router.post("/ingest/kaggle")
def ingest_kaggle_data(
    body: KaggleIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Download and pull data from Kaggle."""
    import threading
    from app.services.ingestors import ingest_kaggle_dataset
    
    thread = threading.Thread(target=ingest_kaggle_dataset, args=(body.dataset_slug, db, current_user.id))
    thread.start()
    return {"detail": f"Kaggle ingestion for {body.dataset_slug} started"}

class PubMedIngestRequest(BaseModel):
    query: str
    limit: int = 5

@router.post("/ingest/pubmed")
def ingest_pubmed_data(
    body: PubMedIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Pull scientific abstracts from PubMed."""
    import threading
    from app.services.ingestors import ingest_pubmed
    
    thread = threading.Thread(target=ingest_pubmed, args=(body.query, db, current_user.id, body.limit))
    thread.start()
    return {"detail": f"PubMed ingestion for '{body.query}' started"}

class SpecializedIngestRequest(BaseModel):
    platform: str # fineweb, cosmopedia, the_stack, etc.

@router.post("/ingest/specialized")
def ingest_specialized_data(
    body: SpecializedIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Trigger ingestion for specialized high-scale datasets."""
    import threading
    from app.services.ingestors import ingest_specialized_llm_data
    
    thread = threading.Thread(target=ingest_specialized_llm_data, args=(body.platform, db, current_user.id))
    thread.start()
    return {"detail": f"Specialized ingestion for {body.platform} started"}

class RegIngestRequest(BaseModel):
    region: str # EU, US, etc.

@router.post("/ingest/regulations")
def ingest_reg_data(
    body: RegIngestRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Trigger ingestion for regional regulatory frameworks."""
    import threading
    from app.services.ingestors import ingest_regulatory_frameworks
    
    thread = threading.Thread(target=ingest_regulatory_frameworks, args=(body.region, db, current_user.id))
    thread.start()
    return {"detail": f"Regulatory ingestion for {body.region} started"}


@router.get("/llm-config")
def get_llm_config(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Return current LLM provider and available providers (with key presence)."""
    return {
        "current_provider": settings.LLM_PROVIDER,
        "providers": {
            "openai": {"has_key": bool(settings.OPENAI_API_KEY)},
            "groq": {"has_key": bool(settings.GROQ_API_KEY)},
            "together": {"has_key": bool(settings.TOGETHER_API_KEY)},
            "gemini": {"has_key": bool(settings.GEMINI_API_KEY)},
            "mistral": {"has_key": bool(settings.MISTRAL_API_KEY)},
            "openrouter": {"has_key": bool(settings.OPENROUTER_API_KEY)},
        }
    }


class UpdateLLMProviderRequest(BaseModel):
    provider: str


@router.put("/llm-config")
def update_llm_provider(
    body: UpdateLLMProviderRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Update the active LLM provider (runtime only, doesn't persist to .env)."""
    valid = ["openai", "groq", "together", "gemini", "mistral", "openrouter"]
    if body.provider not in valid:
         raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of {valid}")
    
    settings.LLM_PROVIDER = body.provider
    return {"detail": f"LLM provider updated to {body.provider}", "current": settings.LLM_PROVIDER}


@router.get("/discovery")
def get_dataset_discovery(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Return catalog of premium training/RAG datasets for discovery."""
    from app.services import discovery
    return {
        "datasets": discovery.get_recommended_datasets(),
        "platforms": discovery.get_platform_links()
    }


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
