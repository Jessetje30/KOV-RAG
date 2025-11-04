"""Chat related Pydantic models."""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


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
