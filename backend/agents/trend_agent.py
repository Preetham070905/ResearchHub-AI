"""
Trend Agent — forecasts research directions for the next 1-3 years.

WHY THIS MATTERS:
Choosing a research direction is a multi-year commitment. This agent analyzes:
- Which methods are gaining traction vs. declining
- Emerging tools and frameworks
- Citation pattern trends
- Cross-domain influence

This helps researchers/students pick topics that will be relevant in 2-3 years,
not just today. It also helps identify when a field is getting saturated.
"""

import json
import logging
from typing import Dict, Any
from services.llm_service import call_llm_async
from agents.system_prompt import TREND_ROLE

logger = logging.getLogger(__name__)


class TrendAgent:
    """Forecasts research trends for 1-year and 3-year horizons."""

    async def run(
        self,
        query: str,
        summaries: Any,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze research trends and predict future directions.

        Args:
            query: The user's research question
            summaries: Paper summaries from SummarizerAgent
            insights: Cross-paper insights from InsightAgent

        Returns:
            Dict with trend analysis, predictions, and emerging tools
        """
        summaries_text = json.dumps(summaries, indent=2) if not isinstance(summaries, str) else summaries
        insights_text = json.dumps(insights, indent=2) if not isinstance(insights, str) else insights

        # If upstream summarizer failed, skip LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "error": "Trend analysis unavailable — summarizer failed upstream."
            }

        messages = [
            {
                "role": "system",
                "content": TREND_ROLE
            },
            {
                "role": "user",
                "content": f"""Analyze research trends for this topic and predict future directions:

TOPIC: {query}

=== CURRENT PAPER SUMMARIES ===
{summaries_text}

=== CROSS-PAPER INSIGHTS ===
{insights_text}

Provide trend analysis in strictly valid JSON:
{{
    "current_research_direction": "<description of where the field is now>",
    "method_adoption_trends": [
        {{"method": "<name>", "trend": "rising|stable|declining", "reason": "<why>"}}
    ],
    "emerging_tools_and_frameworks": [
        {{"name": "<tool/framework>", "impact": "<expected impact>"}}
    ],
    "citation_pattern_insights": "<what citation patterns reveal>",
    "one_year_predictions": [
        "<prediction 1>",
        "<prediction 2>",
        "<prediction 3>"
    ],
    "three_year_predictions": [
        "<prediction 1>",
        "<prediction 2>",
        "<prediction 3>"
    ],
    "rising_topics": ["<topic 1>", "<topic 2>"],
    "declining_topics": ["<topic 1>", "<topic 2>"],
    "cross_domain_opportunities": ["<opportunity 1>", "<opportunity 2>"]
}}

JSON only. No markdown."""
            }
        ]

        response = await call_llm_async(messages, max_tokens=1200)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Trend agent parse failed: {e}")
            return {
                "error": "Unable to parse trend analysis",
                "raw_output": response
            }
