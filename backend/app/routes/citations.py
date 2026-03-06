from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core import security
from app.agents import verifier
from app.models.query import QueryRecord

router = APIRouter(prefix="/api/v1/citations", tags=["citations"])

class VerifyRequest(BaseModel):
    answer: str
    chunks: List[Dict[str, Any]]

@router.post("/verify")
def verify_citations(
    body: VerifyRequest,
    current_user: security.User = Depends(security.get_current_user),
):
    """Verify citations against provided source chunks."""
    result = verifier.run(body.answer, [], body.chunks)
    return {
        "verification_rate": result.get("verification_rate", 0),
        "hallucinations": result.get("hallucinations", []),
        "verified_claims": result.get("verified_claims", []),
        "step_log": result.get("step_log", {})
    }

@router.get("/{query_id}")
def get_query_citations(
    query_id: int,
    current_user: security.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Get citations for a specific query."""
    query = db.query(QueryRecord).filter(QueryRecord.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
        
    return {
        "query_id": query.id,
        "citations": query.citations,
        "hallucination_detected": query.hallucination_detected,
        "requires_review": query.requires_review
    }
