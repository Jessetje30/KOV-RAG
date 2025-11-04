"""
FastAPI main application for RAG system.
Handles authentication, document upload, and query endpoints.
"""
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from models import (
    UserRegister,
    UserLogin,
    Token,
    User,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
    QueryRequest,
    QueryResponse,
    SourceChunk,
    HealthCheck,
    ErrorResponse,
    ChatSessionCreate,
    ChatSession,
    ChatSessionSummary,
    ChatQueryRequest,
    ChatQueryResponse,
    Citation,
    ChatMessage
)
from db import get_db, UserRepository, ChatRepository, init_db, crud
from auth import create_access_token, get_current_user, get_current_user_db
from rag_bbl import BBLRAGPipeline  # Use BBL-specific RAG pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global RAG pipeline instance
rag_pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    global rag_pipeline
    rag_pipeline = BBLRAGPipeline()  # Use BBL-specific collection
    logger.info("RAG pipeline initialized")

    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down application...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG Application API",
    description="GDPR-compliant RAG system with OpenAI GPT-5 and Qdrant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
# Parse CORS_ORIGINS from environment (comma-separated list)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS]  # Remove whitespace

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Maximum file size (from environment or default to 10MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# Health Check Endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    rag_healthy = rag_pipeline.health_check() if rag_pipeline else False

    return HealthCheck(
        status="healthy" if rag_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc),
        qdrant_status="healthy",
        rag_status="healthy" if rag_healthy else "unhealthy"
    )


# Authentication Endpoints
@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If username or email already exists
    """
    try:
        # Create user
        db_user = UserRepository.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )

        # Create access token
        access_token = create_access_token(
            data={"sub": db_user.username, "user_id": db_user.id}
        )

        logger.info(f"New user registered: {db_user.username}")

        return Token(access_token=access_token)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token.

    Args:
        user_data: User login credentials
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = UserRepository.authenticate_user(
        db=db,
        username=user_data.username,
        password=user_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    logger.info(f"User logged in: {user.username}")

    return Token(access_token=access_token)


@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user information
    """
    return current_user


# Document Management Endpoints
@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process a document.

    Args:
        file: Uploaded file (PDF, DOCX, or TXT)
        current_user: Current authenticated user

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


@app.get("/api/documents", response_model=DocumentListResponse)
async def list_documents(current_user: User = Depends(get_current_user)):
    """
    Get list of all documents for current user.

    Args:
        current_user: Current authenticated user

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


@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document and all its chunks.

    Args:
        document_id: Document ID to delete
        current_user: Current authenticated user

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


# Query Endpoint
@app.post("/api/query", response_model=QueryResponse)
async def query_documents(
    query_data: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Query the RAG system with a question.

    Args:
        query_data: Query request with question and parameters
        current_user: Current authenticated user

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
                summary=source.get("summary")  # AI-generated summary
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


# Chat Session Endpoints
@app.post("/api/chat/sessions", response_model=ChatSession)
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


@app.get("/api/chat/sessions", response_model=List[ChatSessionSummary])
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


@app.get("/api/chat/sessions/{session_id}", response_model=ChatSession)
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


@app.delete("/api/chat/sessions/{session_id}")
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


@app.post("/api/chat/query", response_model=ChatQueryResponse)
async def chat_query(
    query_data: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in a chat session and get an AI response with inline citations.

    Args:
        query_data: Chat query with session_id and message
        current_user: Current authenticated user
        db: Database session

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


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Application API",
        "version": "1.0.0",
        "description": "GDPR-compliant RAG system with Mistral AI and Qdrant",
        "docs": "/docs",
        "health": "/health"
    }


# Run application
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
