from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Workspace, User
from auth import get_current_user
from schemas import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# ---------------- CREATE WORKSPACE ----------------
@router.post("/", response_model=WorkspaceResponse)
def create_workspace(
    request: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_workspace = Workspace(
        name=request.name,
        owner_id=current_user.id
    )

    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)

    return new_workspace


# ---------------- LIST USER WORKSPACES ----------------
@router.get("/", response_model=List[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    workspaces = db.query(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).all()

    return workspaces


# ---------------- UPDATE WORKSPACE ----------------
@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: int,
    request: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Workspace name cannot be empty")

    workspace.name = request.name.strip()
    db.commit()
    db.refresh(workspace)

    return workspace


# ---------------- DELETE WORKSPACE ----------------
@router.delete("/{workspace_id}")
def delete_workspace(
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

    db.delete(workspace)
    db.commit()

    return {"message": "Workspace deleted successfully"}