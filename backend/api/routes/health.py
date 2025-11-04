"""Health check endpoint."""
from datetime import datetime, timezone
from fastapi import APIRouter
import logging

from models import HealthCheck

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    # Import rag_pipeline from main
    from main import rag_pipeline

    rag_healthy = rag_pipeline.health_check() if rag_pipeline else False

    return HealthCheck(
        status="healthy" if rag_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc),
        qdrant_status="healthy",
        rag_status="healthy" if rag_healthy else "unhealthy"
    )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Application API",
        "version": "1.0.0",
        "description": "GDPR-compliant RAG system with Mistral AI and Qdrant",
        "docs": "/docs",
        "health": "/health"
    }
