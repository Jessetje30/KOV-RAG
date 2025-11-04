"""Query endpoint for RAG system."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import QueryRequest, QueryResponse, SourceChunk, User
from auth import get_current_user
from dependencies import get_rag_pipeline

logger = logging.getLogger(__name__)

# Rate limiter for query endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/minute")
async def query_documents(
    request: Request,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_user),
    rag_pipeline = Depends(get_rag_pipeline)
):
    """
    Query the RAG system with a question.

    Args:
        query_data: Query request with question and parameters
        current_user: Current authenticated user
        rag_pipeline: RAG pipeline instance

    Returns:
        QueryResponse: Generated answer with sources

    Raises:
        HTTPException: If query processing fails
    """
    try:
        # Execute RAG query
        answer, sources, processing_time = rag_pipeline.query(
            user_id=current_user.id,
            query_text=query_data.query,
            top_k=query_data.top_k
        )

        # Convert sources to response models
        source_chunks = [
            SourceChunk(
                text=source["text"],
                document_id=source["document_id"],
                filename=source["filename"],
                score=source["score"],
                chunk_index=source["chunk_index"],
                summary=source.get("summary"),  # AI-generated summary
                title=source.get("title")  # AI-generated title
            )
            for source in sources
        ]

        logger.info(f"Query by {current_user.username}: '{query_data.query}' ({processing_time:.2f}s)")

        return QueryResponse(
            answer=answer,
            sources=source_chunks,
            query=query_data.query,
            processing_time_seconds=round(processing_time, 2)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )
