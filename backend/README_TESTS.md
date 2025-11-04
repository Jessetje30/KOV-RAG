# Running Tests

This directory contains comprehensive tests for the RAG application backend.

## Setup

Install test dependencies:

```bash
cd /Users/jesse/PycharmProjects/fontysRAG/rag-app/backend
source venv/bin/activate
pip install pytest pytest-cov pytest-mock
```

## Running Tests

### Run all tests:
```bash
PYTHONPATH=. pytest
```

### Run specific test file:
```bash
pytest test_auth.py
pytest test_models.py
pytest test_rag.py
```

### Run with verbose output:
```bash
pytest -v
```

### Run with coverage report:
```bash
pytest --cov=. --cov-report=html
# View coverage report at htmlcov/index.html
```

### Run specific test:
```bash
pytest test_auth.py::TestJWTAuthentication::test_create_access_token
```

## Test Files

- **test_auth.py**: Tests for JWT authentication (create_access_token, decode_access_token)
- **test_models.py**: Tests for Pydantic models and validation (UserRegister, QueryRequest, etc.)
- **test_rag.py**: Tests for RAG functionality (document processing, text extraction, chunking)

## Test Coverage

The tests cover:

### Authentication (test_auth.py)
- ✅ JWT token creation
- ✅ JWT token validation
- ✅ Token expiration handling
- ✅ Invalid token handling
- ✅ Missing claims handling

### Models (test_models.py)
- ✅ User registration validation (email, username, password)
- ✅ Query request validation (empty queries, length limits, top_k bounds)
- ✅ Document model validation
- ✅ Error response models

### RAG Functionality (test_rag.py)
- ✅ Text extraction from TXT files
- ✅ Text extraction from PDF files (mocked)
- ✅ Text extraction from DOCX files (mocked)
- ✅ Text chunking with overlap
- ✅ Ollama LLM provider (mocked)

## Common Test Scenarios

### Test that would have caught the NoneType error:

The bug that caused `TypeError: 'NoneType' object is not subscriptable` would be caught by an integration test like:

```python
def test_main_page_requires_user():
    """Test that main page handles missing user gracefully."""
    st.session_state.token = "valid_token"
    st.session_state.user = None  # This is the bug condition

    # Should not raise TypeError, should redirect to login
    main()
    assert st.session_state.page == 'login'
```

## Best Practices

1. **Run tests before committing**: Always run tests before pushing changes
2. **Write tests for bugs**: When you find a bug, write a test that reproduces it first
3. **Test edge cases**: Test boundary conditions, None values, empty strings, etc.
4. **Use mocking**: Mock external dependencies (Ollama, Qdrant) to make tests fast and reliable
5. **Keep tests independent**: Each test should be able to run alone

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd backend
    source venv/bin/activate
    pytest --cov=. --cov-report=xml
```

## Troubleshooting

### Import errors
If you get import errors, make sure you're in the backend directory and the virtual environment is activated:
```bash
cd /Users/jesse/PycharmProjects/fontysRAG/rag-app/backend
source venv/bin/activate
```

### Missing dependencies
Install test dependencies:
```bash
pip install -r requirements.txt
```
