# 🏗️ Refactoring Plan: RAG BBL Application

**Doel**: Van monolithische files naar een gestructureerde, onderhoudbare codebase
**Strategie**: Incrementele refactoring - na elke fase werkt de applicatie nog
**Tijdsinschatting**: 8-12 uur voor volledig plan

---

## **FASE 1: Configuratie Centraliseren** ⏱️ 30 min

### Doelstelling
Alle environment variabelen en configuratie op één plek verzamelen voor betere overzichtelijkheid.

### Stappen

#### 1.1 Maak het configuratie bestand
```bash
cd /Users/jesse/PycharmProjects/RAG\ BBL\ KOV/rag-app/backend
touch config.py
```

#### 1.2 Schrijf config.py
```python
"""
Centralized configuration for RAG BBL application.
All environment variables are loaded here.
"""
import os
from functools import lru_cache

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_app.db")

# ============================================================================
# QDRANT CONFIGURATION
# ============================================================================
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# ============================================================================
# OPENAI CONFIGURATION
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-5")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# ============================================================================
# RAG CONFIGURATION
# ============================================================================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "100"))
MINIMUM_RELEVANCE_THRESHOLD = float(os.getenv("MINIMUM_RELEVANCE_THRESHOLD", "0.4"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))

# ============================================================================
# FILE UPLOAD CONFIGURATION
# ============================================================================
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# ============================================================================
# JWT CONFIGURATION
# ============================================================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# EMBEDDING CONFIGURATION
# ============================================================================
EMBEDDING_DIMENSION = 3072  # text-embedding-3-large dimension


@lru_cache()
def get_settings():
    """
    Cached settings instance.
    Use this in FastAPI dependencies.
    """
    return {
        "database_url": DATABASE_URL,
        "qdrant_host": QDRANT_HOST,
        "qdrant_port": QDRANT_PORT,
        "openai_api_key": OPENAI_API_KEY,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
```

#### 1.3 Update rag.py om config te gebruiken
#### 1.4 Update auth.py om config te gebruiken
#### 1.5 Verificatie

---

[Resterende fases 2-9 zoals eerder beschreven...]

---

## Uitvoering Status

- [ ] Fase 1: Configuratie Centraliseren
- [ ] Fase 2: Prompts Isoleren
- [ ] Fase 3: Models Splitsen
- [ ] Fase 4: RAG Components Splitsen
- [ ] Fase 5: Database Layer Herstructureren
- [ ] Fase 6: API Routes Splitsen
- [ ] Fase 7: Dependencies Centraliseren
- [ ] Fase 8: Main.py Opschonen
- [ ] Fase 9: Testing & Cleanup
