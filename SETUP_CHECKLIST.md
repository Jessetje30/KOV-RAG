# Setup Checklist

Use this checklist to ensure your RAG application is properly configured and running.

## Pre-Installation Checklist

- [ ] Python 3.11 or higher installed
  ```bash
  python3 --version
  ```

- [ ] Docker installed and running
  ```bash
  docker --version
  docker ps
  ```

- [ ] Docker Compose installed
  ```bash
  docker-compose --version
  ```

- [ ] Mistral AI account created
  - Sign up at: https://console.mistral.ai/

- [ ] Mistral AI API key obtained
  - Get from: https://console.mistral.ai/api-keys/

## Configuration Checklist

- [ ] Environment file created
  ```bash
  cp .env.example .env
  ```

- [ ] Mistral API key added to `.env`
  ```bash
  MISTRAL_API_KEY=your_actual_api_key_here
  ```

- [ ] JWT secret key generated and added to `.env`
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] All environment variables reviewed in `.env`

## Installation Checklist

### Option 1: Automated Setup

- [ ] Make scripts executable
  ```bash
  chmod +x start.sh stop.sh
  ```

- [ ] Run startup script
  ```bash
  ./start.sh
  ```

- [ ] Verify all services started successfully

### Option 2: Manual Setup

- [ ] Qdrant started
  ```bash
  docker-compose up -d
  ```

- [ ] Backend dependencies installed
  ```bash
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] Backend server started
  ```bash
  python main.py
  ```

- [ ] Frontend dependencies installed (new terminal)
  ```bash
  cd frontend
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] Frontend server started
  ```bash
  streamlit run app.py
  ```

## Verification Checklist

- [ ] Qdrant is accessible
  ```bash
  curl http://localhost:6333
  ```
  Expected: JSON response with version info

- [ ] Backend is running
  ```bash
  curl http://localhost:8000/health
  ```
  Expected: Health status JSON

- [ ] Backend API docs accessible
  - Open: http://localhost:8000/docs
  - Should see Swagger UI

- [ ] Frontend is accessible
  - Open: http://localhost:8501
  - Should see login/register page

## Functionality Checklist

- [ ] User can register
  - Username (min 3 chars)
  - Valid email
  - Password (min 8 chars)

- [ ] User can login
  - Correct credentials work
  - Invalid credentials rejected

- [ ] User can upload documents
  - PDF file uploads successfully
  - DOCX file uploads successfully
  - TXT file uploads successfully
  - Invalid file types rejected
  - Files over 10MB rejected

- [ ] Documents are processed
  - Chunks created
  - Document appears in "Manage Documents"

- [ ] User can query documents
  - Query returns answer
  - Sources are displayed
  - Relevance scores shown

- [ ] User can manage documents
  - Documents listed correctly
  - Document deletion works
  - Deleted documents don't appear in search

- [ ] User can logout
  - Logout button works
  - Redirected to login page

## Security Checklist

- [ ] JWT secret key is strong and unique
  - Not using example/default value
  - At least 32 characters

- [ ] Passwords are hashed
  - Verify in database: passwords are not plain text

- [ ] Users can only see their own documents
  - Test with multiple user accounts

- [ ] File size limits enforced
  - Test uploading file > 10MB

- [ ] File type validation works
  - Test uploading .exe or other invalid types

## Performance Checklist

- [ ] Document upload completes in reasonable time
  - Small files (< 1MB): < 10 seconds
  - Large files (5-10MB): < 30 seconds

- [ ] Queries return results quickly
  - Simple queries: < 5 seconds
  - Complex queries: < 10 seconds

- [ ] Qdrant has sufficient resources
  ```bash
  docker stats rag-qdrant
  ```
  - Memory usage reasonable
  - CPU not constantly maxed

## Production Readiness Checklist

Only for production deployment:

- [ ] Using strong JWT secret (not from example)
- [ ] CORS configured for specific origins (not *)
- [ ] Using PostgreSQL instead of SQLite
- [ ] HTTPS/TLS configured
- [ ] Reverse proxy (nginx/traefik) set up
- [ ] Rate limiting implemented
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] Backup strategy implemented
- [ ] Error tracking (e.g., Sentry) enabled
- [ ] Environment variables secured (not in code)
- [ ] API keys rotated regularly
- [ ] Database backups automated
- [ ] Qdrant data backed up
- [ ] Load testing performed
- [ ] Security audit completed

## Troubleshooting Checklist

If something doesn't work:

- [ ] Check all environment variables are set
  ```bash
  cat .env | grep -v "^#"
  ```

- [ ] Check backend logs
  ```bash
  tail -f backend.log
  ```

- [ ] Check Qdrant logs
  ```bash
  docker-compose logs qdrant
  ```

- [ ] Check frontend terminal output

- [ ] Verify Mistral API key is valid
  - Check at: https://console.mistral.ai/

- [ ] Verify Mistral account has credits

- [ ] Restart all services
  ```bash
  ./stop.sh && ./start.sh
  ```

- [ ] Check ports are not in use
  ```bash
  lsof -i :6333  # Qdrant
  lsof -i :8000  # Backend
  lsof -i :8501  # Frontend
  ```

- [ ] Review full README.md for detailed troubleshooting

## Testing Checklist

- [ ] Upload sample_document.txt
  ```
  Located in: rag-app/sample_document.txt
  ```

- [ ] Test sample queries:
  - [ ] "What are the main benefits of RAG systems?"
  - [ ] "How does the chunking strategy affect performance?"
  - [ ] "What components are needed for a RAG implementation?"
  - [ ] "How can RAG systems be made GDPR-compliant?"

- [ ] Verify sources are displayed correctly

- [ ] Check relevance scores make sense

## Documentation Checklist

- [ ] Read README.md
- [ ] Read QUICKSTART.md
- [ ] Review PROJECT_STRUCTURE.md
- [ ] Bookmark API docs: http://localhost:8000/docs

## Next Steps

After completing this checklist:

1. Start using the application with your own documents
2. Experiment with different chunk sizes and overlap settings
3. Try different numbers of retrieved sources (top_k)
4. Monitor performance and resource usage
5. Provide feedback or report issues

---

**Date Completed:** _______________

**Completed By:** _______________

**Notes:**
_________________________________
_________________________________
_________________________________
