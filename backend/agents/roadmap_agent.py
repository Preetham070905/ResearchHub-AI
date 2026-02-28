"""
Roadmap Agent — generates a 30-day researcher learning roadmap.

WHY THIS EXISTS:
New researchers face "where do I even start?" paralysis. This agent
creates a structured 30-day plan broken into 4 weekly phases:
- Week 1: Foundations & literature review
- Week 2: Technical deep dive & reproduce baselines
- Week 3: Experimental work & novel extensions
- Week 4: Write-up & peer feedback

Also provides project ideas, dataset suggestions, and baseline models
so the researcher has everything they need to get started.
"""

import json
import logging
from typing import Dict, Any
from services.llm_service import call_llm_async
from agents.system_prompt import ROADMAP_ROLE

logger = logging.getLogger(__name__)


class RoadmapAgent:
    """Generates a 30-day learning and research plan."""

    async def run(
        self,
        query: str,
        summaries: Any,
        gaps: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a structured 30-day researcher roadmap.

        Args:
            query: The user's research topic
            summaries: Paper summaries from SummarizerAgent
            gaps: Research gaps from GapAgent

        Returns:
            Dict with weekly plans, project ideas, datasets, and baselines
        """
        summaries_text = json.dumps(summaries, indent=2) if not isinstance(summaries, str) else summaries
        gaps_text = json.dumps(gaps, indent=2) if not isinstance(gaps, str) else gaps

        # If upstream summarizer failed, skip LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "error": "Roadmap generation unavailable — summarizer failed upstream."
            }

        messages = [
            {
                "role": "system",
                "content": ROADMAP_ROLE
            },
            {
                "role": "user",
                "content": f"""Create a 30-day researcher roadmap for this topic:

TOPIC: {query}

=== EXISTING PAPER SUMMARIES ===
{summaries_text}

=== IDENTIFIED RESEARCH GAPS ===
{gaps_text}

Return strictly valid JSON:
{{
    "roadmap": {{
        "week_1": {{
            "theme": "Foundations & Literature Review",
            "tasks": ["<task 1>", "<task 2>", "<task 3>"],
            "resources": ["<resource 1>", "<resource 2>"]
        }},
        "week_2": {{
            "theme": "Technical Deep Dive",
            "tasks": ["<task 1>", "<task 2>", "<task 3>"],
            "resources": ["<resource 1>", "<resource 2>"]
        }},
        "week_3": {{
            "theme": "Experimental Work",
            "tasks": ["<task 1>", "<task 2>", "<task 3>"],
            "resources": ["<resource 1>", "<resource 2>"]
        }},
        "week_4": {{
            "theme": "Synthesis & Write-up",
            "tasks": ["<task 1>", "<task 2>", "<task 3>"],
            "resources": ["<resource 1>", "<resource 2>"]
        }}
    }},
    "project_ideas": [
        {{"title": "<project>", "difficulty": "beginner|intermediate|advanced", "description": "<brief>"}}
    ],
    "recommended_datasets": [
        {{"name": "<dataset>", "description": "<what it contains>", "url": "<if known>"}}
    ],
    "baseline_models": [
        {{"name": "<model>", "description": "<what it does>", "implementation": "<where to find>"}}
    ],
    "key_papers_to_read": ["<paper title 1>", "<paper title 2>", "<paper title 3>"]
}}

Provide at least 5 project ideas, 5 datasets, and 3 baseline models.
JSON only. No markdown."""
            }
        ]

        response = await call_llm_async(messages, max_tokens=1500)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Roadmap agent parse failed: {e}")
            return {
                "error": "Unable to parse roadmap",
                "raw_output": response
            }
