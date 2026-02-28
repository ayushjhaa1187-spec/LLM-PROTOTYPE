"""Pure-Python vector store using numpy for cosine similarity search.

Persists to a JSON file on disk — no external DB or C++ compilation needed.
Drop-in replacement for ChromaDB with the same API surface.
"""

import json
import os
import threading
from pathlib import Path

import numpy as np

from app.config import settings

_STORE_FILE = os.path.join(settings.CHROMA_PERSIST_DIR, "vectors.json")
_lock = threading.Lock()


def _load_store() -> dict:
    """Load the vector store from disk."""
    if os.path.exists(_STORE_FILE):
        try:
            with open(_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}


def _save_store(store: dict):
    """Persist the vector store to disk."""
    Path(os.path.dirname(_STORE_FILE)).mkdir(parents=True, exist_ok=True)
    with open(_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f)


def add_chunks(
    doc_id: str,
    chunks: list[str],
    metadatas: list[dict],
    embeddings: list[list[float]],
) -> int:
    """Add document chunks with embeddings to the vector store."""
    with _lock:
        store = _load_store()

        for i in range(len(chunks)):
            chunk_id = f"{doc_id}__chunk_{i}"

            # Skip if already exists (idempotent)
            if chunk_id in store["ids"]:
                continue

            store["ids"].append(chunk_id)
            store["documents"].append(chunks[i])
            store["metadatas"].append(metadatas[i])
            store["embeddings"].append(embeddings[i])

        _save_store(store)
        return len(chunks)


def search(
    query_embedding: list[float],
    k: int = 5,
    where_filter: dict | None = None,
) -> list[dict]:
    """Search for similar chunks by embedding vector using cosine similarity.

    Returns list of dicts: {id, text, metadata, distance}
    """
    store = _load_store()

    if not store["embeddings"]:
        return []

    # Filter by metadata if requested
    indices = list(range(len(store["ids"])))
    if where_filter:
        filtered = []
        for i in indices:
            meta = store["metadatas"][i]
            match = True
            for k_, v in where_filter.items():
                meta_v = meta.get(k_)
                if isinstance(v, list):
                    if meta_v not in v:
                        match = False
                        break
                elif meta_v != v:
                    match = False
                    break
            if match:
                filtered.append(i)
        indices = filtered

    if not indices:
        return []

    # Compute cosine similarity
    query_vec = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []
    query_vec = query_vec / query_norm

    similarities = []
    for i in indices:
        doc_vec = np.array(store["embeddings"][i], dtype=np.float32)
        doc_norm = np.linalg.norm(doc_vec)
        if doc_norm == 0:
            similarities.append((i, 2.0))  # max distance
            continue
        cos_sim = float(np.dot(query_vec, doc_vec / doc_norm))
        # Convert similarity to distance (0 = identical, 2 = opposite)
        distance = 1.0 - cos_sim
        similarities.append((i, distance))

    # Sort by distance (ascending = most similar first)
    similarities.sort(key=lambda x: x[1])

    results = []
    for i, distance in similarities[:k]:
        results.append({
            "id": store["ids"][i],
            "text": store["documents"][i],
            "metadata": store["metadatas"][i],
            "distance": round(distance, 6),
        })

    return results


def delete_document(doc_id: str):
    """Delete all chunks for a given document."""
    with _lock:
        store = _load_store()

        keep_indices = [
            i for i, mid in enumerate(store["metadatas"])
            if mid.get("doc_id") != doc_id
        ]

        store["ids"] = [store["ids"][i] for i in keep_indices]
        store["documents"] = [store["documents"][i] for i in keep_indices]
        store["metadatas"] = [store["metadatas"][i] for i in keep_indices]
        store["embeddings"] = [store["embeddings"][i] for i in keep_indices]

        _save_store(store)


def get_collection_stats() -> dict:
    """Return stats about the vector store."""
    store = _load_store()
    return {
        "total_chunks": len(store["ids"]),
        "collection_name": "gov_documents",
    }
