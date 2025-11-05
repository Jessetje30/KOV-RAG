"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


# Set testing environment variable
os.environ["TESTING"] = "1"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    yield
    # Cleanup
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function", autouse=True)
def disable_rate_limiting(monkeypatch):
    """
    Disable rate limiting for tests by setting enabled=False.
    This prevents 429 errors when running multiple tests.
    """
    # Import here to avoid circular import
    from slowapi import Limiter

    # Create a mock limiter that does nothing
    mock_limiter = Mock(spec=Limiter)
    mock_limiter.enabled = False
    mock_limiter.limit = lambda *args, **kwargs: lambda f: f  # Return identity function

    # Patch the limiter in main
    with patch('main.limiter', mock_limiter):
        yield


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Clean database between tests."""
    from db.base import SessionLocal
    from db.models import UserDB, ChatSessionDB, ChatMessageDB, UserInvitationDB

    yield

    # Cleanup after each test
    db = SessionLocal()
    try:
        # Delete in correct order to respect foreign keys
        db.query(ChatMessageDB).delete()
        db.query(ChatSessionDB).delete()
        db.query(UserInvitationDB).delete()
        db.query(UserDB).delete()
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_db():
    """Set up test database."""
    from db.base import Base, engine

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield

    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
