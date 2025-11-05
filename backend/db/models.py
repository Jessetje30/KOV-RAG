"""SQLAlchemy database models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
import enum
import bcrypt

from db.base import Base

# Password hashing context (kept for backwards compatibility with hash creation)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, enum.Enum):
    """User roles enum."""
    ADMIN = "admin"
    USER = "user"


class InvitationStatus(str, enum.Enum):
    """Invitation status enum."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


# Helper function for timezone-aware UTC datetime
def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)

# Helper function for password truncation (bcrypt 72-byte limit)
def truncate_password_for_bcrypt(password: str) -> str:
    """
    Truncate password to 72 bytes for bcrypt compatibility.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        while len(password_bytes) > 0:
            try:
                password_truncated = password_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                password_bytes = password_bytes[:-1]
    else:
        password_truncated = password
    return password_truncated


class UserDB(Base):
    """SQLAlchemy model for users table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for invited users without password yet
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who invited this user

    # Relationships
    chat_sessions = relationship("ChatSessionDB", back_populates="user", cascade="all, delete-orphan")
    invitations_sent = relationship("UserInvitationDB", foreign_keys="UserInvitationDB.invited_by", back_populates="inviter")

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the hashed password.
        Uses bcrypt directly to avoid passlib/bcrypt 5.0.0 compatibility issues.
        """
        if not self.hashed_password:
            return False

        # Truncate password to 72 bytes (bcrypt limitation)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Get hash as bytes
        hash_bytes = self.hashed_password.encode('utf-8')

        # Use bcrypt directly for verification
        try:
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            # Fallback: hash might not be a valid bcrypt hash
            return False


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


class UserInvitationDB(Base):
    """SQLAlchemy model for user_invitations table."""
    __tablename__ = "user_invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)  # Secure random token
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)  # Invitation expiry (e.g., 7 days)
    accepted_at = Column(DateTime, nullable=True)  # When user completed setup
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Created user after acceptance

    # Relationships
    inviter = relationship("UserDB", foreign_keys=[invited_by], back_populates="invitations_sent")
    accepted_user = relationship("UserDB", foreign_keys=[user_id])
