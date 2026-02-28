"""RAG service: retrieval-augmented generation with citation extraction."""

import time
from openai import OpenAI

from app.config import settings
from app.services import vector_store


def _get_query_embedding(query: str) -> list[float]:
    """Generate embedding for a query string."""
    # Embedding still uses OpenAI as it's the standard for our vector store chunks
    # Alternatively, could add more embedding providers if needed.
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

    system_prompt = """You are an elite US Federal Procurement & Compliance Expert. Your goal is to provide authoritative, highly accurate, and professional guidance based EXCLUSIVELY on the provided source documents.

RULES FOR SUCCESS:
1. **Source-Only Content**: Every statement must be derived from the provided context. If the context is insufficient, explicitly state: "The provided documents do not contain information regarding [Topic]."
2. **Dense Inline Citations**: Every fact, number, date, or specific requirement MUST be followed by an inline citation like [1], [2]. If multiple sources support a claim, use [1][2].
3. **Professional Tone**: Use clear, formal, and objective language. Structure your answer logically with headings if appropriate.
4. **Specific References**: Always include section numbers, clause IDs (e.g., "FAR 52.212-4"), and dates exactly as they appear in the sources.
5. **Transparency**: If a source is ambiguous or contradictory, highlight this to the user rather than choosing one interpretation.
6. **"Sources Used" Section**: Conclude with a clear list of all cited documents, including their source filename and page number.

ANTI-HALLUCINATION PROTOCOL:
- Never assume knowledge outside the provided context.
- Never "guess" a section number or page.
- If you find a partial match, explain the limitation.

EXAMPLE FORMAT:
Based on the Federal Acquisition Regulation [1], the micro-purchase threshold is currently set at $10,000 for most supplies [1][2]. However, under specific emergency conditions, this limit may be increased as outlined in Section 13.201 [3].

Sources Used:
[1] FAR_Part_13.pdf (Page 4)
[2] Procurement_Memo_2023.docx (Page 1)
[3] Emergency_Provisions.pdf (Page 12)"""

    user_prompt = f"""Source Documents:
{context_str}

---

Question: {query}

Provide a detailed, accurate answer with inline citations [1], [2], etc. referencing the source documents above."""

    from app.utils.llm_client import get_llm_client, get_model_name
    client = get_llm_client()
    model = get_model_name()
    
    response = client.chat.completions.create(
        model=model,
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
