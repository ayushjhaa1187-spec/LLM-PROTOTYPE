"""Verification agent: checks every citation claim against source documents."""

import re
import time
from thefuzz import fuzz


def _normalize(text: str) -> str:
    """Normalize text for comparison: lowercase, collapse whitespace."""
    return re.sub(r'\s+', ' ', text.lower().strip())


def _extract_claims(answer: str) -> list[dict]:
    """Extract individual claims from the answer, each with their citation refs.

    A 'claim' is a sentence or clause that contains a [N] citation.
    """
    claims = []
    # Split by sentences (handling abbreviations roughly)
    sentences = re.split(r'(?<=[.!?])\s+', answer)

    for sentence in sentences:
        refs = re.findall(r'\[(\d+)\]', sentence)
        if refs:
            # Clean the sentence of citation markers for comparison
            clean = re.sub(r'\[\d+\]', '', sentence).strip()
            if len(clean) > 10:  # Skip trivially short claims
                claims.append({
                    "text": clean,
                    "refs": [int(r) for r in refs],
                    "original": sentence.strip(),
                })

    return claims


def run(answer: str, citations: list[dict], chunks: list[dict]) -> dict:
    """Execute the verification step: check each claim against source documents.

    For each claim with a citation [N]:
    - Find the referenced chunk
    - Fuzzy-match the claim text against the chunk text
    - Flag as verified (score >= 60) or hallucination (score < 60)

    Returns:
        dict with keys: verified, hallucinations, verification_summary, step_log
    """
    start = time.time()

    claims = _extract_claims(answer)
    verified: list[dict] = []
    hallucinations: list[dict] = []
    logs: list[str] = [f"Extracted {len(claims)} claims with citations"]

    for claim in claims:
        best_score = 0
        best_source = ""
        best_ref = 0

        for ref_num in claim["refs"]:
            idx = ref_num - 1  # Convert to 0-indexed
            if 0 <= idx < len(chunks):
                chunk_text = chunks[idx]["text"]
                # Use token_set_ratio for best partial matching
                score = fuzz.token_set_ratio(
                    _normalize(claim["text"]),
                    _normalize(chunk_text),
                )
                if score > best_score:
                    best_score = score
                    best_source = chunk_text[:200]
                    best_ref = ref_num

        entry = {
            "claim": claim["text"],
            "original": claim["original"],
            "ref": best_ref,
            "match_score": best_score / 100.0,
            "source_snippet": best_source,
        }

        if best_score >= 60:
            entry["status"] = "verified"
            verified.append(entry)
            logs.append(f"✓ Claim verified against [{best_ref}] (score: {best_score}%)")
        else:
            entry["status"] = "hallucination"
            hallucinations.append(entry)
            logs.append(f"✗ HALLUCINATION detected: \"{claim['text'][:60]}...\" (score: {best_score}%)")

    elapsed_ms = int((time.time() - start) * 1000)

    # Overall verification rate
    total = len(verified) + len(hallucinations)
    verification_rate = len(verified) / total if total > 0 else 1.0

    step_log = {
        "step": "verify",
        "name": "Verify Citations",
        "status": "completed",
        "time_ms": elapsed_ms,
        "output": {
            "total_claims": total,
            "verified_count": len(verified),
            "hallucination_count": len(hallucinations),
            "verification_rate": round(verification_rate, 3),
        },
        "logs": logs,
    }

    return {
        "verified": verified,
        "hallucinations": hallucinations,
        "verification_rate": verification_rate,
        "step_log": step_log,
    }
