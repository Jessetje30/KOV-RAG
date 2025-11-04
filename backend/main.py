"""
FastAPI main application for RAG system.
Main entry point that initializes app and registers route modules.
"""
import os
from pathlib import Path
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from rag_bbl import BBLRAGPipeline

# Import routers
from api import (
    health_router,
    auth_router,
    documents_router,
    query_router,
    chat_router,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global RAG pipeline instance
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    global rag_pipeline
    rag_pipeline = BBLRAGPipeline()  # Use BBL-specific collection
    app.state.rag_pipeline = rag_pipeline  # Store in app state
    logger.info("RAG pipeline initialized")

    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down application...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG Application API",
    description="GDPR-compliant RAG system with OpenAI GPT-5 and Qdrant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
# Parse CORS_ORIGINS from environment (comma-separated list)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS]  # Remove whitespace

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(chat_router)


# Run application
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
