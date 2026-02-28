"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "FAR Copilot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Auth
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # LLM Providers (OpenAI-compatible)
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    # Selected Provider (default: openai)
    LLM_PROVIDER: str = "openai" 

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # File uploads
    UPLOAD_DIR: str = "./uploads"

    # Rate limiting
    RATE_LIMIT: str = "30/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
