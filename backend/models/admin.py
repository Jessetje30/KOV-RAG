"""Admin-related Pydantic models."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from db.models import UserRole, InvitationStatus


# ============================================
# Invitation Models
# ============================================

class InviteUserRequest(BaseModel):
    """Request model for inviting a new user."""
    email: EmailStr = Field(..., description="Email address of the user to invite")


class InvitationResponse(BaseModel):
    """Response model for invitation data."""
    id: int
    email: str
    token: str
    invited_by: int
    inviter_username: Optional[str] = None
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class InvitationListResponse(BaseModel):
    """Response model for list of invitations."""
    invitations: List[InvitationResponse]
    total: int
    page: int
    page_size: int


# ============================================
# User Management Models
# ============================================

class UserAdminResponse(BaseModel):
    """Response model for user data (admin view)."""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    invited_by: Optional[int] = None
    inviter_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Response model for list of users."""
    users: List[UserAdminResponse]
    total: int
    page: int
    page_size: int


class UpdateUserRequest(BaseModel):
    """Request model for updating user (admin only)."""
    is_active: Optional[bool] = Field(None, description="Set user active/inactive status")
    role: Optional[UserRole] = Field(None, description="Change user role (admin/user)")


class UpdateUserResponse(BaseModel):
    """Response model for user update."""
    success: bool
    message: str
    user: UserAdminResponse


# ============================================
# Account Setup Models (Public - No Auth Required)
# ============================================

class ValidateInvitationResponse(BaseModel):
    """Response model for invitation validation."""
    valid: bool
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


class SetupAccountRequest(BaseModel):
    """Request model for setting up account from invitation."""
    token: str = Field(..., min_length=32, max_length=255)
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class SetupAccountResponse(BaseModel):
    """Response model for account setup."""
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
