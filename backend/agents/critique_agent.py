"""
Critique Agent — scientific methodology critique + argument strength analysis.

WHY TWO RESPONSIBILITIES IN ONE AGENT:
Both critique and argument analysis need the same input (summaries + comparison)
and share the same mindset: "Is this research rigorous?" Splitting them into
two agents would mean two redundant LLM calls with nearly identical context.

WHAT IT CHECKS:
1. Scientific Critique: experimental design, sample size, baselines, ablations,
   reproducibility, statistical validity, dataset quality → strong/weak points
2. Argument Strength: For each major claim, rates evidence strength,
   reliability, and flags missing evidence

This combined output maps to TWO walkthrough sections:
- Section 12: Argument Strength Analysis
- Section 13: Bias & Critique Review (Scientific Critique)
"""

import json
import logging
from typing import Dict, Any
from services.llm_service import call_llm_async
from agents.system_prompt import CRITIQUE_ROLE

logger = logging.getLogger(__name__)


class CritiqueAgent:
    """Critiques research methodology and evaluates argument strength."""

    async def run(
        self,
        summaries: Any,
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Critique methodologies and analyze argument strength.

        Args:
            summaries: Paper summaries from SummarizerAgent
            comparison: Comparative analysis from ComparisonAgent

        Returns:
            Dict with strong_points, weak_points, and argument_strength_table
        """
        summaries_text = json.dumps(summaries, indent=2) if not isinstance(summaries, str) else summaries
        comparison_text = json.dumps(comparison, indent=2) if not isinstance(comparison, str) else comparison

        # If upstream summarizer failed, skip LLM call
        if isinstance(summaries, dict) and "error" in summaries:
            return {
                "scientific_critique": {"strong_points": [], "weak_points": []},
                "argument_strength": [],
                "error": "Critique unavailable — summarizer failed upstream."
            }

        messages = [
            {
                "role": "system",
                "content": CRITIQUE_ROLE
            },
            {
                "role": "user",
                "content": f"""Critique these research papers and evaluate argument strength:

=== PAPER SUMMARIES ===
{summaries_text}

=== COMPARATIVE ANALYSIS ===
{comparison_text}

Provide two analyses in strictly valid JSON:

{{
    "scientific_critique": {{
        "strong_points": [
            {{"aspect": "<what>", "detail": "<why it's strong>"}}
        ],
        "weak_points": [
            {{"aspect": "<what>", "detail": "<why it's weak>", "severity": "minor|moderate|major"}}
        ],
        "experimental_design_assessment": "<brief assessment>",
        "reproducibility_assessment": "<brief assessment>",
        "statistical_validity": "<brief assessment>",
        "dataset_quality": "<brief assessment>"
    }},
    "argument_strength": [
        {{
            "claim": "<extracted claim>",
            "evidence_strength": "strong|moderate|weak",
            "reliability": "high|medium|low",
            "missing_evidence": "<what's needed to strengthen this>",
            "bias_indicators": "<any bias detected or 'none'>"
        }}
    ]
}}

Extract at least 5 claims for argument analysis.
JSON only. No markdown."""
            }
        ]

        response = await call_llm_async(messages, max_tokens=1500)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Critique agent parse failed: {e}")
            return {
                "scientific_critique": {
                    "strong_points": [],
                    "weak_points": [],
                    "error": "Unable to parse critique"
                },
                "argument_strength": [],
                "raw_output": response
            }
