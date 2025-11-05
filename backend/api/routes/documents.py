"""Document management endpoints."""
import os
import logging
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import DocumentUploadResponse, DocumentListResponse, DocumentInfo, User
from auth import get_current_user
from dependencies import get_rag_pipeline

logger = logging.getLogger(__name__)

# Rate limiter for document endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename with only the basename

    Raises:
        ValueError: If filename is empty or invalid
    """
    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty")

    # Get only the basename (removes any path components)
    basename = Path(filename).name

    # Remove any remaining path traversal patterns
    basename = basename.replace("..", "").replace("/", "").replace("\\", "")

    # Remove or replace invalid characters
    # Allow: alphanumeric, dots, dashes, underscores, spaces
    basename = re.sub(r'[^a-zA-Z0-9._\- ]', '_', basename)

    # Ensure filename is not empty after sanitization
    if not basename or basename.strip() in ["", ".", ".."]:
        raise ValueError("Invalid filename after sanitization")

    # Limit filename length
    if len(basename) > 255:
        # Keep extension if possible
        name_parts = basename.rsplit('.', 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            basename = name[:250] + '.' + ext
        else:
            basename = basename[:255]

    return basename

# Maximum file size (from environment or default to 10MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    rag_pipeline = Depends(get_rag_pipeline)
):
    """
    Upload and process a document.

    Args:
        file: Uploaded file (PDF, DOCX, or TXT)
        current_user: Current authenticated user
        rag_pipeline: RAG pipeline instance

    Returns:
        DocumentUploadResponse: Upload result with document ID and chunk count

    Raises:
        HTTPException: If file processing fails
    """
    try:
        # Sanitize filename to prevent path traversal
        try:
            safe_filename = sanitize_filename(file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename: {str(e)}"
            )

        # Validate file extension
        allowed_extensions = ['pdf', 'docx', 'txt', 'xml']
        file_extension = safe_filename.lower().split('.')[-1]

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Process document with sanitized filename
        document_id, chunks_count = rag_pipeline.process_document(
            user_id=current_user.id,
            filename=safe_filename,
            file_content=file_content,
            file_size=file_size
        )

        logger.info(f"Document uploaded by {current_user.username}: {safe_filename} ({chunks_count} chunks)")

        return DocumentUploadResponse(
            document_id=document_id,
            filename=safe_filename,
            file_size=file_size,
            chunks_created=chunks_count,
            message="Document uploaded and processed successfully"
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )


@router.get("", response_model=DocumentListResponse)
@limiter.limit("30/minute")
async def list_documents(
    request: Request,
    current_user: User = Depends(get_current_user),
    rag_pipeline = Depends(get_rag_pipeline)
):
    """
    Get list of all documents for current user.

    Args:
        current_user: Current authenticated user
        rag_pipeline: RAG pipeline instance

    Returns:
        DocumentListResponse: List of user's documents
    """
    try:
        documents = rag_pipeline.get_user_documents(current_user.id)

        document_info_list = [
            DocumentInfo(
                document_id=doc["document_id"],
                filename=doc["filename"],
                file_size=doc["file_size"],
                upload_date=doc["upload_date"],
                chunks_count=doc["chunks_count"]
            )
            for doc in documents
        ]

        return DocumentListResponse(
            documents=document_info_list,
            total_count=len(document_info_list)
        )

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.delete("/{document_id}")
@limiter.limit("30/minute")
async def delete_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(get_current_user),
    rag_pipeline = Depends(get_rag_pipeline)
):
    """
    Delete a document and all its chunks.

    Args:
        document_id: Document ID to delete
        current_user: Current authenticated user
        rag_pipeline: RAG pipeline instance

    Returns:
        dict: Success message

    Raises:
        HTTPException: If deletion fails
    """
    try:
        rag_pipeline.delete_document(current_user.id, document_id)

        logger.info(f"Document deleted by {current_user.username}: {document_id}")

        return {"message": "Document deleted successfully", "document_id": document_id}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
