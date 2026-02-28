"""
Gap Detection Agent — identifies research gaps, missing experiments, and opportunities.

WHY THIS IS CRITICAL:
This is where ResearchHub-AI adds the most unique value. Any tool can
summarize papers. But *detecting what's MISSING* — that's what researchers
actually need. This agent combines summaries, comparison data, and insights
to find:

1. Repeated limitations nobody is solving
2. Method+dataset combinations nobody has tried
3. Missing benchmarks (no standard way to evaluate)
4. Contradictory findings across papers
5. Novel research directions the field hasn't explored

These gaps directly feed into the Experiment Suggestions (Section 10)
and the Researcher Roadmap (Section 11).
"""

import json
import logging
from typing import Dict, Any
from services.llm_service import call_llm_async
from agents.system_prompt import GAP_ROLE

logger = logging.getLogger(__name__)


class GapDetectionAgent:
    """Agent for detecting research gaps and unexplored opportunities."""

    async def run(self, summaries, comparison, insights) -> Dict[str, Any]:
        """
        Detect research gaps from combined analysis data.

        Args:
            summaries: Paper summaries from SummarizerAgent
            comparison: Comparative analysis from ComparisonAgent
            insights: Cross-paper insights from InsightAgent

        Returns:
            Dict with gap categories or error dict
        """
        # If upstream summarizer failed, skip LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "repeated_limitations": [],
                "underexplored_combinations": [],
                "missing_benchmarks": [],
                "conflicting_findings": [],
                "novel_research_directions": [],
                "error": f"Skipped — summarizer failed: {summaries['error']}"
            }

        summaries_text = json.dumps(summaries, indent=2)
        comparison_text = json.dumps(comparison, indent=2)
        insights_text = json.dumps(insights, indent=2)

        messages = [
            {
                "role": "system",
                "content": GAP_ROLE
            },
            {
                "role": "user",
                "content": f"""
                Using the following structured research data:

                === SUMMARIES ===
                {summaries_text}

                === COMPARISON ===
                {comparison_text}

                === INSIGHTS ===
                {insights_text}

                Perform research gap analysis.

                Return strictly valid JSON in this format:

                {{
                    "repeated_limitations": [],
                    "underexplored_combinations": [],
                    "missing_benchmarks": [],
                    "conflicting_findings": [],
                    "novel_research_directions": []
                }}

                Do NOT include markdown.
                Do NOT include explanations.
                JSON only.
                """
            }
        ]

        response = await call_llm_async(messages, max_tokens=1200)

        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Gap agent parse failed: {e}")
            return {
                "error": "Invalid JSON from LLM",
                "raw_output": response
            }