"""Full pipeline test — runs the orchestrator end-to-end."""
import asyncio
import json
import time
from agents.orchestrator import AgentOrchestrator

async def test_pipeline():
    orchestrator = AgentOrchestrator()
    query = "explain 6g technology"

    print(f"Running full pipeline for: '{query}'")
    print("=" * 60)
    start = time.time()

    result = await orchestrator.run(query, workspace_id=None)

    elapsed = round(time.time() - start, 2)
    print(f"\nPipeline completed in {elapsed}s")
    print("=" * 60)

    # Check each section
    sections = [
        "direct_answer", "context_summary", "knowledge_graph",
        "comparison", "gap_analysis", "deep_insights",
        "novelty_score", "trend_forecast", "recommended_methods_datasets",
        "experiment_suggestions", "researcher_roadmap",
        "argument_strength", "scientific_critique",
        "literature_review", "final_simplified_answer",
        "confidence_score", "explainability_log"
    ]

    print("\nSection Status:")
    for section in sections:
        value = result.get(section)
        if value is None:
            status = "MISSING"
        elif isinstance(value, dict) and "error" in value:
            status = f"ERROR: {value['error'][:60]}"
        elif isinstance(value, str) and len(value) < 10:
            status = f"WEAK: '{value[:50]}'"
        else:
            status = "OK"
        print(f"  [{status:6s}] {section}")

    # Print timing
    log = result.get("explainability_log", {})
    print(f"\nAgents activated: {log.get('total_agents', '?')}")
    print(f"Total time: {log.get('total_pipeline_time_seconds', '?')}s")
    timing = log.get("timing_breakdown", {})
    for agent, t in timing.items():
        print(f"  {agent}: {t}s")

    # Print confidence
    conf = result.get("confidence_score", {})
    print(f"\nConfidence: {conf.get('score', '?')}/100")
    for reason in conf.get("breakdown", []):
        print(f"  - {reason}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
