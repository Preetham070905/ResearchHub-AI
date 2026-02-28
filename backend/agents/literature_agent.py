import json
import logging
from typing import List, Dict, Any, Union
from services.llm_service import call_llm_async
from agents.system_prompt import LITERATURE_ROLE

logger = logging.getLogger(__name__)


class LiteratureReviewAgent:
    """Agent for generating a structured academic literature review from research analysis outputs."""

    async def run(
        self,
        summaries: Union[List[Dict[str, Any]], Dict[str, Any]],
        comparison: Dict[str, Any],
        insights: Dict[str, Any],
        gaps: Dict[str, Any]
    ) -> str:
        """
        Generate a structured literature review.

        Args:
            summaries: Structured summaries from SummarizerAgent
            comparison: Comparative analysis from ComparisonAgent
            insights: Cross-paper insights from InsightAgent
            gaps: Research gaps from GapAgent

        Returns:
            Markdown-formatted literature review string
        """
        if not summaries:
            raise ValueError("summaries cannot be empty")

        # If upstream summarizer failed, return a clear message instead of wasting an LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return "Literature review unavailable — the summarizer agent failed upstream."

        summaries_text = json.dumps(summaries, indent=2)
        comparison_text = json.dumps(comparison, indent=2)
        insights_text = json.dumps(insights, indent=2)
        gaps_text = json.dumps(gaps, indent=2)

        messages = [
            {
                "role": "system",
                "content": LITERATURE_ROLE
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

                === GAPS ===
                {gaps_text}

                Generate a structured literature review with the following sections:

                1. Background
                2. Taxonomy of Approaches
                3. Comparative Discussion
                4. Key Limitations
                5. Identified Research Gaps
                6. Future Work Directions

                Return clean markdown format.
                Do NOT include citations.
                Do NOT mention that you are an AI.
                """
            }
        ]

        try:
            response = await call_llm_async(messages, max_tokens=1500)
            return response.strip()
        except Exception as e:
            logger.error(f"Literature review generation failed: {str(e)}")
            raise RuntimeError(f"Literature review generation failed: {str(e)}")