"""Multi-agent orchestrator: Research → Draft → Verify → Score pipeline."""

import time


def run_pipeline(query: str, document_ids: list[str] = None) -> dict:
    """Execute the full multi-agent RAG pipeline.

    Steps:
    1. Research — retrieve relevant chunks from vector DB
    2. Draft — generate response with citations
    3. Verify — check citations against sources
    4. Score — calculate final confidence

    Returns complete result with answer, citations, confidence, agent_logs, timing.
    """
    from app.agents import research_agent, drafting_agent, verifier

    pipeline_start = time.time()
    agent_logs: list[dict] = []

    # ── Step 1: Research ────────────────────────────────────────────
    research_result = research_agent.run(query, k=6, document_ids=document_ids)
    agent_logs.append(research_result["step_log"])
    chunks = research_result["chunks"]

    if not chunks:
        # No documents found — return early
        agent_logs.append({
            "step": "draft",
            "name": "Draft Response",
            "status": "skipped",
            "time_ms": 0,
            "logs": ["No relevant documents found — skipping generation"],
        })
        total_ms = int((time.time() - pipeline_start) * 1000)
        return {
            "answer": "I couldn't find any relevant documents to answer your question. "
                      "Please upload relevant regulation documents first.",
            "citations": [],
            "confidence": 0.0,
            "tokens_used": 0,
            "processing_time_ms": total_ms,
            "agent_logs": agent_logs,
            "verification": {"verified": [], "hallucinations": [], "verification_rate": 0.0},
        }

    # ── Step 2: Draft ───────────────────────────────────────────────
    draft_result = drafting_agent.run(query, chunks)
    agent_logs.append(draft_result["step_log"])

    # ── Step 3: Verify ──────────────────────────────────────────────
    verify_result = verifier.run(
        answer=draft_result["answer"],
        citations=draft_result["citations"],
        chunks=chunks,
    )
    agent_logs.append(verify_result["step_log"])

    # ── Step 4: Score (compute final confidence) ────────────────────
    score_start = time.time()

    # Blend retrieval confidence with verification rate
    retrieval_confidence = draft_result["confidence"]
    verification_rate = verify_result["verification_rate"]
    final_confidence = (retrieval_confidence * 0.4) + (verification_rate * 0.6)

    # Penalize if hallucinations were found
    if verify_result["hallucinations"]:
        penalty = len(verify_result["hallucinations"]) * 0.10  # Increased penalty
        final_confidence = max(0.0, final_confidence - penalty)

    final_confidence = round(final_confidence, 3)

    score_ms = int((time.time() - score_start) * 1000)
    agent_logs.append({
        "step": "score",
        "name": "Calculate Confidence",
        "status": "completed",
        "time_ms": score_ms,
        "output": {
            "retrieval_confidence": retrieval_confidence,
            "verification_rate": round(verification_rate, 3),
            "final_confidence": final_confidence,
        },
        "logs": [
            f"Retrieval confidence: {retrieval_confidence}",
            f"Verification rate: {round(verification_rate, 3)}",
            f"Hallucinations detected: {len(verify_result['hallucinations'])}",
            f"Final blended confidence: {final_confidence}",
        ],
    })

    total_ms = int((time.time() - pipeline_start) * 1000)

    return {
        "answer": draft_result["answer"],
        "citations": draft_result["citations"],
        "confidence": final_confidence,
        "tokens_used": draft_result["tokens_used"],
        "processing_time_ms": total_ms,
        "agent_logs": agent_logs,
        "verification": {
            "claims": verify_result["results"],
            "verified_count": len(verify_result["verified_claims"]),
            "hallucination_count": len(verify_result["hallucinations"]),
            "verification_rate": round(verification_rate, 3),
        },
    }
