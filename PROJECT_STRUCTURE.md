# RAG Application - Complete Project Structure

```
rag-app/
│
├── backend/                          # Backend API server
│   ├── __init__.py                   # Package initialization
│   ├── main.py                       # FastAPI application entry point
│   ├── auth.py                       # JWT authentication logic
│   ├── rag.py                        # RAG pipeline implementation
│   ├── models.py                     # Pydantic data models
│   ├── database.py                   # SQLAlchemy database & user management
│   └── requirements.txt              # Backend Python dependencies
│
├── frontend/                         # Streamlit web interface
│   ├── __init__.py                   # Package initialization
│   ├── app.py                        # Streamlit application
│   └── requirements.txt              # Frontend Python dependencies
│
├── docker-compose.yml                # Qdrant container configuration
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
│
├── start.sh                          # Automated startup script
├── stop.sh                           # Automated shutdown script
│
├── README.md                         # Comprehensive documentation
├── QUICKSTART.md                     # Quick start guide
├── PROJECT_STRUCTURE.md              # This file
│
├── requirements-all.txt              # All dependencies combined
└── sample_document.txt               # Sample document for testing

Generated at runtime:
├── .env                              # Environment configuration (not in git)
├── rag_app.db                        # SQLite user database (not in git)
├── qdrant_storage/                   # Qdrant vector data (not in git)
├── backend.log                       # Backend logs (not in git)
└── backend.pid                       # Backend process ID (not in git)
```

## File Descriptions

### Backend Files

**main.py** (343 lines)
- FastAPI application setup
- All API endpoints (auth, documents, query)
- CORS middleware configuration
- Error handling and logging

**auth.py** (138 lines)
- JWT token creation and validation
- User authentication dependencies
- Security scheme implementation

**rag.py** (341 lines)
- DocumentProcessor class for text extraction
- RAGPipeline class for embedding and querying
- Qdrant integration
- Mistral AI API integration

**models.py** (105 lines)
- Pydantic models for all API requests/responses
- Input validation
- Type definitions

**database.py** (154 lines)
- SQLAlchemy configuration
- User database model
- User CRUD operations
- Password hashing with bcrypt

### Frontend Files

**app.py** (369 lines)
- Streamlit UI implementation
- Authentication pages (login/register)
- Document upload interface
- Query interface
- Document management page
- API communication helpers

### Configuration Files

**docker-compose.yml**
- Qdrant container setup
- Port mappings (6333, 6334)
- Volume configuration

**.env.example**
- All environment variables with descriptions
- Default values
- Configuration guide

**requirements.txt** (Backend)
- FastAPI and web server packages
- Database packages (SQLAlchemy)
- Authentication packages (JWT, bcrypt)
- Mistral AI SDK
- Qdrant client
- Document processing (PyPDF2, python-docx)

**requirements.txt** (Frontend)
- Streamlit framework
- HTTP requests library

### Scripts

**start.sh**
- Automated startup sequence
- Environment validation
- Service health checks
- Log management

**stop.sh**
- Graceful shutdown of all services
- Process cleanup

### Documentation

**README.md**
- Complete project documentation
- Installation instructions
- API reference
- Configuration guide
- Troubleshooting
- Production deployment tips

**QUICKSTART.md**
- 5-minute setup guide
- Step-by-step instructions
- Common troubleshooting
- Example workflow

**sample_document.txt**
- Comprehensive RAG overview
- Testing examples
- Sample queries

## Key Components

### Authentication Flow
1. User registers/logs in via frontend
2. Backend validates credentials
3. JWT token issued
4. Token included in subsequent requests
5. Backend validates token for protected endpoints

### Document Processing Flow
1. User uploads file via frontend
2. Backend receives and validates file
3. Text extracted based on file type
4. Text chunked with overlap
5. Chunks embedded via Mistral AI
6. Vectors stored in Qdrant with metadata
7. Success response returned

### Query Flow
1. User submits question via frontend
2. Backend receives query
3. Query embedded via Mistral AI
4. Vector search in Qdrant
5. Top-k chunks retrieved
6. Context built from chunks
7. LLM generates answer via Mistral AI
8. Answer + sources returned

### Data Isolation
- Each user has separate Qdrant collection
- Collection naming: `user_{user_id}_documents`
- Vector search filtered by user_id
- Complete data separation

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Framework | FastAPI | High-performance async API |
| Frontend Framework | Streamlit | Rapid UI development |
| Vector Database | Qdrant | Embedding storage & search |
| User Database | SQLite + SQLAlchemy | User authentication data |
| Embedding Provider | Mistral AI | Text-to-vector conversion |
| LLM Provider | Mistral AI | Answer generation |
| Authentication | JWT | Stateless auth tokens |
| Password Hashing | Bcrypt | Secure password storage |
| Container Platform | Docker | Qdrant deployment |
| Document Processing | PyPDF2, python-docx | Text extraction |

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List user documents
- `DELETE /api/documents/{id}` - Delete document

### Query
- `POST /api/query` - Query RAG system

### System
- `GET /health` - Health check
- `GET /` - API information

## Security Features

1. **Password Security**: Bcrypt hashing
2. **Authentication**: JWT tokens with expiration
3. **Data Isolation**: User-specific collections
4. **Input Validation**: Pydantic models
5. **CORS**: Configurable origin restrictions
6. **File Validation**: Size and type checks
7. **GDPR Compliance**: European data processing

## Production Checklist

- [ ] Change JWT_SECRET_KEY to a strong secret
- [ ] Configure CORS allowed origins
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up HTTPS/TLS
- [ ] Configure reverse proxy (nginx)
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Configure backups
- [ ] Use secrets management
- [ ] Scale Qdrant (cluster or cloud)
- [ ] Add error tracking (Sentry)
- [ ] Implement caching
- [ ] Add API versioning
- [ ] Set up CI/CD pipeline

## Development Workflow

1. **Setup**: Run `./start.sh` or follow manual steps
2. **Development**: Make changes to code
3. **Testing**: Upload test documents and query
4. **Debugging**: Check logs in `backend.log`
5. **Cleanup**: Run `./stop.sh`

## Useful Commands

```bash
# View backend logs
tail -f backend.log

# View Qdrant logs
docker-compose logs -f qdrant

# Check Qdrant status
curl http://localhost:6333

# Check backend health
curl http://localhost:8000/health

# View Qdrant collections
curl http://localhost:6333/collections

# Rebuild everything
./stop.sh && rm -rf qdrant_storage/ rag_app.db && ./start.sh

# Install all dependencies at once
pip install -r requirements-all.txt
```

## Support & Resources

- Mistral AI Docs: https://docs.mistral.ai/
- Qdrant Docs: https://qdrant.tech/documentation/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Streamlit Docs: https://docs.streamlit.io/
