# Project Architectuur

## Systeem Overzicht

De RAG BBL/KOV applicatie is een full-stack systeem voor het doorzoeken van BBL en KOV documenten met behulp van AI.

```
┌─────────────┐
│  Streamlit  │  Frontend (Port 8501)
│  Frontend   │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   FastAPI   │  Backend API (Port 8000)
│   Backend   │  - Authentication (JWT)
│             │  - Document Management
│             │  - RAG Pipeline
└──────┬──────┘
       │
       ├─────────┐
       │         │
       ▼         ▼
┌─────────┐  ┌──────────┐
│ SQLite  │  │  Qdrant  │  Databases
│  Users  │  │  Vectors │  - SQLite: Port 6333
│  Chats  │  │  Docs    │  - Qdrant: localhost
└─────────┘  └──────────┘
       │         │
       │         ▼
       │    ┌──────────────┐
       └───►│   OpenAI     │  External Services
            │   API        │  - GPT-4-turbo
            │              │  - text-embedding-3-large
            └──────────────┘
```

## Component Diagram

### Frontend (Streamlit)

**Locatie**: `frontend/app.py`

**Responsibilities**:
- User interface
- Authentication flow
- Document upload
- Query interface
- Chat sessions
- Source display

**Tech**:
- Streamlit 1.x
- Python 3.12
- Requests library voor API calls

### Backend (FastAPI)

**Locatie**: `backend/`

**Responsibilities**:
- REST API endpoints
- JWT authentication
- Rate limiting
- Request validation
- RAG pipeline orchestration

**Tech**:
- FastAPI 0.1x
- Pydantic voor validation
- slowapi voor rate limiting
- python-jose voor JWT

### RAG Pipeline

**Locatie**: `backend/rag/`

**Responsibilities**:
- Document processing (PDF/text extraction)
- Text chunking
- Embedding generation
- Vector search
- LLM query answering
- Source summarization

**Components**:
```
RAGPipeline
├── DocumentProcessor    # PDF/text extraction
├── TextChunker         # Split into chunks
├── VectorStore         # Qdrant interface
└── LLMProvider         # OpenAI interface
```

### BBL-Specific Components

**Locatie**: `backend/rag/bbl/`

**Responsibilities**:
- BBL/KOV XML/HTML parsing
- Article extraction met labels
- Metadata enrichment
- BBL-aware chunking

**Components**:
```
BBLRAGPipeline
├── BBLParser          # XML/HTML to structured data
├── BBLChunker         # Chunk preserving structure
└── BBLRAGPipeline     # Orchestration
```

### Database Layer

#### SQLite
**Locatie**: `backend/db/`

**Schema**:
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Qdrant (Vector Store)
**Port**: 6333

**Collections**:
- `user_{user_id}_documents` - Per-user document collections

**Vector Schema**:
```python
{
    "vector": [0.123, ...],  # 3072 dimensions (text-embedding-3-large)
    "payload": {
        "text": "chunk text",
        "document_id": "uuid",
        "filename": "doc.pdf",
        "chunk_index": 0,
        "upload_date": "2025-11-04T...",
        "file_size": 12345,
        "user_id": 1,
        # BBL-specific:
        "artikel_label": "Artikel 1.2",
        "artikel_titel": "Definitie BBL-leerling"
    }
}
```

### External Services

#### OpenAI API

**Models gebruikt**:
- **GPT-4-turbo**: Answer generation (queries)
- **GPT-4-turbo**: Summaries & titles
- **text-embedding-3-large**: Document embeddings (3072 dim)

**Rate limits**:
- Geconfigureerd via slowapi in backend
- OpenAI tier limits apply

## Data Flow Diagrams

### Document Upload Flow

```
User
  │
  ├─► Upload PDF via Frontend
  │
  ▼
FastAPI (/api/documents/upload)
  │
  ├─► Validate file (type, size)
  ├─► Authenticate user (JWT)
  │
  ▼
RAG Pipeline.process_document()
  │
  ├─► Extract text (DocumentProcessor)
  │     - PDF → text
  │     - BBL XML/HTML → structured data
  │
  ├─► Chunk text (TextChunker / BBLChunker)
  │     - Chunk size: 1200 chars
  │     - Overlap: 200 chars
  │     - Preserve BBL article structure
  │
  ├─► Generate embeddings (OpenAI)
  │     - text-embedding-3-large
  │     - Batch: all chunks at once
  │
  ▼
Qdrant.add_points()
  │
  └─► Store vectors + metadata

Response to User
  - Document ID
  - Chunks created count
```

### Query Flow

```
User Query: "Wat zijn de eisen voor BBL?"
  │
  ▼
FastAPI (/api/query)
  │
  ├─► Authenticate user (JWT)
  ├─► Check cache (QueryCache)
  │     - Cache HIT? → Return cached result ✅
  │     - Cache MISS? → Continue ⬇
  │
  ▼
RAG Pipeline.query()
  │
  ├─► Generate query embedding (OpenAI)
  │     - text-embedding-3-large
  │
  ├─► Vector search (Qdrant)
  │     - Similarity search
  │     - Top K=3 results
  │     - Filter: user_id + threshold
  │
  ├─► Build context from sources
  │     - Format: [1] text\n[2] text\n...
  │
  ├─► Generate answer (OpenAI GPT-4-turbo) ──┐
  │                                            │
  ├─► Generate summaries (GPT-4-turbo) ───────┼─► Parallel!
  │                                            │
  └─► Generate titles (GPT-4-turbo) ──────────┘
       │
       ├─► Combine results
       ├─► Cache result (1 hour TTL)
       │
       ▼
Response to User
  - Answer text
  - Sources with summaries & titles
  - Processing time
```

### Chat Query Flow (with History)

```
User Query + Chat Session ID
  │
  ▼
FastAPI (/api/chat/sessions/{id}/query)
  │
  ├─► Authenticate user
  ├─► Validate session ownership
  │
  ▼
RAG Pipeline.query_with_chat()
  │
  ├─► Generate query embedding
  │
  ├─► Vector search (same as simple query)
  │
  ├─► Build context:
  │     - Retrieved sources
  │     - Last 5 chat messages (conversation history)
  │
  ├─► Generate answer with context (GPT-4-turbo)
  │     - Prompt includes conversation
  │     - Citations preserved
  │
  └─► Response (no cache for chat queries)
```

## Security Architecture

### Authentication Flow

```
User Registration
  │
  ├─► POST /api/auth/register
  │     - Email, username, password
  │     - Password validation (8+ chars, special char)
  │
  ├─► Hash password (bcrypt)
  │
  └─► Store in SQLite

User Login
  │
  ├─► POST /api/auth/login
  │     - Username, password
  │
  ├─► Verify password (bcrypt)
  │
  ├─► Generate JWT token
  │     - Expiry: 24 hours
  │     - Algorithm: HS256
  │
  └─► Return token

Protected Endpoint
  │
  ├─► Authorization: Bearer {token}
  │
  ├─► Validate JWT
  │     - Check signature
  │     - Check expiry
  │
  ├─► Extract user_id
  │
  └─► Process request
```

### Data Isolation

**User-specific collections**:
- Elke user heeft eigen Qdrant collection: `user_{user_id}_documents`
- Geen cross-user data leakage mogelijk

**Query-time filtering**:
```python
# Vector search altijd gefiltered op user_id
search_results = vector_store.search(
    collection_name=f"user_{user_id}_documents",
    query_embedding=embedding,
    user_id=user_id,  # Extra filter
    top_k=3
)
```

## Deployment Architecture

### Development

```
localhost:8501  → Streamlit Frontend
localhost:8000  → FastAPI Backend
localhost:6333  → Qdrant Vector DB
SQLite file     → backend/bbl_rag_app.db
```

### Production (Conceptual)

```
Internet
  │
  ├─► HTTPS (443)
  │
  ▼
Reverse Proxy (nginx)
  │
  ├─► :8501 → Streamlit (Docker container)
  │
  └─► :8000 → FastAPI (Docker container)
        │
        ├─► Qdrant (Docker container)
        │
        └─► SQLite (Volume mount)

Environment:
- ENFORCE_HTTPS=true
- CORS_ORIGINS=https://your-domain.com
- Secrets via .env (not committed)
```

## Configuration Management

### Environment Variables

**Backend `.env`**:
```bash
# Security
JWT_SECRET_KEY=<random-secret>
ENFORCE_HTTPS=false

# Database
DATABASE_URL=sqlite:///./bbl_rag_app.db
QDRANT_HOST=localhost
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=<your-key>
OPENAI_LLM_MODEL=gpt-4-turbo
OPENAI_EMBED_MODEL=text-embedding-3-large

# RAG Config
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.7
DEFAULT_TOP_K=3
MAX_TOP_K=10

# API Config
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:8501
```

**Frontend `.env`**:
```bash
BACKEND_URL=http://localhost:8000
```

## Monitoring & Logging

### Log Levels

```python
DEBUG   # Cache operations, detailed flow
INFO    # Query timing, successful operations
WARNING # Fallbacks, non-critical issues
ERROR   # API errors, processing failures
```

### Key Metrics Logged

- Query processing time
- Cache hit/miss ratio
- LLM finish reasons
- Document processing stats
- API request counts (via rate limiter)

## Scalability Considerations

### Current Limitations (Single Instance)

- In-memory cache (lost on restart)
- SQLite (single writer)
- No load balancing

### Future Improvements

1. **Redis cache**: Persistent, shared across instances
2. **PostgreSQL**: Multi-writer database
3. **Load balancer**: Distribute requests
4. **Async processing**: Celery for document processing
5. **Monitoring**: Prometheus + Grafana

## References

- FastAPI: https://fastapi.tiangolo.com/
- Qdrant: https://qdrant.tech/
- OpenAI: https://platform.openai.com/docs
- Streamlit: https://streamlit.io/
