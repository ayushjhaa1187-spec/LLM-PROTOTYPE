"""Red Team Agent: adversarial testing to detect hallucinations before delivery.

This agent attempts to break the drafted response by:
1. Cross-checking facts against source materials
2. Identifying unsupported claims
3. Flagging potential hallucinations
4. Assigning an adversarial confidence score
"""

import json
import time
from app.utils.llm_client import get_llm_client, get_model_name


def run(answer: str, chunks: list[dict], query: str) -> dict:
    """Execute adversarial red team analysis on a drafted response.

    Args:
        answer: The drafted response to test
        chunks: Source document chunks used to generate the response
        query: The original user query

    Returns:
        dict with keys: issues, adversarial_score, should_block, step_log
    """
    start = time.time()
    client = get_llm_client()
    model = get_model_name()

    # Build source context for verification
    source_context = "\n\n---\n\n".join([
        f"[Source {i+1}] ({c.get('metadata', {}).get('source', 'Unknown')}, "
        f"Page {c.get('metadata', {}).get('page', '?')})\n{c['text']}"
        for i, c in enumerate(chunks[:6])
    ])

    prompt = f"""You are a Red Team Agent performing adversarial analysis on an AI-generated response.
Your job is to AGGRESSIVELY find flaws, unsupported claims, and hallucinations.

ORIGINAL QUESTION: "{query}"

AI-GENERATED RESPONSE:
\"\"\"{answer}\"\"\"

SOURCE DOCUMENTS:
\"\"\"{source_context}\"\"\"

ADVERSARIAL ANALYSIS INSTRUCTIONS:
1. **Fact Verification**: For EVERY factual claim, check if it's directly supported by the source documents.
2. **Citation Accuracy**: Verify every cited section number (e.g., "FAR 52.219-8") actually appears in sources.
3. **Logical Consistency**: Check for contradictions within the response.
4. **Scope Creep**: Flag any information that goes beyond what the sources state.
5. **Numerical Accuracy**: Verify all numbers, dates, thresholds, and dollar amounts.
6. **Omission Detection**: Note critical information in sources that the response omits.

OUTPUT FORMAT (JSON ONLY):
{{
    "issues": [
        {{
            "type": "hallucination|unsupported_claim|citation_error|scope_creep|numerical_error|omission",
            "severity": "critical|high|medium|low",
            "description": "Specific description of the issue",
            "affected_text": "The specific text in the response that has the issue",
            "evidence": "What the sources actually say (or don't say)"
        }}
    ],
    "adversarial_score": 0.0-1.0,
    "overall_assessment": "PASS|WARN|FAIL",
    "recommendation": "Brief recommendation"
}}

SCORING:
- 0.0-0.3: Critical issues found, DO NOT deliver this response
- 0.3-0.6: Significant issues, response needs revision
- 0.6-0.8: Minor issues, acceptable with caveats
- 0.8-1.0: Response is well-supported by sources

Strictly output valid JSON only."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        result = {
            "issues": [{"type": "error", "severity": "high",
                        "description": f"Red team analysis failed: {str(e)}"}],
            "adversarial_score": 0.5,
            "overall_assessment": "WARN",
            "recommendation": "Manual review recommended - automated analysis failed"
        }

    elapsed_ms = int((time.time() - start) * 1000)
    score = result.get("adversarial_score", 0.5)
    issues = result.get("issues", [])
    assessment = result.get("overall_assessment", "WARN")

    # Should block if score is below threshold
    should_block = score < 0.3 or assessment == "FAIL"

    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    high_count = sum(1 for i in issues if i.get("severity") == "high")

    step_log = {
        "step": "red_team",
        "name": "Red Team Analysis",
        "status": "completed",
        "time_ms": elapsed_ms,
        "output": {
            "adversarial_score": score,
            "assessment": assessment,
            "total_issues": len(issues),
            "critical_issues": critical_count,
            "high_issues": high_count,
            "should_block": should_block,
        },
        "logs": [
            f"Red Team adversarial score: {score}",
            f"Assessment: {assessment}",
            f"Issues found: {len(issues)} (Critical: {critical_count}, High: {high_count})",
            f"Recommendation: {result.get('recommendation', 'N/A')}",
        ],
    }

    return {
        "issues": issues,
        "adversarial_score": score,
        "assessment": assessment,
        "should_block": should_block,
        "recommendation": result.get("recommendation", ""),
        "step_log": step_log,
    }
