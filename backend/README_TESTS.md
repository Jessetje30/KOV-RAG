# Test Suite Documentation

Comprehensive test suite for the RAG BBL/KOV Application backend.

## Test Files Overview

### Core Test Files

| Test File | Coverage | Test Count |
|-----------|----------|------------|
| `test_api_endpoints.py` | All API routes (health, auth, documents, query, chat) | 25+ tests |
| `test_cache.py` | Query cache (LRU, TTL, hit/miss) | 15+ tests |
| `test_core_functionality.py` | Vector store, LLM, document processing, BBL | 20+ tests |
| `test_auth.py` | JWT authentication | 5 tests |
| `test_models.py` | Pydantic model validation | 10+ tests |
| `test_rag.py` | RAG functionality | 8 tests |
| `test_bbl_parser.py` | BBL XML/HTML parsing | 5+ tests |
| `test_bbl_chunker.py` | BBL-specific chunking | 5+ tests |

**Total**: ~95+ tests covering all major functionality

## Setup

### Prerequisites

```bash
cd /Users/jesse/PycharmProjects/RAG\ BBL\ KOV/rag-app/backend
source venv/bin/activate
```

### Install Test Dependencies

Already included in `requirements.txt`:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## Running Tests

### Run All Tests

```bash
# Basic run
pytest

# Verbose output
pytest -v

# With test summary
pytest -v --tb=short
```

### Run Specific Test Files

```bash
# API endpoint tests
pytest test_api_endpoints.py -v

# Cache tests
pytest test_cache.py -v

# Core functionality tests
pytest test_core_functionality.py -v

# Authentication tests
pytest test_auth.py -v
```

### Run Specific Test Classes

```bash
# Test only health endpoints
pytest test_api_endpoints.py::TestHealthEndpoints -v

# Test only cache functionality
pytest test_cache.py::TestQueryCache -v

# Test only vector store
pytest test_core_functionality.py::TestVectorStore -v
```

### Run Specific Tests

```bash
# Single test
pytest test_api_endpoints.py::TestAuthenticationEndpoints::test_register_valid_user -v

# Multiple tests with pattern
pytest -k "cache" -v
pytest -k "test_query" -v
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=. --cov-report=term-missing
```

## Test Coverage by Module

### API Endpoints (`test_api_endpoints.py`)

**Health Endpoints**
- ✅ Health check returns status
- ✅ Root endpoint returns API info

**Authentication**
- ✅ User registration with valid data
- ✅ Duplicate username/email validation
- ✅ Weak password validation
- ✅ Login with valid credentials
- ✅ Login with invalid password
- ✅ Login for nonexistent user

**Document Management**
- ✅ Upload document
- ✅ Upload without authentication
- ✅ List user documents
- ✅ Delete document

**Query**
- ✅ Query documents with sources
- ✅ Query without authentication
- ✅ Empty query validation
- ✅ Top-k bounds validation

**Chat Sessions**
- ✅ Create chat session
- ✅ List chat sessions
- ✅ Query with chat history
- ✅ Delete chat session

**Rate Limiting**
- ✅ Rate limit enforcement on query endpoint

### Cache Functionality (`test_cache.py`)

**Basic Operations**
- ✅ Cache set and get
- ✅ Cache miss returns None
- ✅ Cache key uniqueness (user_id, query_text, top_k)

**TTL (Time To Live)**
- ✅ Cache entries expire after TTL
- ✅ Fresh entries are accessible

**LRU Eviction**
- ✅ LRU eviction when cache is full
- ✅ Access updates LRU order
- ✅ Most recently used items kept

**Cache Management**
- ✅ Clear entire cache
- ✅ Get cache statistics
- ✅ Large results caching
- ✅ Concurrent operations
- ✅ Update existing key

### Core Functionality (`test_core_functionality.py`)

**Vector Store**
- ✅ Collection creation
- ✅ Adding vectors to collection
- ✅ Search returns relevant results
- ✅ Delete by document ID

**LLM Provider**
- ✅ Generate embeddings
- ✅ Generate answers
- ✅ Generate summaries (batch)
- ✅ Parallel summaries and titles

**Document Processing**
- ✅ Extract text from .txt files
- ✅ Extract text from PDFs
- ✅ Unsupported file type error

**Text Chunking**
- ✅ Basic text chunking
- ✅ Chunk overlap
- ✅ Short text single chunk
- ✅ Empty text handling

**BBL Parser**
- ✅ Parse BBL XML structure
- ✅ Extract articles with labels
- ✅ Empty document handling

**BBL Chunker**
- ✅ Preserve article structure
- ✅ Article metadata in chunks

**RAG Pipeline Integration**
- ✅ Complete document processing flow
- ✅ Query with cache hit

## Test Patterns & Best Practices

### Fixtures

```python
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    # Register and login, return headers
```

### Mocking External Services

```python
@patch('rag.llm.openai_provider.OpenAI')
def test_with_mock_openai(mock_openai):
    # Test without hitting actual OpenAI API
    mock_client = Mock()
    mock_openai.return_value = mock_client
    # ... test code
```

### Testing Authentication

```python
def test_protected_endpoint(client, auth_headers):
    # Use auth_headers fixture for authenticated requests
    response = client.get("/api/documents", headers=auth_headers)
    assert response.status_code == 200
```

### Testing Validation

```python
def test_invalid_input(client):
    response = client.post("/api/query", json={"query": ""})
    assert response.status_code == 422  # Validation error
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in backend directory
cd /Users/jesse/PycharmProjects/RAG\ BBL\ KOV/rag-app/backend

# Activate venv
source venv/bin/activate

# Run with PYTHONPATH
PYTHONPATH=. pytest
```

### Database Conflicts

```bash
# Tests use a separate test database
# If you see conflicts, ensure tests clean up properly
pytest --lf  # Run last failed tests only
```

### Slow Tests

```bash
# Run only fast tests (skip integration)
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Mock Issues

If mocks aren't working:
- Check patch path matches actual import path
- Use `@patch` decorator or context manager
- Verify mock is set up before test runs

## Coverage Goals

- **Target**: 80%+ coverage
- **Critical paths**: 95%+ (auth, query, document upload)
- **Edge cases**: Comprehensive error handling tests

## Adding New Tests

When adding new features:

1. **Write tests first** (TDD)
2. **Test happy path** - normal operation
3. **Test edge cases** - empty inputs, None values
4. **Test error cases** - invalid inputs, failures
5. **Test authentication** - with/without auth
6. **Test authorization** - user can only access own data

### Test Template

```python
class TestNewFeature:
    """Tests for new feature."""

    def test_basic_operation(self):
        """Test basic functionality works."""
        # Arrange
        # Act
        # Assert

    def test_error_handling(self):
        """Test error cases are handled."""
        # Test with invalid input

    def test_edge_cases(self):
        """Test boundary conditions."""
        # Test with empty, None, max values
```

## Performance Testing

For performance-critical paths:

```python
import time

def test_query_performance():
    """Test query completes within acceptable time."""
    start = time.time()

    # Run query
    result = query_function()

    elapsed = time.time() - start
    assert elapsed < 10.0  # Should complete in <10s
```

## Test Data

Test data is mocked and not dependent on actual:
- OpenAI API (mocked)
- Qdrant database (mocked)
- Real documents (sample data used)

This makes tests:
- **Fast** - no external API calls
- **Reliable** - no network dependencies
- **Isolated** - tests don't affect production

## Maintenance

- Run tests before each commit
- Update tests when changing functionality
- Keep test coverage above 80%
- Review and update mocks when dependencies update

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
