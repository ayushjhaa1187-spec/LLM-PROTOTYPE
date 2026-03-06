"""Multi-agent orchestrator: Research → Draft → Verify → Red Team → Score pipeline.

Integrates semantic caching, robust citation verification, and adversarial testing.
"""

import time
import asyncio
from typing import List, Optional, Dict, Any

from app.config import settings
from app.services import semantic_cache
from app.core.citation_verification import verify_citations_robust
from app.agents import research_agent, drafting_agent, verifier, red_team_agent, contract_agent, compliance_agent


def run_pipeline(query: str, document_ids: List[int] = None, user_id: int = None) -> Dict[str, Any]:
    """Execute the full multi-agent RAG pipeline with semantic caching and safety checks."""
    pipeline_start = time.time()
    agent_logs: List[Dict[str, Any]] = []

    # ── Step 0: Semantic Cache Check ────────────────────────────────
    if settings.ENABLE_SEMANTIC_CACHE:
        # We need an embedding for the query to search the semantic cache
        from app.services import rag_service
        query_embedding = rag_service._get_query_embedding(query)
        
        cached_res = semantic_cache.search_cache(query_embedding)
        if cached_res:
            total_ms = int((time.time() - pipeline_start) * 1000)
            cached_res["processing_time_ms"] = total_ms
            cached_res["agent_logs"] = [{
                "step": "cache",
                "name": "Semantic Cache",
                "status": "hit",
                "time_ms": total_ms,
                "output": {"similarity": cached_res.get("cache_similarity")}
            }]
            return cached_res

    # ── Step 1: Research (Retrieve Chunks) ──────────────────────────
    research_result = research_agent.run(query, k=8, document_ids=document_ids)
    agent_logs.append(research_result["step_log"])
    chunks = research_result["chunks"]

    if not chunks:
        total_ms = int((time.time() - pipeline_start) * 1000)
        return {
            "answer": "I couldn't find any relevant documents to answer your question. Please ensure the relevant regulations are uploaded.",
            "confidence": 0.0,
            "processing_time_ms": total_ms,
            "agent_logs": agent_logs,
            "is_blocked": False,
            "blocking_reason": None,
            "contract_analysis": None,
            "compliance_analysis": None
        }

    # ── Step 2: Draft (Generate Answer) ─────────────────────────────
    draft_result = drafting_agent.run(query, chunks)
    agent_logs.append(draft_result["step_log"])
    answer = draft_result["answer"]
    citations = draft_result["citations"]

    # ── Step 3: Verify (Semantic & Pattern Checks) ──────────────────
    # A. Semantic Verification (existing LLM-based)
    verify_result = verifier.run(answer=answer, citations=citations, chunks=chunks)
    agent_logs.append(verify_result["step_log"])
    
    # B. Robust Citation Verification (Regex & Metadata - Day 1 Fix)
    robust_verify = verify_citations_robust(answer, chunks)
    agent_logs.append({
        "step": "verify_robust",
        "name": "Robust Citation Check",
        "status": "completed",
        "output": {
            "confidence": robust_verify["overall_confidence"],
            "hallucinations": [h.citation for h in robust_verify["hallucinations"]],
            "blocking_reason": robust_verify["blocking_reason"]
        }
    })

    # ── Step 4: Red Team (Adversarial Testing) ──────────────────────
    red_team_result = red_team_agent.run(answer, chunks, query)
    agent_logs.append(red_team_result["step_log"])

    # ── Step 5: Final Scoring & Safety Blocking ─────────────────────
    score_start = time.time()
    
    # Combine signals: retrieval confidence, semantic verification, robust verification, red team score
    retrieval_conf = draft_result.get("confidence", 0.5)
    semantic_conf = verify_result.get("verification_rate", 0.0)
    robust_conf = robust_verify["overall_confidence"]
    red_team_conf = red_team_result["adversarial_score"]
    
    # Weighted Blend
    final_confidence = (
        (retrieval_conf * 0.2) + 
        (semantic_conf * 0.3) + 
        (robust_conf * 0.2) + 
        (red_team_conf * 0.3)
    )
    
    # SAFETY BLOCKING (Day 1 ISSUE #2)
    # Block if red team says "FAIL" or confidence is extremely low
    blocked = False
    blocking_reason = None
    
    if red_team_result["should_block"]:
        blocked = True
        blocking_reason = f"Red Team: {red_team_result['recommendation']}"
    elif final_confidence < settings.CONFIDENCE_THRESHOLD:
        blocked = True
        blocking_reason = f"Low Confidence: {final_confidence:.2f} < {settings.CONFIDENCE_THRESHOLD}"
    elif robust_verify["hallucinations"]:
        blocked = True
        blocking_reason = f"Unverified Citations detected: {', '.join([h.citation for h in robust_verify['hallucinations']])}"

    if blocked and settings.BLOCK_LOW_CONFIDENCE:
        answer = f"I cannot confidently answer this question based on the provided documents. Reason: {blocking_reason}"
        final_confidence = min(final_confidence, 0.4) # Forced low

    # ── Step 6: Enterprise Audit (Contract & Compliance Agents) ─────
    contract_result = None
    compliance_result = None
    
    if document_ids:
        try:
            from app.services.vector_store import get_document_chunks
            import concurrent.futures
            
            # Fetch the uploaded document's full text
            str_ids = [str(did) for did in document_ids]
            doc_chunks = get_document_chunks(str_ids)
            doc_text = "\n".join([c["text"] for c in doc_chunks])
            
            # Fetch the retrieved regulatory texts
            context_str = "\n".join([c["text"] for c in chunks])
            
            # Run concurrent secondary analysis if the document exists
            if doc_text:
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    f1 = executor.submit(contract_agent.run, doc_text[:15000], context_str[:15000])
                    f2 = executor.submit(compliance_agent.run, query, context_str[:15000] + "\n\nDoc: " + doc_text[:15000])
                    
                    contract_result = f1.result(timeout=30)
                    compliance_result = f2.result(timeout=30)
        except Exception as e:
            print(f"Enterprise Audit Agent Error: {e}")

    score_ms = int((time.time() - score_start) * 1000)
    total_ms = int((time.time() - pipeline_start) * 1000)

    result = {
        "answer": answer,
        "citations": citations,
        "confidence": round(final_confidence, 3),
        "tokens_used": draft_result.get("tokens_used", 0),
        "processing_time_ms": total_ms,
        "agent_logs": agent_logs,
        "verification": robust_verify,
        "red_team": red_team_result,
        "is_blocked": blocked,
        "blocking_reason": blocking_reason,
        "contract_analysis": contract_result,
        "compliance_analysis": compliance_result
    }

    # Add to Semantic Cache if it was a high-confidence valid answer
    if settings.ENABLE_SEMANTIC_CACHE and not blocked and final_confidence > 0.8:
        semantic_cache.add_to_cache(query_embedding, query, result)

    return result
