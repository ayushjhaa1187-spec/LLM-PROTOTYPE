"""Research agent: retrieves relevant document chunks from vector store."""

import time
from app.services.rag_service import retrieve_relevant_chunks


def run(query: str, k: int = 5, document_ids: list[str] = None) -> dict:
    """Execute the research step: query the vector DB and return ranked chunks.

    Returns:
        dict with keys: chunks (list), step_log (dict)
    """
    start = time.time()

    chunks = retrieve_relevant_chunks(query, k=k, document_ids=document_ids)

    # Apply Authority Weighting: Boost chunks from regulation/law sources
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        tags = meta.get("tags") or []
        filename = meta.get("source", "").lower()
        
        # Determine weighting boost (1.2x for regulatory sources)
        weight = 1.0
        if any(t in tags for t in ["compliance", "law", "regulation", "statute"]):
            weight = 1.2
        if any(k in filename for k in ["gdpr", "ccpa", "hipaa", "ai_act", "act_", "law_"]):
            weight = 1.3  # Official frameworks get higher boost
            
        # Adjust internal rank if distance is available
        if "distance" in chunk:
            chunk["distance"] = chunk["distance"] / weight

    # Re-sort after weighting
    chunks = sorted(chunks, key=lambda x: x.get("distance", 1.0))

    elapsed_ms = int((time.time() - start) * 1000)

    step_log = {
        "step": "research",
        "name": "Search Vector DB",
        "status": "completed",
        "time_ms": elapsed_ms,
        "output": {
            "chunks_found": len(chunks),
            "top_sources": [
                {
                    "source": c["metadata"].get("source", "?"),
                    "page": c["metadata"].get("page", "?"),
                    "score": round(1.0 - (c.get("distance", 1.0) / 2.0), 3),
                }
                for c in chunks[:3]
            ],
        },
        "logs": [
            f"Querying vector DB with k={k}",
            f"Found {len(chunks)} relevant chunks",
        ] + [
            f"Top match: {c['metadata'].get('source', '?')} p.{c['metadata'].get('page', '?')} "
            f"(Score: {round(1.0 - (c.get('distance', 1.0) / 2.0), 2)})"
            for c in chunks[:3]
        ],
    }

    return {"chunks": chunks, "step_log": step_log}
