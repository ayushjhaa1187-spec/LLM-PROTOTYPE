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
