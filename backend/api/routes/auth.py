"""Authentication endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models import UserRegister, UserLogin, Token, User
from db import get_db, UserRepository
from auth import create_access_token, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
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

        return Token(access_token=access_token)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
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

    return Token(access_token=access_token)


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user information
    """
    return current_user
