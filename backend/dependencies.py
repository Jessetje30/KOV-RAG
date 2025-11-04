"""Shared dependencies for FastAPI routes."""
from fastapi import Depends, HTTPException, status, Request

def get_rag_pipeline(request: Request):
    """
    Dependency to get the RAG pipeline instance from app state.
    This ensures we get the initialized pipeline after lifespan startup.
    """
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)

    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline is not initialized"
        )

    return rag_pipeline
