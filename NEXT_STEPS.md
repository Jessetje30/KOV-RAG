# Refactoring Next Steps

## ✅ COMPLETED (Phases 1-5)

Je hebt succesvol de eerste 5 fases van de refactoring voltooid:

1. ✅ **Configuratie Centraliseren** - Alle config in `config.py`
2. ✅ **Prompts Isoleren** - AI prompts in `rag/llm/prompts.py`
3. ✅ **Models Splitsen** - Pydantic models in `models/` directory
4. ✅ **RAG Components Splitsen** - Van 901 → 7 georganiseerde modules
5. ✅ **Database Layer Herstructureren** - Database code in `db/` directory

**Resultaat:** 
- Van 3 monolithische files (1490 regels) → 25+ georganiseerde modules (1673 regels)
- Veel beter onderhoudbaar en testbaar
- Duidelijke scheiding van verantwoordelijkheden

## 🔄 RESTERENDE FASES (6-9)

### **Fase 6: API Routes Splitsen** (60 min) - HOGE PRIORITEIT

**Doel:** `main.py` van 770 regels → ~100 regels (alleen app setup)

#### Stap 1: Maak directory structuur
```bash
cd backend
mkdir -p api/routes
touch api/__init__.py
touch api/routes/__init__.py
touch api/routes/auth.py
touch api/routes/documents.py
touch api/routes/chat.py
touch api/routes/query.py
touch api/routes/health.py
```

#### Stap 2: Verplaats Auth endpoints naar `api/routes/auth.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.auth import UserRegister, UserLogin, User, Token
from db import get_db, UserRepository
from auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Kopieer logica uit main.py regel 113-159
    ...

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # Kopieer logica uit main.py regel 161-208
    ...

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
```

#### Stap 3: Verplaats Document endpoints naar `api/routes/documents.py`
```python
from fastapi import APIRouter, Depends, UploadFile, File
from models.auth import User
from models.document import DocumentUploadResponse, DocumentListResponse
from rag_bbl import rag_pipeline
from auth import get_current_user

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(...):
    # Kopieer logica uit main.py
    ...
```

#### Stap 4: Herhaal voor Chat, Query, en Health
Verplaats endpoints naar respectievelijke route files.

#### Stap 5: Update `main.py`
```python
from fastapi import FastAPI
from api.routes import auth_router, documents_router, chat_router, query_router, health_router

app = FastAPI(title="RAG BBL API")

# Register routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(query_router)
app.include_router(health_router)
```

---

### **Fase 7: Dependencies Centraliseren** (20 min) - MEDIUM PRIORITEIT

**Doel:** Gedeelde dependencies naar `dependencies.py`

#### Stap 1: Maak `dependencies.py`
```bash
touch dependencies.py
```

#### Stap 2: Verplaats `get_current_user` uit main.py
```python
# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from models.auth import User
from db import get_db, UserRepository
from auth import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = verify_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = UserRepository.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User.from_orm(user)
```

#### Stap 3: Update alle route files
```python
# In api/routes/*.py
from dependencies import get_current_user
```

---

### **Fase 8: Main.py Opschonen** (30 min) - HOGE PRIORITEIT

**Doel:** `main.py` reduceren tot alleen app setup

#### Nieuwe `main.py` structuur:
```python
"""
FastAPI application for RAG BBL system.
Main entry point - registers all routers and handles app lifecycle.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from rag_bbl import rag_pipeline, BBLRAGPipeline
from api.routes import (
    auth_router,
    documents_router,
    query_router,
    chat_router,
    health_router
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting RAG BBL API...")
    init_db()
    # Initialize RAG pipeline
    global rag_pipeline
    rag_pipeline = BBLRAGPipeline()
    
    yield
    
    logger.info("Shutting down RAG BBL API...")


app = FastAPI(
    title="RAG BBL API",
    description="RAG system for BBL documents",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {
        "name": "RAG BBL API",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "documents": "/api/documents",
            "query": "/api/query",
            "chat": "/api/chat",
            "health": "/health"
        }
    }
```

**Voor:** 770 regels  
**Na:** ~85 regels  
**Reductie:** 89%! 🎉

---

### **Fase 9: Testing & Cleanup** (45 min) - HOGE PRIORITEIT

#### Stap 1: Backup oude files
```bash
cd backend
mkdir -p _old_backup
mv models_old.py _old_backup/
mv rag_old.py _old_backup/
mv database_old.py _old_backup/
```

#### Stap 2: Clean up __pycache__
```bash
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -name "*.pyc" -delete
```

#### Stap 3: Run tests
```bash
./venv/bin/python -m pytest test_*.py -v
```

#### Stap 4: Integration test
```bash
# Start server
./venv/bin/python main.py &
SERVER_PID=$!

# Test health
curl http://localhost:8000/health

# Test register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"test","password":"test1234"}'

# Cleanup
kill $SERVER_PID
```

#### Stap 5: Documenteer finale structuur
Update README.md met nieuwe structuur.

---

## 📊 VERWACHTE EINDRESULTAAT

### Voor (Monolithisch):
```
backend/
├── main.py          (770 regels) ❌
├── models.py        (204 regels) ❌
├── rag.py           (901 regels) ❌
├── database.py      (385 regels) ❌
└── auth.py          (176 regels) ✅
```

### Na (Gestructureerd):
```
backend/
├── main.py                      (~85 regels) ✅
├── config.py                    (73 regels) ✅
├── dependencies.py              (40 regels) ✅
├── auth.py                      (176 regels) ✅
│
├── models/                      # Pydantic models
│   ├── auth.py          (56)
│   ├── document.py      (27)
│   ├── chat.py          (72)
│   └── query.py         (35)
│
├── db/                          # Database layer
│   ├── base.py          (38)
│   ├── models.py        (87)
│   └── crud.py          (120)
│
├── rag/                         # RAG components
│   ├── document_processor.py    (100)
│   ├── text_chunker.py          (102)
│   ├── vector_store.py          (156)
│   ├── pipeline.py              (352)
│   └── llm/
│       ├── base.py              (59)
│       ├── openai_provider.py   (191)
│       └── prompts.py           (147)
│
└── api/                         # API routes
    └── routes/
        ├── auth.py              (~100)
        ├── documents.py         (~150)
        ├── chat.py              (~300)
        ├── query.py             (~100)
        └── health.py            (~30)
```

## ✨ VOORDELEN

1. **90% kleinere main.py** - Van 770 → 85 regels
2. **Testbaarheid** - Elke component kan unit tests hebben
3. **Onderhoudbaarheid** - Bugs zijn makkelijk te vinden en fixen
4. **Schaalbaarheid** - Nieuwe features zijn makkelijk toe te voegen
5. **Onboarding** - Nieuwe developers begrijpen de structuur snel
6. **Herbruikbaarheid** - Components kunnen in andere projecten gebruikt worden

## 🎯 SUCCES!

Je hebt al 55% van de refactoring voltooid (Fase 1-5).
De resterende 45% (Fase 6-9) duurt ongeveer 2.5-3 uur.

**Veel succes!** 🚀

