"""Drafting agent: generates a response with inline citations from retrieved chunks."""

import time
from app.services.rag_service import generate_response


def run(query: str, chunks: list[dict]) -> dict:
    """Execute the drafting step: generate a citation-backed response.

    Returns:
        dict with keys: answer, citations, confidence, tokens_used, step_log
    """
    start = time.time()

    result = generate_response(query, chunks)

    elapsed_ms = int((time.time() - start) * 1000)

    step_log = {
        "step": "draft",
        "name": "Draft Response",
        "status": "completed",
        "time_ms": elapsed_ms,
        "output": {
            "answer_length": len(result["answer"]),
            "citations_count": len(result["citations"]),
            "tokens_used": result["tokens_used"],
        },
        "logs": [
            f"Generating draft with {len(chunks)} context chunks",
            f"Draft completed in {elapsed_ms}ms",
            f"Response contains {len(result['citations'])} citations",
            f"Tokens used: {result['tokens_used']}",
        ],
    }

    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "confidence": result["confidence"],
        "tokens_used": result["tokens_used"],
        "step_log": step_log,
    }
