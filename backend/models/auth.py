"""Authentication related Pydantic models."""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


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
    def password_length_check(cls, v):
        """Ensure password is within bcrypt's 72-byte limit."""
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long. Maximum 72 characters allowed.')
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
