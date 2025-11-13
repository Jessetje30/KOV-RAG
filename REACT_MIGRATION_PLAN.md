# KOV-RAG React + TypeScript Migratie Bouwplan

## Inhoudsopgave
1. [Executive Summary](#executive-summary)
2. [Huidige Applicatie Overview](#huidige-applicatie-overview)
3. [Functionaliteiten](#functionaliteiten)
4. [Backend Architectuur (blijft behouden)](#backend-architectuur-blijft-behouden)
5. [Frontend Migratie naar React + TypeScript](#frontend-migratie-naar-react--typescript)
6. [Implementatie Stappenplan](#implementatie-stappenplan)
7. [Design Beslissingen & Aanbevelingen](#design-beslissingen--aanbevelingen)
8. [Belangrijke Aandachtspunten](#belangrijke-aandachtspunten)

---

## Executive Summary

### Wat is KOV-RAG?
KOV-RAG is een **multi-user Retrieval-Augmented Generation (RAG) systeem** specifiek gebouwd voor het doorzoeken van **BBL (Besluit Bouwwerken Leefomgeving)** documenten. Het stelt gebruikers in staat om natuurlijke taal vragen te stellen over BBL regelgeving en krijgt dan intelligente antwoorden met bronverwijzingen.

### Kernfunctionaliteit
- **BBL-specifieke documentverwerking**: Upload BWB XML bestanden die automatisch worden geparsed met behoud van juridische structuur
- **Intelligente zoekfunctie**: Semantic search met metadata filtering (functie types, bouw types, thema's)
- **Multi-user isolatie**: Elke gebruiker heeft eigen documentcollectie en zoekresultaten
- **Admin functionaliteit**: Uitnodigingssysteem, gebruikersbeheer
- **Chat interface**: Perplexity-style conversationele interface met inline citaties

### Waarom migreren naar React?
- **Betere UX**: Single Page Application zonder page reloads
- **Modernere tech stack**: React is industry standard voor complexe web apps
- **Type safety**: TypeScript voorkomt runtime errors
- **Performance**: Client-side rendering is sneller dan Streamlit's server-side rendering
- **Developer experience**: Betere tooling, grotere community, meer flexibiliteit
- **Mobile support**: React biedt betere responsive capabilities

### Wat blijft hetzelfde?
✅ **Backend blijft volledig intact** (FastAPI, RAG pipeline, database)
✅ **API endpoints blijven ongewijzigd**
✅ **Authenticatie systeem blijft hetzelfde** (JWT)
✅ **BBL processing logic blijft in Python**

### Wat verandert?
❌ **Frontend framework**: Streamlit → React + TypeScript
❌ **State management**: Server-side session → Client-side state (Zustand/React Query)
❌ **UI Components**: Streamlit widgets → Custom React components
❌ **Styling**: Streamlit CSS → Tailwind CSS + Headless UI

---

## Huidige Applicatie Overview

### Technologie Stack (Huidig)

**Backend:**
- **Framework**: FastAPI 0.120.2 (Python 3.11+)
- **Database**: SQLite + SQLAlchemy 2.0.36
- **Vector Database**: Qdrant (Docker container)
- **LLM**: OpenAI GPT-4-turbo
- **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
- **Authentication**: JWT (HS256, 24h expiry) + Bcrypt password hashing
- **Rate Limiting**: SlowAPI
- **Document Processing**: PyMuPDF (PDF), python-docx (DOCX), custom BBL XML parser

**Frontend:**
- **Framework**: Streamlit 1.51.0 (Python)
- **HTTP Client**: requests library
- **State Management**: Streamlit session_state + encrypted cookies
- **Styling**: Custom CSS injected via st.markdown

**Infrastructure:**
- **Deployment**: Uvicorn ASGI server (backend), Streamlit server (frontend)
- **Containerization**: Docker Compose voor Qdrant
- **Storage**: Local filesystem (SQLite DB, uploaded files via embeddings in Qdrant)

### Applicatie Flow (High-Level)

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Login   │  │  Query    │  │Documents │  │  Admin    │ │
│  │  Page    │  │  Page     │  │  Page    │  │  Panel    │ │
│  └──────────┘  └───────────┘  └──────────┘  └───────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (JWT Bearer Token)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Routes Layer                                     │   │
│  │  • /api/auth (login, register, me)                   │   │
│  │  • /api/documents (upload, list, delete)             │   │
│  │  • /api/query (RAG query)                            │   │
│  │  • /api/chat (sessions, messages)                    │   │
│  │  • /api/admin (invite, users, invitations)           │   │
│  └───────────────┬──────────────────────────────────────┘   │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐   │
│  │  Business Logic Layer                                │   │
│  │  • RAG Pipeline (rag/pipeline.py)                    │   │
│  │  • BBL Processing (bbl/xml_parser.py)                │   │
│  │  • Query Analyzer (rag/query_analyzer.py)            │   │
│  │  • Reranker (rag/reranker.py)                        │   │
│  └───────────────┬──────────────────────────────────────┘   │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐   │
│  │  Data Access Layer                                   │   │
│  │  • Repository Pattern (db/crud.py)                   │   │
│  │  • SQLAlchemy Models (db/models.py)                  │   │
│  └───────────────┬──────────────────────────────────────┘   │
└──────────────────┼────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌─────────┐         ┌──────────────┐
   │ SQLite  │         │   Qdrant     │
   │   DB    │         │ Vector Store │
   └─────────┘         └──────────────┘
```

---

## Functionaliteiten

### 1. Authenticatie & Gebruikersbeheer

#### 1.1 Registratie via Uitnodiging
**Flow:**
1. Admin stuurt uitnodiging naar email adres
2. Systeem genereert unieke token (7 dagen geldig)
3. Gebruiker ontvangt email met registratie link
4. Gebruiker klikt link, valideert token
5. Gebruiker vult gebruikersnaam + wachtwoord in
6. Account wordt aangemaakt en linked aan uitnodiging

**Validatie regels:**
- **Wachtwoord**: Min 8 karakters, 1 hoofdletter, 1 kleine letter, 1 cijfer, 1 speciaal karakter
- **Gebruikersnaam**: Alleen alphanumeriek + underscore
- **Email**: Valide email format
- **Token**: Moet bestaan, niet expired, status PENDING

**API Endpoints:**
- `GET /api/auth/validate-invitation/{token}` - Valideer token (public)
- `POST /api/auth/setup-account` - Voltooi registratie (public)

#### 1.2 Login
**Flow:**
1. Gebruiker vult username/email + wachtwoord in
2. Backend verifieert credentials (bcrypt)
3. Bij succes: genereer JWT token (24h geldig)
4. Frontend slaat token op in localStorage + session state
5. Token wordt gebruikt in Authorization header voor alle requests

**API Endpoint:**
- `POST /api/auth/login` - Login (rate limit: 5/min)

**JWT Payload:**
```json
{
  "sub": "username",
  "user_id": 123,
  "exp": 1234567890
}
```

#### 1.3 Current User Info
**API Endpoint:**
- `GET /api/auth/me` - Haal current user info op (rate limit: 30/min)

**Response:**
```json
{
  "id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "USER",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. Document Management

#### 2.1 Document Upload
**Ondersteunde formaten:**
- **PDF**: Text extractie via PyMuPDF
- **DOCX**: Text extractie via python-docx
- **TXT**: Direct inlezen
- **XML (BBL)**: Speciaal BWB XML parser met hierarchische extractie

**Upload Flow:**
```
1. User selecteert bestand
   ↓
2. Frontend valideert bestandstype + grootte
   ↓
3. POST /api/documents/upload (multipart/form-data)
   ↓
4. Backend sanitized filename (path traversal protection)
   ↓
5. Extract text (DocumentProcessor)
   ├─ PDF → PyMuPDF.open() → extract text per page
   ├─ DOCX → Document() → extract paragraphs
   ├─ TXT → open().read()
   └─ XML → BBLXMLParser.parse() → extract artikelen met metadata
   ↓
6. Chunk text
   ├─ Standard: 800 chars, 100 overlap
   └─ BBL: 1 artikel = 1 chunk (behoud juridische structuur)
   ↓
7. BBL Metadata Enrichment (alleen voor XML)
   ├─ Extract functie_types (Woonfunctie, Kantoorfunctie, etc.)
   ├─ Extract bouw_type (Nieuwbouw / Bestaande bouw)
   └─ Extract thema_tags (brandveiligheid, ventilatie, MPG, etc.)
   ↓
8. Generate embeddings (OpenAI text-embedding-3-large)
   ├─ Check embedding cache (file + memory)
   ├─ Batch embeddings (50 per API call)
   └─ Cache results
   ↓
9. Store in Qdrant
   ├─ Collection name: user_{user_id}_bbl_documents
   ├─ Vector: 3072-dim embedding
   ├─ Payload: text, metadata, filename, chunk_index, user_id
   └─ Batch upsert (100 points per batch)
   ↓
10. Return document_id + chunks_count
```

**BBL XML Parsing Details:**
- BWB XML heeft hierarchische structuur: `<wettekst>` → `<wetgeving>` → `<wet-besluit>` → `<artikel>`
- Elk artikel heeft:
  - **artikel_nr**: Artikel nummer (bijv. "3.44")
  - **kop**: Titel/onderwerp
  - **inhoud**: Volledige artikel tekst
  - **metadata**: functie_types, bouw_type, thema_tags
- Parser extraheert alle artikelen met behoud van structuur
- Functie types: Woonfunctie, Kantoorfunctie, Bijeenkomstfunctie, Celfunctie, Gezondheidszorgfunctie, Industriefunctie, Logiesfunctie, Onderwijsfunctie, Sportfunctie, Winkelfunctie, Overige gebruiksfunctie, Bouwwerk geen gebouw zijnde
- Bouw types: Nieuwbouw, Bestaande bouw, Tijdelijke bouw
- Thema's: brandveiligheid, constructieve veiligheid, ventilatie, MPG, geluidwering, energieprestatie, daglicht, bereikbaarheid, etc.

**API Endpoint:**
- `POST /api/documents/upload` - Upload document (rate limit: 10/min, max 10MB)

**Request:**
```
Content-Type: multipart/form-data
file: <binary data>
```

**Response:**
```json
{
  "document_id": "doc_123456",
  "filename": "BBL_artikel_3.xml",
  "chunks_count": 42,
  "message": "Document uploaded and processed successfully"
}
```

#### 2.2 Document Listing
**API Endpoint:**
- `GET /api/documents` - Lijst alle documenten van gebruiker (rate limit: 30/min)

**Response:**
```json
{
  "documents": [
    {
      "document_id": "doc_123",
      "filename": "BBL_artikel_3.xml",
      "chunks_count": 42,
      "uploaded_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total_chunks": 156
}
```

#### 2.3 Document Deletion
**Flow:**
1. User klikt delete button bij document
2. Confirmation dialog
3. DELETE /api/documents/{document_id}
4. Backend deletes alle chunks met dit document_id uit Qdrant
5. Document verdwijnt uit lijst

**API Endpoint:**
- `DELETE /api/documents/{document_id}` - Delete document (rate limit: 30/min)

#### 2.4 Document Count
**API Endpoint:**
- `GET /api/documents/count` - Totaal aantal chunks (rate limit: 60/min)

**Response:**
```json
{
  "total_chunks": 156
}
```

### 3. Query Interface (RAG Search)

#### 3.1 Simple Query Flow
**User Experience:**
1. User ziet query interface met:
   - Model info box (GPT-4-turbo, embedding model, aantal artikelen)
   - Voorbeeldvragen (2 kolommen, klikbaar)
   - Query text area (max 500 chars)
   - Submit button "Zoek in Bbl"
2. User typt vraag of klikt voorbeeld
3. Submit → Loading state
4. Results verschijnen:
   - AI-gegenereerde titel per bron
   - Relevance score badge (🟢 ≥0.65 hoge relevantie, 🟡 0.40-0.64 medium)
   - AI-gegenereerde samenvatting (GPT-4-turbo)
   - Expandable volledige tekst
   - Metadata (bestandsnaam, chunk index)
   - Table detection (als tabel gedetecteerd: aparte rendering)

**Backend Processing:**
```
1. POST /api/query
   ↓
2. Check query cache (user_id + query + top_k → cached result)
   ↓ (cache miss)
3. Query Analysis (rag/query_analyzer.py)
   ├─ Extract metadata van query via LLM:
   │  • functie_types: ["Woonfunctie", "Kantoorfunctie"]
   │  • bouw_type: "Nieuwbouw"
   │  • thema: "brandveiligheid"
   │  • hoofdstuk_nr: 3
   ├─ Generate enhanced query (expanded met synoniemen)
   └─ Return metadata + enhanced query + confidence score
   ↓
4. Generate query embedding (enhanced query via OpenAI)
   ↓
5. Vector Search in Qdrant WITH metadata filters
   ├─ Search in collection: user_{user_id}_bbl_documents
   ├─ Fetch 3x top_k candidates (bijv. 15 voor top_k=5)
   ├─ Apply metadata filters (functie_types, bouw_type, thema)
   └─ Return scored results
   ↓
6. Relevance Filtering
   ├─ Primary threshold: score ≥ 0.65
   ├─ Fallback: if < top_k results, include score ≥ 0.40 (max 3 extra)
   └─ Return filtered results
   ↓
7. Reranking (rag/reranker.py)
   ├─ Score based on metadata matching:
   │  • Functie type match: +0.3
   │  • Bouw type match: +0.2
   │  • Thema match: +0.2
   │  • Hoofdstuk match: +0.1
   ├─ If confidence < 0.6: LLM verification
   └─ Return reranked results
   ↓
8. Build context met citations
   ├─ Format: "Context 1: [1]\n{text}\n\nContext 2: [2]\n{text}"
   └─ Limit: top_k sources
   ↓
9. Generate answer via OpenAI GPT-4-turbo
   ├─ System prompt: "Je bent een behulpzame assistent..."
   ├─ Context: retrieved chunks met citations
   └─ Query: user vraag
   ↓
10. Generate summaries + titles (parallel via asyncio.gather)
    ├─ Batch summary generation (alle sources in 1 call)
    └─ Batch title generation (alle sources in 1 call)
    ↓
11. Cache result (user_id + query + top_k → result)
    ↓
12. Return response
```

**API Endpoint:**
- `POST /api/query` - RAG query (rate limit: 20/min)

**Request:**
```json
{
  "query": "Wat zijn de eisen voor brandveiligheid in een woonfunctie?",
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "Voor brandveiligheid in een woonfunctie gelden de volgende eisen...",
  "sources": [
    {
      "text": "Artikel 3.44 Brandveiligheid woonfunctie...",
      "metadata": {
        "filename": "BBL_artikel_3.xml",
        "chunk_index": 0,
        "artikel_nr": "3.44",
        "functie_types": ["Woonfunctie"],
        "bouw_type": "Nieuwbouw",
        "thema_tags": ["brandveiligheid"]
      },
      "relevance_score": 0.89,
      "summary": "Dit artikel beschrijft de brandveiligheidseisen...",
      "title": "Brandveiligheid Woonfunctie - Artikel 3.44"
    }
  ],
  "processing_time": 2.34
}
```

#### 3.2 Query Analysis Details
**Query Analyzer** (`rag/query_analyzer.py`) gebruikt LLM om metadata te extraheren:

**Prompt naar LLM:**
```
Analyseer de volgende vraag over het BBL en extract metadata:

Vraag: "Wat zijn de ventilatie-eisen voor nieuwbouw kantoren?"

Return JSON:
{
  "functie_types": ["Kantoorfunctie"],
  "bouw_type": "Nieuwbouw",
  "thema": "ventilatie",
  "hoofdstuk_nr": null,
  "enhanced_query": "ventilatie eisen nieuwbouw kantoren luchtverversing kantoorgebouwen",
  "confidence": 0.85
}
```

**Confidence scoring:**
- 0.8-1.0: Zeer zeker
- 0.6-0.8: Redelijk zeker
- 0.4-0.6: Onzeker (triggers LLM verification in reranker)
- <0.4: Zeer onzeker

#### 3.3 Reranking Logic
**BBL Reranker** (`rag/reranker.py`) scoort chunks op metadata match:

```python
def calculate_metadata_score(query_metadata, chunk_metadata):
    score = 0.0

    # Functie type match (+0.3)
    if query_metadata.functie_types:
        if any(ft in chunk_metadata.functie_types for ft in query_metadata.functie_types):
            score += 0.3

    # Bouw type match (+0.2)
    if query_metadata.bouw_type:
        if query_metadata.bouw_type == chunk_metadata.bouw_type:
            score += 0.2

    # Thema match (+0.2)
    if query_metadata.thema:
        if query_metadata.thema in chunk_metadata.thema_tags:
            score += 0.2

    # Hoofdstuk match (+0.1)
    if query_metadata.hoofdstuk_nr:
        if chunk_metadata.artikel_nr.startswith(str(query_metadata.hoofdstuk_nr)):
            score += 0.1

    return score

# Combine met original similarity score
final_score = similarity_score + metadata_score
```

**LLM Verification** (bij confidence < 0.6):
```
Prompt: "Is dit chunk relevant voor de vraag? Ja/Nee"
Chunk: {text}
Vraag: {query}

→ Als "Nee": score -= 0.2
```

### 4. Chat Interface (Perplexity-style)

#### 4.1 Chat Session Management
**Chat Flow:**
1. User opent chat interface
2. Systeem creëert nieuwe sessie (of laadt bestaande)
3. User typt bericht
4. Submit → RAG query MET conversation history
5. Antwoord verschijnt met inline citations [1], [2], [3]
6. User kan verder chatten (context blijft behouden)

**API Endpoints:**
- `POST /api/chat/sessions` - Creëer nieuwe sessie (rate limit: 30/min)
- `GET /api/chat/sessions` - Lijst alle sessies van user (rate limit: 30/min)
- `GET /api/chat/sessions/{id}` - Haal sessie met messages op (rate limit: 30/min)
- `DELETE /api/chat/sessions/{id}` - Delete sessie (rate limit: 30/min)
- `POST /api/chat/query` - Verstuur chat bericht (rate limit: 20/min)

#### 4.2 Chat Query Flow
**Verschillen met simple query:**
- **Conversation history**: Laatste 5 berichten worden meegestuurd naar LLM
- **Inline citations**: Antwoord bevat [1], [2], [3] referenties in de tekst
- **Session persistence**: Berichten worden opgeslagen in database

**Chat Query Request:**
```json
{
  "session_id": "sess_123",
  "message": "En wat geldt er voor bestaande bouw?"
}
```

**Backend Processing:**
```
1. POST /api/chat/query
   ↓
2. Load chat session + last 5 messages
   ↓
3. Save user message to DB
   ↓
4. Build conversation context:
   messages = [
     {"role": "user", "content": "Wat zijn de eisen voor brandveiligheid?"},
     {"role": "assistant", "content": "Voor brandveiligheid gelden..."},
     {"role": "user", "content": "En wat geldt er voor bestaande bouw?"}
   ]
   ↓
5. RAG Query (same as simple query)
   ├─ Query analysis
   ├─ Vector search
   ├─ Reranking
   └─ Context building
   ↓
6. Generate answer WITH conversation history
   ├─ System prompt: "Je bent een behulpzame assistent..."
   ├─ Context: conversation history + retrieved chunks
   └─ Include inline citations [1], [2], [3]
   ↓
7. Save assistant message to DB
   ├─ content: answer text
   └─ sources: JSON array met citation details
   ↓
8. Return response
```

**Chat Query Response:**
```json
{
  "session_id": "sess_123",
  "message": {
    "role": "assistant",
    "content": "Voor bestaande bouw gelden aangepaste eisen [1]. De ventilatie-eisen zijn...",
    "citations": [
      {
        "id": 1,
        "text": "Artikel 4.12 Bestaande bouw...",
        "metadata": {
          "filename": "BBL_artikel_4.xml",
          "artikel_nr": "4.12"
        },
        "relevance_score": 0.87
      }
    ]
  },
  "processing_time": 2.1
}
```

#### 4.3 Session Data Model
**Database Schema:**
```sql
-- Chat Sessions
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Chat Messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSON,  -- Array of citation objects (only for assistant)
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

### 5. Admin Functionaliteit

#### 5.1 User Invitation System
**Admin Flow:**
1. Admin opent admin panel
2. Tab "Uitnodigingen"
3. Vul email in
4. Klik "Verstuur Uitnodiging"
5. Systeem creëert invitation met:
   - Unieke token (UUID)
   - Status: PENDING
   - Expires_at: now + 7 dagen
   - Invited_by: current admin
6. Email wordt gestuurd (simulatie: return registration link)
7. Invitation verschijnt in lijst

**API Endpoint:**
- `POST /api/admin/invite` - Verstuur uitnodiging (admin only)

**Request:**
```json
{
  "email": "newuser@example.com"
}
```

**Response:**
```json
{
  "invitation_id": 123,
  "email": "newuser@example.com",
  "token": "abc123...",
  "registration_url": "http://localhost:8501/register?token=abc123...",
  "expires_at": "2024-01-08T00:00:00Z"
}
```

#### 5.2 Invitation Management
**API Endpoints:**
- `GET /api/admin/invitations` - Lijst alle uitnodigingen (admin only)
- `DELETE /api/admin/invitations/{id}` - Revoke uitnodiging (admin only)

**Invitation States:**
- **PENDING**: Nog niet geaccepteerd
- **ACCEPTED**: Gebruiker heeft account aangemaakt
- **EXPIRED**: Token verlopen (>7 dagen)

#### 5.3 User Management
**API Endpoints:**
- `GET /api/admin/users` - Lijst alle gebruikers (admin only)
- `PUT /api/admin/users/{id}` - Update gebruiker (admin only)
- `DELETE /api/admin/users/{id}` - Delete gebruiker (admin only)

**User Update Request:**
```json
{
  "is_active": false,  // Deactivate user
  "role": "ADMIN"      // Promote to admin
}
```

**User Deletion:**
- Deletes user from database
- Deletes user's Qdrant collection (alle documenten)
- Cascade deletes: chat sessions, messages, invitations

### 6. Security Features

#### 6.1 Rate Limiting
**Limiten per endpoint:**
- `/api/auth/register`: 5/min
- `/api/auth/login`: 5/min
- `/api/auth/me`: 30/min
- `/api/documents/upload`: 10/min
- `/api/documents/*`: 30/min
- `/api/query`: 20/min
- `/api/chat/query`: 20/min
- `/api/chat/sessions`: 30/min

**Implementatie:** SlowAPI (gebaseerd op IP adres)

#### 6.2 Input Sanitization
**Filename Sanitization:**
```python
def sanitize_filename(filename: str) -> str:
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    # Remove non-alphanumeric (keep dots, dashes, underscores)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename
```

**Query Validation:**
- Max length: 500 characters
- Strip leading/trailing whitespace
- Check for SQL injection patterns (basic)

#### 6.3 Security Headers
**Middleware** (`middleware/security.py`) voegt headers toe:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
Referrer-Policy: strict-origin-when-cross-origin
```

#### 6.4 Security Event Logging
**Logged Events:**
- Login success/failure
- Registration success/failure
- Password change
- Admin actions (user creation, deletion, etc.)
- Rate limit violations

**Log Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event_type": "login_success",
  "user_id": 123,
  "username": "john_doe",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

#### 6.5 CORS Configuration
**Configureerbaar via environment:**
```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Backend Architectuur (blijft behouden)

### Waarom backend NIET migreren?
✅ **FastAPI is modern & performant** (asyncio, auto OpenAPI docs)
✅ **Python is ideaal voor RAG/LLM workloads** (ecosystem: openai, qdrant-client, PyMuPDF, etc.)
✅ **Database schema is goed ontworpen** (SQLAlchemy ORM)
✅ **API is RESTful en goed gedocumenteerd** (werkt perfect met React)
✅ **Security is goed geïmplementeerd** (JWT, rate limiting, input sanitization)

### Backend Structuur (blijft ongewijzigd)

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Centralized configuration
├── dependencies.py            # FastAPI dependencies (get_current_user, etc.)
├── auth.py                    # JWT helper functions
│
├── api/routes/               # API endpoints (blijven allemaal hetzelfde)
│   ├── auth.py              # Authentication endpoints
│   ├── documents.py         # Document management
│   ├── query.py             # Simple RAG query
│   ├── chat.py              # Chat interface
│   ├── admin.py             # Admin panel
│   └── health.py            # Health check
│
├── models/                   # Pydantic models (request/response schemas)
│   ├── auth.py
│   ├── document.py
│   ├── query.py
│   ├── chat.py
│   └── admin.py
│
├── db/                       # Database layer (SQLAlchemy)
│   ├── models.py            # Database models (UserDB, ChatSessionDB, etc.)
│   ├── crud.py              # Repository classes (UserRepository, ChatRepository)
│   └── base.py              # DB session management
│
├── rag/                      # RAG pipeline (core intelligence)
│   ├── pipeline.py          # RAG orchestration
│   ├── document_processor.py  # Text extraction (PDF, DOCX, TXT, XML)
│   ├── text_chunker.py      # Text chunking
│   ├── vector_store.py      # Qdrant wrapper
│   ├── query_analyzer.py    # Query metadata extraction
│   ├── reranker.py          # BBL-specific reranking
│   └── llm/
│       ├── openai_provider.py  # OpenAI integration
│       ├── prompts.py       # LLM prompts
│       └── embedding_cache.py  # Embedding cache
│
├── bbl/                      # BBL-specific logic
│   ├── xml_parser.py        # BWB XML parser
│   ├── chunker.py           # BBL chunking (1 artikel = 1 chunk)
│   └── metadata_extractor.py  # Metadata enrichment
│
├── middleware/               # Middleware
│   ├── security.py          # Security headers
│   └── request_id.py        # Request ID tracking
│
└── utils/                    # Utilities
    ├── security_logger.py   # Security event logging
    └── table_detector.py    # Table detection in text
```

### Backend Configuration (Environment Variables)

**Required:**
```bash
OPENAI_API_KEY=sk-...          # OpenAI API key
JWT_SECRET_KEY=...             # Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Optional (met defaults):**
```bash
# LLM Configuration
USE_OPENAI=true
OPENAI_LLM_MODEL=gpt-4-turbo
OPENAI_EMBED_MODEL=text-embedding-3-large

# Database
DATABASE_URL=sqlite:///./rag_app.db

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:8501,http://localhost:3000

# RAG Settings
CHUNK_SIZE=800
CHUNK_OVERLAP=100
MAX_FILE_SIZE_MB=10
DEFAULT_TOP_K=5
MAX_TOP_K=100
MINIMUM_RELEVANCE_THRESHOLD=0.4
SIMILARITY_THRESHOLD=0.65
```

### Backend Dependencies (requirements-all.txt)

**Core:**
- fastapi==0.120.2
- uvicorn[standard]==0.32.1
- python-multipart==0.0.18
- pydantic==2.10.3
- python-dotenv==1.0.1

**Database:**
- sqlalchemy==2.0.36
- alembic==1.14.0

**Authentication:**
- bcrypt==4.0.1
- pyjwt==2.10.1

**LLM & AI:**
- openai==1.57.2
- qdrant-client==1.15.1

**Document Processing:**
- PyMuPDF==1.26.5
- python-docx==1.1.2

**Utilities:**
- slowapi (rate limiting)
- requests==2.32.3

---

## Frontend Migratie naar React + TypeScript

### Waarom React + TypeScript?

**React voordelen:**
- ✅ **Industry standard**: Grootste community, beste tooling
- ✅ **Component-based**: Herbruikbare UI componenten
- ✅ **Virtual DOM**: Efficiënte updates
- ✅ **Rich ecosystem**: Enorme bibliotheek aan packages
- ✅ **Single Page App**: Geen page reloads, betere UX
- ✅ **Better mobile support**: Responsive design capabilities

**TypeScript voordelen:**
- ✅ **Type safety**: Catch errors at compile time
- ✅ **Better IDE support**: Autocomplete, refactoring
- ✅ **Self-documenting code**: Types as documentation
- ✅ **Easier maintenance**: Refactoring is safer
- ✅ **Better collaboration**: Clear interfaces between components

**Alternatieve frameworks:**
- **Vue 3 + TypeScript**: Ook goed, minder populair maar eenvoudiger
- **SvelteKit**: Nieuwer, sneller, maar kleinere community
- **Next.js**: React framework met SSR, overkill voor deze app
- **Solid.js**: Sneller dan React, maar jonger ecosystem

**Aanbeveling: React + TypeScript** (beste balans tussen functionaliteit, community support, en developer experience)

### Nieuwe Frontend Architectuur

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── src/
│   ├── index.tsx                # Entry point
│   ├── App.tsx                  # Main app component
│   ├── vite-env.d.ts           # Vite type definitions
│   │
│   ├── components/              # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   │   ├── Footer.tsx             # Footer with version info
│   │   │   ├── Header.tsx             # Top bar (optional)
│   │   │   └── Layout.tsx             # Main layout wrapper
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx          # Login form
│   │   │   ├── RegisterForm.tsx       # Registration form
│   │   │   └── ProtectedRoute.tsx     # Route guard
│   │   ├── query/
│   │   │   ├── QueryInput.tsx         # Query text area + submit
│   │   │   ├── ExampleQuestions.tsx   # Clickable example questions
│   │   │   ├── ModelInfo.tsx          # Model info box
│   │   │   └── ResultsList.tsx        # List of query results
│   │   ├── source/
│   │   │   ├── SourceCard.tsx         # Single source card
│   │   │   ├── SourceTitle.tsx        # AI-generated title
│   │   │   ├── SourceSummary.tsx      # AI-generated summary
│   │   │   ├── SourceText.tsx         # Full text (expandable)
│   │   │   ├── RelevanceBadge.tsx     # Relevance score badge
│   │   │   └── SourceMetadata.tsx     # Filename, chunk index, etc.
│   │   ├── document/
│   │   │   ├── DocumentUpload.tsx     # File upload component
│   │   │   ├── DocumentList.tsx       # List of user documents
│   │   │   └── DocumentCard.tsx       # Single document card
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx         # Chat interface
│   │   │   ├── ChatMessage.tsx        # Single message (user/assistant)
│   │   │   ├── ChatInput.tsx          # Chat input field
│   │   │   ├── ChatSidebar.tsx        # Chat session list
│   │   │   └── CitationPopover.tsx    # Inline citation [1] hover
│   │   ├── admin/
│   │   │   ├── InviteUser.tsx         # Invitation form
│   │   │   ├── InvitationList.tsx     # List of invitations
│   │   │   ├── UserList.tsx           # List of users
│   │   │   └── UserCard.tsx           # Single user card
│   │   └── common/
│   │       ├── Button.tsx             # Reusable button
│   │       ├── Input.tsx              # Reusable input field
│   │       ├── TextArea.tsx           # Reusable text area
│   │       ├── Card.tsx               # Reusable card component
│   │       ├── Badge.tsx              # Reusable badge
│   │       ├── Modal.tsx              # Modal dialog
│   │       ├── Spinner.tsx            # Loading spinner
│   │       └── Alert.tsx              # Alert/notification
│   │
│   ├── pages/                   # Page components (route targets)
│   │   ├── LoginPage.tsx             # Login page
│   │   ├── RegisterPage.tsx          # Registration page (via invitation)
│   │   ├── QueryPage.tsx             # Simple query interface
│   │   ├── ChatPage.tsx              # Chat interface
│   │   ├── DocumentsPage.tsx         # Document management
│   │   ├── AdminPage.tsx             # Admin panel
│   │   └── NotFoundPage.tsx          # 404 page
│   │
│   ├── services/                # API clients
│   │   ├── api.ts                   # Axios instance + interceptors
│   │   ├── authService.ts           # Auth endpoints (login, register, me)
│   │   ├── documentService.ts       # Document endpoints (upload, list, delete)
│   │   ├── queryService.ts          # Query endpoints (query)
│   │   ├── chatService.ts           # Chat endpoints (sessions, messages, query)
│   │   └── adminService.ts          # Admin endpoints (invite, users, etc.)
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAuth.ts              # Auth state & operations
│   │   ├── useDocuments.ts         # Document state & operations
│   │   ├── useQuery.ts             # Query state & operations
│   │   ├── useChat.ts              # Chat state & operations
│   │   ├── useDebounce.ts          # Debounce utility
│   │   └── useLocalStorage.ts      # LocalStorage helper
│   │
│   ├── context/                 # React Context providers
│   │   ├── AuthContext.tsx         # Auth state (user, token, isAuthenticated)
│   │   └── ThemeContext.tsx        # Theme state (optional dark mode)
│   │
│   ├── types/                   # TypeScript type definitions
│   │   ├── api.ts                 # API request/response types
│   │   ├── auth.ts                # Auth types (User, LoginRequest, etc.)
│   │   ├── document.ts            # Document types
│   │   ├── query.ts               # Query types (QueryRequest, QueryResponse, Source)
│   │   ├── chat.ts                # Chat types (Session, Message, Citation)
│   │   └── admin.ts               # Admin types (Invitation, UserUpdate, etc.)
│   │
│   ├── utils/                   # Utility functions
│   │   ├── security.ts           # Input sanitization, XSS protection
│   │   ├── formatting.ts         # Date formatting, text truncation
│   │   ├── validation.ts         # Form validation helpers
│   │   ├── tableDetector.ts      # Table detection in text
│   │   └── constants.ts          # App constants (BBL theme colors, etc.)
│   │
│   └── styles/                  # Global styles
│       ├── index.css            # Global CSS + Tailwind imports
│       └── variables.css        # CSS variables (colors, spacing, etc.)
│
├── .env.example                 # Environment template
├── .env.local                   # Local environment (gitignored)
├── package.json
├── tsconfig.json                # TypeScript config
├── vite.config.ts               # Vite config
└── tailwind.config.js           # Tailwind CSS config
```

### Tech Stack voor React Frontend

**Build Tool: Vite**
```bash
npm create vite@latest kov-rag-frontend -- --template react-ts
```

**Waarom Vite?**
- ⚡ Sneller dan Create React App
- 🔥 Hot Module Replacement (HMR)
- 📦 Kleinere bundle size
- 🛠️ Betere developer experience
- ✅ Native TypeScript support

**Core Dependencies:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",      // Routing (SPA)
    "axios": "^1.6.0",                   // HTTP client
    "zustand": "^4.4.0",                 // State management (lightweight)
    "@tanstack/react-query": "^5.0.0",  // Server state management + caching
    "react-markdown": "^9.0.0",          // Markdown rendering (voor responses)
    "dompurify": "^3.0.0",               // XSS protection
    "tailwindcss": "^3.3.0",             // CSS framework
    "@headlessui/react": "^1.7.0",       // Accessible UI components
    "@heroicons/react": "^2.1.0",        // Icons
    "clsx": "^2.0.0",                    // Conditional className helper
    "date-fns": "^3.0.0"                 // Date formatting
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/dompurify": "^3.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0"
  }
}
```

**Alternatieve State Management:**
- **Zustand** (aanbevolen): Lightweight, eenvoudig, geen boilerplate
- **Redux Toolkit**: Meer features, meer boilerplate, overkill voor deze app
- **Jotai**: Atomic state management, modern maar minder bekend
- **MobX**: Reactive state, steile learning curve

**Aanbeveling: Zustand + React Query** (beste balans tussen eenvoud en functionaliteit)

### State Management Strategy

#### 1. Zustand voor Client State
**Client state**: Data die alleen in de browser bestaat (UI state, form state, etc.)

**Voorbeeld `stores/authStore.ts`:**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types/auth';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      setAuth: (token, user) => set({
        token,
        user,
        isAuthenticated: true
      }),

      clearAuth: () => set({
        token: null,
        user: null,
        isAuthenticated: false
      }),
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        token: state.token, // Alleen token persist
      }),
    }
  )
);
```

**Gebruik in component:**
```typescript
function Sidebar() {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) return null;

  return (
    <div>
      <p>Welkom, {user?.username}</p>
    </div>
  );
}
```

#### 2. React Query voor Server State
**Server state**: Data die van de backend komt (documents, queries, etc.)

**Voorbeeld `hooks/useDocuments.ts`:**
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentService } from '../services/documentService';

export function useDocuments() {
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documents, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: documentService.list,
    staleTime: 1000 * 60 * 5, // 5 minutes cache
  });

  // Upload document
  const uploadMutation = useMutation({
    mutationFn: documentService.upload,
    onSuccess: () => {
      // Invalidate cache to refetch
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Delete document
  const deleteMutation = useMutation({
    mutationFn: documentService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  return {
    documents: documents?.documents || [],
    totalChunks: documents?.total_chunks || 0,
    isLoading,
    error,
    uploadDocument: uploadMutation.mutate,
    deleteDocument: deleteMutation.mutate,
    isUploading: uploadMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
```

**Gebruik in component:**
```typescript
function DocumentsPage() {
  const {
    documents,
    totalChunks,
    isLoading,
    uploadDocument,
    deleteDocument
  } = useDocuments();

  if (isLoading) return <Spinner />;

  return (
    <div>
      <h1>Bbl Documenten ({totalChunks} artikelen)</h1>
      <DocumentUpload onUpload={uploadDocument} />
      <DocumentList
        documents={documents}
        onDelete={deleteDocument}
      />
    </div>
  );
}
```

### API Service Layer

**Base API client** (`services/api.ts`):
```typescript
import axios, { AxiosError, AxiosResponse } from 'axios';
import { useAuthStore } from '../stores/authStore';

// Create axios instance
export const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor (add JWT token)
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // Unauthorized → clear auth and redirect to login
    if (error.response?.status === 401) {
      useAuthStore.getState().clearAuth();
      window.location.href = '/login';
    }

    // Rate limit → show error
    if (error.response?.status === 429) {
      console.error('Rate limit exceeded');
    }

    return Promise.reject(error);
  }
);

export default api;
```

**Auth Service** (`services/authService.ts`):
```typescript
import api from './api';
import { LoginRequest, LoginResponse, User, RegisterRequest } from '../types/auth';

export const authService = {
  // Login
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/api/auth/login', data);
    return response.data;
  },

  // Get current user
  async me(): Promise<User> {
    const response = await api.get<User>('/api/auth/me');
    return response.data;
  },

  // Validate invitation token
  async validateInvitation(token: string): Promise<{ email: string }> {
    const response = await api.get(`/api/auth/validate-invitation/${token}`);
    return response.data;
  },

  // Complete registration
  async setupAccount(data: RegisterRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/api/auth/setup-account', data);
    return response.data;
  },
};
```

**Document Service** (`services/documentService.ts`):
```typescript
import api from './api';
import { DocumentListResponse, DocumentUploadResponse } from '../types/document';

export const documentService = {
  // List documents
  async list(): Promise<DocumentListResponse> {
    const response = await api.get<DocumentListResponse>('/api/documents');
    return response.data;
  },

  // Upload document
  async upload(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<DocumentUploadResponse>(
      '/api/documents/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000, // 2 minutes for large files
      }
    );
    return response.data;
  },

  // Delete document
  async delete(documentId: string): Promise<void> {
    await api.delete(`/api/documents/${documentId}`);
  },

  // Get document count
  async count(): Promise<{ total_chunks: number }> {
    const response = await api.get<{ total_chunks: number }>('/api/documents/count');
    return response.data;
  },
};
```

**Query Service** (`services/queryService.ts`):
```typescript
import api from './api';
import { QueryRequest, QueryResponse } from '../types/query';

export const queryService = {
  // Simple RAG query
  async query(data: QueryRequest): Promise<QueryResponse> {
    const response = await api.post<QueryResponse>('/api/query', data);
    return response.data;
  },
};
```

**Chat Service** (`services/chatService.ts`):
```typescript
import api from './api';
import {
  ChatSession,
  ChatMessage,
  ChatQueryRequest,
  ChatQueryResponse
} from '../types/chat';

export const chatService = {
  // Create session
  async createSession(title?: string): Promise<ChatSession> {
    const response = await api.post<ChatSession>('/api/chat/sessions', { title });
    return response.data;
  },

  // List sessions
  async listSessions(): Promise<ChatSession[]> {
    const response = await api.get<ChatSession[]>('/api/chat/sessions');
    return response.data;
  },

  // Get session with messages
  async getSession(sessionId: string): Promise<ChatSession & { messages: ChatMessage[] }> {
    const response = await api.get(`/api/chat/sessions/${sessionId}`);
    return response.data;
  },

  // Delete session
  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/api/chat/sessions/${sessionId}`);
  },

  // Send chat message
  async query(data: ChatQueryRequest): Promise<ChatQueryResponse> {
    const response = await api.post<ChatQueryResponse>('/api/chat/query', data);
    return response.data;
  },
};
```

**Admin Service** (`services/adminService.ts`):
```typescript
import api from './api';
import {
  InviteUserRequest,
  InviteUserResponse,
  Invitation,
  User,
  UserUpdateRequest
} from '../types/admin';

export const adminService = {
  // Invite user
  async invite(data: InviteUserRequest): Promise<InviteUserResponse> {
    const response = await api.post<InviteUserResponse>('/api/admin/invite', data);
    return response.data;
  },

  // List invitations
  async listInvitations(): Promise<Invitation[]> {
    const response = await api.get<Invitation[]>('/api/admin/invitations');
    return response.data;
  },

  // Revoke invitation
  async revokeInvitation(invitationId: number): Promise<void> {
    await api.delete(`/api/admin/invitations/${invitationId}`);
  },

  // List users
  async listUsers(): Promise<User[]> {
    const response = await api.get<User[]>('/api/admin/users');
    return response.data;
  },

  // Update user
  async updateUser(userId: number, data: UserUpdateRequest): Promise<User> {
    const response = await api.put<User>(`/api/admin/users/${userId}`, data);
    return response.data;
  },

  // Delete user
  async deleteUser(userId: number): Promise<void> {
    await api.delete(`/api/admin/users/${userId}`);
  },
};
```

### TypeScript Type Definitions

**Auth Types** (`types/auth.ts`):
```typescript
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'ADMIN' | 'USER';
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
}

export interface RegisterRequest {
  token: string;
  username: string;
  password: string;
}

export interface ValidateInvitationResponse {
  email: string;
}
```

**Document Types** (`types/document.ts`):
```typescript
export interface Document {
  document_id: string;
  filename: string;
  chunks_count: number;
  uploaded_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total_chunks: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  chunks_count: number;
  message: string;
}

export interface DocumentCountResponse {
  total_chunks: number;
}
```

**Query Types** (`types/query.ts`):
```typescript
export interface QueryRequest {
  query: string;
  top_k?: number; // Default: 5
}

export interface Source {
  text: string;
  metadata: {
    filename: string;
    chunk_index: number;
    artikel_nr?: string;
    functie_types?: string[];
    bouw_type?: string;
    thema_tags?: string[];
  };
  relevance_score: number;
  summary?: string;  // AI-generated summary
  title?: string;    // AI-generated title
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  processing_time: number;
}
```

**Chat Types** (`types/chat.ts`):
```typescript
export interface ChatSession {
  id: string;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id: number;
  text: string;
  metadata: {
    filename: string;
    chunk_index: number;
    artikel_nr?: string;
  };
  relevance_score: number;
}

export interface ChatMessage {
  id: number;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Citation[];  // Only for assistant messages
  created_at: string;
}

export interface ChatQueryRequest {
  session_id?: string;  // Optional: create new if not provided
  message: string;
}

export interface ChatQueryResponse {
  session_id: string;
  message: ChatMessage;
  processing_time: number;
}
```

**Admin Types** (`types/admin.ts`):
```typescript
export interface Invitation {
  id: number;
  email: string;
  token: string;
  invited_by: number;
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED';
  created_at: string;
  expires_at: string;
  accepted_at?: string;
  user_id?: number;
}

export interface InviteUserRequest {
  email: string;
}

export interface InviteUserResponse {
  invitation_id: number;
  email: string;
  token: string;
  registration_url: string;
  expires_at: string;
}

export interface UserUpdateRequest {
  is_active?: boolean;
  role?: 'ADMIN' | 'USER';
}
```

### Routing Setup

**App Router** (`App.tsx`):
```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './stores/authStore';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import QueryPage from './pages/QueryPage';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import AdminPage from './pages/AdminPage';
import NotFoundPage from './pages/NotFoundPage';

// Layout
import Layout from './components/layout/Layout';

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Admin Route Component
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'ADMIN') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

// React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/query" replace />} />
            <Route path="query" element={<QueryPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route
              path="admin"
              element={
                <AdminRoute>
                  <AdminPage />
                </AdminRoute>
              }
            />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

### UI Components met Tailwind CSS

**Tailwind Configuration** (`tailwind.config.js`):
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // BBL Brand Colors
        primary: {
          50: '#fff5f2',
          100: '#ffe8e0',
          200: '#ffd4c7',
          300: '#ffb69e',
          400: '#ff8a64',
          500: '#ff6b35',  // Main brand color
          600: '#f04e1a',
          700: '#c93d10',
          800: '#a63311',
          900: '#8a2e14',
        },
        // Neutral colors
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

**Example Component: SourceCard** (`components/source/SourceCard.tsx`):
```typescript
import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { Source } from '../../types/query';
import RelevanceBadge from './RelevanceBadge';
import SourceMetadata from './SourceMetadata';
import clsx from 'clsx';

interface SourceCardProps {
  source: Source;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            [{index + 1}] {source.title || 'Zonder titel'}
          </h3>
          <SourceMetadata metadata={source.metadata} />
        </div>
        <RelevanceBadge score={source.relevance_score} />
      </div>

      {/* Summary */}
      {source.summary && (
        <div className="mb-3 p-3 bg-blue-50 rounded-md">
          <p className="text-sm text-gray-700">{source.summary}</p>
        </div>
      )}

      {/* Expandable full text */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
      >
        {isExpanded ? (
          <>
            <ChevronUpIcon className="w-4 h-4 mr-1" />
            Verberg volledige tekst
          </>
        ) : (
          <>
            <ChevronDownIcon className="w-4 h-4 mr-1" />
            Toon volledige tekst
          </>
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md prose prose-sm max-w-none">
          <pre className="whitespace-pre-wrap font-sans text-sm">
            {source.text}
          </pre>
        </div>
      )}
    </div>
  );
}
```

**Example Component: RelevanceBadge** (`components/source/RelevanceBadge.tsx`):
```typescript
import clsx from 'clsx';

interface RelevanceBadgeProps {
  score: number;
}

export default function RelevanceBadge({ score }: RelevanceBadgeProps) {
  const isHighRelevance = score >= 0.65;
  const percentage = Math.round(score * 100);

  return (
    <div
      className={clsx(
        'px-3 py-1 rounded-full text-sm font-medium',
        isHighRelevance
          ? 'bg-green-100 text-green-800'
          : 'bg-yellow-100 text-yellow-800'
      )}
    >
      {isHighRelevance ? '🟢' : '🟡'} {percentage}% relevant
    </div>
  );
}
```

---

## Implementatie Stappenplan

### Fase 1: Project Setup (1-2 uur)

#### Stap 1: Initialiseer React Project
```bash
# Maak nieuwe Vite + React + TypeScript project
npm create vite@latest kov-rag-frontend -- --template react-ts

cd kov-rag-frontend

# Installeer dependencies
npm install

# Installeer extra packages
npm install react-router-dom axios zustand @tanstack/react-query
npm install react-markdown dompurify
npm install @heroicons/react @headlessui/react clsx date-fns

# Installeer Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Installeer types
npm install -D @types/dompurify
```

#### Stap 2: Configureer Tailwind CSS
**Bewerk `tailwind.config.js`:**
```javascript
// Zie Tailwind Configuration hierboven
```

**Bewerk `src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom CSS variables */
:root {
  --color-primary: #ff6b35;
  --color-gray-900: #111827;
}

/* Global styles */
body {
  font-family: 'Inter', system-ui, sans-serif;
}
```

#### Stap 3: Maak .env.example
```bash
VITE_BACKEND_URL=http://localhost:8000
```

#### Stap 4: Maak basis directory structuur
```bash
mkdir -p src/{components,pages,services,hooks,stores,types,utils,styles}
mkdir -p src/components/{layout,auth,query,source,document,chat,admin,common}
```

### Fase 2: Type Definitions (30 min)

**Maak alle TypeScript type files:**
- `src/types/auth.ts`
- `src/types/document.ts`
- `src/types/query.ts`
- `src/types/chat.ts`
- `src/types/admin.ts`

**Inhoud:** Zie [TypeScript Type Definitions](#typescript-type-definitions) sectie hierboven.

### Fase 3: API Services (1-2 uur)

**Maak API service layer:**
1. `src/services/api.ts` - Base axios instance + interceptors
2. `src/services/authService.ts` - Auth endpoints
3. `src/services/documentService.ts` - Document endpoints
4. `src/services/queryService.ts` - Query endpoint
5. `src/services/chatService.ts` - Chat endpoints
6. `src/services/adminService.ts` - Admin endpoints

**Inhoud:** Zie [API Service Layer](#api-service-layer) sectie hierboven.

### Fase 4: State Management (1 uur)

**Maak Zustand stores:**
1. `src/stores/authStore.ts` - Auth state (token, user, isAuthenticated)

**Maak React Query hooks:**
1. `src/hooks/useAuth.ts` - Auth operations (login, logout, me)
2. `src/hooks/useDocuments.ts` - Document operations
3. `src/hooks/useQuery.ts` - Query operations
4. `src/hooks/useChat.ts` - Chat operations

**Inhoud:** Zie [State Management Strategy](#state-management-strategy) sectie hierboven.

### Fase 5: Common Components (2-3 uur)

**Maak reusable UI components:**
1. `src/components/common/Button.tsx` - Reusable button
2. `src/components/common/Input.tsx` - Reusable input field
3. `src/components/common/TextArea.tsx` - Reusable text area
4. `src/components/common/Card.tsx` - Reusable card
5. `src/components/common/Badge.tsx` - Reusable badge
6. `src/components/common/Modal.tsx` - Modal dialog
7. `src/components/common/Spinner.tsx` - Loading spinner
8. `src/components/common/Alert.tsx` - Alert/notification

**Example Button.tsx:**
```typescript
import { ButtonHTMLAttributes } from 'react';
import clsx from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export default function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center font-medium rounded-md',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'transition-colors',
        {
          // Variants
          'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500':
            variant === 'primary',
          'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500':
            variant === 'secondary',
          'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500':
            variant === 'danger',
          // Sizes
          'px-3 py-1.5 text-sm': size === 'sm',
          'px-4 py-2 text-base': size === 'md',
          'px-6 py-3 text-lg': size === 'lg',
        },
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
```

### Fase 6: Layout Components (1-2 uur)

**Maak layout components:**
1. `src/components/layout/Sidebar.tsx` - Navigation sidebar
2. `src/components/layout/Footer.tsx` - Footer with version info
3. `src/components/layout/Layout.tsx` - Main layout wrapper (Outlet voor nested routes)

**Example Layout.tsx:**
```typescript
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Footer from './Footer';

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
        <Footer />
      </div>
    </div>
  );
}
```

### Fase 7: Auth Pages (2-3 uur)

**Maak auth components en pages:**
1. `src/components/auth/LoginForm.tsx` - Login form component
2. `src/components/auth/RegisterForm.tsx` - Registration form component
3. `src/components/auth/ProtectedRoute.tsx` - Route guard component
4. `src/pages/LoginPage.tsx` - Login page
5. `src/pages/RegisterPage.tsx` - Registration page (via invitation)

**Example LoginPage.tsx:**
```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authService } from '../services/authService';
import { useAuthStore } from '../stores/authStore';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Alert from '../components/common/Alert';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: async (data) => {
      // Store token
      const token = data.access_token;

      // Fetch user info
      const user = await authService.me();

      // Set auth state
      setAuth(token, user);

      // Redirect to query page
      navigate('/query');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-6">
          Bbl RAG - Kijk op Veiligheid
        </h1>

        {loginMutation.isError && (
          <Alert variant="error" className="mb-4">
            Ongeldige inloggegevens. Probeer het opnieuw.
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Gebruikersnaam"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <Input
            label="Wachtwoord"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            isLoading={loginMutation.isPending}
          >
            Inloggen
          </Button>
        </form>
      </div>
    </div>
  );
}
```

### Fase 8: Query Page (3-4 uur)

**Maak query components en page:**
1. `src/components/query/QueryInput.tsx` - Query text area + submit button
2. `src/components/query/ExampleQuestions.tsx` - Clickable example questions
3. `src/components/query/ModelInfo.tsx` - Model info box
4. `src/components/query/ResultsList.tsx` - List of query results
5. `src/components/source/SourceCard.tsx` - Single source card
6. `src/components/source/SourceTitle.tsx` - AI-generated title
7. `src/components/source/SourceSummary.tsx` - AI-generated summary
8. `src/components/source/SourceText.tsx` - Full text (expandable)
9. `src/components/source/RelevanceBadge.tsx` - Relevance score badge
10. `src/components/source/SourceMetadata.tsx` - Filename, chunk index, etc.
11. `src/pages/QueryPage.tsx` - Query page

**Example QueryPage.tsx:**
```typescript
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { queryService } from '../services/queryService';
import { useDocuments } from '../hooks/useDocuments';
import QueryInput from '../components/query/QueryInput';
import ExampleQuestions from '../components/query/ExampleQuestions';
import ModelInfo from '../components/query/ModelInfo';
import ResultsList from '../components/query/ResultsList';
import Alert from '../components/common/Alert';

export default function QueryPage() {
  const [query, setQuery] = useState('');
  const { totalChunks } = useDocuments();

  const queryMutation = useMutation({
    mutationFn: queryService.query,
  });

  const handleSubmit = () => {
    if (!query.trim()) return;
    queryMutation.mutate({ query, top_k: 5 });
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Bbl Vragen Stellen</h1>

      {totalChunks === 0 && (
        <Alert variant="warning" className="mb-6">
          Je hebt nog geen documenten geüpload. Upload eerst Bbl documenten.
        </Alert>
      )}

      <ModelInfo totalChunks={totalChunks} className="mb-6" />

      <ExampleQuestions
        onExampleClick={handleExampleClick}
        className="mb-6"
      />

      <QueryInput
        value={query}
        onChange={setQuery}
        onSubmit={handleSubmit}
        isLoading={queryMutation.isPending}
        className="mb-8"
      />

      {queryMutation.isError && (
        <Alert variant="error" className="mb-6">
          Er ging iets mis bij het verwerken van je vraag. Probeer het opnieuw.
        </Alert>
      )}

      {queryMutation.data && (
        <ResultsList
          answer={queryMutation.data.answer}
          sources={queryMutation.data.sources}
          processingTime={queryMutation.data.processing_time}
        />
      )}
    </div>
  );
}
```

### Fase 9: Documents Page (2-3 uur)

**Maak document components en page:**
1. `src/components/document/DocumentUpload.tsx` - File upload component
2. `src/components/document/DocumentList.tsx` - List of user documents
3. `src/components/document/DocumentCard.tsx` - Single document card
4. `src/pages/DocumentsPage.tsx` - Document management page

**Example DocumentUpload.tsx:**
```typescript
import { useState } from 'react';
import { DocumentIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import Button from '../common/Button';
import Alert from '../common/Alert';

interface DocumentUploadProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export default function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/xml',
      'application/xml',
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Ongeldig bestandstype. Upload een PDF, DOCX, TXT of XML bestand.');
      setFile(null);
      return;
    }

    // Validate file size (10MB max)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('Bestand is te groot. Maximum is 10MB.');
      setFile(null);
      return;
    }

    setError(null);
    setFile(selectedFile);
  };

  const handleUpload = () => {
    if (!file) return;
    onUpload(file);
    setFile(null);
    // Reset input
    const input = document.getElementById('file-upload') as HTMLInputElement;
    if (input) input.value = '';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold mb-4">Upload Bbl Document</h2>

      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      <div className="flex items-center space-x-4">
        <label
          htmlFor="file-upload"
          className="flex-1 flex items-center justify-center px-4 py-8 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-primary-500 transition-colors"
        >
          <div className="text-center">
            <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              {file ? file.name : 'Klik om een bestand te selecteren'}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              PDF, DOCX, TXT, XML (max 10MB)
            </p>
          </div>
          <input
            id="file-upload"
            type="file"
            className="sr-only"
            accept=".pdf,.docx,.txt,.xml"
            onChange={handleFileChange}
          />
        </label>

        {file && (
          <Button
            onClick={handleUpload}
            isLoading={isUploading}
            disabled={!file || isUploading}
          >
            Upload
          </Button>
        )}
      </div>
    </div>
  );
}
```

### Fase 10: Chat Page (4-5 uur)

**Maak chat components en page:**
1. `src/components/chat/ChatWindow.tsx` - Chat interface
2. `src/components/chat/ChatMessage.tsx` - Single message (user/assistant)
3. `src/components/chat/ChatInput.tsx` - Chat input field
4. `src/components/chat/ChatSidebar.tsx` - Chat session list
5. `src/components/chat/CitationPopover.tsx` - Inline citation [1] hover
6. `src/pages/ChatPage.tsx` - Chat page

**Note:** Chat interface is complexer:
- Real-time message updates
- Session management (create, switch, delete)
- Inline citation rendering [1], [2], [3]
- Citation popover on hover/click
- Auto-scroll to bottom on new message

**Example ChatMessage.tsx:**
```typescript
import { ChatMessage as ChatMessageType } from '../../types/chat';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

interface ChatMessageProps {
  message: ChatMessageType;
  onCitationClick?: (citationId: number) => void;
}

export default function ChatMessage({ message, onCitationClick }: ChatMessageProps) {
  const isUser = message.role === 'user';

  // Replace [1], [2], etc. with clickable citations
  const renderContent = () => {
    if (isUser || !message.sources) {
      return <ReactMarkdown>{message.content}</ReactMarkdown>;
    }

    // Parse citations [1], [2], [3]
    const parts = message.content.split(/(\[\d+\])/g);

    return (
      <div>
        {parts.map((part, index) => {
          const match = part.match(/\[(\d+)\]/);
          if (match) {
            const citationId = parseInt(match[1]);
            return (
              <button
                key={index}
                onClick={() => onCitationClick?.(citationId)}
                className="text-primary-600 hover:underline font-medium"
              >
                {part}
              </button>
            );
          }
          return <ReactMarkdown key={index}>{part}</ReactMarkdown>;
        })}
      </div>
    );
  };

  return (
    <div
      className={clsx(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-3xl rounded-lg p-4',
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-100 text-gray-900'
        )}
      >
        {renderContent()}
        <p className="text-xs mt-2 opacity-70">
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
```

### Fase 11: Admin Page (3-4 uur)

**Maak admin components en page:**
1. `src/components/admin/InviteUser.tsx` - Invitation form
2. `src/components/admin/InvitationList.tsx` - List of invitations
3. `src/components/admin/UserList.tsx` - List of users
4. `src/components/admin/UserCard.tsx` - Single user card
5. `src/pages/AdminPage.tsx` - Admin panel (tabs: Users, Invitations)

**Example AdminPage.tsx:**
```typescript
import { useState } from 'react';
import { Tab } from '@headlessui/react';
import clsx from 'clsx';
import InviteUser from '../components/admin/InviteUser';
import InvitationList from '../components/admin/InvitationList';
import UserList from '../components/admin/UserList';

export default function AdminPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Admin Panel</h1>

      <Tab.Group>
        <Tab.List className="flex space-x-1 rounded-xl bg-primary-100 p-1 mb-6">
          <Tab
            className={({ selected }) =>
              clsx(
                'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-primary-400 focus:outline-none focus:ring-2',
                selected
                  ? 'bg-white text-primary-700 shadow'
                  : 'text-primary-600 hover:bg-white/[0.12] hover:text-primary-800'
              )
            }
          >
            Gebruikers
          </Tab>
          <Tab
            className={({ selected }) =>
              clsx(
                'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-primary-400 focus:outline-none focus:ring-2',
                selected
                  ? 'bg-white text-primary-700 shadow'
                  : 'text-primary-600 hover:bg-white/[0.12] hover:text-primary-800'
              )
            }
          >
            Uitnodigingen
          </Tab>
        </Tab.List>

        <Tab.Panels>
          <Tab.Panel>
            <UserList />
          </Tab.Panel>

          <Tab.Panel>
            <div className="space-y-6">
              <InviteUser />
              <InvitationList />
            </div>
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
```

### Fase 12: Routing & App Setup (1-2 uur)

**Maak routing setup:**
1. `src/App.tsx` - Main app component met routing
2. Protected routes (ProtectedRoute component)
3. Admin routes (AdminRoute component)
4. 404 page

**Inhoud:** Zie [Routing Setup](#routing-setup) sectie hierboven.

### Fase 13: Testing & Refinement (3-4 uur)

**Test alle functionaliteit:**
1. ✅ Login/logout
2. ✅ Registration via invitation
3. ✅ Document upload (PDF, DOCX, TXT, XML)
4. ✅ Document list en delete
5. ✅ Query interface
6. ✅ Query results met sources
7. ✅ Chat interface
8. ✅ Chat sessions
9. ✅ Admin: invite user
10. ✅ Admin: user management

**Bug fixes:**
- Error handling (network errors, validation errors)
- Loading states
- Empty states (geen documenten, geen query results, etc.)
- Mobile responsiveness
- Accessibility (keyboard navigation, screen readers)

### Fase 14: Deployment Setup (1-2 uur)

**Build voor productie:**
```bash
npm run build
```

**Test production build:**
```bash
npm run preview
```

**Deploy opties:**
- **Vercel**: `vercel --prod` (eenvoudigst, gratis tier)
- **Netlify**: `netlify deploy --prod`
- **Docker**: Maak Dockerfile voor Nginx + static files
- **AWS S3 + CloudFront**: Static hosting

**Backend CORS update:**
Voeg frontend URL toe aan `CORS_ORIGINS`:
```bash
CORS_ORIGINS=http://localhost:8501,http://localhost:3000,https://your-frontend.vercel.app
```

---

## Design Beslissingen & Aanbevelingen

### 1. State Management: Zustand + React Query

**Rationale:**
- **Zustand**: Lightweight, geen boilerplate, eenvoudig te gebruiken
- **React Query**: Beste library voor server state (caching, refetching, etc.)
- **Alternatief**: Redux Toolkit (overkill voor deze app)

**Aanbeveling:** ✅ Zustand + React Query

### 2. Styling: Tailwind CSS + Headless UI

**Rationale:**
- **Tailwind CSS**: Utility-first, geen CSS files, snelle development
- **Headless UI**: Accessible components zonder styling (perfect met Tailwind)
- **Alternatief**: Material-UI (zwaarder, minder flexibel)

**Aanbeveling:** ✅ Tailwind CSS + Headless UI

### 3. Routing: React Router v6

**Rationale:**
- **React Router**: Industry standard, beste documentatie
- **Nested routes**: Perfect voor Layout + protected routes
- **Alternatief**: TanStack Router (nieuwer, minder ecosystem)

**Aanbeveling:** ✅ React Router v6

### 4. Build Tool: Vite

**Rationale:**
- **Vite**: Sneller dan CRA, moderne build tool
- **HMR**: Instant updates tijdens development
- **Alternatief**: Create React App (deprecated)

**Aanbeveling:** ✅ Vite

### 5. HTTP Client: Axios

**Rationale:**
- **Axios**: Betere API dan fetch, interceptors, automatic JSON parsing
- **Alternatief**: fetch (native, maar minder features)

**Aanbeveling:** ✅ Axios

### 6. Markdown Rendering: react-markdown

**Rationale:**
- **react-markdown**: Secure by default, customizable, goed onderhouden
- **Alternatief**: marked (niet React-specifiek)

**Aanbeveling:** ✅ react-markdown + DOMPurify (XSS protection)

### 7. Date Formatting: date-fns

**Rationale:**
- **date-fns**: Lightweight, tree-shakeable, goede i18n support
- **Alternatief**: moment.js (deprecated), day.js (kleiner maar minder features)

**Aanbeveling:** ✅ date-fns

### 8. Icons: Heroicons

**Rationale:**
- **Heroicons**: Mooie icons, goed geïntegreerd met Tailwind/Headless UI
- **Alternatief**: Font Awesome (zwaarder), Lucide (ook goed)

**Aanbeveling:** ✅ Heroicons

---

## Belangrijke Aandachtspunten

### 1. Security

#### XSS Protection
**Probleem:** User-generated content (query responses, chat messages) kan malicious HTML bevatten.

**Oplossing:**
```typescript
import DOMPurify from 'dompurify';

// Sanitize HTML before rendering
const cleanHTML = DOMPurify.sanitize(dirtyHTML);
```

**React-markdown is safe by default**, maar bij custom renderers: altijd sanitizen!

#### CORS Configuration
**Backend moet frontend URL whitelisten:**
```bash
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
```

#### JWT Token Storage
**Opties:**
1. **localStorage** (eenvoudig, maar XSS-vulnerable)
2. **sessionStorage** (verdwijnt bij tab close)
3. **httpOnly cookie** (veiligst, maar requires backend change)

**Aanbeveling voor deze migratie:** localStorage (backend blijft ongewijzigd)

**Later verbeteren:** Backend issue httpOnly cookies + CSRF tokens.

### 2. Performance

#### React Query Caching
**Standaard config:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
      retry: 1,
    },
  },
});
```

**Per-query config:**
```typescript
useQuery({
  queryKey: ['documents'],
  queryFn: documentService.list,
  staleTime: 1000 * 60, // 1 minute (documents change vaak)
});
```

#### Code Splitting
**Lazy load pages:**
```typescript
import { lazy, Suspense } from 'react';

const AdminPage = lazy(() => import('./pages/AdminPage'));

// In routing:
<Route
  path="admin"
  element={
    <Suspense fallback={<Spinner />}>
      <AdminPage />
    </Suspense>
  }
/>
```

#### Bundle Size Optimization
**Check bundle size:**
```bash
npm run build
```

**Analyze bundle:**
```bash
npm install -D rollup-plugin-visualizer
# Voeg toe aan vite.config.ts
```

### 3. Error Handling

#### API Error Types
```typescript
interface APIError {
  status: number;
  message: string;
  detail?: string;
}

// In services:
try {
  const response = await api.post('/api/query', data);
  return response.data;
} catch (error) {
  if (axios.isAxiosError(error)) {
    const apiError: APIError = {
      status: error.response?.status || 500,
      message: error.response?.data?.detail || 'Something went wrong',
    };
    throw apiError;
  }
  throw error;
}
```

#### Error Boundaries
```typescript
import { Component, ReactNode } from 'react';

class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Er ging iets mis. Herlaad de pagina.</h1>;
    }

    return this.props.children;
  }
}

// Wrap App:
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

### 4. Accessibility

#### Keyboard Navigation
- **Tab order**: Logische volgorde (top → bottom, left → right)
- **Focus indicators**: Visible focus states (Tailwind `focus:ring`)
- **Keyboard shortcuts**: Escape om modals te sluiten, Enter om forms te submitten

#### Screen Readers
- **Semantic HTML**: `<button>` i.p.v. `<div onClick>`
- **ARIA labels**: `aria-label`, `aria-labelledby`, `aria-describedby`
- **Alt text**: Alle images hebben `alt` attribute

**Headless UI heeft accessibility built-in!**

### 5. Mobile Responsiveness

#### Tailwind Breakpoints
```typescript
// Mobile first approach
<div className="
  flex flex-col          // Mobile: stacked
  md:flex-row           // Desktop: side-by-side
  space-y-4             // Mobile: vertical spacing
  md:space-y-0 md:space-x-4  // Desktop: horizontal spacing
">
```

#### Touch Targets
**Minimum 44x44px voor touch targets** (buttons, links):
```typescript
<button className="min-h-[44px] min-w-[44px]">
```

#### Viewport Meta Tag
**In `index.html`:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### 6. Testing Strategy

#### Unit Tests
**Test utility functions:**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

**Example test:**
```typescript
import { describe, it, expect } from 'vitest';
import { sanitizeFilename } from './security';

describe('sanitizeFilename', () => {
  it('removes path traversal attempts', () => {
    expect(sanitizeFilename('../../../etc/passwd')).toBe('passwd');
  });
});
```

#### Integration Tests
**Test user flows:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import LoginPage from './LoginPage';

it('logs in user', async () => {
  render(<LoginPage />);

  fireEvent.change(screen.getByLabelText('Gebruikersnaam'), {
    target: { value: 'testuser' },
  });

  fireEvent.change(screen.getByLabelText('Wachtwoord'), {
    target: { value: 'password123' },
  });

  fireEvent.click(screen.getByText('Inloggen'));

  // Assert redirect of token storage
});
```

#### E2E Tests (Optional)
**Playwright voor end-to-end tests:**
```bash
npm install -D @playwright/test
```

### 7. Development Workflow

#### Environment Setup
```bash
# Development
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

#### Hot Module Replacement
**Vite HMR werkt out of the box!** Code changes reflecteren instant in browser.

#### Linting & Formatting
```bash
# ESLint
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Prettier
npm install -D prettier eslint-config-prettier eslint-plugin-prettier

# Run lint
npm run lint

# Format
npm run format
```

---

## Samenvatting

### Wat is de KOV-RAG Applicatie?
Een **multi-user RAG systeem** voor het intelligent doorzoeken van BBL (Besluit Bouwwerken Leefomgeving) documenten met:
- BBL-specifieke document processing (BWB XML parsing)
- Intelligente semantic search met metadata filtering
- Chat interface met inline citaties (Perplexity-style)
- Admin functionaliteit (user invitations, user management)
- Multi-user isolatie (per-user Qdrant collections)

### Wat blijft hetzelfde?
✅ **Backend** (FastAPI, RAG pipeline, database, BBL processing)
✅ **API endpoints** (RESTful, goed gedocumenteerd)
✅ **Authenticatie** (JWT + bcrypt)
✅ **BBL intelligence** (query analysis, reranking, metadata filtering)

### Wat verandert?
❌ **Frontend**: Streamlit → React + TypeScript
❌ **State**: Server-side → Client-side (Zustand + React Query)
❌ **UI**: Streamlit widgets → Custom Tailwind components
❌ **Rendering**: Server-side → Client-side (SPA)

### Tech Stack (Nieuw)
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State**: Zustand (client state) + React Query (server state)
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS + Headless UI
- **Icons**: Heroicons
- **Markdown**: react-markdown + DOMPurify

### Implementatie Volgorde
1. **Project setup** (Vite + dependencies)
2. **Type definitions** (alle TypeScript types)
3. **API services** (axios + interceptors)
4. **State management** (Zustand stores + React Query hooks)
5. **Common components** (Button, Input, Card, etc.)
6. **Layout components** (Sidebar, Footer, Layout)
7. **Auth pages** (Login, Register)
8. **Query page** (met sources, relevance badges, etc.)
9. **Documents page** (upload, list, delete)
10. **Chat page** (sessions, messages, inline citations)
11. **Admin page** (invitations, user management)
12. **Routing** (App.tsx met protected routes)
13. **Testing & refinement**
14. **Deployment**

### Geschatte Timeline
- **Setup & Base Components**: 2-3 dagen
- **Auth & Routing**: 1 dag
- **Query Interface**: 2 dagen
- **Documents Management**: 1 dag
- **Chat Interface**: 2-3 dagen
- **Admin Panel**: 1-2 dagen
- **Testing & Refinement**: 2-3 dagen
- **Total**: ~12-15 dagen voor ervaren React developer

### Key Takeaways
1. **Backend hoeft NIET te veranderen** - API is al perfect voor React
2. **Zustand + React Query** is de beste state management combo voor deze use case
3. **Tailwind CSS** is de snelste manier om een mooie UI te bouwen
4. **Type safety** (TypeScript) voorkomt 90% van de bugs
5. **React Query caching** verbetert performance drastisch
6. **Headless UI** geeft accessible components out of the box
7. **Vite** is significant sneller dan Create React App

### Belangrijkste Aandachtspunten
⚠️ **Security**: XSS protection (DOMPurify), CORS config, JWT storage
⚠️ **Performance**: React Query caching, code splitting, bundle size
⚠️ **Accessibility**: Keyboard navigation, screen readers, ARIA labels
⚠️ **Mobile**: Responsive design, touch targets, viewport meta tag
⚠️ **Error handling**: API errors, loading states, empty states, error boundaries

---

**Dit bouwplan is een complete blauwdruk voor het herbouwen van de KOV-RAG applicatie in React + TypeScript. Een AI developer (zoals Claude Code) kan dit document gebruiken om stap-voor-stap de migratie uit te voeren, met alle nodige context over architectuur, data flows, en design beslissingen.**
