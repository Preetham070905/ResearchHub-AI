from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import os
import shutil

from database import get_db
from models import Paper, Workspace, User
from auth import get_current_user
from schemas import PaperResponse

router = APIRouter(prefix="/papers", tags=["Papers"])

MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".pdf"}


class PaperImportRequest(BaseModel):
    title: str
    authors: str
    abstract: str
    year: str = ""
    source: str = ""
    url: str = ""


# ---------------- UPLOAD PAPER ----------------
@router.post("/{workspace_id}", response_model=PaperResponse)
async def upload_paper(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Verify workspace ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Only PDF files are allowed."
        )

    # Validate file size (read and check)
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed is {MAX_FILE_SIZE_MB} MB."
        )

    # Create workspace uploads directory
    upload_dir = f"uploads/workspace_{workspace_id}"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    # Save metadata to DB
    new_paper = Paper(
        filename=file.filename,
        workspace_id=workspace_id
    )

    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)

    return new_paper


# ---------------- LIST PAPERS IN WORKSPACE ----------------
@router.get("/{workspace_id}", response_model=List[PaperResponse])
def list_papers(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    papers = db.query(Paper).filter(
        Paper.workspace_id == workspace_id
    ).all()

    return papers


# ---------------- DELETE PAPER ----------------
@router.delete("/{workspace_id}/{paper_id}")
def delete_paper(
    workspace_id: int,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.workspace_id == workspace_id
    ).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Delete file from disk
    file_path = os.path.join(f"uploads/workspace_{workspace_id}", paper.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(paper)
    db.commit()

    return {"message": "Paper deleted successfully"}


# ---------------- DOWNLOAD PAPER ----------------
@router.get("/{workspace_id}/{paper_id}/download")
def download_paper(
    workspace_id: int,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.workspace_id == workspace_id
    ).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    file_path = os.path.join(f"uploads/workspace_{workspace_id}", paper.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=paper.filename,
        media_type="application/pdf"
    )


# ---------------- IMPORT PAPER FROM SEARCH ----------------
@router.post("/{workspace_id}/import", response_model=PaperResponse)
def import_paper(
    workspace_id: int,
    request: PaperImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import a paper from search results (metadata only, no PDF file)."""
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Use title as filename for imported papers
    safe_title = "".join(c for c in request.title if c.isalnum() or c in " -_").strip()[:100]
    filename = f"[{request.source}] {safe_title}.pdf" if safe_title else f"imported_paper_{request.source}.pdf"

    new_paper = Paper(
        filename=filename,
        workspace_id=workspace_id
    )

    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)

    return new_paper