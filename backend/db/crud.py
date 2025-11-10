"""Database CRUD operations and repository classes."""
from typing import Optional, List
from sqlalchemy.orm import Session
import bcrypt

from db.models import UserDB, ChatSessionDB, ChatMessageDB, truncate_password_for_bcrypt


class UserRepository:
    """Repository class for user database operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt directly."""
        password_truncated = truncate_password_for_bcrypt(password)
        password_bytes = password_truncated.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> UserDB:
        """Create a new user in the database."""
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
        """Get user by username."""
        return db.query(UserDB).filter(UserDB.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserDB]:
        """Get user by ID."""
        return db.query(UserDB).filter(UserDB.id == user_id).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[UserDB]:
        """
        Authenticate a user by username/email and password.
        Accepts both username and email for login.
        """
        # Try to find user by username first
        user = UserRepository.get_user_by_username(db, username)

        # If not found, try by email
        if not user:
            user = db.query(UserDB).filter(UserDB.email == username).first()

        if not user:
            return None

        # Verify password
        if not user.verify_password(password):
            return None

        return user


# Chat session CRUD
def create_chat_session(db: Session, user_id: int, title: str) -> ChatSessionDB:
    """Create a new chat session."""
    session = ChatSessionDB(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_session(db: Session, session_id: int, user_id: int) -> Optional[ChatSessionDB]:
    """Get a chat session by ID."""
    return db.query(ChatSessionDB).filter(
        ChatSessionDB.id == session_id,
        ChatSessionDB.user_id == user_id
    ).first()


def list_chat_sessions(db: Session, user_id: int) -> List[ChatSessionDB]:
    """List all chat sessions for a user."""
    return db.query(ChatSessionDB).filter(
        ChatSessionDB.user_id == user_id
    ).order_by(ChatSessionDB.updated_at.desc()).all()


def delete_chat_session(db: Session, session_id: int, user_id: int) -> bool:
    """Delete a chat session."""
    session = get_chat_session(db, session_id, user_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


# Chat message CRUD
def create_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    sources: Optional[List[dict]] = None
) -> ChatMessageDB:
    """Create a new chat message."""
    message = ChatMessageDB(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_session_messages(db: Session, session_id: int, user_id: Optional[int] = None) -> List[ChatMessageDB]:
    """Get all messages for a session. user_id parameter is for backward compatibility but not used."""
    return db.query(ChatMessageDB).filter(
        ChatMessageDB.session_id == session_id
    ).order_by(ChatMessageDB.id).all()


# ChatRepository wrapper for backward compatibility with main.py
class ChatRepository:
    """Repository class for chat operations - backward compatibility wrapper."""

    create_session = staticmethod(create_chat_session)
    get_session = staticmethod(get_chat_session)
    get_user_sessions = staticmethod(list_chat_sessions)
    delete_session = staticmethod(delete_chat_session)
    create_message = staticmethod(create_chat_message)
    add_message = staticmethod(create_chat_message)  # Alias for backward compatibility
    get_session_messages = staticmethod(get_session_messages)
