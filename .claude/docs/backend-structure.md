# Backend Structuur

## Overzicht

De backend is een FastAPI applicatie die de RAG pipeline, authentication, en document management verzorgt.

## Directory Structuur

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration & environment variables
├── dependencies.py        # Dependency injection helpers
├── cache.py              # Query cache implementation
├── middleware.py         # Security headers middleware
│
├── api/                  # API routes
│   ├── __init__.py
│   └── routes/
│       ├── health.py     # Health check endpoint
│       ├── auth.py       # Authentication (register/login)
│       ├── documents.py  # Document upload/list/delete
│       ├── query.py      # RAG query endpoint
│       └── chat.py       # Chat session endpoints
│
├── models/               # Pydantic models
│   ├── __init__.py
│   ├── auth.py          # User, Token, Register/Login
│   ├── document.py      # Document request/response models
│   ├── query.py         # Query request/response models
│   └── chat.py          # Chat session models
│
├── db/                  # Database layer
│   ├── __init__.py
│   ├── base.py         # SQLAlchemy engine & session
│   └── models.py       # User & ChatSession ORM models
│
├── rag/                 # RAG pipeline
│   ├── pipeline.py     # Main RAG orchestration
│   ├── document_processor.py  # PDF/text extraction
│   ├── text_chunker.py        # Document chunking
│   ├── vector_store.py        # Qdrant interface
│   ├── llm/
│   │   ├── base.py           # LLM provider interface
│   │   ├── openai_provider.py # OpenAI implementation
│   │   └── prompts.py        # System & query prompts
│   └── bbl/
│       ├── __init__.py
│       ├── bbl_parser.py     # BBL XML/HTML parsing
│       ├── bbl_chunker.py    # BBL-specific chunking
│       └── rag_bbl.py        # BBL RAG pipeline
│
├── auth.py             # JWT authentication logic
├── test_*.py          # Unit tests
├── pytest.ini         # Pytest configuration
└── .env               # Environment variables
```

## Key Modules

### main.py
Entry point voor de FastAPI applicatie.

**Responsibilities**:
- App initialization met lifespan
- RAG pipeline setup en storage in `app.state`
- CORS middleware configuratie
- Rate limiting setup
- Router registration

**Belangrijke code**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    global rag_pipeline
    rag_pipeline = BBLRAGPipeline()
    app.state.rag_pipeline = rag_pipeline  # Store for dependency injection
    logger.info("RAG pipeline initialized")
    yield
    # Shutdown
    logger.info("Shutting down application...")
```

### dependencies.py
Dependency injection helpers voor FastAPI routes.

**Belangrijke code**:
```python
def get_rag_pipeline(request: Request):
    """Get RAG pipeline instance from app state."""
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline is not initialized"
        )
    return rag_pipeline
```

**Usage in routes**:
```python
@router.post("/query")
async def query_documents(
    query_data: QueryRequest,
    current_user: User = Depends(get_current_user),
    rag_pipeline = Depends(get_rag_pipeline)  # Injected!
):
    answer, sources, time = rag_pipeline.query(...)
```

### cache.py
In-memory LRU cache voor query results.

**Features**:
- Max 100 entries met LRU eviction
- 1 uur TTL (Time To Live)
- MD5 hash keys: `user_id:query_text:top_k`
- Automatic expiry checking

**Code snippet**:
```python
class QueryCache:
    def get(self, user_id: int, query_text: str, top_k: int) -> Optional[...]:
        key = self._generate_key(user_id, query_text, top_k)
        if key in self.cache:
            timestamp, result = self.cache[key]
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]  # Expired
                return None
            self.access_times[key] = time.time()  # Update LRU
            return result
        return None
```

### config.py
Centralized configuration met environment variable loading.

**Belangrijke settings**:
```python
# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_LLM_MODEL = "gpt-4-turbo"
OPENAI_EMBED_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072

# Qdrant
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# RAG
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
SIMILARITY_THRESHOLD = 0.7
DEFAULT_TOP_K = 3
```

## API Routes Structure

### Health (`/health`)
- `GET /health` - System health check

### Auth (`/api/auth`)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT)

### Documents (`/api/documents`)
- `POST /api/documents/upload` - Upload PDF/text document
- `GET /api/documents` - List user's documents
- `DELETE /api/documents/{document_id}` - Delete document

### Query (`/api`)
- `POST /api/query` - Query RAG system (simple)

### Chat (`/api/chat`)
- `POST /api/chat/sessions` - Create chat session
- `GET /api/chat/sessions` - List user's sessions
- `POST /api/chat/sessions/{session_id}/query` - Query with history
- `DELETE /api/chat/sessions/{session_id}` - Delete session

## Rate Limiting

Geïmplementeerd met `slowapi`:

```python
# In main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# In routes
@router.post("/query")
@limiter.limit("20/minute")  # Max 20 queries per minuut
async def query_documents(request: Request, ...):
    pass
```

**Limieten**:
- Query endpoints: 20/minute
- Upload endpoints: 10/minute
- Chat endpoints: 20/minute

## Dependency Injection Pattern

Voorkomt circular imports en zorgt voor proper initialization:

**Probleem (oud)**:
```python
# In routes/query.py
from main import rag_pipeline  # ❌ Circular import, None tijdens import
```

**Oplossing (nieuw)**:
```python
# In routes/query.py
from dependencies import get_rag_pipeline

@router.post("/query")
async def query_documents(
    rag_pipeline = Depends(get_rag_pipeline)  # ✅ Injected from app.state
):
    pass
```

## Error Handling

Consistent error responses:

```python
# 401 Unauthorized
{"detail": "Could not validate credentials"}

# 403 Forbidden
{"detail": "Not authorized to access this document"}

# 429 Too Many Requests
{"detail": "Rate limit exceeded: 20 per 1 minute"}

# 503 Service Unavailable
{"detail": "RAG pipeline is not initialized"}
```

## Logging

Structured logging met Python `logging`:

```python
import logging
logger = logging.getLogger(__name__)

# Levels gebruikt:
logger.debug("Cache MISS for query: ...")
logger.info("Query processed in 6.32s with 3 sources")
logger.warning("Summary parsing failed, using fallback")
logger.error("Error generating answer: ...")
```

## Security

### CORS
Configured voor frontend origins:
```python
CORS_ORIGINS = ["http://localhost:8501", "http://localhost:3000"]
```

### Security Headers
Custom middleware voor security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (production only)

### File Upload Sanitization
```python
def sanitize_filename(filename: str) -> str:
    """Prevent path traversal attacks."""
    basename = Path(filename).name
    basename = basename.replace("..", "").replace("/", "").replace("\\", "")
    basename = re.sub(r'[^a-zA-Z0-9._\- ]', '_', basename)
    return basename
```

## Testing

Zie `backend/README_TESTS.md` en test files:
- `test_auth.py` - Authentication tests
- `test_models.py` - Pydantic model validation
- `test_rag.py` - RAG pipeline tests
- `test_bbl_parser.py` - BBL parsing tests
- `test_bbl_chunker.py` - BBL chunking tests

Run tests:
```bash
pytest -v
```

## References

- FastAPI docs: https://fastapi.tiangolo.com/
- Dependency injection: https://fastapi.tiangolo.com/tutorial/dependencies/
- slowapi: https://github.com/laurentS/slowapi
