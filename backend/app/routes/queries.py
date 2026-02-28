"""Query API routes: run RAG pipeline, get history."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.query import QueryRecord
from app.models.audit import AuditLog
from app.models.user import User
from app.agents import orchestrator
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str
    document_ids: list[str] = []

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query is too short (minimum 3 characters)")
        if len(v) > 2000:
            raise ValueError("Query is too long (maximum 2000 characters)")
        return v


def _query_to_dict(q: QueryRecord) -> dict:
    return {
        "id": q.id,
        "user_id": q.user_id,
        "query_text": q.query_text,
        "response_text": q.response_text,
        "citations": q.citations or [],
        "confidence_score": q.confidence_score,
        "tokens_used": q.tokens_used,
        "processing_time_ms": q.processing_time_ms,
        "agent_logs": q.agent_logs or [],
        "created_at": q.created_at.isoformat() if q.created_at else "",
    }


@router.post("")
def run_query(
    body: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run the full multi-agent RAG pipeline on a user query."""
    from app.models.document import Document, AccessLevel
    
    # Get user's accessible documents
    query = db.query(Document.id)
    if current_user.role.value != "admin":
        query = query.filter(
            (Document.access_level == AccessLevel.PUBLIC) |
            (Document.owner_id == current_user.id)
        )
    accessible_docs = {row[0] for row in query.all()}
    
    # Check if a specific subset is requested
    if body.document_ids:
        unauthorized = set(body.document_ids) - accessible_docs
        if unauthorized:
            raise HTTPException(status_code=403, detail="Access denied to one or more selected documents")
        search_doc_ids = body.document_ids
    else:
        search_doc_ids = list(accessible_docs)
    
    try:
        result = orchestrator.run_pipeline(body.query, document_ids=search_doc_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    # Save query record
    record = QueryRecord(
        user_id=current_user.id,
        query_text=body.query,
        response_text=result["answer"],
        citations=result["citations"],
        confidence_score=result["confidence"],
        tokens_used=result["tokens_used"],
        processing_time_ms=result["processing_time_ms"],
        agent_logs=result["agent_logs"],
    )
    db.add(record)

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="RAG_QUERY",
        resource=record.id,
        detail=body.query[:200],
    ))
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "answer": result["answer"],
        "citations": result["citations"],
        "confidence": result["confidence"],
        "tokens_used": result["tokens_used"],
        "processing_time_ms": result["processing_time_ms"],
        "agent_logs": result["agent_logs"],
        "verification": result["verification"],
    }


@router.get("/history")
def query_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's query history."""
    queries = (
        db.query(QueryRecord)
        .filter(QueryRecord.user_id == current_user.id)
        .order_by(QueryRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_query_to_dict(q) for q in queries]


@router.get("/{query_id}")
def get_query(
    query_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single query's details (including full agent logs)."""
    record = db.query(QueryRecord).filter(QueryRecord.id == query_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Query not found")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _query_to_dict(record)
