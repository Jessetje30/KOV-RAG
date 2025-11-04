"""
JWT authentication and authorization logic.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from models import TokenData, User
from db import get_db, UserRepository, UserDB
from db.models import UserRole

# Import centralized configuration
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# JWT Configuration (using centralized config)
JWT_SECRET_KEY = SECRET_KEY
JWT_ALGORITHM = ALGORITHM
JWT_EXPIRATION_HOURS = ACCESS_TOKEN_EXPIRE_MINUTES // 60  # Convert minutes to hours

# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        TokenData or None: Token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            return None

        return TokenData(username=username, user_id=user_id)

    except InvalidTokenError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from the request
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Get token from credentials
    token = credentials.credentials

    # Decode token
    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception

    # Get user from database
    user_db = UserRepository.get_user_by_username(db, username=token_data.username)
    if user_db is None:
        raise credentials_exception

    # Check if user is active
    if not user_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Convert to Pydantic model
    user = User(
        id=user_db.id,
        username=user_db.username,
        email=user_db.email,
        role=user_db.role.value,  # Convert enum to string
        is_active=user_db.is_active,
        created_at=user_db.created_at
    )

    return user


async def get_current_user_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserDB:
    """
    Dependency to get the current authenticated user (database object).
    Useful when you need the full database object instead of Pydantic model.

    Args:
        credentials: HTTP Bearer credentials from the request
        db: Database session

    Returns:
        UserDB: Current authenticated user database object

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Get token from credentials
    token = credentials.credentials

    # Decode token
    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception

    # Get user from database
    user_db = UserRepository.get_user_by_username(db, username=token_data.username)
    if user_db is None:
        raise credentials_exception

    # Check if user is active
    if not user_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user_db


def verify_token(token: str) -> bool:
    """
    Verify if a token is valid.

    Args:
        token: JWT token string

    Returns:
        bool: True if token is valid, False otherwise
    """
    token_data = decode_access_token(token)
    return token_data is not None


async def get_current_admin_user(
    current_user: UserDB = Depends(get_current_user_db)
) -> UserDB:
    """
    Dependency to get the current authenticated admin user.

    This checks that:
    1. User is authenticated (via get_current_user_db)
    2. User is active (checked in get_current_user_db)
    3. User has ADMIN role

    Args:
        current_user: Current authenticated user (from get_current_user_db)

    Returns:
        UserDB: Current authenticated admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_user
