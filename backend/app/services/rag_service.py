"""RAG service: retrieval-augmented generation with citation extraction."""

import time
from openai import OpenAI

from app.config import settings
from app.services import vector_store


def _get_query_embedding(query: str) -> list[float]:
    """Generate embedding for a query string."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
    )
    return response.data[0].embedding


def retrieve_relevant_chunks(query: str, k: int = 5, document_ids: list[str] = None) -> list[dict]:
    """Retrieve the top-k most relevant document chunks for a query."""
    embedding = _get_query_embedding(query)
    where_filter = {"doc_id": document_ids} if document_ids else None
    results = vector_store.search(query_embedding=embedding, k=k, where_filter=where_filter)
    return results


def generate_response(query: str, context_chunks: list[dict]) -> dict:
    """Generate a response using the LLM with retrieved context.

    Returns dict with: answer, citations, confidence, tokens_used
    """
    if not context_chunks:
        return {
            "answer": "I don't have any documents to reference. Please upload relevant documents first.",
            "citations": [],
            "confidence": 0.0,
            "tokens_used": 0,
        }

    # Build context string with numbered references
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        source = chunk["metadata"].get("source", "Unknown")
        page = chunk["metadata"].get("page", "?")
        context_parts.append(f"[{i + 1}] (Source: {source}, Page {page})\n{chunk['text']}")

    context_str = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are a US federal procurement compliance expert assistant.

RULES:
1. Answer ONLY based on the provided source documents below.
2. For EVERY claim or fact, include an inline citation like [1], [2], etc. that references the source document number.
3. If the sources don't contain enough information, say so explicitly — do NOT make up information.
4. Be specific: cite section numbers (e.g., "FAR 19.502-2") when they appear in the sources.
5. End your response with a "Sources Used" section listing which document references you cited.

IMPORTANT: Never invent or hallucinate information. If uncertain, state your uncertainty."""

    user_prompt = f"""Source Documents:
{context_str}

---

Question: {query}

Provide a detailed, accurate answer with inline citations [1], [2], etc. referencing the source documents above."""

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=2000,
    )

    answer = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else 0

    # Extract citations from the response by mapping [N] references
    citations = _extract_citations(answer, context_chunks)

    # Calculate confidence from retrieval distances
    avg_distance = sum(c.get("distance", 1.0) for c in context_chunks) / len(context_chunks)
    # ChromaDB cosine distance: 0 = identical, 2 = opposite. Convert to 0-1 confidence.
    confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))

    return {
        "answer": answer,
        "citations": citations,
        "confidence": round(confidence, 3),
        "tokens_used": tokens_used,
    }


def _extract_citations(answer: str, context_chunks: list[dict]) -> list[dict]:
    """Extract citation references from the answer and map to source metadata."""
    import re
    # Find all [N] references in the answer
    cited_indices = set()
    for match in re.finditer(r'\[(\d+)\]', answer):
        idx = int(match.group(1)) - 1  # Convert to 0-indexed
        if 0 <= idx < len(context_chunks):
            cited_indices.add(idx)

    citations = []
    for idx in sorted(cited_indices):
        chunk = context_chunks[idx]
        meta = chunk.get("metadata", {})
        citations.append({
            "ref": idx + 1,
            "source": meta.get("source", "Unknown"),
            "page": meta.get("page", 0),
            "text": chunk["text"][:300],  # First 300 chars as preview
            "confidence": round(1.0 - (chunk.get("distance", 1.0) / 2.0), 3),
        })

    return citations
