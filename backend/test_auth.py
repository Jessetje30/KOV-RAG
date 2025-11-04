"""
Tests for authentication and authorization functionality.
"""
import pytest
from datetime import datetime, timedelta, timezone
import jwt
from auth import create_access_token, decode_access_token, JWT_SECRET_KEY, JWT_ALGORITHM
from models import TokenData


class TestJWTAuthentication:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating a valid access token."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiration(self):
        """Test creating a token with custom expiration time."""
        data = {"sub": "testuser", "user_id": 1}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)

        # Decode to verify expiration
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        exp_timestamp = payload.get("exp")

        assert exp_timestamp is not None
        # Should be in the future
        now = datetime.now(timezone.utc).timestamp()
        assert exp_timestamp > now

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        token_data = decode_access_token(token)

        assert token_data is not None
        assert isinstance(token_data, TokenData)
        assert token_data.username == "testuser"
        assert token_data.user_id == 1

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        invalid_token = "invalid.token.here"

        token_data = decode_access_token(invalid_token)

        assert token_data is None

    def test_decode_expired_token(self):
        """Test decoding an expired token returns None."""
        data = {"sub": "testuser", "user_id": 1}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        token = create_access_token(data, expires_delta)

        token_data = decode_access_token(token)

        assert token_data is None

    def test_decode_token_without_username(self):
        """Test decoding a token without 'sub' field returns None."""
        data = {"user_id": 1}  # Missing 'sub'
        token = create_access_token(data)

        token_data = decode_access_token(token)

        assert token_data is None

    def test_decode_token_without_user_id(self):
        """Test decoding a token without 'user_id' field returns None."""
        data = {"sub": "testuser"}  # Missing 'user_id'
        token = create_access_token(data)

        token_data = decode_access_token(token)

        assert token_data is None

    def test_token_includes_expiration(self):
        """Test that created tokens include expiration claim."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert "exp" in payload
        assert isinstance(payload["exp"], int)
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
