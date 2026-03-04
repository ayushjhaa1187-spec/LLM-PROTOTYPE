"""Semantic caching layer for LLM responses.

Caches query-response pairs using embedding similarity to avoid
redundant LLM calls for semantically similar questions.
"""

import hashlib
import json
import os
import time
import threading
from pathlib import Path

import numpy as np

from app.config import settings

_CACHE_FILE = os.path.join(settings.CHROMA_PERSIST_DIR, "semantic_cache.json")
_EMBEDDING_CACHE_FILE = os.path.join(settings.CHROMA_PERSIST_DIR, "embedding_cache.json")
_lock = threading.Lock()

# Similarity threshold for cache hits (cosine similarity)
CACHE_SIMILARITY_THRESHOLD = 0.95


def _load_cache() -> dict:
    """Load semantic cache from disk."""
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"entries": []}


def _save_cache(cache: dict):
    """Persist semantic cache to disk."""
    Path(os.path.dirname(_CACHE_FILE)).mkdir(parents=True, exist_ok=True)
    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def _load_embedding_cache() -> dict:
    """Load embedding cache from disk."""
    if os.path.exists(_EMBEDDING_CACHE_FILE):
        try:
            with open(_EMBEDDING_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_embedding_cache(cache: dict):
    """Persist embedding cache to disk."""
    Path(os.path.dirname(_EMBEDDING_CACHE_FILE)).mkdir(parents=True, exist_ok=True)
    with open(_EMBEDDING_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def _text_hash(text: str) -> str:
    """Generate a SHA-256 hash for a text string."""
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


def get_cached_embedding(text: str) -> list[float] | None:
    """Get cached embedding for a text string, if available."""
    text_key = _text_hash(text)
    cache = _load_embedding_cache()
    return cache.get(text_key)


def cache_embedding(text: str, embedding: list[float]):
    """Cache an embedding for a text string."""
    with _lock:
        cache = _load_embedding_cache()
        text_key = _text_hash(text)
        cache[text_key] = embedding
        # Keep cache size reasonable (max 10000 entries)
        if len(cache) > 10000:
            keys = list(cache.keys())
            for old_key in keys[:1000]:
                del cache[old_key]
        _save_embedding_cache(cache)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def search_cache(query_embedding: list[float]) -> dict | None:
    """Search semantic cache for a similar query.

    Returns cached response if found within similarity threshold, else None.
    """
    if not settings.ENABLE_SEMANTIC_CACHE:
        return None

    cache = _load_cache()
    best_match = None
    best_similarity = 0.0

    now = time.time()

    for entry in cache["entries"]:
        # Check TTL
        if now - entry.get("timestamp", 0) > settings.SEMANTIC_CACHE_TTL_SECONDS:
            continue

        similarity = _cosine_similarity(query_embedding, entry["query_embedding"])
        if similarity > best_similarity and similarity >= CACHE_SIMILARITY_THRESHOLD:
            best_similarity = similarity
            best_match = entry

    if best_match:
        return {
            "answer": best_match["answer"],
            "citations": best_match["citations"],
            "confidence": best_match["confidence"],
            "tokens_used": 0,
            "cache_hit": True,
            "cache_similarity": round(best_similarity, 4),
        }

    return None


def add_to_cache(query_embedding: list[float], query_text: str, response: dict):
    """Add a query-response pair to the semantic cache."""
    if not settings.ENABLE_SEMANTIC_CACHE:
        return

    with _lock:
        cache = _load_cache()

        entry = {
            "query_text": query_text,
            "query_embedding": query_embedding,
            "answer": response.get("answer", ""),
            "citations": response.get("citations", []),
            "confidence": response.get("confidence", 0.0),
            "timestamp": time.time(),
        }

        cache["entries"].append(entry)

        # Evict old entries (keep max 500)
        now = time.time()
        cache["entries"] = [
            e for e in cache["entries"]
            if now - e.get("timestamp", 0) <= settings.SEMANTIC_CACHE_TTL_SECONDS
        ][-500:]

        _save_cache(cache)
