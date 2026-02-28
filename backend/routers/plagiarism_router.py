"""
Plagiarism Router — API endpoints for plagiarism detection.

Endpoints:
  POST /plagiarism/check          — Check uploaded PDF against workspace papers
  POST /plagiarism/check-text     — Check raw text against workspace papers
  POST /plagiarism/compare-papers — Compare two specific papers against each other
"""

import os
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

import fitz  # PyMuPDF

from auth import get_current_user
from database import get_db
from models import User, Paper

from services.plagiarism_service import (
    DocumentInput,
    plagiarism_checker,
)
from agents.plagiarism_agent import PlagiarismAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plagiarism", tags=["plagiarism"])

plagiarism_agent = PlagiarismAgent()


# ── Helpers ───────────────────────────────────────────────────

def _extract_pdf_text(file_path: str, max_pages: int = 10) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(file_path)
        text_chunks = []
        for i in range(min(max_pages, len(doc))):
            text_chunks.append(doc.load_page(i).get_text())
        doc.close()
        return "\n".join(text_chunks).strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def _load_workspace_docs(workspace_id: int, db: Session, exclude_paper_id: Optional[int] = None) -> List[DocumentInput]:
    """Load all papers in a workspace as DocumentInput objects."""
    papers = db.query(Paper).filter(Paper.workspace_id == workspace_id).all()
    docs = []
    for paper in papers:
        if exclude_paper_id and paper.id == exclude_paper_id:
            continue

        # Try to extract text from the stored PDF
        upload_dir = f"uploads/workspace_{workspace_id}"
        file_path = os.path.join(upload_dir, paper.filename)

        if os.path.exists(file_path):
            text = _extract_pdf_text(file_path)
        else:
            # For imported papers (no PDF), use stored abstract/metadata
            text = getattr(paper, 'abstract', '') or paper.filename
        
        if text:
            docs.append(DocumentInput(
                id=str(paper.id),
                title=paper.filename.replace(".pdf", ""),
                text=text,
                source="workspace",
            ))

    return docs


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/check")
async def check_uploaded_file(
    file: UploadFile = File(...),
    workspace_id: int = Form(...),
    use_llm: bool = Form(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF and check it for plagiarism against all papers in the workspace.

    - **file**: PDF file to check
    - **workspace_id**: Workspace containing reference papers
    - **use_llm**: Whether to include LLM-powered interpretation (default: true)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    # Save uploaded file temporarily
    temp_path = f"uploads/_plagiarism_temp_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Extract text from uploaded PDF
        target_text = _extract_pdf_text(temp_path)
        if not target_text:
            raise HTTPException(400, "Could not extract text from the uploaded PDF.")

        target_doc = DocumentInput(
            id="uploaded",
            title=file.filename.replace(".pdf", ""),
            text=target_text,
            source="uploaded",
        )

        # Load workspace papers as reference
        ref_docs = _load_workspace_docs(workspace_id, db)
        if not ref_docs:
            return {
                "status": "no_references",
                "message": "No papers found in workspace to compare against.",
                "result": None,
            }

        # Run plagiarism check
        result = await plagiarism_agent.analyze(target_doc, ref_docs, use_llm=use_llm)

        return {"status": "success", "result": result}

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/check-text")
async def check_text(
    text: str = Form(...),
    title: str = Form("Untitled Document"),
    workspace_id: int = Form(...),
    use_llm: bool = Form(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check raw text for plagiarism against all papers in the workspace.

    - **text**: The text to check
    - **title**: Optional title for the document
    - **workspace_id**: Workspace containing reference papers
    """
    if len(text.strip()) < 50:
        raise HTTPException(400, "Text too short for meaningful plagiarism analysis.")

    target_doc = DocumentInput(
        id="text_input",
        title=title,
        text=text,
        source="text_input",
    )

    ref_docs = _load_workspace_docs(workspace_id, db)
    if not ref_docs:
        return {
            "status": "no_references",
            "message": "No papers found in workspace to compare against.",
            "result": None,
        }

    result = await plagiarism_agent.analyze(target_doc, ref_docs, use_llm=use_llm)
    return {"status": "success", "result": result}


@router.post("/compare-papers")
async def compare_two_papers(
    paper_a_id: int = Form(...),
    paper_b_id: int = Form(...),
    workspace_id: int = Form(...),
    use_llm: bool = Form(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare two specific papers in a workspace for similarity.

    - **paper_a_id**: First paper ID (the one being checked)
    - **paper_b_id**: Second paper ID (the reference)
    - **workspace_id**: Workspace both papers belong to
    """
    paper_a = db.query(Paper).filter(Paper.id == paper_a_id, Paper.workspace_id == workspace_id).first()
    paper_b = db.query(Paper).filter(Paper.id == paper_b_id, Paper.workspace_id == workspace_id).first()

    if not paper_a or not paper_b:
        raise HTTPException(404, "One or both papers not found in the workspace.")

    upload_dir = f"uploads/workspace_{workspace_id}"

    text_a = _extract_pdf_text(os.path.join(upload_dir, paper_a.filename))
    text_b = _extract_pdf_text(os.path.join(upload_dir, paper_b.filename))

    if not text_a or not text_b:
        raise HTTPException(400, "Could not extract text from one or both papers.")

    target = DocumentInput(
        id=str(paper_a.id),
        title=paper_a.filename.replace(".pdf", ""),
        text=text_a,
        source="workspace",
    )
    ref = DocumentInput(
        id=str(paper_b.id),
        title=paper_b.filename.replace(".pdf", ""),
        text=text_b,
        source="workspace",
    )

    result = await plagiarism_agent.analyze(target, [ref], use_llm=use_llm)
    return {"status": "success", "result": result}
