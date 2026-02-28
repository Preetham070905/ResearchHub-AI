"""
Novelty Agent — scores research novelty from 0 to 100.

WHY THIS AGENT EXISTS:
Researchers often spend months on an idea only to discover it's already been done.
This agent evaluates novelty across 5 dimensions BEFORE deep investment:

1. Uniqueness: How different is this from existing work?
2. Scientific Novelty: Does it advance theoretical understanding?
3. Practical Novelty: Does it solve a real-world problem in a new way?
4. Redundancy Risk: How much overlap with published work?
5. Opportunity Areas: Where can this be extended?

The score helps researchers decide: "Is this worth pursuing?"
"""

import json
import logging
from typing import Dict, Any
from services.llm_service import call_llm_async
from agents.system_prompt import NOVELTY_ROLE

logger = logging.getLogger(__name__)


class NoveltyAgent:
    """Scores research novelty on a 0-100 scale with breakdown."""

    async def run(
        self,
        query: str,
        summaries: Any,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score the novelty of a research topic/query against existing papers.

        Args:
            query: The user's research question
            summaries: Paper summaries from SummarizerAgent
            insights: Cross-paper insights from InsightAgent

        Returns:
            Dict with overall score, sub-scores, and explanation
        """
        summaries_text = json.dumps(summaries, indent=2) if not isinstance(summaries, str) else summaries
        insights_text = json.dumps(insights, indent=2) if not isinstance(insights, str) else insights

        # If upstream summarizer failed, return a neutral score instead of wasting an LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "overall_score": 0,
                "explanation": "Novelty scoring unavailable — summarizer failed upstream.",
                "error": summaries["error"]
            }

        messages = [
            {
                "role": "system",
                "content": NOVELTY_ROLE
            },
            {
                "role": "user",
                "content": f"""Evaluate the novelty of this research query against existing work:

QUERY: {query}

=== EXISTING PAPER SUMMARIES ===
{summaries_text}

=== CROSS-PAPER INSIGHTS ===
{insights_text}

Score the research on these dimensions (0-100 each):

1. uniqueness_score: How different from existing approaches?
2. scientific_novelty_score: Does it advance theory?
3. practical_novelty_score: New real-world applications?
4. redundancy_risk_score: Overlap with existing work? (100 = NO redundancy, 0 = fully redundant)
5. opportunity_score: Room for extension and new work?

Return strictly valid JSON:
{{
    "overall_score": <weighted average 0-100>,
    "uniqueness_score": <0-100>,
    "scientific_novelty_score": <0-100>,
    "practical_novelty_score": <0-100>,
    "redundancy_risk_score": <0-100>,
    "opportunity_score": <0-100>,
    "explanation": "<2-3 sentence justification>",
    "opportunity_areas": ["<area 1>", "<area 2>", "<area 3>"]
}}

JSON only. No markdown."""
            }
        ]

        response = await call_llm_async(messages, max_tokens=1500)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Novelty agent parse failed: {e}")
            return {
                "overall_score": 50,
                "explanation": "Unable to parse novelty assessment",
                "raw_output": response
            }
