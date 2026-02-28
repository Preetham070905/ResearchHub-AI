"""
Summarizer Agent — produces structured summaries for each paper.

WHY THIS IS STEP 1 IN THE PIPELINE:
Every other agent depends on summaries. The comparison agent needs them
to compare methodologies. The insight agent needs them to find themes.
The gap agent needs them to detect missing work. Without structured
summaries, nothing downstream can function.

WHAT IT EXTRACTS:
For each paper: Title, Research Problem, Methodology, Dataset,
Evaluation Metrics, Key Results, Limitations.
"""

import json
import logging
from typing import List, Dict, Any
from services.llm_service import call_llm_async
from agents.system_prompt import SUMMARIZER_ROLE

logger = logging.getLogger(__name__)


class SummarizerAgent:
    """Agent for summarizing academic research papers."""

    async def run(self, papers: List[Any]) -> List[Dict[str, Any]]:
        """
        Summarize a list of research papers.

        Args:
            papers: List of paper objects with title and abstract attributes

        Returns:
            List of structured summaries or error dict
        """
        if not papers:
            raise ValueError("papers list cannot be empty")

        paper_text = ""

        for paper in papers:
            paper_text += f"""
            Title: {paper.title}
            Abstract: {paper.abstract}
            """

        messages = [
            {
                "role": "system",
                "content": SUMMARIZER_ROLE
            },
            {
                "role": "user",
                "content": f"""
                Using only the provided papers:

                Extract structured summaries for each paper:

                - Title
                - Research Problem
                - Methodology
                - Dataset
                - Evaluation Metrics
                - Key Results
                - Limitations

                Return strictly valid JSON list.

                Papers:
                {paper_text}
                """
            }
        ]

        response = await call_llm_async(messages, max_tokens=1500)

        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {"error": "Invalid JSON from LLM", "raw_output": response}