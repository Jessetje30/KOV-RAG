"""Chat session endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models import (
    ChatSessionCreate,
    ChatSession,
    ChatSessionSummary,
    ChatQueryRequest,
    ChatQueryResponse,
    Citation,
    ChatMessage,
    User
)
from db import get_db, ChatRepository
from auth import get_current_user
from dependencies import get_rag_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new chat session for the current user.

    Args:
        session_data: Session creation data with title
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatSession: Created session with empty messages list

    Raises:
        HTTPException: If session creation fails
    """
    try:
        session = ChatRepository.create_session(
            db=db,
            user_id=current_user.id,
            title=session_data.title
        )

        logger.info(f"Chat session created by {current_user.username}: {session.title}")

        return ChatSession(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[]
        )

    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@router.get("/sessions", response_model=List[ChatSessionSummary])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ChatSessionSummary]: List of user's chat sessions (without messages)
    """
    try:
        sessions = ChatRepository.get_user_sessions(db=db, user_id=current_user.id)

        return [
            ChatSessionSummary(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            for session in sessions
        ]

    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific chat session with all messages.

    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatSession: Session with messages

    Raises:
        HTTPException: If session not found or access denied
    """
    try:
        messages = ChatRepository.get_session_messages(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )

        session = ChatRepository.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        chat_messages = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                sources=msg.sources,
                created_at=msg.created_at
            )
            for msg in messages
        ]

        return ChatSession(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=chat_messages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all its messages.

    Args:
        session_id: Session ID to delete
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If session not found or access denied
    """
    try:
        deleted = ChatRepository.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        logger.info(f"Chat session deleted by {current_user.username}: {session_id}")

        return {"message": "Chat session deleted successfully", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )


@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(
    query_data: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag_pipeline = Depends(get_rag_pipeline)
):
    """
    Send a message in a chat session and get an AI response with inline citations.

    Args:
        query_data: Chat query with session_id and message
        current_user: Current authenticated user
        db: Database session
        rag_pipeline: RAG pipeline instance

    Returns:
        ChatQueryResponse: AI response with inline citations

    Raises:
        HTTPException: If query processing fails
    """
    try:
        # Verify session belongs to user
        session = ChatRepository.get_session(
            db=db,
            session_id=query_data.session_id,
            user_id=current_user.id
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        # Get conversation history
        messages = ChatRepository.get_session_messages(
            db=db,
            session_id=query_data.session_id,
            user_id=current_user.id
        )

        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Save user message
        ChatRepository.add_message(
            db=db,
            session_id=query_data.session_id,
            role="user",
            content=query_data.message,
            sources=None
        )

        # Execute RAG query with chat history
        answer, sources, processing_time = rag_pipeline.query_with_chat(
            user_id=current_user.id,
            query_text=query_data.message,
            chat_history=chat_history,
            top_k=query_data.top_k
        )

        # Convert sources to citations
        citations = [
            Citation(
                number=source["citation_number"],
                text=source["text"],
                document_id=source["document_id"],
                filename=source["filename"],
                score=source["score"],
                chunk_index=source["chunk_index"]
            )
            for source in sources
        ]

        # Save assistant response with citations
        citations_dict = [
            {
                "number": c.number,
                "text": c.text,
                "document_id": c.document_id,
                "filename": c.filename,
                "score": c.score,
                "chunk_index": c.chunk_index
            }
            for c in citations
        ]

        ChatRepository.add_message(
            db=db,
            session_id=query_data.session_id,
            role="assistant",
            content=answer,
            sources=citations_dict
        )

        logger.info(f"Chat query by {current_user.username} in session {query_data.session_id}: '{query_data.message}' ({processing_time:.2f}s)")

        return ChatQueryResponse(
            answer=answer,
            citations=citations,
            session_id=query_data.session_id,
            processing_time_seconds=round(processing_time, 2)
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat query"
        )
