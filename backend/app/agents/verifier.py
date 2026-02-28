import re
import time
from thefuzz import fuzz
from openai import OpenAI
from app.config import settings


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


def _llm_verify_claim(claim_text: str, context_text: str) -> dict:
    """Use an LLM to semantically verify if a claim is supported by the context.
    
    Returns: { "verified": bool, "score": float, "reasoning": str }
    """
    from app.utils.llm_client import get_llm_client, get_model_name
    client = get_llm_client()
    model = get_model_name()
    
    prompt = f"""You are a Fact-Checking Agent (Red Team).
Your task is to verify if the 'Claim' below is supported by the 'Source Context'.

Claim: "{claim_text}"
Source Context: "{context_text}"

INSTRUCTIONS:
1. Determine if the Claim is directly supported, partially supported, or not supported (hallucinated).
2. Assign a confidence score from 0.0 to 1.0 (1.0 = perfect support).
3. Provide a very brief reasoning (max 15 words).

OUTPUT FORMAT (JSON):
{{
  "verified": true/false,
  "score": 0.0-1.0,
  "reasoning": "Reasoning string"
}}

Strictly output valid JSON only."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        import json
        result = json.loads(response.choices[0].message.content or "{}")
        return {
            "verified": result.get("verified", False),
            "score": result.get("score", 0.0),
            "reasoning": result.get("reasoning", "Unknown error during verification")
        }
    except Exception as e:
        return {
            "verified": False,
            "score": 0.0,
            "reasoning": f"Verification failed: {str(e)}"
        }


def run(answer: str, citations: list[dict], chunks: list[dict]) -> dict:
    """Execute the verification step: check each claim against source documents using LLM.

    For each claim with a citation [N]:
    - Find the referenced chunk
    - Perform semantic LLM verification
    - Flag as verified or hallucination based on LLM output

    Returns:
        dict with keys: verified_claims, hallucinations, verification_rate, step_log
    """
    start = time.time()

    claims = _extract_claims(answer)
    results: list[dict] = []
    logs: list[str] = [f"Extracted {len(claims)} claims with citations"]

    for claim in claims:
        best_llm_result = {"verified": False, "score": 0.0, "reasoning": "No context found"}
        best_ref = 0
        best_source_snippet = ""

        for ref_num in claim["refs"]:
            idx = ref_num - 1  # Convert to 0-indexed
            if 0 <= idx < len(chunks):
                chunk_text = chunks[idx]["text"]
                
                # Semantic LLM Check
                verify_res = _llm_verify_claim(claim["text"], chunk_text)
                
                if verify_res["score"] > best_llm_result["score"]:
                    best_llm_result = verify_res
                    best_ref = ref_num
                    best_source_snippet = chunk_text[:200]

        entry = {
            "claim": claim["text"],
            "original": claim["original"],
            "ref": best_ref,
            "match_score": best_llm_result["score"],
            "reasoning": best_llm_result["reasoning"],
            "source_snippet": best_source_snippet,
            "status": "verified" if best_llm_result["verified"] else "hallucination"
        }
        
        results.append(entry)
        
        if entry["status"] == "verified":
            logs.append(f"✓ Verified against [{best_ref}] ({int(entry['match_score']*100)}%): {entry['reasoning']}")
        else:
            logs.append(f"✗ HALLUCINATION in [{best_ref}] ({int(entry['match_score']*100)}%): {entry['reasoning']}")

    elapsed_ms = int((time.time() - start) * 1000)

    # Summary metrics
    verified_count = sum(1 for r in results if r["status"] == "verified")
    hallucination_count = len(results) - verified_count
    verification_rate = verified_count / len(results) if results else 1.0

    step_log = {
        "step": "verify",
        "name": "Verify Citations",
        "status": "completed",
        "time_ms": elapsed_ms,
        "output": {
            "total_claims": len(results),
            "verified_count": verified_count,
            "hallucination_count": hallucination_count,
            "verification_rate": round(verification_rate, 3),
            "claims": results # Include full structured data
        },
        "logs": logs,
    }

    return {
        "verified_claims": [r for r in results if r["status"] == "verified"],
        "hallucinations": [r for r in results if r["status"] == "hallucination"],
        "verification_rate": verification_rate,
        "results": results, # Full structured list
        "step_log": step_log,
    }
