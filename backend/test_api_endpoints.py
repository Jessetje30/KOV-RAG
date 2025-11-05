"""
Comprehensive tests for all API endpoints.
Tests authentication, document management, query, and chat functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import io

# Import app and dependencies
from main import app
from models.auth import UserRegister, UserLogin
from db.models import UserDB


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline for testing."""
    mock_pipeline = Mock()
    mock_pipeline.process_document.return_value = ("doc-123", 5)
    mock_pipeline.query.return_value = (
        "Test answer",
        [
            {
                "text": "Source text",
                "document_id": "doc-123",
                "filename": "test.pdf",
                "score": 0.95,
                "chunk_index": 0,
                "summary": "Test summary",
                "title": "Test title"
            }
        ],
        1.5
    )
    mock_pipeline.get_user_documents.return_value = [
        {
            "document_id": "doc-123",
            "filename": "test.pdf",
            "upload_date": datetime.now(timezone.utc).isoformat(),
            "file_size": 1024,
            "chunks_count": 5
        }
    ]
    mock_pipeline.delete_document.return_value = True
    mock_pipeline.health_check.return_value = True
    return mock_pipeline


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing."""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test@Pass123"
    }

    # Register
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "qdrant_status" in data
        assert "rag_status" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RAG Application API"
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "health" in data


class TestAuthenticationEndpoints:
    """Tests for authentication endpoints."""

    def test_register_valid_user(self, client):
        """Test user registration with valid data."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewUser@123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, client):
        """Test registration fails with duplicate username."""
        user_data = {
            "email": "user1@example.com",
            "username": "duplicate",
            "password": "Pass@123"
        }
        # Register first user
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register with same username
        user_data2 = {
            "email": "user2@example.com",
            "username": "duplicate",
            "password": "Pass@456"
        }
        response = client.post("/api/auth/register", json=user_data2)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration fails with weak password."""
        user_data = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak"  # Too short, no special char
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

    def test_login_valid_credentials(self, client):
        """Test login with valid credentials."""
        # Register user
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "password": "Login@Pass123"
        }
        client.post("/api/auth/register", json=user_data)

        # Login
        login_data = {
            "username": "loginuser",
            "password": "Login@Pass123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client):
        """Test login fails with wrong password."""
        # Register user
        user_data = {
            "email": "wrong@example.com",
            "username": "wronguser",
            "password": "Correct@Pass123"
        }
        client.post("/api/auth/register", json=user_data)

        # Login with wrong password
        login_data = {
            "username": "wronguser",
            "password": "Wrong@Pass123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login fails for nonexistent user."""
        login_data = {
            "username": "nonexistent",
            "password": "Pass@123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401


class TestDocumentEndpoints:
    """Tests for document management endpoints."""

    @patch('main.rag_pipeline')
    def test_upload_document(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test document upload."""
        mock_pipeline.return_value = mock_rag_pipeline
        app.state.rag_pipeline = mock_rag_pipeline

        # Create fake PDF file
        file_content = b"PDF content here"
        files = {
            "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
        }

        response = client.post(
            "/api/documents/upload",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "filename" in data
        assert data["chunks_created"] > 0

    def test_upload_document_without_auth(self, client):
        """Test upload fails without authentication."""
        file_content = b"PDF content"
        files = {
            "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
        }

        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 403

    @patch('main.rag_pipeline')
    def test_list_documents(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test listing user documents."""
        app.state.rag_pipeline = mock_rag_pipeline

        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["documents"], list)
        assert "total" in data

    @patch('main.rag_pipeline')
    def test_delete_document(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test deleting a document."""
        app.state.rag_pipeline = mock_rag_pipeline

        response = client.delete(
            "/api/documents/doc-123",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document deleted successfully"


class TestQueryEndpoints:
    """Tests for query endpoints."""

    @patch('main.rag_pipeline')
    def test_query_documents(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test querying documents."""
        app.state.rag_pipeline = mock_rag_pipeline

        query_data = {
            "query": "What is BBL?",
            "top_k": 3
        }

        response = client.post(
            "/api/query",
            json=query_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "processing_time" in data
        assert isinstance(data["sources"], list)

    def test_query_without_auth(self, client):
        """Test query fails without authentication."""
        query_data = {
            "query": "What is BBL?",
            "top_k": 3
        }

        response = client.post("/api/query", json=query_data)
        assert response.status_code == 403

    @patch('main.rag_pipeline')
    def test_query_empty_text(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test query with empty text fails validation."""
        query_data = {
            "query": "",
            "top_k": 3
        }

        response = client.post(
            "/api/query",
            json=query_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

    @patch('main.rag_pipeline')
    def test_query_with_top_k_bounds(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test query respects top_k bounds."""
        app.state.rag_pipeline = mock_rag_pipeline

        # Test with very high top_k
        query_data = {
            "query": "Test query",
            "top_k": 100
        }

        response = client.post(
            "/api/query",
            json=query_data,
            headers=auth_headers
        )
        assert response.status_code == 200


class TestChatEndpoints:
    """Tests for chat session endpoints."""

    def test_create_chat_session(self, client, auth_headers):
        """Test creating a new chat session."""
        session_data = {
            "title": "Test Chat Session"
        }

        response = client.post(
            "/api/chat/sessions",
            json=session_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Chat Session"

    def test_list_chat_sessions(self, client, auth_headers):
        """Test listing user's chat sessions."""
        response = client.get("/api/chat/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["sessions"], list)
        assert "total" in data

    @patch('main.rag_pipeline')
    def test_chat_query_with_history(self, mock_pipeline, client, auth_headers, mock_rag_pipeline):
        """Test querying with chat history."""
        app.state.rag_pipeline = mock_rag_pipeline
        mock_rag_pipeline.query_with_chat.return_value = (
            "Answer with context",
            [],
            1.2
        )

        # Create session
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Query with history
        query_data = {
            "query": "Follow-up question",
            "top_k": 3
        }

        response = client.post(
            f"/api/chat/sessions/{session_id}/query",
            json=query_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_delete_chat_session(self, client, auth_headers):
        """Test deleting a chat session."""
        # Create session
        session_response = client.post(
            "/api/chat/sessions",
            json={"title": "To Delete"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_on_query(self, client, auth_headers):
        """Test that rate limiting is enforced on query endpoint."""
        query_data = {
            "query": "Test query",
            "top_k": 3
        }

        # Make many requests quickly
        responses = []
        for _ in range(25):  # Limit is 20/minute
            response = client.post(
                "/api/query",
                json=query_data,
                headers=auth_headers
            )
            responses.append(response.status_code)

        # Should have at least one 429 (Too Many Requests)
        assert 429 in responses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
