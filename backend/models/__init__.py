"""Pydantic models for API validation."""

# Auth models
from .auth import (
    UserRegister,
    UserLogin,
    User,
    Token,
    TokenData
)

# Document models
from .document import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListResponse
)

# Chat models
from .chat import (
    ChatMessage,
    ChatSessionCreate,
    ChatSession,
    ChatSessionSummary,
    ChatQueryRequest,
    Citation,
    ChatQueryResponse
)

# Query models
from .query import (
    HealthCheck,
    ErrorResponse,
    QueryRequest,
    SourceChunk,
    QueryResponse
)

# Admin models
from .admin import (
    InviteUserRequest,
    InvitationResponse,
    InvitationListResponse,
    UserAdminResponse,
    UserListResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    ValidateInvitationResponse,
    SetupAccountRequest,
    SetupAccountResponse
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "User",
    "Token",
    "TokenData",
    # Document
    "DocumentUploadResponse",
    "DocumentInfo",
    "DocumentListResponse",
    # Chat
    "ChatMessage",
    "ChatSessionCreate",
    "ChatSession",
    "ChatSessionSummary",
    "ChatQueryRequest",
    "Citation",
    "ChatQueryResponse",
    # Query
    "HealthCheck",
    "ErrorResponse",
    "QueryRequest",
    "SourceChunk",
    "QueryResponse",
    # Admin
    "InviteUserRequest",
    "InvitationResponse",
    "InvitationListResponse",
    "UserAdminResponse",
    "UserListResponse",
    "UpdateUserRequest",
    "UpdateUserResponse",
    "ValidateInvitationResponse",
    "SetupAccountRequest",
    "SetupAccountResponse",
]
