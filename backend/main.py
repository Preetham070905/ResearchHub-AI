"""
ResearchHub AI Backend — v4.0
Multi-agent scientific reasoning system.

This is the FastAPI entry point. All it does:
1. Load environment variables
2. Configure logging
3. Set up CORS (so frontend can talk to backend)
4. Include all 4 routers (auth, workspace, paper, chat)
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import auth_router
from routers import workspace_router
from routers import paper_router
from routers import chat_router
from routers import agent_router

load_dotenv()

# Auto-create all tables on startup (safe to call repeatedly)
from database import init_db
init_db()

# Configure logging so all agents/services log properly
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

app = FastAPI(
    title="ResearchHub AI",
    description="Multi-agent scientific reasoning system with 16-section analysis pipeline",
    version="4.0"
)

# CORS middleware — explicit origins required when credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router.router)
app.include_router(workspace_router.router)
app.include_router(paper_router.router)
app.include_router(chat_router.router)
app.include_router(agent_router.router)


@app.get("/")
def root():
    return {"message": "ResearchHub AI Backend Running", "version": "4.0"}
