"""Query related Pydantic models."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class HealthCheck(BaseModel):
    """Model for health check response."""
    status: str
    timestamp: datetime
    qdrant_status: str
    rag_status: str


class ErrorResponse(BaseModel):
    """Model for error responses."""
    detail: str
    error_type: Optional[str] = None


class QueryRequest(BaseModel):
    """Model for RAG query request."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=100)

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v):
        """Ensure query is not just whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty or just whitespace')
        return v.strip()


class SourceChunk(BaseModel):
    """Model for a source chunk retrieved from vector database."""
    text: str
    document_id: str
    filename: str
    score: float
    chunk_index: int
    summary: str | None = None  # AI-generated summary
    title: str | None = None  # AI-generated title


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str
    sources: List[SourceChunk]
    query: str
    processing_time_seconds: float
