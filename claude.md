# RAG BBL/KOV Application - Claude Code Documentation

Dit is de centrale documentatie index voor het RAG BBL/KOV project. Alle Claude Code specifieke documentatie staat in de `.claude/docs/` directory.

## Project Overzicht

Een GDPR-compliant RAG (Retrieval-Augmented Generation) applicatie voor het doorzoeken van BBL (Beroeps Begeleidende Leerweg) en KOV (Kwalificatie OnderwijsVorm) documenten.

**Tech Stack:**
- Backend: FastAPI + Python 3.12
- LLM: OpenAI GPT-4-turbo
- Embeddings: OpenAI text-embedding-3-large (3072 dim)
- Vector Database: Qdrant
- Frontend: Streamlit
- Database: SQLite

## Documentatie Structuur

### Architectuur & Design
- [Project Architectuur](./.claude/docs/architecture.md) - Systeemoverzicht, componenten en data flows
- [Backend Structuur](./.claude/docs/backend-structure.md) - API routes, pipeline, en module organisatie
- [📊 **Complete Code Structure Analysis**](./.claude/docs/code-structure-analysis.md) - **Uitgebreide codebase analyse met refactoring roadmap**

### Features & Functionaliteit
- [RAG Pipeline](./.claude/docs/rag-pipeline.md) - Document processing, chunking, embeddings, en query flows
- [BBL Document Parsing](./.claude/docs/bbl-parsing.md) - Specifieke BBL/KOV document parsing logica
- [Performance Optimalisaties](./.claude/docs/performance.md) - Cache, parallel processing, model keuzes

### Development
- [API Endpoints](./.claude/docs/api-endpoints.md) - Alle routes met examples
- [Testing](./.claude/docs/testing.md) - Test setup en voorbeelden
- [Deployment](./.claude/docs/deployment.md) - Setup, environment variables, docker

### Security & Compliance
- [Security](./.claude/docs/security.md) - Rate limiting, GDPR, data privacy
- [Environment Setup](./.claude/docs/environment.md) - API keys, configuratie

## Quick Start

```bash
# Backend starten
cd backend
./venv/bin/python main.py

# Frontend starten
cd frontend
streamlit run app.py

# Tests runnen
cd backend
pytest -v
```

## Recente Wijzigingen

### Performance Optimalisaties (4 Nov 2025)
- ✅ Switch van GPT-5 (o1-preview) naar GPT-4-turbo (~75% sneller)
- ✅ Parallelle generatie van summaries & titles (~15-20% sneller)
- ✅ In-memory query cache met LRU eviction (instant voor herhaalde queries)
- **Resultaat**: Van 25-47s naar 4-8s voor eerste query, <0.1s voor cached queries

### Backend Refactoring (4 Nov 2025)
- ✅ Gesplitst van monolithic main.py naar modulaire structuur
- ✅ API routes opgesplitst per functionaliteit
- ✅ Dependency injection pattern voor RAG pipeline
- ✅ Rate limiting toegevoegd met slowapi

## Contact & Support

Voor vragen over dit project:
- Check de documentatie in `.claude/docs/`
- Zie `backend/README_TESTS.md` voor test informatie
- Zie `.env.example` bestanden voor configuratie opties
