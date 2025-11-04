"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL

# Create SQLAlchemy engine with connection pooling and timeouts
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

# Add timeout for non-SQLite databases
if "sqlite" not in DATABASE_URL:
    connect_args["connect_timeout"] = 10  # 10 seconds connection timeout

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,  # Maximum 5 connections in pool
    max_overflow=10  # Allow 10 additional connections if pool is full
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
