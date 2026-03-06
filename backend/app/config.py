"""Application configuration loaded from environment variables.

Security-hardened for government/enterprise deployment.
"""

import os
import secrets
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "FAR Compliance Copilot API"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False  # SECURITY: Default to False, require explicit override

    # Security / Auth
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Auto-generated if not set
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Short-lived tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password requirements (Day 1 Secure Auth from Audit Report)
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBER: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # API Key Authentication
    API_KEY: str = ""

    # Database (PostgreSQL for production, SQLite for dev)
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Audit Database (Separate for compliance)
    AUDIT_DATABASE_URL: Optional[str] = None
    AUDIT_SECRET_KEY: str = secrets.token_urlsafe(32)

    # CORS Origins
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    # HTTPS enforcement
    FORCE_HTTPS: bool = False

    # LLM Providers
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.0
    LLM_PROVIDER: str = "openai"
    
    # EMBEDDING
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vectors / Files
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    KNOWLEDGE_BASE_DIR: str = "./data/knowledge_base"

    # Rate limiting
    RATE_LIMIT: str = "30/minute"
    AUTH_RATE_LIMIT: str = "5/minute"

    # RAG / Compliance settings
    CONFIDENCE_THRESHOLD: float = 0.8
    CITATION_CONFIDENCE_THRESHOLD: float = 0.8
    ENABLE_SEMANTIC_CACHE: bool = True
    SEMANTIC_CACHE_TTL_SECONDS: int = 3600
    BLOCK_LOW_CONFIDENCE: bool = True

    # Government data sources
    FAR_XML_URL: str = "https://www.acquisition.gov/far/far-xml"
    DFARS_XML_URL: str = "https://www.acquisition.gov/dfars/dfars-xml"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        case_sensitive = True
        extra = "ignore"


settings = Settings()

# Startup Validation
def validate_settings():
    issues = []
    if settings.DEBUG:
        issues.append("WARNING: Debug mode enabled - DO NOT use in production!")
    if not os.getenv("SECRET_KEY") and not os.path.exists(".env"):
        issues.append("WARNING: SECRET_KEY not set and no .env file found - using random value")
    if not settings.OPENAI_API_KEY:
        issues.append("CRITICAL: OPENAI_API_KEY not configured")
    return issues


# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.KNOWLEDGE_BASE_DIR).mkdir(parents=True, exist_ok=True)

# Run validation on import
for msg in validate_settings():
    print(f"[{'CRITICAL' if 'CRITICAL' in msg else 'WARNING'}] {msg}")
