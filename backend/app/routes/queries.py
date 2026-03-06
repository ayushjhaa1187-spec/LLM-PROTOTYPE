"""Query and RAG conversation routes (SEC-02).

Includes multi-turn conversation support, result streaming (SSE), and secure query handling.
"""

import time
import json
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.core import security
from app.core.audit import AuditLogger
from app.models.query import QueryRecord
from app.models.conversation import Conversation
from app.agents.orchestrator import run_pipeline
from pydantic import BaseModel
from app.services.webhooks import dispatch_event

router = APIRouter(prefix="/api/v1/queries", tags=["queries"])


class QueryRequest(BaseModel):
    query: str
    document_ids: Optional[List[int]] = None
    conversation_id: Optional[int] = None


class QueryResponse(BaseModel):
    id: int
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    processing_time_ms: int
    is_blocked: bool
    blocking_reason: Optional[str]
    contract_analysis: Optional[Dict[str, Any]] = None
    compliance_analysis: Optional[Dict[str, Any]] = None


@router.post("/", response_model=QueryResponse)
async def ask_query(
    request: Request,
    query_in: QueryRequest,
    db: Session = Depends(get_db),
    user: security.User = Depends(security.get_current_user)
):
    """Securely ask a RAG query with multi-agent orchestration and audit logging."""
    start_time = time.time()
    
    # 1. Execute Pipeline (Day 1-3 SEC-02)
    result = run_pipeline(query_in.query, document_ids=query_in.document_ids, user_id=user.id)
    
    # 2. Handle Multi-turn Conversation
    conv_id = query_in.conversation_id
    if not conv_id:
        # Create new conversation
        conv = Conversation(user_id=user.id, title=query_in.query[:50])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id
        
    # 3. Create Query Record (Day 1 Audit Trail)
    total_ms = int((time.time() - start_time) * 1000)
    query_rec = QueryRecord(
        user_id=user.id,
        conversation_id=conv_id,
        query_text=query_in.query,
        response_text=result["answer"],
        citations=result.get("citations", []),
        confidence_score=result["confidence"],
        tokens_used=result.get("tokens_used", 0),
        processing_time_ms=total_ms,
        agent_logs=result.get("agent_logs", []),
        hallucination_detected=1.0 if (result.get("verification", {}).get("hallucinations") or result.get("is_blocked")) else 0.0,
        requires_review=1.0 if result.get("is_blocked") else 0.0
    )
    
    db.add(query_rec)
    db.commit()
    db.refresh(query_rec)
    
    # 4. Audit log (SEC-03)
    AuditLogger.log(
        db, user.id, "QUERY", "query", 
        {"id": query_rec.id, "confidence": result["confidence"], "blocked": result.get("is_blocked")}, 
        request.client.host
    )
    
    # 5. Webhook Events
    try:
        await dispatch_event(db, "query.completed", {
            "id": query_rec.id, 
            "confidence": result["confidence"], 
            "blocked": result.get("is_blocked", False)
        })
        if result.get("is_blocked"):
            await dispatch_event(db, "compliance.failed", {
                "query_id": query_rec.id,
                "blocking_reason": result.get("blocking_reason")
            })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to dispatch event: {e}")
    
    return {
        "id": query_rec.id,
        "answer": result["answer"],
        "confidence": result["confidence"],
        "citations": result.get("citations", []),
        "processing_time_ms": total_ms,
        "is_blocked": result.get("is_blocked", False),
        "blocking_reason": result.get("blocking_reason"),
        "contract_analysis": result.get("contract_analysis"),
        "compliance_analysis": result.get("compliance_analysis")
    }


@router.get("/conversations", response_model=List[Dict[str, Any]])
async def list_conversations(
    db: Session = Depends(get_db),
    user: security.User = Depends(security.get_current_user)
):
    """List conversations for the current user."""
    convs = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc()).all()
    return [{"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in convs]


@router.get("/conversations/{conv_id}", response_model=Dict[str, Any])
async def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    user: security.User = Depends(security.get_current_user)
):
    """Retrieve history of a specific conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    queries = db.query(QueryRecord).filter(QueryRecord.conversation_id == conv_id).order_by(QueryRecord.created_at.asc()).all()
    
    messages = []
    for q in queries:
        messages.append({"role": "user", "text": q.query_text, "timestamp": q.created_at.isoformat()})
        messages.append({"role": "assistant", "text": q.response_text, "timestamp": q.created_at.isoformat(), "citations": q.citations, "confidence": q.confidence_score})
        
    return {
        "id": conv.id,
        "title": conv.title,
        "messages": messages
    }
