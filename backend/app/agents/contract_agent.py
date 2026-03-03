"""Contract Analysis Agent: specialized for risk discovery and legal compliance analysis."""

import json
from app.utils.llm_client import get_llm_client, get_model_name

def run(contract_text: str, context: str = ""):
    """Performs deep analysis on contract text to find risks and obligations."""
    client = get_llm_client()
    model = get_model_name()
    
    prompt = f"""You are an Expert Legal Auditor and AI Compliance Officer. 
Your goal is 100% precision in risk discovery, utilizing patterns from the CUAD (Contract Understanding Atticus Dataset).

Contract Text Segement:
"{contract_text}"

Retrieved Regulatory/Compliance Context:
"{context}"

INSTRUCTIONS:
1. **Apply CUAD Taxonomy**: Specifically look for Change of Control, Anti-Assignment, Exclusivity, Indemnification, and Limitation of Liability.
2. **Detect Red Flags**: Identify "At Will" termination, one-sided Governing Law, or indefinite survival clauses.
3. **Cross-Reference**: Check if the text conflicts with the 'Retrieved Context' (e.g. GDPR/DPA requirements).
4. **Remediation**: Provide a "Drafting Suggestion" for every identified risk.

OUTPUT FORMAT (JSON ONLY):
{{
  "risks": [{{ 
      "category": "CUAD Category",
      "clause": "exact snippet from text", 
      "level": "high/medium/low", 
      "reason": "legal explanation", 
      "remediation": "suggested revised drafting"
  }}],
  "obligations": [{{ "task": "string", "deadline": "date or condition" }}],
  "compliance_audit": {{
      "status": "compliant/risk/fail",
      "issues": [{{ "regulation": "GDPR/FAR/etc", "gap": "explanation" }}]
  }},
  "executive_summary": "Comprehensive 50-word synthesis."
}}

Strictly output valid JSON. Use 'null' if a field is empty."""

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
            "error": f"Contract analysis failed: {str(e)}",
            "risks": [],
            "obligations": [],
            "compliance_issues": [],
            "summary": "Analysis could not be completed."
        }
