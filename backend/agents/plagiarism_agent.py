"""
Plagiarism Detection Agent — LLM-enhanced plagiarism analysis.

Uses the PlagiarismChecker service (TF-IDF + cosine similarity) for
quantitative analysis, then wraps results with LLM interpretation for:
  - Contextual judgement (is high similarity expected, e.g. same author?)
  - Passage-level breakdown with severity markers
  - Actionable recommendations for the researcher
  - Distinction between common phrasing vs. actual plagiarism

This is agent #12 in the ResearchHub AGI pipeline.
"""

import json
import logging
from typing import List, Dict, Any

from services.llm_service import call_llm_async
from services.plagiarism_service import (
    PlagiarismChecker,
    DocumentInput,
    PlagiarismReport,
    plagiarism_checker,
)
from agents.system_prompt import PLAGIARISM_ROLE

logger = logging.getLogger(__name__)


class PlagiarismAgent:
    """Agent that combines TF-IDF plagiarism detection with LLM interpretation."""

    def __init__(self):
        self.checker = plagiarism_checker

    async def analyze(
        self,
        target: DocumentInput,
        reference_docs: List[DocumentInput],
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Run plagiarism check and optionally enhance with LLM analysis.

        Args:
            target: Document to check
            reference_docs: Documents to compare against
            use_llm: Whether to add LLM-powered interpretation

        Returns:
            Dict with plagiarism report + optional LLM analysis
        """
        # 1. Run TF-IDF plagiarism check
        report = self.checker.check(target, reference_docs)

        # 2. Serialize report to dict
        result = self._report_to_dict(report)

        # 3. Optionally enhance with LLM analysis
        if use_llm and report.pair_results:
            try:
                llm_analysis = await self._llm_interpret(report)
                result["llm_analysis"] = llm_analysis
            except Exception as e:
                logger.error(f"LLM plagiarism analysis failed: {e}")
                result["llm_analysis"] = {
                    "interpretation": "LLM analysis unavailable.",
                    "error": str(e),
                }

        return result

    async def _llm_interpret(self, report: PlagiarismReport) -> Dict[str, Any]:
        """Use LLM to provide nuanced interpretation of plagiarism results."""

        # Build context for the LLM
        top_pairs_text = ""
        for pair in report.pair_results[:5]:
            top_pairs_text += (
                f"\n- '{pair.doc_b_title}': {pair.overall_similarity}% similarity"
            )
            if pair.sentence_matches:
                top_pairs_text += f" ({len(pair.sentence_matches)} matching passages)"

        top_sentences_text = ""
        for match in report.top_matching_sentences[:8]:
            top_sentences_text += (
                f"\n  Source: \"{match.source_sentence[:150]}...\""
                f"\n  Match:  \"{match.matched_sentence[:150]}...\""
                f"\n  Similarity: {match.similarity * 100:.1f}%\n"
            )

        prompt = f"""Analyze these plagiarism detection results and provide expert interpretation.

TARGET DOCUMENT: "{report.target_doc_title}"
OVERALL PLAGIARISM SCORE: {report.overall_plagiarism_score}%
RISK LEVEL: {report.risk_level}

TOP SIMILAR DOCUMENTS:{top_pairs_text}

TOP MATCHING PASSAGES:{top_sentences_text}

STATISTICS:
- Documents compared: {report.stats.get('reference_count', 0)}
- Sentence matches found: {report.stats.get('total_sentence_matches', 0)}
- Max document similarity: {report.stats.get('max_document_similarity', 0)}%
- Average document similarity: {report.stats.get('avg_document_similarity', 0)}%

Return JSON with:
{{
  "interpretation": "2-3 paragraph expert analysis of whether this constitutes plagiarism or expected similarity",
  "severity": "none|minor|moderate|significant|critical",
  "is_likely_plagiarism": true/false,
  "key_concerns": ["list of specific concerns"],
  "mitigating_factors": ["factors that reduce plagiarism likelihood"],
  "recommendations": ["actionable steps for the researcher"],
  "common_phrasing_ratio": float (0-1, estimated % of matches that are just common academic phrasing)
}}"""

        raw = await call_llm_async(PLAGIARISM_ROLE, prompt)

        try:
            # Try to parse JSON from response
            json_str = raw.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {
                "interpretation": raw,
                "severity": report.risk_level,
                "is_likely_plagiarism": report.overall_plagiarism_score > 45,
                "recommendations": ["Review flagged passages manually."],
            }

    @staticmethod
    def _report_to_dict(report: PlagiarismReport) -> Dict[str, Any]:
        """Convert PlagiarismReport dataclass to JSON-serializable dict."""
        return {
            "target_doc_id": report.target_doc_id,
            "target_doc_title": report.target_doc_title,
            "overall_plagiarism_score": report.overall_plagiarism_score,
            "risk_level": report.risk_level,
            "summary": report.summary,
            "pair_results": [
                {
                    "doc_id": pr.doc_b_id,
                    "doc_title": pr.doc_b_title,
                    "similarity_pct": pr.overall_similarity,
                    "matching_passages": [
                        {
                            "source_text": sm.source_sentence,
                            "matched_text": sm.matched_sentence,
                            "similarity": round(sm.similarity * 100, 1),
                        }
                        for sm in pr.sentence_matches
                    ],
                }
                for pr in report.pair_results
            ],
            "top_matching_sentences": [
                {
                    "source_text": sm.source_sentence,
                    "matched_text": sm.matched_sentence,
                    "similarity": round(sm.similarity * 100, 1),
                    "matched_doc_id": sm.matched_doc_id,
                }
                for sm in report.top_matching_sentences
            ],
            "stats": report.stats,
        }
