"""Evaluation runner for FAR Compliance Copilot.

Runs the ground truth scenarios through the pipeline and calculates alignment metrics.
"""

import json
import asyncio
import pandas as pd
from typing import List, Dict, Any
from app.agents.orchestrator import run_pipeline
from app.config import settings

GROUND_TRUTH_PATH = "tests/eval/ground_truth.json"

async def run_evaluation():
    """Run full evaluation suite and print results."""
    with open(GROUND_TRUTH_PATH, "r") as f:
        ground_truth = json.load(f)
        
    results = []
    
    print(f"🚀 Starting Evaluation: {len(ground_truth)} scenarios...")
    
    for scenario in ground_truth:
        print(f"  Testing: {scenario['id']} - {scenario['query'][:50]}...")
        
        # Execute pipeline
        res = run_pipeline(scenario["query"])
        
        # Calculate Metrics
        answer = res["answer"].lower()
        
        # 1. Citation Recall
        actual_citations = [c.get("section_id", "") for c in res.get("citations", [])]
        found_cits = [c for c in scenario["expected_citations"] if any(c in ac for ac in actual_citations)]
        citation_recall = len(found_cits) / len(scenario["expected_citations"]) if scenario["expected_citations"] else 1.0
        
        # 2. Keyword Accuracy
        found_keywords = [k for k in scenario["expected_keywords"] if k.lower() in answer]
        keyword_score = len(found_keywords) / len(scenario["expected_keywords"]) if scenario["expected_keywords"] else 1.0
        
        # 3. Block Rate / Hallucination Detection
        blocked = res.get("is_blocked", False)
        
        results.append({
            "id": scenario["id"],
            "query": scenario["query"],
            "recall": citation_recall,
            "keywords": keyword_score,
            "confidence": res["confidence"],
            "blocked": blocked,
            "category": scenario["category"]
        })
        
    # Summarize Results
    df = pd.DataFrame(results)
    print("\n📊 EVALUATION SUMMARY:")
    print(f"Average Citation Recall: {df['recall'].mean():.2%}")
    print(f"Average Keyword Score: {df['keywords'].mean():.2%}")
    print(f"Average Confidence: {df['confidence'].mean():.2f}")
    print(f"Blocked Percent: {df['blocked'].mean():.1%}")
    
    # Category summary
    cat_summary = df.groupby('category')[['recall', 'keywords']].mean()
    print("\n📈 PERFORMANCE BY CATEGORY:")
    print(cat_summary)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_evaluation())
