"""Global Law & Regulation Agent: Specialized in statutory interpretation and multi-jurisdictional compliance."""

import json
from app.utils.llm_client import get_llm_client, get_model_name

def run(query: str, context: str):
    """Provides high-authority regulatory analysis using statutory context."""
    client = get_llm_client()
    model = get_model_name()
    
    prompt = f"""You are a Senior Regulatory Compliance Officer and Global Legal Consultant.
Your task is to provide an accurate, high-authority analysis based on the 'Retrieved Statutory Context'.

Retrieved Statutory Context (Laws/Regulations/Evidence):
"{context}"

User Query:
"{query}"

INSTRUCTIONS:
1. **Apply Statutory Interpretation**: Analyze based on specific legal articles, recitals, or sections where possible.
2. **Jurisdictional Mapping**: Identify which regions (EU, US, Asia, etc.) specifically apply.
3. **Authority Weighting**: Prioritize official regulatory text over summaries. 
4. **Risk & Penalty Assessment**: Identify potential regulatory fines or legal repercussions for non-compliance.
5. **Regulatory Actions**: Provide a specific, actionable checklist for conformity.

OUTPUT FORMAT (JSON ONLY):
{{
  "jurisdiction_summary": ["string"],
  "applicable_regulations": [{{ "name": "string", "article_ref": "string", "status": "active/proposed" }}],
  "deep_analysis": "comprehensive regulatory interpretation",
  "checklist": ["string"],
  "compliance_score": 0-100,
  "estimated_fines": "string/none",
  "executive_summary": "max 50 words"
}}

SCORING SCHEMA:
- 0-40: Missing critical statutory evidence.
- 40-75: Relevant laws identified but specific conformity steps are unclear.
- 75-100: Explicit compliance paths identified with official citations.

Strictly output valid JSON only."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        return {
            "error": f"Regulatory analysis failed: {str(e)}",
            "jurisdiction_summary": [],
            "deep_analysis": "A system error occurred during statutory processing.",
            "compliance_score": 0
        }
