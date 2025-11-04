"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Database session dependency for FastAPI.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create all tables)."""
    from db.models import UserDB, ChatSessionDB, ChatMessageDB
    Base.metadata.create_all(bind=engine)
