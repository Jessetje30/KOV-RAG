"""
Data models for the RAG application using Pydantic for validation.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


# User Authentication Models
class UserRegister(BaseModel):
    """Model for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        """Ensure username contains only alphanumeric characters and underscores."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v

    @field_validator('password')
    @classmethod
    def password_length_check(cls, v):
        """Ensure password is within bcrypt's 72-byte limit."""
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long. Maximum 72 characters allowed.')
        return v


class UserLogin(BaseModel):
    """Model for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Model for token payload data."""
    username: Optional[str] = None
    user_id: Optional[int] = None


class User(BaseModel):
    """Model for user data."""
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Document Models
class DocumentUploadResponse(BaseModel):
    """Response model after document upload."""
    document_id: str
    filename: str
    file_size: int
    chunks_created: int
    message: str


class DocumentInfo(BaseModel):
    """Model for document information."""
    document_id: str
    filename: str
    file_size: int
    upload_date: str
    chunks_count: int


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentInfo]
    total_count: int


# RAG Query Models
class QueryRequest(BaseModel):
    """Model for RAG query request."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=100)  # Verhoogd voor complete zoekresultaten

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


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str
    sources: List[SourceChunk]
    query: str
    processing_time_seconds: float


# Error Response Models
class ErrorResponse(BaseModel):
    """Model for error responses."""
    detail: str
    error_type: Optional[str] = None


# Health Check Model
class HealthCheck(BaseModel):
    """Model for health check response."""
    status: str
    timestamp: datetime
    qdrant_status: str
    mistral_status: str


# Chat Models
class ChatMessage(BaseModel):
    """Model for a chat message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    sources: Optional[List[dict]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    """Model for creating a new chat session."""
    title: str = Field(..., min_length=1, max_length=200)


class ChatSession(BaseModel):
    """Model for a chat session with messages."""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ChatMessage]] = []

    model_config = ConfigDict(from_attributes=True)


class ChatSessionSummary(BaseModel):
    """Model for chat session summary (without messages)."""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatQueryRequest(BaseModel):
    """Model for sending a message in a chat session."""
    session_id: int
    message: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=100)

    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v):
        """Ensure message is not just whitespace."""
        if not v.strip():
            raise ValueError('Message cannot be empty or just whitespace')
        return v.strip()


class Citation(BaseModel):
    """Model for an inline citation."""
    number: int
    text: str
    document_id: str
    filename: str
    score: float
    chunk_index: int


class ChatQueryResponse(BaseModel):
    """Response model for chat query with inline citations."""
    answer: str
    citations: List[Citation]
    session_id: int
    processing_time_seconds: float
