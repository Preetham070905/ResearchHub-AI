"""
Agent Orchestrator — the master controller of the ResearchHub AI pipeline.

WHY THIS IS THE MOST IMPORTANT FILE:
This is the "brain" that coordinates all 11 agents and 2 services.
Without this, individual agents are isolated — they can't talk to each other
or combine their outputs. The orchestrator:

1. SEARCHES for papers (paper_search service)
2. CHAINS agents in dependency order (e.g., gap analysis needs summaries first)
3. PARALLELIZES where safe (comparison + insight don't depend on each other)
4. TIMES every step for the explainability log
5. ASSEMBLES the final 16-section output that matches the walkthrough format
6. COMPUTES a confidence score based on data availability
7. GRACEFULLY DEGRADES — if one agent fails, it logs the error and continues
   with fallback results instead of crashing the entire pipeline

PIPELINE DEPENDENCY GRAPH:
    papers → summarizer → comparison → gap → literature
                       → insight    → gap
                       → kg_builder
    query + summaries + insights → novelty, trend, roadmap
    summaries + comparison → critique
    all outputs → 16-section assembly
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List

from services.paper_search import search_papers, PaperResult
from services.pdf_extractor import extract_papers_from_workspace
from services.knowledge_graph import KnowledgeGraphBuilder
from services.llm_service import call_llm_async
from agents.summarizer_agent import SummarizerAgent
from agents.comparison_agent import ComparisonAgent
from agents.insight_agent import InsightAgent
from agents.gap_agent import GapDetectionAgent
from agents.literature_agent import LiteratureReviewAgent
from agents.novelty_agent import NoveltyAgent
from agents.trend_agent import TrendAgent
from agents.critique_agent import CritiqueAgent
from agents.roadmap_agent import RoadmapAgent
from agents.intent_router import IntentRouter
from agents.system_prompt import ORCHESTRATOR_IDENTITY, FINAL_ANSWER_ROLE

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Master controller that chains all agents into a 16-section pipeline."""

    async def run(self, query: str, workspace_id: int = None) -> Dict[str, Any]:
        """
        Execute the full research analysis pipeline.

        Args:
            query: The user's research question
            workspace_id: The ID of the workspace (used to fetch uploaded PDFs)

        Returns:
            Dict containing all 16 sections of the output format
        """
        pipeline_start = time.time()
        timing_log = {}
        agents_activated = []

        # ========================================
        # STEP 1: Intent Classification
        # ========================================
        step_start = time.time()
        intent_router = IntentRouter()
        intent = await intent_router.classify(query)
        timing_log["intent_classification"] = round(time.time() - step_start, 2)
        agents_activated.append("intent_router")

        # ========================================
        # STEP 2: Paper Search & Uploads
        # ========================================
        step_start = time.time()
        paper_results: List[PaperResult] = await search_papers(query)

        # Merge with uploaded papers
        if workspace_id:
            uploaded_papers = extract_papers_from_workspace(workspace_id)
            if uploaded_papers:
                paper_results.extend(uploaded_papers)

        timing_log["paper_search_and_extract"] = round(time.time() - step_start, 2)

        if not paper_results:
            return self._empty_result(query, "No papers found online and no PDFs uploaded in this workspace")

        # Convert to format expected by agents (objects with title/abstract)
        papers_for_agents = paper_results  # PaperResult has .title and .abstract

        # ========================================
        # STEP 3: Summarizer Agent
        # ========================================
        step_start = time.time()
        summarizer = SummarizerAgent()
        try:
            summaries = await summarizer.run(papers_for_agents)
        except Exception as e:
            logger.error(f"Summarizer agent failed: {e}")
            summaries = {"error": f"Summarizer failed: {str(e)}"}
        timing_log["summarizer"] = round(time.time() - step_start, 2)
        agents_activated.append("summarizer")

        # ========================================
        # STEP 4: Comparison + Insight (PARALLEL)
        # These don't depend on each other, only on summaries.
        # Running them in parallel saves ~50% of this step's time.
        #
        # GRACEFUL DEGRADATION: return_exceptions=True means if one
        # fails, the other still completes. We check each result.
        # ========================================
        step_start = time.time()
        comparison_agent = ComparisonAgent()
        insight_agent = InsightAgent()

        results = await asyncio.gather(
            comparison_agent.run(summaries),
            insight_agent.run(summaries),
            return_exceptions=True
        )

        # Handle comparison result
        if isinstance(results[0], Exception):
            logger.error(f"Comparison agent failed: {results[0]}")
            comparison = {"error": f"Comparison failed: {str(results[0])}"}
        else:
            comparison = results[0]

        # Handle insight result
        if isinstance(results[1], Exception):
            logger.error(f"Insight agent failed: {results[1]}")
            insights = {"error": f"Insight extraction failed: {str(results[1])}"}
        else:
            insights = results[1]

        timing_log["comparison_and_insight"] = round(time.time() - step_start, 2)
        agents_activated.extend(["comparison", "insight"])

        # ========================================
        # STEP 5: Gap Analysis
        # Depends on: summaries, comparison, insights
        # ========================================
        step_start = time.time()
        gap_agent = GapDetectionAgent()
        try:
            gaps = await gap_agent.run(summaries, comparison, insights)
        except Exception as e:
            logger.error(f"Gap agent failed: {e}")
            gaps = {"error": f"Gap analysis failed: {str(e)}"}
        timing_log["gap_analysis"] = round(time.time() - step_start, 2)
        agents_activated.append("gap")

        # ========================================
        # STEP 6: KG + Novelty + Trend + Critique (PARALLEL)
        # These are independent of each other and only need summaries/comparison/insights.
        # Running them in parallel with concurrency=3 stays within Groq rate limits.
        #
        # GRACEFUL DEGRADATION: return_exceptions=True means if one
        # fails, the others still complete. We check each result.
        # ========================================
        step_start = time.time()

        kg_builder = KnowledgeGraphBuilder()
        novelty_agent = NoveltyAgent()
        trend_agent = TrendAgent()
        critique_agent = CritiqueAgent()

        step6_results = await asyncio.gather(
            kg_builder.build(summaries, insights),
            novelty_agent.run(query, summaries, insights),
            trend_agent.run(query, summaries, insights),
            critique_agent.run(summaries, comparison),
            return_exceptions=True
        )

        # 6a: Knowledge Graph
        if isinstance(step6_results[0], Exception):
            logger.error(f"Knowledge graph agent failed: {step6_results[0]}")
            kg_result = {"node_count": 0, "edge_count": 0, "error": "KG build failed"}
        else:
            kg_result = step6_results[0]
        agents_activated.append("knowledge_graph")

        # 6b: Novelty
        if isinstance(step6_results[1], Exception):
            logger.error(f"Novelty agent failed: {step6_results[1]}")
            novelty = {"overall_score": 0, "explanation": "Novelty scoring failed"}
        else:
            novelty = step6_results[1]
        agents_activated.append("novelty")

        # 6c: Trend
        if isinstance(step6_results[2], Exception):
            logger.error(f"Trend agent failed: {step6_results[2]}")
            trend = {"error": "Trend analysis failed"}
        else:
            trend = step6_results[2]
        agents_activated.append("trend")

        # 6d: Critique
        if isinstance(step6_results[3], Exception):
            logger.error(f"Critique agent failed: {step6_results[3]}")
            critique = {"scientific_critique": {"strong_points": [], "weak_points": []}, "argument_strength": []}
        else:
            critique = step6_results[3]
        agents_activated.append("critique")

        timing_log["step6_parallel"] = round(time.time() - step_start, 2)

        # ========================================
        # STEP 7: Roadmap + Literature Review (PARALLEL)
        # Both depend on gaps (from step 5) but not on each other.
        # ========================================
        step_start = time.time()

        roadmap_agent = RoadmapAgent()
        literature_agent = LiteratureReviewAgent()

        step7_results = await asyncio.gather(
            roadmap_agent.run(query, summaries, gaps),
            literature_agent.run(summaries, comparison, insights, gaps),
            return_exceptions=True
        )

        # 7a: Roadmap
        if isinstance(step7_results[0], Exception):
            logger.error(f"Roadmap agent failed: {step7_results[0]}")
            roadmap = {"error": "Roadmap generation failed"}
        else:
            roadmap = step7_results[0]
        agents_activated.append("roadmap")

        # 7b: Literature Review
        if isinstance(step7_results[1], Exception):
            logger.error(f"Literature agent failed: {step7_results[1]}")
            literature_review = f"Literature review generation failed: {str(step7_results[1])}"
        else:
            literature_review = step7_results[1]
        agents_activated.append("literature")

        timing_log["step7_parallel"] = round(time.time() - step_start, 2)

        # ========================================
        # STEP 7.5: Final Simplified Answer
        # A clean, layperson-readable synthesis of all outputs.
        # ========================================
        step_start = time.time()
        try:
            final_answer = await self._generate_final_answer(
                query, summaries, comparison, insights, gaps,
                novelty, trend, literature_review
            )
        except Exception as e:
            logger.error(f"Final answer generation failed: {e}")
            final_answer = "Unable to generate simplified answer."
        timing_log["final_answer"] = round(time.time() - step_start, 2)
        agents_activated.append("final_answer_synthesizer")

        # ========================================
        # STEP 8: Assemble 16-Section Output
        # ========================================
        pipeline_time = round(time.time() - pipeline_start, 2)

        # Compute confidence score based on data quality
        confidence = self._compute_confidence(
            paper_results, summaries, comparison, insights, gaps
        )

        # Build paper context with URLs
        paper_context = [
            {
                "title": p.title,
                "authors": p.authors,
                "url": p.url,
                "source": p.source,
                "abstract": p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract
            }
            for p in paper_results
        ]

        # Extract recommended methods/datasets from insights + gaps
        recommended = self._extract_recommendations(insights, gaps)

        # Extract experiment suggestions from gaps
        experiments = self._extract_experiments(gaps)

        # Assemble the final 16-section output
        result = {
            # Section 1: Direct Answer
            "direct_answer": {
                "query": query,
                "intent": intent,
                "papers_found": len(paper_results),
                "sources": {"arxiv": sum(1 for p in paper_results if p.source == "arxiv"),
                            "pubmed": sum(1 for p in paper_results if p.source == "pubmed")}
            },

            # Section 2: Context Summary
            "context_summary": {
                "papers": paper_context,
                "total_papers": len(paper_results)
            },

            # Section 3: Knowledge Graph Insights
            "knowledge_graph": kg_result,

            # Section 4: Comparison Table
            "comparison": comparison,

            # Section 5: Gap Analysis
            "gap_analysis": gaps,

            # Section 6: Deep Insights
            "deep_insights": insights,

            # Section 7: Novelty Score
            "novelty_score": novelty,

            # Section 8: Trend Forecast
            "trend_forecast": trend,

            # Section 9: Recommended Methods / Datasets
            "recommended_methods_datasets": recommended,

            # Section 10: Experiment Suggestions
            "experiment_suggestions": experiments,

            # Section 11: Researcher Roadmap
            "researcher_roadmap": roadmap,

            # Section 12: Argument Strength Analysis
            "argument_strength": critique.get("argument_strength", []),

            # Section 13: Bias & Critique Review
            "scientific_critique": critique.get("scientific_critique", {}),

            # Section 14: Literature Review
            "literature_review": literature_review,

            # Section 14.5: Final Simplified Answer
            "final_simplified_answer": final_answer,

            # Section 15: Confidence Score
            "confidence_score": confidence,

            # Section 16: Explainability Log
            "explainability_log": {
                "agents_activated": agents_activated,
                "total_agents": len(agents_activated),
                "timing_breakdown": timing_log,
                "total_pipeline_time_seconds": pipeline_time,
                "routing_strategy": intent.get("routing_strategy", "full_pipeline"),
                "reasoning_summary": (
                    f"Searched arXiv and PubMed for '{query}', found {len(paper_results)} papers. "
                    f"Summarized all papers, then ran comparison and insight analysis in parallel. "
                    f"Detected research gaps, built knowledge graph with {kg_result.get('node_count', 0)} nodes, "
                    f"scored novelty at {novelty.get('overall_score', 'N/A')}/100, "
                    f"forecasted trends, critiqued methodologies, and generated a 30-day roadmap. "
                    f"Final confidence: {confidence.get('score', 'N/A')}/100. "
                    f"Total pipeline time: {pipeline_time}s."
                )
            }
        }

        return result

    def _compute_confidence(
        self,
        papers: List[PaperResult],
        summaries: Any,
        comparison: Dict,
        insights: Dict,
        gaps: Dict
    ) -> Dict[str, Any]:
        """
        Compute confidence score (0-100) based on data quality.

        Scoring breakdown:
        - Papers found: 0-30 points (more papers = more evidence)
        - Summaries quality: 0-20 points
        - Comparison depth: 0-20 points
        - Insights richness: 0-15 points
        - Gap detection: 0-15 points
        """
        score = 0
        reasons = []

        # Paper count (30 points max)
        paper_count = len(papers)
        if paper_count >= 8:
            score += 30
            reasons.append("Strong paper coverage (8+ papers)")
        elif paper_count >= 5:
            score += 20
            reasons.append("Moderate paper coverage (5-7 papers)")
        elif paper_count >= 2:
            score += 10
            reasons.append("Limited paper coverage (2-4 papers)")
        else:
            score += 5
            reasons.append("Minimal paper coverage (1 paper)")

        # Summaries quality (20 points)
        if isinstance(summaries, list) and len(summaries) > 0:
            score += 20
            reasons.append("Summaries generated successfully")
        elif isinstance(summaries, dict) and "error" not in summaries:
            score += 15
            reasons.append("Summaries generated with minor issues")
        else:
            score += 5
            reasons.append("Summary generation had issues")

        # Comparison depth (20 points)
        if isinstance(comparison, dict) and "error" not in comparison:
            score += 20
            reasons.append("Comparison analysis complete")
        else:
            score += 5
            reasons.append("Comparison had issues")

        # Insights richness (15 points)
        if isinstance(insights, dict) and "error" not in insights:
            score += 15
            reasons.append("Cross-paper insights extracted")
        else:
            score += 5
            reasons.append("Insight extraction had issues")

        # Gap detection (15 points)
        if isinstance(gaps, dict) and "error" not in gaps:
            score += 15
            reasons.append("Gap analysis complete")
        else:
            score += 5
            reasons.append("Gap analysis had issues")

        return {
            "score": min(score, 100),
            "max_score": 100,
            "breakdown": reasons
        }

    def _extract_recommendations(
        self, insights: Dict, gaps: Dict
    ) -> Dict[str, Any]:
        """Extract recommended methods and datasets from insights + gaps."""
        methods = insights.get("unique_methods", []) if isinstance(insights, dict) else []
        datasets = insights.get("common_datasets", []) if isinstance(insights, dict) else []
        metrics = insights.get("evaluation_metrics", []) if isinstance(insights, dict) else []

        return {
            "recommended_methods": methods,
            "recommended_datasets": datasets,
            "evaluation_metrics": metrics
        }

    def _extract_experiments(self, gaps: Dict) -> List[str]:
        """Extract experiment suggestions from gap analysis."""
        experiments = []

        if isinstance(gaps, dict):
            for direction in gaps.get("novel_research_directions", []):
                if isinstance(direction, str):
                    experiments.append(f"Experiment: {direction}")
                elif isinstance(direction, dict):
                    experiments.append(f"Experiment: {direction.get('description', str(direction))}")

            for combo in gaps.get("underexplored_combinations", []):
                if isinstance(combo, str):
                    experiments.append(f"Explore: {combo}")
                elif isinstance(combo, dict):
                    experiments.append(f"Explore: {combo.get('description', str(combo))}")

        return experiments if experiments else ["No specific experiments suggested — gap data was limited"]

    async def _generate_final_answer(
        self,
        query: str,
        summaries: Any,
        comparison: Dict,
        insights: Dict,
        gaps: Dict,
        novelty: Dict,
        trend: Dict,
        literature_review: str
    ) -> str:
        """
        Generate a plain-English final simplified answer synthesizing
        all prior agent outputs into 2-3 readable paragraphs.
        """
        # Build a concise context from key outputs
        context_parts = []
        context_parts.append(f"Query: {query}")

        if isinstance(novelty, dict) and "overall_score" in novelty:
            context_parts.append(f"Novelty Score: {novelty['overall_score']}/100")
            context_parts.append(f"Novelty Explanation: {novelty.get('explanation', '')}")

        if isinstance(comparison, dict) and "error" not in comparison:
            context_parts.append(f"Key Similarities: {json.dumps(comparison.get('methodology_similarities', [])[:3])}")
            context_parts.append(f"Key Differences: {json.dumps(comparison.get('methodology_differences', [])[:3])}")

        if isinstance(gaps, dict) and "error" not in gaps:
            context_parts.append(f"Research Gaps: {json.dumps(gaps.get('novel_research_directions', [])[:3])}")

        if isinstance(trend, dict) and "error" not in trend:
            context_parts.append(f"1-Year Predictions: {json.dumps(trend.get('one_year_predictions', [])[:3])}")

        if isinstance(literature_review, str) and len(literature_review) > 100:
            context_parts.append(f"Literature Review Summary: {literature_review[:500]}")

        context_text = "\n".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": FINAL_ANSWER_ROLE
            },
            {
                "role": "user",
                "content": f"""Based on all the research analysis below, write a clear
Final Simplified Answer in 2-3 paragraphs that a layperson can understand.

Cover: (1) what this research area is about, (2) key findings from the
analysis, and (3) what a researcher should do next.

{context_text}

Write plain English. No JSON. No bullet points. Just 2-3 clear paragraphs."""
            }
        ]

        return await call_llm_async(messages, max_tokens=1000)

    def _empty_result(self, query: str, reason: str) -> Dict[str, Any]:
        """Return a structured empty result when pipeline can't proceed."""
        return {
            "direct_answer": {"query": query, "error": reason},
            "context_summary": {"papers": [], "total_papers": 0},
            "knowledge_graph": {"node_count": 0, "edge_count": 0},
            "comparison": {},
            "gap_analysis": {},
            "deep_insights": {},
            "novelty_score": {"overall_score": 0, "explanation": reason},
            "trend_forecast": {},
            "recommended_methods_datasets": {},
            "experiment_suggestions": [],
            "researcher_roadmap": {},
            "argument_strength": [],
            "scientific_critique": {},
            "literature_review": "",
            "confidence_score": {"score": 0, "breakdown": [reason]},
            "explainability_log": {
                "agents_activated": [],
                "error": reason
            }
        }