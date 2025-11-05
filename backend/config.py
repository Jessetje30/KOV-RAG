"""
Centralized configuration for RAG BBL application.
All environment variables are loaded here.
"""
import os
from functools import lru_cache

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_app.db")

# ============================================================================
# QDRANT CONFIGURATION
# ============================================================================
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# ============================================================================
# OPENAI CONFIGURATION
# ============================================================================
_openai_key = os.getenv("OPENAI_API_KEY", "")
if not _openai_key or _openai_key in [
    "your-openai-api-key-here",
    "your-new-openai-api-key-here",
    "sk-..."
]:
    raise ValueError(
        "CRITICAL SECURITY ERROR: OPENAI_API_KEY must be set in .env file!\n"
        "Get your API key from: https://platform.openai.com/api-keys\n"
        "Then add it to backend/.env: OPENAI_API_KEY=<your-api-key>"
    )
OPENAI_API_KEY = _openai_key
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4-turbo")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# ============================================================================
# RAG CONFIGURATION
# ============================================================================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "100"))
MINIMUM_RELEVANCE_THRESHOLD = float(os.getenv("MINIMUM_RELEVANCE_THRESHOLD", "0.4"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))

# ============================================================================
# FILE UPLOAD CONFIGURATION
# ============================================================================
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# ============================================================================
# JWT CONFIGURATION
# ============================================================================
# Fail fast if SECRET_KEY or JWT_SECRET_KEY is not set
_jwt_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
if not _jwt_secret or _jwt_secret in [
    "your-secret-key-change-in-production",
    "your_jwt_secret_key_here",
    "your-secure-jwt-secret-key-here"
]:
    raise ValueError(
        "CRITICAL SECURITY ERROR: JWT_SECRET_KEY must be set in .env file!\n"
        "Generate a secure key with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
        "Then add it to backend/.env: JWT_SECRET_KEY=<your-generated-key>"
    )
SECRET_KEY = _jwt_secret
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# EMBEDDING CONFIGURATION
# ============================================================================
EMBEDDING_DIMENSION = 3072  # text-embedding-3-large dimension


@lru_cache()
def get_settings():
    """
    Cached settings instance.
    Use this in FastAPI dependencies.
    """
    return {
        "database_url": DATABASE_URL,
        "qdrant_host": QDRANT_HOST,
        "qdrant_port": QDRANT_PORT,
        "openai_api_key": OPENAI_API_KEY,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
