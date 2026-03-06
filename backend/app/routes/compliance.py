"""FAR Compliance workflow routes for the three hero workflows.

Hero Workflows:
1. Part 19: Small Business Set-Aside Eligibility
2. Part 22: Labor Standards Compliance
3. Part 39: IT/Cybersecurity Requirements
"""

import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from app.config import settings
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.core import security
from app.core.audit import AuditLogger
from app.models.query import QueryRecord
from app.agents import orchestrator
from app.utils.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


# ── Structured Models ──────────────────────────────────────────────

class Citation(BaseModel):
    ref: int
    source: str
    page: int = 0
    text: str = ""
    confidence: float = 0.0
    section_id: str = ""


class ComplianceResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: float
    is_blocked: bool = False
    blocking_reason: str = ""
    workflow: str = ""
    processing_time_ms: int = 0
    agent_logs: List[Dict[str, Any]] = []
    verification: Dict[str, Any] = {}
    red_team: Dict[str, Any] = {}


class SetAsideRequest(BaseModel):
    business_description: str = Field(..., min_length=10)
    naics_code: str = ""
    annual_revenue: float = 0.0
    employee_count: int = 0
    document_ids: Optional[List[int]] = None


class LaborStandardsRequest(BaseModel):
    contract_description: str = Field(..., min_length=10)
    contract_value: float = 0.0
    location: str = ""
    worker_type: str = ""
    document_ids: Optional[List[int]] = None


class ITCyberRequest(BaseModel):
    system_description: str = Field(..., min_length=10)
    data_classification: str = ""  # CUI, classified, unclassified
    impact_level: str = ""  # low, moderate, high
    cloud_deployment: bool = False
    document_ids: Optional[List[int]] = None


# ── Internal Executor ──────────────────────────────────────────────

def _run_compliance_workflow(query: str, workflow_name: str, document_ids: List[int], 
                           user: security.User, db: Session, request: Request) -> Dict[str, Any]:
    """Execute a structured compliance workflow with orchestration and auditing."""
    start_time = time.time()
    
    # 1. Pipeline Execution
    result = orchestrator.run_pipeline(query, document_ids=document_ids, user_id=user.id)
    
    total_ms = int((time.time() - start_time) * 1000)
    
    # 2. Record keeping
    query_rec = QueryRecord(
        user_id=user.id,
        query_text=query,
        response_text=result["answer"],
        citations=result.get("citations", []),
        confidence_score=result["confidence"],
        tokens_used=result.get("tokens_used", 0),
        processing_time_ms=total_ms,
        agent_logs=result.get("agent_logs", []),
        hallucination_detected=1.0 if result.get("is_blocked") else 0.0,
        requires_review=1.0 if result.get("is_blocked") else 0.0
    )
    db.add(query_rec)
    
    # 3. Audit Log (Day 1 SEC-03)
    AuditLogger.log(
        db, user.id, f"COMPLIANCE_{workflow_name.upper()}", "workflow",
        {"id": query_rec.id, "confidence": result["confidence"], "blocked": result.get("is_blocked")},
        request.client.host
    )
    
    db.commit()
    
    return {
        "answer": result["answer"],
        "citations": result.get("citations", []),
        "confidence": result["confidence"],
        "is_blocked": result.get("is_blocked", False),
        "blocking_reason": result.get("blocking_reason", ""),
        "workflow": workflow_name,
        "processing_time_ms": total_ms,
        "agent_logs": result.get("agent_logs", []),
        "verification": result.get("verification", {}),
        "red_team": result.get("red_team", {})
    }


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/set-aside-eligibility", response_model=ComplianceResponse)
@limiter.limit(settings.RATE_LIMIT)
async def check_set_aside(
    request: Request,
    body: SetAsideRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    query = f"""Analyze Part 19 Small Business Set-Aside Eligibility.
Business: {body.business_description}
NAICS: {body.naics_code}
Revenue: ${body.annual_revenue:,.2f}
Employees: {body.employee_count}
Focus: FAR 19.102 Size Standards, 19.502 Set-Aside criteria, Socioeconomic eligibility (8(a), HUBZone, WOSB)."""
    return _run_compliance_workflow(query, "set_aside", body.document_ids, current_user, db, request)


@router.post("/labor-standards", response_model=ComplianceResponse)
@limiter.limit(settings.RATE_LIMIT)
async def check_labor(
    request: Request,
    body: LaborStandardsRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    query = f"""Analyze Part 22 Labor Standards Compliance.
Contract: {body.contract_description}
Value: ${body.contract_value:,.2f}
Location: {body.location}
Type: {body.worker_type}
Focus: Davis-Bacon (FAR 22.403), SCA (FAR 22.10), EEO (FAR 22.8), Wage Determinations."""
    return _run_compliance_workflow(query, "labor_standards", body.document_ids, current_user, db, request)


@router.post("/it-cyber", response_model=ComplianceResponse)
@limiter.limit(settings.RATE_LIMIT)
async def check_cyber(
    request: Request,
    body: ITCyberRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    query = f"""Analyze Part 39 IT/Cybersecurity Requirements.
System: {body.system_description}
Classification: {body.data_classification}
Impact: {body.impact_level}
Cloud: {'Yes' if body.cloud_deployment else 'No'}
Focus: FedRAMP (FAR 39.101), NIST 800-171, CMMC, DFARS 252.204-7012, Section 508."""
    return _run_compliance_workflow(query, "it_cyber", body.document_ids, current_user, db, request)
