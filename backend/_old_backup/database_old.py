"""
Database configuration and user management using SQLAlchemy and SQLite.
"""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session, relationship
from passlib.context import CryptContext
from typing import Optional, List

# Load environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_app.db")

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

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Helper function for timezone-aware UTC datetime
def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


# Helper function for password truncation (bcrypt 72-byte limit)
def truncate_password_for_bcrypt(password: str) -> str:
    """
    Truncate password to 72 bytes for bcrypt compatibility.

    Bcrypt has a maximum password length of 72 bytes. This function ensures
    passwords are truncated safely without breaking UTF-8 character boundaries.

    Args:
        password: Plain text password

    Returns:
        str: Truncated password (if needed) that's safe for bcrypt
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate byte by byte until we have valid UTF-8
        password_bytes = password_bytes[:72]
        while len(password_bytes) > 0:
            try:
                password_truncated = password_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                password_bytes = password_bytes[:-1]
        else:
            # Fallback: just use first 72 chars
            password_truncated = password[:72]
    else:
        password_truncated = password

    return password_truncated


# Database Models
class UserDB(Base):
    """SQLAlchemy model for users table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    chat_sessions = relationship("ChatSessionDB", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the hashed password.
        Truncates to 72 bytes to comply with bcrypt limitation.
        """
        password_truncated = truncate_password_for_bcrypt(password)
        return pwd_context.verify(password_truncated, self.hashed_password)


class ChatSessionDB(Base):
    """SQLAlchemy model for chat_sessions table."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("UserDB", back_populates="chat_sessions")
    messages = relationship("ChatMessageDB", back_populates="session", cascade="all, delete-orphan")


class ChatMessageDB(Base):
    """SQLAlchemy model for chat_messages table."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # JSON array of source citations
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    session = relationship("ChatSessionDB", back_populates="messages")


# Database initialization
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Database dependency for FastAPI
def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# User CRUD operations
class UserRepository:
    """Repository class for user database operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        Bcrypt has a 72-byte limit, so we truncate if necessary.
        """
        password_truncated = truncate_password_for_bcrypt(password)
        return pwd_context.hash(password_truncated)

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> UserDB:
        """
        Create a new user in the database.

        Args:
            db: Database session
            username: User's username
            email: User's email
            password: User's plain text password (will be hashed)

        Returns:
            UserDB: Created user object

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username already exists
        if db.query(UserDB).filter(UserDB.username == username).first():
            raise ValueError("Username already exists")

        # Check if email already exists
        if db.query(UserDB).filter(UserDB.email == email).first():
            raise ValueError("Email already exists")

        # Create new user
        hashed_password = UserRepository.hash_password(password)
        db_user = UserDB(
            username=username,
            email=email,
            hashed_password=hashed_password
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserDB]:
        """
        Get user by username.

        Args:
            db: Database session
            username: Username to search for

        Returns:
            UserDB or None: User object if found, None otherwise
        """
        return db.query(UserDB).filter(UserDB.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserDB]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID to search for

        Returns:
            UserDB or None: User object if found, None otherwise
        """
        return db.query(UserDB).filter(UserDB.id == user_id).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[UserDB]:
        """
        Authenticate a user with username and password.

        Args:
            db: Database session
            username: User's username
            password: User's plain text password

        Returns:
            UserDB or None: User object if authentication successful, None otherwise
        """
        user = UserRepository.get_user_by_username(db, username)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user

    @staticmethod
    def get_user_count(db: Session) -> int:
        """
        Get total number of users.

        Args:
            db: Database session

        Returns:
            int: Total number of users
        """
        return db.query(UserDB).count()


# Chat CRUD operations
class ChatRepository:
    """Repository class for chat database operations."""

    @staticmethod
    def create_session(db: Session, user_id: int, title: str) -> ChatSessionDB:
        """
        Create a new chat session.

        Args:
            db: Database session
            user_id: User ID
            title: Session title

        Returns:
            ChatSessionDB: Created session object
        """
        session = ChatSessionDB(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[ChatSessionDB]:
        """
        Get all chat sessions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List[ChatSessionDB]: List of user's chat sessions
        """
        return db.query(ChatSessionDB).filter(
            ChatSessionDB.user_id == user_id
        ).order_by(ChatSessionDB.updated_at.desc()).all()

    @staticmethod
    def get_session(db: Session, session_id: int, user_id: int) -> Optional[ChatSessionDB]:
        """
        Get a chat session by ID (with user verification).

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID for verification

        Returns:
            ChatSessionDB or None: Session if found and belongs to user
        """
        return db.query(ChatSessionDB).filter(
            ChatSessionDB.id == session_id,
            ChatSessionDB.user_id == user_id
        ).first()

    @staticmethod
    def delete_session(db: Session, session_id: int, user_id: int) -> bool:
        """
        Delete a chat session (with user verification).

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID for verification

        Returns:
            bool: True if deleted, False if not found
        """
        session = ChatRepository.get_session(db, session_id, user_id)
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    @staticmethod
    def add_message(db: Session, session_id: int, role: str, content: str, sources: Optional[List[dict]] = None) -> ChatMessageDB:
        """
        Add a message to a chat session.

        Args:
            db: Database session
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            sources: Optional source citations

        Returns:
            ChatMessageDB: Created message object
        """
        message = ChatMessageDB(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources
        )
        db.add(message)

        # Update session's updated_at timestamp
        session = db.query(ChatSessionDB).filter(ChatSessionDB.id == session_id).first()
        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_session_messages(db: Session, session_id: int, user_id: int) -> List[ChatMessageDB]:
        """
        Get all messages for a chat session (with user verification).

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID for verification

        Returns:
            List[ChatMessageDB]: List of messages
        """
        # Verify session belongs to user
        session = ChatRepository.get_session(db, session_id, user_id)
        if not session:
            return []

        return db.query(ChatMessageDB).filter(
            ChatMessageDB.session_id == session_id
        ).order_by(ChatMessageDB.created_at.asc()).all()
