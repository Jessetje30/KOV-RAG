# RAG Application - GDPR-Compliant Document Q&A System

A complete Retrieval-Augmented Generation (RAG) web application built with FastAPI, Streamlit, Qdrant, and Mistral AI. This application allows users to upload documents, process them into searchable embeddings, and ask questions that are answered using retrieved context.

## Features

- **GDPR-Compliant**: Uses Mistral AI (European provider) for embeddings and LLM
- **User Authentication**: Secure JWT-based authentication system
- **Document Management**: Upload and manage PDF, DOCX, and TXT files
- **RAG Pipeline**: Automatic document chunking, embedding, and vector storage
- **Intelligent Q&A**: Ask questions and get answers with source citations
- **User Isolation**: Each user's documents are kept separate and private
- **Modern UI**: Clean Streamlit interface for easy interaction

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLite**: User database with SQLAlchemy ORM
- **Qdrant**: Vector database for embeddings
- **Mistral AI**: Embeddings and LLM completions
- **JWT**: Secure token-based authentication

### Frontend
- **Streamlit**: Interactive web interface

### Infrastructure
- **Docker**: Containerized Qdrant deployment
- **Python 3.11+**: Programming language

## Project Structure

```
rag-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── auth.py              # JWT authentication
│   ├── rag.py               # RAG pipeline
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLAlchemy database
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── app.py               # Streamlit application
│   └── requirements.txt     # Python dependencies
├── docker-compose.yml       # Qdrant container setup
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Mistral AI API key (get one at https://console.mistral.ai/)

## Installation

### 1. Clone or Navigate to the Project

```bash
cd rag-app
```

### 2. Set Up Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and add your Mistral API key:

```bash
# Get your API key from https://console.mistral.ai/
MISTRAL_API_KEY=your_mistral_api_key_here

# Generate a secure JWT secret key
JWT_SECRET_KEY=your_jwt_secret_key_here
```

To generate a secure JWT secret key, run:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start Qdrant Vector Database

Start the Qdrant container using Docker Compose:

```bash
docker-compose up -d
```

Verify Qdrant is running:

```bash
curl http://localhost:6333
```

### 4. Set Up Backend

Navigate to the backend directory and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### 5. Set Up Frontend

In a new terminal, navigate to the frontend directory and install dependencies:

```bash
cd frontend
pip install -r requirements.txt
```

## Running the Application

### Start the Backend Server

From the `backend/` directory:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Start the Frontend Application

From the `frontend/` directory:

```bash
streamlit run app.py
```

The Streamlit frontend will be available at:
- Frontend: http://localhost:8501

## Usage

### 1. Register/Login

- Open http://localhost:8501 in your browser
- Create a new account or login with existing credentials
- Minimum password length: 8 characters

### 2. Upload Documents

- Navigate to "Upload Documents" in the sidebar
- Upload PDF, DOCX, or TXT files (max 10MB)
- The system will automatically:
  - Extract text from the document
  - Split it into chunks (800 characters with 100 character overlap)
  - Generate embeddings using Mistral AI
  - Store vectors in Qdrant

### 3. Ask Questions

- Navigate to "Query Documents"
- Enter your question in the text area
- Choose the number of source chunks to retrieve (1-10)
- Click "Submit Query"
- View the generated answer and source citations

### 4. Manage Documents

- Navigate to "Manage Documents"
- View all uploaded documents
- See document details (chunks, size, upload date)
- Delete documents as needed

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### Documents
- `POST /api/documents/upload` - Upload and process document
- `GET /api/documents` - List user's documents
- `DELETE /api/documents/{document_id}` - Delete document

### Query
- `POST /api/query` - Query documents with RAG

### Health
- `GET /health` - System health check

## Configuration

All configuration is done via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MISTRAL_API_KEY` | Mistral AI API key | Required |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_EXPIRATION_HOURS` | Token expiration time | 24 |
| `DATABASE_URL` | SQLite database path | sqlite:///./rag_app.db |
| `QDRANT_HOST` | Qdrant host | localhost |
| `QDRANT_PORT` | Qdrant port | 6333 |
| `BACKEND_HOST` | Backend host | 0.0.0.0 |
| `BACKEND_PORT` | Backend port | 8000 |
| `BACKEND_URL` | Backend URL for frontend | http://localhost:8000 |
| `CHUNK_SIZE` | Text chunk size in characters | 800 |
| `CHUNK_OVERLAP` | Chunk overlap in characters | 100 |
| `MAX_FILE_SIZE_MB` | Maximum file size | 10 |
| `MISTRAL_EMBEDDING_MODEL` | Mistral embedding model | mistral-embed |
| `MISTRAL_LLM_MODEL` | Mistral LLM model | mistral-small-latest |

## Security Features

- **Password Hashing**: Bcrypt for secure password storage
- **JWT Tokens**: Secure stateless authentication
- **User Isolation**: Each user's data is completely isolated
- **Input Validation**: Pydantic models for all inputs
- **CORS Protection**: Configurable CORS middleware
- **GDPR Compliance**: All data stored locally/in Europe via Mistral AI

## Troubleshooting

### Backend won't start
- Ensure all dependencies are installed: `pip install -r backend/requirements.txt`
- Check that Qdrant is running: `docker ps`
- Verify environment variables are set in `.env`

### Frontend can't connect to backend
- Ensure backend is running on http://localhost:8000
- Check `BACKEND_URL` in `.env` or frontend environment

### Qdrant connection errors
- Verify Qdrant container is running: `docker-compose ps`
- Check Qdrant logs: `docker-compose logs qdrant`
- Ensure port 6333 is not being used by another service

### Mistral API errors
- Verify your API key is correct in `.env`
- Check your Mistral AI account has available credits
- Ensure you have internet connectivity

### Document processing fails
- Check file size is under 10MB
- Verify file format is PDF, DOCX, or TXT
- Ensure the file contains extractable text

## Development

### Running in Development Mode

Backend with auto-reload:
```bash
cd backend
uvicorn main:app --reload
```

Frontend with auto-reload (default):
```bash
cd frontend
streamlit run app.py
```

### Database Migrations

The application uses SQLAlchemy and creates tables automatically on startup. To reset the database:

```bash
cd backend
rm rag_app.db  # Delete the database file
python main.py  # Restart to recreate tables
```

### Viewing Qdrant Data

Access Qdrant's web UI (if enabled):
```bash
http://localhost:6333/dashboard
```

Or use the Qdrant API:
```bash
curl http://localhost:6333/collections
```

## Production Deployment

For production deployment, consider:

1. **Use a production-grade database**: PostgreSQL instead of SQLite
2. **Secure environment variables**: Use secrets management
3. **Enable HTTPS**: Use nginx or traefik as reverse proxy
4. **Configure CORS properly**: Specify exact allowed origins
5. **Use production ASGI server**: Gunicorn with uvicorn workers
6. **Set up monitoring**: Add logging and monitoring tools
7. **Backup strategy**: Regular backups of database and Qdrant data
8. **Scale Qdrant**: Use Qdrant Cloud or cluster setup
9. **Rate limiting**: Add rate limiting to API endpoints
10. **Container orchestration**: Use Kubernetes or Docker Swarm

## Performance Tips

- Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` based on your document types
- Increase `top_k` for more comprehensive answers (but slower)
- Use Mistral's smaller models for faster responses
- Consider caching frequently asked questions
- Monitor Qdrant memory usage and scale as needed

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at http://localhost:8000/docs
3. Check Qdrant documentation at https://qdrant.tech/documentation/
4. Review Mistral AI documentation at https://docs.mistral.ai/

## Acknowledgments

- **Mistral AI**: GDPR-compliant LLM and embeddings
- **Qdrant**: High-performance vector database
- **FastAPI**: Modern Python web framework
- **Streamlit**: Rapid UI development framework
