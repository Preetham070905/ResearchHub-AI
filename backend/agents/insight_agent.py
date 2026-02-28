"""
Insight Agent — extracts cross-paper themes, methods, datasets, and patterns.

WHY THIS AGENT EXISTS:
Reading 10 papers individually tells you what each paper does.
But the REAL value is in the cross-cutting patterns:
- What methods keep appearing? (popular approaches)
- What datasets are everyone using? (standard benchmarks)
- What limitations repeat? (systemic problems in the field)
- What themes are emerging? (research frontiers)

This agent finds those patterns that a human reader might miss
when reading papers one at a time.
"""

import json
import logging
from typing import List, Dict, Any, Union
from services.llm_service import call_llm_async
from agents.system_prompt import INSIGHT_ROLE

logger = logging.getLogger(__name__)


class InsightAgent:
    """Agent for extracting cross-paper insights from research summaries."""

    async def run(self, summaries: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract cross-paper insights from structured summaries.

        Args:
            summaries: Structured summaries from SummarizerAgent

        Returns:
            Dict with extracted insights or error dict
        """
        if not summaries:
            raise ValueError("summaries cannot be empty")

        # If upstream summarizer failed, skip LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "unique_methods": [],
                "common_datasets": [],
                "evaluation_metrics": [],
                "recurring_limitations": [],
                "emerging_themes": [],
                "error": f"Skipped — summarizer failed: {summaries['error']}"
            }

        # Convert summaries to string safely
        summaries_text = json.dumps(summaries, indent=2)

        messages = [
            {
                "role": "system",
                "content": INSIGHT_ROLE
            },
            {
                "role": "user",
                "content": f"""
                Using the following structured summaries:

                {summaries_text}

                Extract:

                1. Unique methods used across papers
                2. Common datasets used
                3. Frequently used evaluation metrics
                4. Recurring limitations
                5. Emerging research themes

                Return strictly valid JSON in this format:

                {{
                    "unique_methods": [],
                    "common_datasets": [],
                    "evaluation_metrics": [],
                    "recurring_limitations": [],
                    "emerging_themes": []
                }}

                Do NOT include explanations.
                Do NOT include markdown.
                JSON only.
                """
            }
        ]

        response = await call_llm_async(messages, max_tokens=1500)

        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "error": "Invalid JSON from LLM",
                "raw_output": response
            }