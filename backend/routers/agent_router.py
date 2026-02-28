"""
Agent Router — exposes individual agent endpoints for the frontend.

Each agent can be called independently for interactive use.
The full orchestrator pipeline (/chat/analyze) chains them all together,
but these endpoints let users interact with agents one-at-a-time.
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import User

from services.paper_search import search_papers, PaperResult
from services.llm_service import call_llm_async
from services.knowledge_graph import KnowledgeGraphBuilder

from agents.summarizer_agent import SummarizerAgent
from agents.comparison_agent import ComparisonAgent
from agents.insight_agent import InsightAgent
from agents.gap_agent import GapDetectionAgent
from agents.novelty_agent import NoveltyAgent
from agents.trend_agent import TrendAgent
from agents.critique_agent import CritiqueAgent
from agents.roadmap_agent import RoadmapAgent
from agents.literature_agent import LiteratureReviewAgent
from agents.intent_router import IntentRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


class AgentRequest(BaseModel):
    query: str
    context: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5


# ── Paper Search ──────────────────────────────────────────────

@router.post("/search-papers")
async def agent_search_papers(
    req: SearchRequest,
    user: User = Depends(get_current_user),
):
    """Search arXiv + PubMed for papers matching a query."""
    try:
        papers = await search_papers(req.query, max_results=req.max_results)
        return {
            "agent": "paper_search",
            "papers": [
                {
                    "title": p.title,
                    "authors": ", ".join(p.authors) if isinstance(p.authors, list) else p.authors,
                    "abstract": p.abstract,
                    "year": getattr(p, 'year', ''),
                    "source": p.source,
                    "url": p.url,
                }
                for p in papers
            ],
        }
    except Exception as e:
        logger.error(f"Paper search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Helper: search + summarize (used by many agents) ─────────

async def _get_papers_and_summaries(query: str):
    """Common helper: search papers, then summarize them."""
    papers = await search_papers(query, max_results=5)
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found for this query")

    summarizer = SummarizerAgent()
    summaries = await summarizer.run(papers)
    return papers, summaries


# ── Summarizer ────────────────────────────────────────────────

@router.post("/summarize")
async def agent_summarize(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Search papers and generate structured summaries."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        return {"agent": "summarizer", "result": summaries}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarizer failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Comparison ────────────────────────────────────────────────

@router.post("/compare")
async def agent_compare(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Search papers, summarize, then compare methodologies."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        agent = ComparisonAgent()
        result = await agent.run(summaries)
        return {"agent": "comparison", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Insight ───────────────────────────────────────────────────

@router.post("/insights")
async def agent_insights(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Extract cross-paper insights from research summaries."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        agent = InsightAgent()
        result = await agent.run(summaries)
        return {"agent": "insight", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insight failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Gap Detection ─────────────────────────────────────────────

@router.post("/gaps")
async def agent_gaps(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Detect research gaps from combined analysis data."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        comparison_agent = ComparisonAgent()
        insight_agent = InsightAgent()
        comparison = await comparison_agent.run(summaries)
        insights = await insight_agent.run(summaries)
        agent = GapDetectionAgent()
        result = await agent.run(summaries, comparison, insights)
        return {"agent": "gap_detection", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gap detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Trend Forecast ────────────────────────────────────────────

@router.post("/trends")
async def agent_trends(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Forecast research trends based on current literature."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        insight_agent = InsightAgent()
        insights = await insight_agent.run(summaries)
        agent = TrendAgent()
        result = await agent.run(req.query, summaries, insights)
        return {"agent": "trend", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trend failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Novelty Scoring ───────────────────────────────────────────

@router.post("/novelty")
async def agent_novelty(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Score the novelty of a research direction."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        insight_agent = InsightAgent()
        insights = await insight_agent.run(summaries)
        agent = NoveltyAgent()
        result = await agent.run(req.query, summaries, insights)
        return {"agent": "novelty", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Novelty failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Critique ──────────────────────────────────────────────────

@router.post("/critique")
async def agent_critique(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Evaluate argument strength, biases, and methodology quality."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        comparison_agent = ComparisonAgent()
        comparison = await comparison_agent.run(summaries)
        agent = CritiqueAgent()
        result = await agent.run(summaries, comparison)
        return {"agent": "critique", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critique failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Roadmap ───────────────────────────────────────────────────

@router.post("/roadmap")
async def agent_roadmap(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Create a 30-day research action plan."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        insight_agent = InsightAgent()
        gap_agent = GapDetectionAgent()
        comparison_agent = ComparisonAgent()
        insights = await insight_agent.run(summaries)
        comparison = await comparison_agent.run(summaries)
        gaps = await gap_agent.run(summaries, comparison, insights)
        agent = RoadmapAgent()
        result = await agent.run(req.query, summaries, gaps)
        return {"agent": "roadmap", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Roadmap failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Literature Review ─────────────────────────────────────────

@router.post("/literature-review")
async def agent_literature_review(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Generate a structured literature review."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        comparison_agent = ComparisonAgent()
        insight_agent = InsightAgent()
        comparison = await comparison_agent.run(summaries)
        insights = await insight_agent.run(summaries)
        gap_agent = GapDetectionAgent()
        gaps = await gap_agent.run(summaries, comparison, insights)
        agent = LiteratureReviewAgent()
        result = await agent.run(summaries, comparison, insights, gaps)
        return {"agent": "literature_review", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Literature review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Knowledge Graph ───────────────────────────────────────────

@router.post("/knowledge-graph")
async def agent_knowledge_graph(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Build a knowledge graph and return nodes + edges for D3.js visualization."""
    try:
        papers, summaries = await _get_papers_and_summaries(req.query)
        insight_agent = InsightAgent()
        insights = await insight_agent.run(summaries)

        builder = KnowledgeGraphBuilder()
        kg_result = await builder.build(summaries, insights)

        # Also extract raw nodes + edges for D3 rendering
        nodes = []
        edges = []
        for n in builder.graph.nodes(data=True):
            nodes.append({
                "id": n[0],
                "type": n[1].get("type", "concept"),
                "label": n[0],
            })
        for e in builder.graph.edges(data=True):
            edges.append({
                "source": e[0],
                "target": e[1],
                "relation": e[2].get("relation", "relates_to"),
            })

        return {
            "agent": "knowledge_graph",
            "result": kg_result,
            "graph": {"nodes": nodes, "edges": edges},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KG build failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Intent Router ─────────────────────────────────────────────

@router.post("/route-intent")
async def agent_route_intent(
    req: AgentRequest,
    user: User = Depends(get_current_user),
):
    """Classify user query intent into a research category."""
    try:
        router_agent = IntentRouter()
        result = await router_agent.run(req.query)
        return {"agent": "intent_router", "result": result}
    except Exception as e:
        logger.error(f"Intent routing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
