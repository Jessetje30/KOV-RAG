"""Authentication endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import UserRegister, UserLogin, Token, User
from db import get_db, UserRepository
from auth import create_access_token, get_current_user
from utils import log_security_event, SecurityEvent

logger = logging.getLogger(__name__)

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
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

        # Log security event
        log_security_event(
            event_type=SecurityEvent.REGISTER_SUCCESS,
            username=db_user.username,
            user_id=db_user.id,
            ip_address=request.client.host if request.client else None,
            details={"email": user_data.email}
        )

        return Token(access_token=access_token)

    except ValueError as e:
        # Log failed registration attempt
        log_security_event(
            event_type=SecurityEvent.REGISTER_FAILURE,
            username=user_data.username,
            ip_address=request.client.host if request.client else None,
            details={"reason": str(e), "email": user_data.email},
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        log_security_event(
            event_type=SecurityEvent.REGISTER_FAILURE,
            username=user_data.username,
            ip_address=request.client.host if request.client else None,
            details={"error": str(e)},
            severity="ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
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
        # Log failed login attempt
        log_security_event(
            event_type=SecurityEvent.LOGIN_FAILURE,
            username=user_data.username,
            ip_address=request.client.host if request.client else None,
            details={"reason": "Invalid credentials"},
            severity="WARNING"
        )
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

    # Log successful login
    log_security_event(
        event_type=SecurityEvent.LOGIN_SUCCESS,
        username=user.username,
        user_id=user.id,
        ip_address=request.client.host if request.client else None
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=User)
@limiter.limit("30/minute")
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user information
    """
    return current_user
