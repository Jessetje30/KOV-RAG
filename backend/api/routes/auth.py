"""Authentication endpoints."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import (
    UserRegister,
    UserLogin,
    Token,
    User,
    ValidateInvitationResponse,
    SetupAccountRequest,
    SetupAccountResponse
)
from db import get_db, UserRepository
from db.models import UserDB, UserInvitationDB, InvitationStatus, UserRole, pwd_context, truncate_password_for_bcrypt
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


# ============================================
# Invitation-Based Account Setup (Public)
# ============================================

@router.get("/validate-invitation/{token}", response_model=ValidateInvitationResponse)
@limiter.limit("10/minute")
async def validate_invitation(request: Request, token: str, db: Session = Depends(get_db)):
    """
    Validate an invitation token (public endpoint).

    Checks if the token is valid, not expired, and not yet accepted.

    Args:
        token: Invitation token from email
        db: Database session

    Returns:
        ValidateInvitationResponse: Validation result with email and expiry
    """
    try:
        # Find invitation by token
        invitation = db.query(UserInvitationDB).filter(UserInvitationDB.token == token).first()

        if not invitation:
            return ValidateInvitationResponse(
                valid=False,
                message="Invalid invitation token"
            )

        # Check if already accepted
        if invitation.status == InvitationStatus.ACCEPTED:
            return ValidateInvitationResponse(
                valid=False,
                message="This invitation has already been used"
            )

        # Check if expired
        if invitation.expires_at < datetime.now(timezone.utc):
            # Update status to expired
            invitation.status = InvitationStatus.EXPIRED
            db.commit()

            return ValidateInvitationResponse(
                valid=False,
                message="This invitation has expired"
            )

        # Valid invitation
        return ValidateInvitationResponse(
            valid=True,
            email=invitation.email,
            expires_at=invitation.expires_at,
            message="Valid invitation"
        )

    except Exception as e:
        logger.error(f"Error validating invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate invitation"
        )


@router.post("/setup-account", response_model=SetupAccountResponse)
@limiter.limit("5/minute")
async def setup_account(request: Request, setup_data: SetupAccountRequest, db: Session = Depends(get_db)):
    """
    Set up user account from invitation (public endpoint).

    Creates a new user account with the provided username and password,
    using the email from the invitation. Automatically logs in the user.

    Args:
        setup_data: Account setup data (token, username, password)
        db: Database session

    Returns:
        SetupAccountResponse: Success status and access token for auto-login

    Raises:
        HTTPException: If token invalid, expired, or username taken
    """
    try:
        # Find and validate invitation
        invitation = db.query(UserInvitationDB).filter(
            UserInvitationDB.token == setup_data.token
        ).first()

        if not invitation:
            log_security_event(
                event_type=SecurityEvent.REGISTER_FAILURE,
                ip_address=request.client.host if request.client else None,
                details={"reason": "Invalid invitation token"},
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation token"
            )

        # Check if already accepted
        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been used"
            )

        # Check if expired
        if invitation.expires_at < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired"
            )

        # Check if username is already taken
        existing_user = db.query(UserDB).filter(UserDB.username == setup_data.username).first()
        if existing_user:
            log_security_event(
                event_type=SecurityEvent.REGISTER_FAILURE,
                username=setup_data.username,
                ip_address=request.client.host if request.client else None,
                details={"reason": "Username already exists"},
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{setup_data.username}' is already taken"
            )

        # Check if email is already registered (shouldn't happen, but safety check)
        existing_email = db.query(UserDB).filter(UserDB.email == invitation.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {invitation.email} is already registered"
            )

        # Hash password
        password_truncated = truncate_password_for_bcrypt(setup_data.password)
        hashed_password = pwd_context.hash(password_truncated)

        # Create user account
        new_user = UserDB(
            username=setup_data.username,
            email=invitation.email,
            hashed_password=hashed_password,
            role=UserRole.USER,  # Default role for invited users
            is_active=True,
            invited_by=invitation.invited_by
        )

        db.add(new_user)
        db.flush()  # Get user ID without committing

        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc)
        invitation.user_id = new_user.id

        db.commit()
        db.refresh(new_user)

        logger.info(f"New user account created from invitation: {new_user.username} ({new_user.email})")
        log_security_event(
            event_type=SecurityEvent.REGISTER_SUCCESS,
            username=new_user.username,
            user_id=new_user.id,
            ip_address=request.client.host if request.client else None,
            details={"email": new_user.email, "invited_by": invitation.invited_by}
        )

        # Create access token for auto-login
        access_token = create_access_token(
            data={"sub": new_user.username, "user_id": new_user.id}
        )

        return SetupAccountResponse(
            success=True,
            message=f"Account created successfully for {new_user.username}",
            access_token=access_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up account: {str(e)}")
        db.rollback()
        log_security_event(
            event_type=SecurityEvent.REGISTER_FAILURE,
            ip_address=request.client.host if request.client else None,
            details={"error": str(e)},
            severity="ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )
