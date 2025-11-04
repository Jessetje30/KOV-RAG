"""
Tests for Pydantic models and validation.
"""
import pytest
from pydantic import ValidationError
from models import (
    UserRegister, UserLogin, QueryRequest,
    DocumentUploadResponse, ErrorResponse
)


class TestUserModels:
    """Test user authentication models."""

    def test_user_register_valid(self):
        """Test creating a valid user registration."""
        user = UserRegister(
            email="test@example.com",
            username="testuser",
            password="securepassword123"
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "securepassword123"

    def test_user_register_invalid_email(self):
        """Test that invalid email is rejected."""
        with pytest.raises(ValidationError):
            UserRegister(
                email="invalid-email",
                username="testuser",
                password="securepassword123"
            )

    def test_user_register_short_username(self):
        """Test that username shorter than 3 chars is rejected."""
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                username="ab",
                password="securepassword123"
            )

    def test_user_register_short_password(self):
        """Test that password shorter than 8 chars is rejected."""
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                username="testuser",
                password="short"
            )

    def test_user_register_username_alphanumeric(self):
        """Test that non-alphanumeric usernames are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                username="test-user",  # Contains hyphen
                password="securepassword123"
            )
        assert "alphanumeric" in str(exc_info.value).lower()

    def test_user_register_username_with_underscore(self):
        """Test that usernames with underscores are accepted."""
        user = UserRegister(
            email="test@example.com",
            username="test_user",
            password="securepassword123"
        )
        assert user.username == "test_user"

    def test_user_register_password_too_long(self):
        """Test that password longer than 72 bytes is rejected."""
        # Create a password longer than 72 bytes (bcrypt limit)
        long_password = "a" * 73

        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                username="testuser",
                password=long_password
            )
        assert "72" in str(exc_info.value)

    def test_user_login_valid(self):
        """Test creating a valid user login."""
        login = UserLogin(
            username="testuser",
            password="securepassword123"
        )

        assert login.username == "testuser"
        assert login.password == "securepassword123"


class TestQueryModels:
    """Test RAG query models."""

    def test_query_request_valid(self):
        """Test creating a valid query request."""
        query = QueryRequest(
            query="What is the meaning of life?",
            top_k=5
        )

        assert query.query == "What is the meaning of life?"
        assert query.top_k == 5

    def test_query_request_default_top_k(self):
        """Test that top_k has a default value."""
        query = QueryRequest(query="Test question")

        assert query.top_k == 5

    def test_query_request_empty_query(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="")

    def test_query_request_whitespace_query(self):
        """Test that whitespace-only query is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="   ")
        assert "whitespace" in str(exc_info.value).lower()

    def test_query_request_strips_whitespace(self):
        """Test that query whitespace is stripped."""
        query = QueryRequest(query="  Test question  ")

        assert query.query == "Test question"

    def test_query_request_top_k_too_low(self):
        """Test that top_k less than 1 is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="Test", top_k=0)

    def test_query_request_top_k_too_high(self):
        """Test that top_k greater than 100 is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="Test", top_k=101)

    def test_query_request_max_length(self):
        """Test that query longer than 1000 chars is rejected."""
        long_query = "a" * 1001

        with pytest.raises(ValidationError):
            QueryRequest(query=long_query)


class TestDocumentModels:
    """Test document-related models."""

    def test_document_upload_response(self):
        """Test creating a document upload response."""
        response = DocumentUploadResponse(
            document_id="doc123",
            filename="test.pdf",
            file_size=1024,
            chunks_created=10,
            message="Success"
        )

        assert response.document_id == "doc123"
        assert response.filename == "test.pdf"
        assert response.file_size == 1024
        assert response.chunks_created == 10
        assert response.message == "Success"


class TestErrorModels:
    """Test error response models."""

    def test_error_response(self):
        """Test creating an error response."""
        error = ErrorResponse(
            detail="Something went wrong",
            error_type="ValueError"
        )

        assert error.detail == "Something went wrong"
        assert error.error_type == "ValueError"

    def test_error_response_without_type(self):
        """Test creating an error response without error_type."""
        error = ErrorResponse(detail="Something went wrong")

        assert error.detail == "Something went wrong"
        assert error.error_type is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
