"""Document related Pydantic models."""
from pydantic import BaseModel
from typing import List


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
