"""Document management endpoints."""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from models import DocumentUploadResponse, DocumentListResponse, DocumentInfo, User
from auth import get_current_user
from dependencies import get_rag_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Maximum file size (from environment or default to 10MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
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
        # Validate file extension
        allowed_extensions = ['pdf', 'docx', 'txt']
        file_extension = file.filename.lower().split('.')[-1]

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

        # Process document
        document_id, chunks_count = rag_pipeline.process_document(
            user_id=current_user.id,
            filename=file.filename,
            file_content=file_content,
            file_size=file_size
        )

        logger.info(f"Document uploaded by {current_user.username}: {file.filename} ({chunks_count} chunks)")

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
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
async def list_documents(
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
async def delete_document(
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
