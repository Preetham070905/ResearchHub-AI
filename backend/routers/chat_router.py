"""
Chat Router — the main API endpoint for research analysis.

WHY THIS IS THE KEY ENDPOINT:
All the agents, services, and orchestrator exist to serve ONE purpose:
answering research queries. This router is the front door.

POST /chat/analyze
- Takes: { "query": "your research question", "workspace_id": 1 }
- Returns: Full 16-section analysis (see walkthrough for format)
- If workspace_id is provided, saves result to DB for history

The endpoint is async because the pipeline makes many LLM calls.
A typical query takes 30-90 seconds to complete.
"""

import time
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, AnalysisResult, Workspace, Conversation
from auth import get_current_user
from schemas import ChatRequest, ChatResponse, ConversationResponse
from agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat & Analysis"])


@router.post("/analyze", response_model=ChatResponse)
async def analyze(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run the full multi-agent research analysis pipeline.

    This endpoint:
    1. Validates the request
    2. Runs the orchestrator (all 11 agents + services)
    3. Saves the result to DB (if workspace_id provided)
    4. Returns the 16-section output

    Typical response time: 30-90 seconds.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Validate workspace ownership if workspace_id provided
    if request.workspace_id:
        workspace = db.query(Workspace).filter(
            Workspace.id == request.workspace_id,
            Workspace.owner_id == current_user.id
        ).first()

        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

    # Run the full pipeline
    start_time = time.time()

    try:
        orchestrator = AgentOrchestrator()
        result = await orchestrator.run(request.query, workspace_id=request.workspace_id)
    except Exception as e:
        logger.error(f"Pipeline failed for query '{request.query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(e)}"
        )

    pipeline_time = round(time.time() - start_time, 2)

    # Save to database if workspace is specified
    if request.workspace_id:
        try:
            analysis = AnalysisResult(
                workspace_id=request.workspace_id,
                user_id=current_user.id,
                query=request.query,
                result_json=result
            )
            db.add(analysis)

            # Also save to conversation history
            ai_summary = result.get("final_simplified_answer", "") or result.get("direct_answer", {}).get("query", "Analysis complete")
            if isinstance(ai_summary, dict):
                ai_summary = json.dumps(ai_summary)
            conversation = Conversation(
                workspace_id=request.workspace_id,
                user_message=request.query,
                ai_response=str(ai_summary)[:2000]
            )
            db.add(conversation)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            # Don't fail the request if DB save fails — still return the result

    return ChatResponse(
        query=request.query,
        result=result,
        pipeline_time_seconds=pipeline_time
    )


@router.get("/history/{workspace_id}")
def get_analysis_history(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get past analysis results for a workspace.
    Returns list of past queries with timestamps (without full results for speed).
    """
    # Verify workspace ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    analyses = db.query(AnalysisResult).filter(
        AnalysisResult.workspace_id == workspace_id
    ).order_by(AnalysisResult.created_at.desc()).all()

    return [
        {
            "id": a.id,
            "query": a.query,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in analyses
    ]


@router.get("/result/{analysis_id}")
def get_analysis_result(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the full result of a past analysis by its ID."""
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.id == analysis_id,
        AnalysisResult.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "id": analysis.id,
        "query": analysis.query,
        "result": analysis.result_json,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None
    }


@router.get("/conversations/{workspace_id}", response_model=List[ConversationResponse])
def get_conversations(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation history for a workspace."""
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    conversations = db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id
    ).order_by(Conversation.timestamp.desc()).all()

    return conversations
