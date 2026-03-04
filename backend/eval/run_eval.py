"""Evaluation framework for FAR Compliance Copilot.

Runs evaluation scenarios from scenarios.jsonl and produces accuracy metrics.
"""

import json
import os
import sys
import time
from pathlib import Path


def load_scenarios(scenarios_file: str = None) -> list[dict]:
    """Load evaluation scenarios from JSONL file."""
    if not scenarios_file:
        scenarios_file = os.path.join(os.path.dirname(__file__), "scenarios.jsonl")

    scenarios = []
    with open(scenarios_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))
    return scenarios


def evaluate_single(scenario: dict, pipeline_func) -> dict:
    """Evaluate a single scenario against the pipeline.

    Args:
        scenario: Dict with query, expected_answer, expected_citations, etc.
        pipeline_func: Callable that takes a query and returns pipeline result

    Returns:
        Dict with evaluation metrics for this scenario
    """
    query = scenario["query"]
    expected_citations = scenario.get("expected_citations", [])

    start = time.time()
    try:
        result = pipeline_func(query)
        elapsed_ms = int((time.time() - start) * 1000)
    except Exception as e:
        return {
            "query": query,
            "status": "error",
            "error": str(e),
            "elapsed_ms": 0,
        }

    answer = result.get("answer", "")
    confidence = result.get("confidence", 0.0)
    citations = result.get("citations", [])

    # Check citation accuracy
    cited_sources = set()
    for c in citations:
        source = c.get("source", "")
        cited_sources.add(source)
        if c.get("section_id"):
            cited_sources.add(c["section_id"])
        if c.get("clause_id"):
            cited_sources.add(c["clause_id"])

    # Check if expected citations appear in the answer text
    citation_hits = 0
    for expected in expected_citations:
        if expected.lower() in answer.lower():
            citation_hits += 1

    citation_accuracy = citation_hits / len(expected_citations) if expected_citations else 1.0

    # Check if answer contains expected content
    expected_answer = scenario.get("expected_answer", "")
    expected_keywords = [w.lower() for w in expected_answer.split() if len(w) > 3]
    keyword_hits = sum(1 for kw in expected_keywords if kw in answer.lower())
    content_accuracy = keyword_hits / len(expected_keywords) if expected_keywords else 0.0

    # Blocked check
    blocked = result.get("blocked", False) or "blocked" in answer.lower()

    return {
        "query": query,
        "status": "success",
        "workflow": scenario.get("workflow", "general"),
        "difficulty": scenario.get("difficulty", "medium"),
        "confidence": confidence,
        "citation_accuracy": round(citation_accuracy, 3),
        "content_accuracy": round(content_accuracy, 3),
        "citations_found": len(citations),
        "expected_citations": len(expected_citations),
        "blocked": blocked,
        "elapsed_ms": elapsed_ms,
        "answer_length": len(answer),
    }


def run_evaluation(scenarios_file: str = None, output_file: str = None) -> dict:
    """Run full evaluation suite.

    Returns summary metrics across all scenarios.
    """
    # Import pipeline (add project root to path)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from app.agents.orchestrator import run_pipeline

    scenarios = load_scenarios(scenarios_file)
    results = []

    print(f"Running {len(scenarios)} evaluation scenarios...")

    for i, scenario in enumerate(scenarios):
        print(f"  [{i+1}/{len(scenarios)}] {scenario['query'][:60]}...")
        result = evaluate_single(scenario, run_pipeline)
        results.append(result)

    # Compute summary metrics
    successful = [r for r in results if r["status"] == "success"]
    total = len(results)
    success_count = len(successful)

    summary = {
        "total_scenarios": total,
        "successful": success_count,
        "errors": total - success_count,
        "avg_confidence": round(sum(r["confidence"] for r in successful) / max(1, success_count), 3),
        "avg_citation_accuracy": round(sum(r["citation_accuracy"] for r in successful) / max(1, success_count), 3),
        "avg_content_accuracy": round(sum(r["content_accuracy"] for r in successful) / max(1, success_count), 3),
        "avg_response_time_ms": int(sum(r["elapsed_ms"] for r in successful) / max(1, success_count)),
        "blocked_count": sum(1 for r in successful if r.get("blocked")),
        "by_workflow": {},
        "by_difficulty": {},
    }

    # Breakdown by workflow
    for workflow in ["set_aside", "labor_standards", "it_cyber", "general"]:
        wf_results = [r for r in successful if r.get("workflow") == workflow]
        if wf_results:
            summary["by_workflow"][workflow] = {
                "count": len(wf_results),
                "avg_confidence": round(sum(r["confidence"] for r in wf_results) / len(wf_results), 3),
                "avg_citation_accuracy": round(sum(r["citation_accuracy"] for r in wf_results) / len(wf_results), 3),
            }

    # Breakdown by difficulty
    for diff in ["easy", "medium", "hard"]:
        diff_results = [r for r in successful if r.get("difficulty") == diff]
        if diff_results:
            summary["by_difficulty"][diff] = {
                "count": len(diff_results),
                "avg_confidence": round(sum(r["confidence"] for r in diff_results) / len(diff_results), 3),
            }

    # Save results
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "results": results}, f, indent=2)
        print(f"Results saved to {output_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Scenarios:       {total}")
    print(f"Successful:            {success_count}")
    print(f"Errors:                {total - success_count}")
    print(f"Avg Confidence:        {summary['avg_confidence']}")
    print(f"Avg Citation Accuracy: {summary['avg_citation_accuracy']}")
    print(f"Avg Content Accuracy:  {summary['avg_content_accuracy']}")
    print(f"Avg Response Time:     {summary['avg_response_time_ms']}ms")
    print(f"Blocked Responses:     {summary['blocked_count']}")
    print("=" * 60)

    return summary


if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "results.json")
    run_evaluation(output_file=output)
