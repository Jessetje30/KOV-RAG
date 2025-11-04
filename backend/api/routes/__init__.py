"""API route modules."""
from .health import router as health_router
from .auth import router as auth_router
from .documents import router as documents_router
from .query import router as query_router
from .chat import router as chat_router

__all__ = [
    "health_router",
    "auth_router",
    "documents_router",
    "query_router",
    "chat_router",
]
