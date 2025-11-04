"""Admin endpoints for user management and invitations."""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import (
    InviteUserRequest,
    InvitationResponse,
    InvitationListResponse,
    UserAdminResponse,
    UserListResponse,
    UpdateUserRequest,
    UpdateUserResponse
)
from db import get_db
from db.models import UserDB, UserInvitationDB, InvitationStatus, UserRole
from auth import get_current_admin_user
from services.email_service import EmailService
from utils import log_security_event, SecurityEvent

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def generate_invitation_token() -> str:
    """Generate a secure random token for invitations."""
    return secrets.token_urlsafe(32)


# ============================================
# User Invitation Endpoints
# ============================================

@router.post("/invite-user", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def invite_user(
    request: Request,
    invite_data: InviteUserRequest,
    db: Session = Depends(get_db),
    admin_user: UserDB = Depends(get_current_admin_user)
):
    """
    Send an invitation email to a new user (admin only).

    Creates an invitation record and sends an email with a secure token link.
    The invited user can use the link to set up their account.

    Args:
        invite_data: Email address to invite
        db: Database session
        admin_user: Current authenticated admin user

    Returns:
        InvitationResponse: Created invitation details

    Raises:
        HTTPException: If email is already registered or invitation already exists
    """
    try:
        # Check if email is already registered
        existing_user = db.query(UserDB).filter(UserDB.email == invite_data.email).first()
        if existing_user:
            log_security_event(
                event_type=SecurityEvent.REGISTER_FAILURE,
                username=admin_user.username,
                user_id=admin_user.id,
                ip_address=request.client.host if request.client else None,
                details={"reason": "Email already registered", "email": invite_data.email},
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {invite_data.email} already exists"
            )

        # Check if there's already a pending invitation for this email
        pending_invitation = db.query(UserInvitationDB).filter(
            UserInvitationDB.email == invite_data.email,
            UserInvitationDB.status == InvitationStatus.PENDING,
            UserInvitationDB.expires_at > datetime.now(timezone.utc)
        ).first()

        if pending_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pending invitation already exists for {invite_data.email}"
            )

        # Generate secure token
        token = generate_invitation_token()

        # Create invitation record
        invitation = UserInvitationDB(
            email=invite_data.email,
            token=token,
            invited_by=admin_user.id,
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # 7 days expiry
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        # Send invitation email
        email_service = EmailService()
        email_sent = email_service.send_invitation_email(
            to_email=invite_data.email,
            invitation_token=token,
            invited_by_name=admin_user.username
        )

        if not email_sent:
            logger.error(f"Failed to send invitation email to {invite_data.email}")
            # Note: We don't fail the request, just log the error
            # Admin can manually resend or user can use token directly

        logger.info(f"Admin {admin_user.username} invited user {invite_data.email}")
        log_security_event(
            event_type=SecurityEvent.REGISTER_SUCCESS,
            username=admin_user.username,
            user_id=admin_user.id,
            ip_address=request.client.host if request.client else None,
            details={"action": "invite_user", "invited_email": invite_data.email}
        )

        # Prepare response
        response = InvitationResponse(
            id=invitation.id,
            email=invitation.email,
            token=invitation.token,
            invited_by=invitation.invited_by,
            inviter_username=admin_user.username,
            status=invitation.status,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
            user_id=invitation.user_id
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation"
        )


@router.get("/invitations", response_model=InvitationListResponse)
@limiter.limit("30/minute")
async def list_invitations(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[InvitationStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    admin_user: UserDB = Depends(get_current_admin_user)
):
    """
    Get list of all invitations (admin only).

    Supports pagination and filtering by status.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Optional filter by invitation status
        db: Database session
        admin_user: Current authenticated admin user

    Returns:
        InvitationListResponse: Paginated list of invitations
    """
    try:
        # Build query
        query = db.query(UserInvitationDB)

        # Apply status filter if provided
        if status_filter:
            query = query.filter(UserInvitationDB.status == status_filter)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        invitations_db = query.order_by(UserInvitationDB.created_at.desc()).offset(offset).limit(page_size).all()

        # Convert to response models
        invitations = []
        for inv in invitations_db:
            # Get inviter username
            inviter = db.query(UserDB).filter(UserDB.id == inv.invited_by).first()
            inviter_username = inviter.username if inviter else None

            invitations.append(InvitationResponse(
                id=inv.id,
                email=inv.email,
                token=inv.token,
                invited_by=inv.invited_by,
                inviter_username=inviter_username,
                status=inv.status,
                created_at=inv.created_at,
                expires_at=inv.expires_at,
                accepted_at=inv.accepted_at,
                user_id=inv.user_id
            ))

        return InvitationListResponse(
            invitations=invitations,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitations"
        )


# ============================================
# User Management Endpoints
# ============================================

@router.get("/users", response_model=UserListResponse)
@limiter.limit("30/minute")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role_filter: Optional[UserRole] = Query(None, description="Filter by role"),
    active_only: bool = Query(False, description="Show only active users"),
    db: Session = Depends(get_db),
    admin_user: UserDB = Depends(get_current_admin_user)
):
    """
    Get list of all users (admin only).

    Supports pagination and filtering by role and active status.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        role_filter: Optional filter by user role
        active_only: Show only active users
        db: Database session
        admin_user: Current authenticated admin user

    Returns:
        UserListResponse: Paginated list of users
    """
    try:
        # Build query
        query = db.query(UserDB)

        # Apply filters
        if role_filter:
            query = query.filter(UserDB.role == role_filter)
        if active_only:
            query = query.filter(UserDB.is_active == True)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        users_db = query.order_by(UserDB.created_at.desc()).offset(offset).limit(page_size).all()

        # Convert to response models
        users = []
        for user in users_db:
            # Get inviter username if applicable
            inviter_username = None
            if user.invited_by:
                inviter = db.query(UserDB).filter(UserDB.id == user.invited_by).first()
                inviter_username = inviter.username if inviter else None

            users.append(UserAdminResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                invited_by=user.invited_by,
                inviter_username=inviter_username
            ))

        return UserListResponse(
            users=users,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.patch("/users/{user_id}", response_model=UpdateUserResponse)
@limiter.limit("20/minute")
async def update_user(
    request: Request,
    user_id: int,
    update_data: UpdateUserRequest,
    db: Session = Depends(get_db),
    admin_user: UserDB = Depends(get_current_admin_user)
):
    """
    Update user settings (admin only).

    Can update user's active status and role.

    Args:
        user_id: ID of user to update
        update_data: Update fields
        db: Database session
        admin_user: Current authenticated admin user

    Returns:
        UpdateUserResponse: Updated user data

    Raises:
        HTTPException: If user not found or trying to modify own admin status
    """
    try:
        # Get user to update
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Prevent admin from deactivating themselves
        if user.id == admin_user.id and update_data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        # Prevent admin from removing their own admin role
        if user.id == admin_user.id and update_data.role == UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove your own admin privileges"
            )

        # Apply updates
        updated_fields = []
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
            updated_fields.append(f"is_active={update_data.is_active}")

        if update_data.role is not None:
            user.role = update_data.role
            updated_fields.append(f"role={update_data.role}")

        db.commit()
        db.refresh(user)

        logger.info(f"Admin {admin_user.username} updated user {user.username}: {', '.join(updated_fields)}")
        log_security_event(
            event_type=SecurityEvent.LOGIN_SUCCESS,  # Reusing event type for admin actions
            username=admin_user.username,
            user_id=admin_user.id,
            ip_address=request.client.host if request.client else None,
            details={"action": "update_user", "target_user_id": user_id, "updates": updated_fields}
        )

        # Get inviter username if applicable
        inviter_username = None
        if user.invited_by:
            inviter = db.query(UserDB).filter(UserDB.id == user.invited_by).first()
            inviter_username = inviter.username if inviter else None

        user_response = UserAdminResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            invited_by=user.invited_by,
            inviter_username=inviter_username
        )

        return UpdateUserResponse(
            success=True,
            message=f"User {user.username} updated successfully",
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def deactivate_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: UserDB = Depends(get_current_admin_user)
):
    """
    Deactivate a user (soft delete - admin only).

    Sets user's is_active to False instead of hard delete.

    Args:
        user_id: ID of user to deactivate
        db: Database session
        admin_user: Current authenticated admin user

    Returns:
        dict: Success message

    Raises:
        HTTPException: If user not found or trying to deactivate self
    """
    try:
        # Get user to deactivate
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Prevent admin from deactivating themselves
        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        # Soft delete (deactivate)
        user.is_active = False
        db.commit()

        logger.info(f"Admin {admin_user.username} deactivated user {user.username}")
        log_security_event(
            event_type=SecurityEvent.LOGIN_SUCCESS,  # Reusing event type for admin actions
            username=admin_user.username,
            user_id=admin_user.id,
            ip_address=request.client.host if request.client else None,
            details={"action": "deactivate_user", "target_user_id": user_id, "target_username": user.username}
        )

        return {
            "success": True,
            "message": f"User {user.username} deactivated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
