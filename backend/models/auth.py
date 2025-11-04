"""Authentication related Pydantic models."""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re


class UserRegister(BaseModel):
    """Model for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        """Ensure username contains only alphanumeric characters and underscores."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v

    @field_validator('password')
    @classmethod
    def password_complexity_check(cls, v):
        """
        Ensure password meets security requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - Within bcrypt's 72-byte limit
        """
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long. Maximum 72 characters allowed.')

        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long.')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\\\/;\'`~).')

        return v


class UserLogin(BaseModel):
    """Model for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Model for token payload data."""
    username: Optional[str] = None
    user_id: Optional[int] = None


class User(BaseModel):
    """Model for user data."""
    id: int
    username: str
    email: str
    role: str  # 'admin' or 'user'
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
