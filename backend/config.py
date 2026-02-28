"""
Centralized configuration for ResearchHub AI Backend.

WHY THIS EXISTS:
Instead of every file doing its own os.getenv() + load_dotenv(),
we load ALL settings once here. Any file can just do:
    from config import settings
    print(settings.GROQ_API_KEY)

Pydantic's BaseSettings auto-reads from .env file.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str

    # --- Auth ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- LLM (Groq) ---
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024
    LLM_CONCURRENCY: int = 3  # max concurrent Groq API calls (3 is safe for free tier ~30 req/min)

    # --- Paper Search ---
    ARXIV_MAX_RESULTS: int = 5
    PUBMED_MAX_RESULTS: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"  # ignore extra vars in .env


settings = Settings()
