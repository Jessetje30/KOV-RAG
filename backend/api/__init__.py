"""API module."""
from .routes import (
    health_router,
    auth_router,
    documents_router,
    query_router,
    chat_router,
    admin_router,
)

__all__ = [
    "health_router",
    "auth_router",
    "documents_router",
    "query_router",
    "chat_router",
    "admin_router",
]
