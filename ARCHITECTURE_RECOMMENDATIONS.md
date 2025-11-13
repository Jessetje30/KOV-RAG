# KOV-RAG: Moderne Architectuur Aanbevelingen (2025)

## Inhoudsopgave
1. [Executive Summary](#executive-summary)
2. [Nieuwe Requirements Analyse](#nieuwe-requirements-analyse)
3. [Huidige Architectuur vs Best Practices](#huidige-architectuur-vs-best-practices)
4. [Aanbevolen Moderne Architectuur](#aanbevolen-moderne-architectuur)
5. [Tech Stack Vergelijking](#tech-stack-vergelijking)
6. [Implementatie Roadmap](#implementatie-roadmap)
7. [Migratie Strategie](#migratie-strategie)
8. [Kosten Analyse](#kosten-analyse)

---

## Executive Summary

### TL;DR: Wat is de beste architectuur voor KOV-RAG?

**🎯 Aanbevolen Stack (Modern, Schaalbaar, Gebruiksvriendelijk):**

```
Frontend:     Next.js 14+ App Router + React + TypeScript + Tailwind CSS
Backend:      Next.js API Routes (simpel) OF FastAPI (complex RAG logic)
Database:     PostgreSQL (via Supabase)
Vector Store: pgvector (unified met PostgreSQL)
Auth:         Clerk (Organizations voor project-based permissions)
ORM:          Prisma (TypeScript-first)
Deployment:   Vercel (frontend) + Railway/Fly.io (backend indien FastAPI)
```

**Waarom deze stack?**
- ✅ **Full-stack TypeScript**: Type safety van frontend tot database
- ✅ **Built-in multi-tenancy**: Clerk Organizations = project-based permissions out-of-the-box
- ✅ **Unified database**: PostgreSQL + pgvector = 1 database voor alles (geen sync issues)
- ✅ **Developer Experience**: Beste tooling, snelste development
- ✅ **Cost-effective**: Supabase ($25/mo) + Clerk (free tot 10K users) + Vercel (free tier)
- ✅ **Scalable**: Kan groeien van MVP tot enterprise

### Wat verandert er ten opzichte van de huidige architectuur?

| Aspect | Huidig | Aanbevolen | Waarom? |
|--------|--------|------------|---------|
| **Frontend** | Streamlit (Python) | Next.js 14 App Router | Modern SPA, betere UX, type safety |
| **Backend** | FastAPI | Next.js API Routes + FastAPI | Unified stack, TypeScript waar mogelijk |
| **Database** | SQLite | PostgreSQL (Supabase) | Production-ready, RLS, scaling |
| **Vector DB** | Qdrant (separate) | pgvector (in PostgreSQL) | Unified data, geen sync, transactional |
| **Auth** | Custom JWT | Clerk | Organizations feature, geen custom code |
| **Multi-tenancy** | Geen (single-user) | **Project-based** | Clerk Orgs + Supabase RLS |
| **Permissions** | Admin/User roles | **Project Admins** | Per-project role management |
| **ORM** | SQLAlchemy | Prisma | TypeScript-first, type-safe queries |
| **Deployment** | Manual | Vercel + Railway | CI/CD, preview deploys |

---

## Nieuwe Requirements Analyse

### Jouw Requirements (van vraag):
1. **Multi-project toegang**: Users kunnen toegang hebben tot meerdere projecten
2. **Project Admins**: Per project kunnen admins users uitnodigen
3. **Project-based isolation**: Data per project gescheiden
4. **Gebruiksvriendelijk**: Intuïtieve UI/UX
5. **Best practices**: Modern, schaalbaar, maintainable

### Vertaling naar Technical Requirements:

#### 1. **Multi-Tenancy Model: Organization-Based**

**Data Model:**
```
Organization (Project)
  ├─ name, slug, settings
  ├─ Members (Users + Roles)
  │   ├─ User 1 (Admin)
  │   ├─ User 2 (Member)
  │   └─ User 3 (Viewer)
  ├─ Documents (BBL files per project)
  └─ Chat Sessions (per project)

User
  ├─ email, name
  └─ Memberships (N:N met Organizations)
```

**Voorbeeld Use Case:**
- **User A** is Admin in **"Project Gemeente X"** en Member in **"Project Bouwbedrijf Y"**
- **User B** is Admin in **"Project Bouwbedrijf Y"**
- User A kan in Project X andere users uitnodigen
- User B kan in Project Y andere users uitnodigen
- User A ziet alleen Project X en Y data, niet andere projecten

#### 2. **Permission Model: RBAC per Organization**

**Roles per Organization:**
- **Admin**: Volledige controle, kan users uitnodigen/verwijderen, documenten uploaden/verwijderen
- **Member**: Kan queries doen, documenten uploaden, chatten
- **Viewer**: Kan alleen queries doen en chatten (read-only)

**Global Roles (optioneel):**
- **Super Admin**: Kan alle organizations beheren (voor platform beheerder)

**Implementation:**
```typescript
// Clerk Organizations model
{
  organization_id: "org_abc123",
  name: "Gemeente Amsterdam",
  members: [
    { user_id: "user_1", role: "org:admin" },
    { user_id: "user_2", role: "org:member" },
    { user_id: "user_3", role: "org:viewer" }
  ]
}

// Supabase RLS policy (Row Level Security)
CREATE POLICY "Users can only see their org's documents"
ON documents FOR SELECT
USING (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.uid()
  )
);
```

#### 3. **Data Isolation Strategy**

**Database Level (PostgreSQL + RLS):**
- Elke tabel heeft `organization_id` kolom
- Row Level Security policies enforces isolation
- Queries automatisch gefilterd op organization_id

**Vector Store Level (pgvector):**
- Vectors hebben `organization_id` in metadata
- Semantic search gefilterd op active organization
- Geen cross-organization data leakage

**Benefits:**
- ✅ **Transactional**: Document + vector operations in 1 transactie
- ✅ **Consistent**: Geen sync issues tussen databases
- ✅ **Performant**: RLS werkt op database level (supersnel)
- ✅ **Secure**: Database enforces isolation, niet applicatie code

---

## Huidige Architectuur vs Best Practices

### Huidige Architectuur (Analyse)

**✅ Wat is goed:**
1. **FastAPI backend**: Modern, async, goed voor Python RAG workloads
2. **Qdrant vector database**: Goede filtering capabilities
3. **BBL-specific logic**: Goed doordachte metadata extraction en reranking
4. **Security**: JWT auth, rate limiting, input sanitization

**❌ Wat kan beter:**
1. **Streamlit frontend**: Niet geschikt voor production SaaS
   - Server-side rendering (traag)
   - Moeilijk te customizen
   - Beperkte UI componenten
   - Geen echte multi-tenancy support

2. **SQLite database**: Niet production-ready
   - Single file (geen concurrent writes)
   - Geen connection pooling
   - Geen replication/backup
   - Geen row-level security

3. **Qdrant separate**: Extra complexity
   - Moet in sync blijven met PostgreSQL
   - 2 databases om te beheren
   - Geen transactional consistency
   - Extra infrastructure kosten

4. **Custom auth**: Veel boilerplate
   - Eigen JWT implementation
   - Invitation system zelf gebouwd
   - Geen organizations/teams concept
   - Geen SSO/MFA out-of-the-box

5. **Geen multi-tenancy**: Niet schaalbaar
   - 1 Qdrant collection per user (doesn't scale)
   - Geen project-based isolation
   - Geen team collaboration

### 2025 Best Practices voor RAG SaaS

**Volgens industry experts (AWS, Azure, Google, Anthropic):**

#### 1. **Architecture Pattern: Monorepo Full-Stack TypeScript**

**Rationale:**
- **Type safety**: End-to-end types van database tot UI
- **Code sharing**: Shared types, utils, validation
- **Developer velocity**: 1 language, 1 ecosystem
- **Easier hiring**: TypeScript devs > Python + JS devs

**Modern Pattern:**
```
monorepo/
├── apps/
│   ├── web/              # Next.js frontend
│   └── api/              # Next.js API routes OF FastAPI
├── packages/
│   ├── db/               # Prisma schema + client
│   ├── ui/               # Shared React components
│   ├── types/            # Shared TypeScript types
│   └── utils/            # Shared utilities
└── infra/                # Deployment configs
```

#### 2. **Database Pattern: Unified PostgreSQL**

**Rationale:**
- **pgvector extension**: Vector search in PostgreSQL (no separate DB needed)
- **Row Level Security**: Multi-tenancy op database level
- **ACID transactions**: Consistency guarantees
- **Proven scalability**: Billions of rows, terabytes of data

**2025 Benchmark:** pgvector + pgvectorscale nu **11.4x sneller** dan Qdrant (471 QPS vs 41 QPS)

#### 3. **Auth Pattern: Managed Provider met Organizations**

**Rationale:**
- **Organizations feature**: Built-in multi-tenancy
- **Invitation system**: No custom code needed
- **SSO/MFA**: Enterprise features out-of-the-box
- **Compliance**: SOC 2, GDPR handled by provider

**Best Providers 2025:**
- **Clerk**: Beste DX, Organizations built-in, $0.02/MAU na free tier
- **Supabase Auth**: Beste prijs ($25/mo tot 100K users), tight DB integration
- **Auth0**: Enterprise features, duur ($240+/mo)

#### 4. **Vector Store Pattern: Hybrid Search**

**Rationale:**
- **Keyword + Semantic**: Best of both worlds
- **pgvector**: Vector search in PostgreSQL
- **PostgreSQL FTS**: Full-text search
- **Hybrid ranking**: Combine scores (RRF, Cohere rerank)

**Benefits:**
- 20-30% better recall than pure vector search
- Handles exact matches (artikel numbers, legal terms)
- No separate vector database needed

#### 5. **Frontend Pattern: React Server Components**

**Rationale:**
- **Next.js 14 App Router**: Server components, streaming, Suspense
- **Type-safe APIs**: tRPC or Server Actions
- **SEO-friendly**: SSR out-of-the-box
- **Better UX**: Instant navigation, optimistic updates

---

## Aanbevolen Moderne Architectuur

### Optie A: **Full Next.js Stack** (Aanbevolen voor snelle development)

**Gebruik dit als:**
- ✅ Je wilt zo snel mogelijk een MVP
- ✅ RAG logic is relatief simpel (OpenAI API calls)
- ✅ Team heeft TypeScript/JavaScript expertise
- ✅ Je wilt minimale infra complexity

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEXT.JS APP                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  App Router (React Server Components)                      │ │
│  │  • Server Components (RSC)                                 │ │
│  │  • Client Components (interactive UI)                      │ │
│  │  • Streaming (Suspense boundaries)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Routes (Backend Logic)                                │ │
│  │  • POST /api/documents/upload                              │ │
│  │  • POST /api/query                                         │ │
│  │  • POST /api/chat/query                                    │ │
│  │  • RAG Pipeline (TypeScript/JavaScript)                    │ │
│  │    - LangChain.js OR llamaindex.ts                         │ │
│  │    - OpenAI SDK                                            │ │
│  │    - Hybrid search (pgvector + FTS)                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          CLERK AUTH                              │
│  • Organizations (Projects)                                      │
│  • Invitations                                                   │
│  • RBAC (Admin/Member/Viewer)                                    │
│  • JWT tokens                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Tables (via Prisma ORM)                                   │ │
│  │  • organizations                                           │ │
│  │  • memberships (N:N users ↔ orgs with roles)              │ │
│  │  • documents (organization_id FK)                          │ │
│  │  • embeddings (pgvector, organization_id)                  │ │
│  │  • chat_sessions (organization_id FK)                      │ │
│  │  • chat_messages                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Row Level Security (RLS)                                  │ │
│  │  • Automatic filtering op organization_id                  │ │
│  │  • Enforced by PostgreSQL (niet app code)                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  pgvector Extension                                        │ │
│  │  • Vector similarity search                                │ │
│  │  • Cosine/Euclidean/Inner Product distance                 │ │
│  │  • HNSW index voor performance                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Tech Stack Details:**
- **Frontend**: Next.js 14 App Router + React 18 + TypeScript + Tailwind CSS
- **Backend**: Next.js API Routes (serverless functions)
- **RAG Framework**: LangChain.js (mature) OF llamaindex.ts (Python compatibility)
- **Database**: Supabase PostgreSQL (managed)
- **ORM**: Prisma (type-safe, migrations)
- **Vector Search**: pgvector extension in PostgreSQL
- **Auth**: Clerk (Organizations + Invitations)
- **LLM**: OpenAI GPT-4 + text-embedding-3-large
- **Deployment**: Vercel (all-in-one)

**Pros:**
- ✅ **Snelste development**: 1 codebase, 1 framework, 1 language
- ✅ **Type safety**: End-to-end TypeScript
- ✅ **Lowest infra cost**: Vercel free tier + Supabase $25/mo
- ✅ **Best DX**: Hot reload, preview deploys, edge functions
- ✅ **Serverless**: Auto-scaling, pay-per-use

**Cons:**
- ❌ **JavaScript RAG ecosystem**: Minder mature dan Python (maar groeit snel!)
- ❌ **Complex RAG logic**: Python libraries (spaCy, NLTK) niet beschikbaar
- ❌ **Vendor lock-in**: Vercel-specific optimizations

**When to choose:** MVP, small-medium teams, standard RAG use cases

---

### Optie B: **Next.js + FastAPI Hybrid** (Aanbevolen voor complex RAG)

**Gebruik dit als:**
- ✅ Je hebt complexe RAG logic (custom BBL parsing, advanced reranking)
- ✅ Team heeft Python expertise
- ✅ Je wilt Python RAG ecosystem (LangChain, LlamaIndex, Haystack)
- ✅ Je hebt zware data processing pipelines

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEXT.JS FRONTEND + API                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  App Router (React Server Components)                      │ │
│  │  • Server Components voor data fetching                    │ │
│  │  • Client Components voor interactivity                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Next.js API Routes (Light backend)                        │ │
│  │  • Authentication proxy naar Clerk                         │ │
│  │  • Simple CRUD operations (Prisma)                         │ │
│  │  • WebSocket proxy voor streaming                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (tRPC / REST)
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  RAG Endpoints                                             │ │
│  │  • POST /api/documents/upload → BBL XML parsing            │ │
│  │  • POST /api/query → RAG pipeline                          │ │
│  │  • POST /api/chat/query → Conversational RAG               │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  RAG Pipeline (Python)                                     │ │
│  │  • LangChain / LlamaIndex / Haystack                       │ │
│  │  • Custom BBL XML parser                                   │ │
│  │  • Query analyzer (metadata extraction)                    │ │
│  │  • Reranker (metadata-based + LLM verification)            │ │
│  │  • Hybrid search (pgvector + BM25)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          CLERK AUTH                              │
│  • JWT verification in FastAPI                                  │
│  • Organization context in requests                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                           │
│  • Same schema als Optie A                                       │
│  • Accessed from both Next.js (Prisma) en FastAPI (SQLAlchemy)  │
│  • pgvector voor embeddings                                     │
│  • RLS policies                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tech Stack Details:**
- **Frontend**: Next.js 14 App Router + React 18 + TypeScript
- **API Layer**: Next.js API Routes (auth, simple CRUD)
- **RAG Backend**: FastAPI (Python, async)
- **RAG Framework**: LangChain / LlamaIndex (Python)
- **Database**: Supabase PostgreSQL
- **ORM**: Prisma (Next.js) + SQLAlchemy (FastAPI)
- **Auth**: Clerk (JWT verification in beide services)
- **Deployment**: Vercel (Next.js) + Railway/Fly.io (FastAPI)

**Pros:**
- ✅ **Best of both worlds**: TypeScript frontend + Python RAG
- ✅ **Python RAG ecosystem**: Mature libraries, meer features
- ✅ **Complex logic**: Behoud huidige BBL processing
- ✅ **Separation of concerns**: Frontend/backend independent

**Cons:**
- ❌ **Meer complexity**: 2 codebases, 2 deployments
- ❌ **Hogere kosten**: Extra server voor FastAPI
- ❌ **Langzamere development**: Context switching tussen TS/Python

**When to choose:** Complex RAG, existing Python codebase, large team

---

### Optie C: **Full Python Stack** (Niet aanbevolen, maar compleet)

**Gebruik dit als:**
- ⚠️ Team heeft ALLEEN Python expertise (geen TypeScript)
- ⚠️ Bestaande Python codebase die je wilt behouden

```
Frontend:  Reflex (Python) OF React + FastAPI backend
Backend:   FastAPI
Database:  PostgreSQL (SQLAlchemy)
Vector:    pgvector OF Qdrant
Auth:      FastAPI-Users + custom Organizations
```

**Waarom niet aanbevolen:**
- ❌ **Reflex is immature**: Nog in beta, kleine community
- ❌ **React + Python**: Betere opties beschikbaar (Next.js)
- ❌ **Slower iteration**: Python frontend is trager dan TypeScript
- ❌ **Beperkte ecosystem**: Minder UI libraries

**Only choose if:** Je team kan absoluut geen TypeScript leren (onrealistisch)

---

## Tech Stack Vergelijking

### 1. Frontend Framework

| Framework | Pros | Cons | Score (0-10) |
|-----------|------|------|--------------|
| **Next.js 14** | RSC, Streaming, Type-safe, Best DX, Vercel integration | Vercel lock-in | ⭐ 10/10 |
| React (Vite) | Flexible, No vendor lock-in | No SSR, Need separate backend | ⭐ 7/10 |
| Streamlit | Fast prototyping | Not for production SaaS | ⭐ 3/10 |
| Reflex (Python) | Python-only stack | Immature, small community | ⭐ 4/10 |

**Winner:** 🏆 **Next.js 14 App Router**

---

### 2. Backend Framework

| Framework | Pros | Cons | Best For | Score |
|-----------|------|------|----------|-------|
| **Next.js API Routes** | Type-safe, Serverless, Same codebase | JavaScript only | Simple RAG, CRUD | ⭐ 9/10 |
| **FastAPI** | Python ecosystem, Async, Auto docs | Separate deployment | Complex RAG | ⭐ 9/10 |
| **tRPC** | End-to-end type safety, No REST | Next.js only | Full Next.js stack | ⭐ 8/10 |
| Express.js | Mature, Flexible | Boilerplate, No type safety | Legacy apps | ⭐ 6/10 |

**Winner (depends):**
- 🏆 **Next.js API Routes** voor simple-medium RAG
- 🏆 **FastAPI** voor complex RAG (behoud Python logic)

---

### 3. Database

| Database | Pros | Cons | Score |
|----------|------|------|-------|
| **PostgreSQL (Supabase)** | Managed, RLS, pgvector, Proven scale | Slight vendor lock-in | ⭐ 10/10 |
| PostgreSQL (self-hosted) | Full control, No lock-in | Ops overhead | ⭐ 8/10 |
| SQLite | Simple, Embedded | Not for production | ⭐ 2/10 |
| MongoDB | Flexible schema | No RLS, No pgvector | ⭐ 5/10 |

**Winner:** 🏆 **PostgreSQL via Supabase**

---

### 4. Vector Store

| Vector Store | Pros | Cons | Best For | Score |
|--------------|------|------|----------|-------|
| **pgvector** | Unified DB, Transactional, 11x faster (2025) | Less features than specialized | Unified data | ⭐ 10/10 |
| **Qdrant** | Advanced filtering, Rust speed, Open-source | Separate DB, Sync issues | Complex filters | ⭐ 8/10 |
| **Pinecone** | Managed, Serverless, Enterprise SLAs | Expensive, Vendor lock-in | Zero-ops | ⭐ 7/10 |
| Weaviate | GraphQL, Multi-modal | Separate DB | Multi-modal RAG | ⭐ 7/10 |

**Winner:** 🏆 **pgvector** (unified architecture, proven performance)

**When to use Qdrant:** Complex metadata filtering, existing Qdrant expertise

---

### 5. Auth Provider

| Provider | Pros | Cons | Pricing | Score |
|----------|------|------|---------|-------|
| **Clerk** | Best DX, Organizations built-in, Beautiful UI | $0.02/MAU after 10K | Free → $25/mo (10K) | ⭐ 10/10 |
| **Supabase Auth** | Cheapest, DB integration, 100K free users | No Organizations (DIY) | $25/mo (all) | ⭐ 9/10 |
| **Auth0** | Enterprise features, Mature | Expensive, Complex setup | $240+/mo | ⭐ 6/10 |
| NextAuth.js | Free, Flexible | DIY everything | Free | ⭐ 7/10 |

**Winner:** 🏆 **Clerk** (Organizations = project-based permissions out-of-the-box)

**Alternative:** Supabase Auth + DIY Organizations (goedkoper, meer werk)

---

### 6. ORM

| ORM | Pros | Cons | Score |
|-----|------|------|-------|
| **Prisma** | Type-safe, Great DX, Auto-migrations | Node.js only | ⭐ 10/10 |
| **Drizzle** | Lighter, SQL-like, Edge-compatible | Less mature | ⭐ 8/10 |
| SQLAlchemy | Python, Mature, Flexible | Verbose, No type safety | ⭐ 7/10 |

**Winner:** 🏆 **Prisma** (voor TypeScript stack)

---

### 7. RAG Framework

| Framework | Language | Pros | Cons | Score |
|-----------|----------|------|------|-------|
| **LangChain** | Python/JS | Most popular, Rich ecosystem | Complex API, Breaking changes | ⭐ 8/10 |
| **LlamaIndex** | Python/TS | Best for RAG, Simpler API | Smaller than LC | ⭐ 9/10 |
| **Haystack** | Python | Production-ready, Modular | Steeper learning curve | ⭐ 7/10 |
| **Vercel AI SDK** | TypeScript | Next.js integration, Streaming | Limited features | ⭐ 7/10 |

**Winner (depends):**
- 🏆 **LlamaIndex.ts** voor Next.js stack (TypeScript)
- 🏆 **LangChain Python** voor FastAPI stack (mature)

---

## Aanbevolen Architectuur: De Winnaar 🏆

### **Optie A: Full Next.js Stack** (voor 80% van use cases)

```typescript
// Modern Stack 2025
{
  frontend: "Next.js 14 App Router + React 18 + TypeScript",
  backend: "Next.js API Routes (serverless)",
  ragFramework: "LlamaIndex.ts",
  database: "Supabase PostgreSQL",
  orm: "Prisma",
  vectorStore: "pgvector (in PostgreSQL)",
  auth: "Clerk (Organizations)",
  llm: "OpenAI GPT-4 + embeddings",
  deployment: "Vercel (all-in-one)",
  cost: "$25-100/mo (small-medium scale)"
}
```

**Waarom deze stack?**

1. **Developer Velocity** 🚀
   - End-to-end TypeScript = 50% snellere development
   - 1 codebase = geen context switching
   - Type-safe APIs = minder bugs
   - Hot reload everywhere

2. **User Experience** ✨
   - React Server Components = instant loading
   - Streaming responses = real-time RAG answers
   - Optimistic updates = snappy UI
   - Server-side rendering = SEO + performance

3. **Multi-Tenancy Built-in** 👥
   - Clerk Organizations = project-based permissions out-of-the-box
   - Supabase RLS = automatic data isolation
   - No custom auth code needed
   - Invitation system included

4. **Cost-Effective** 💰
   - Vercel: Free → $20/mo (hobby → pro)
   - Supabase: $25/mo (tot 100K users, 8GB database)
   - Clerk: Free tot 10K users, dan $0.02/MAU
   - **Total: $25-50/mo** voor MVP/small scale

5. **Scalable** 📈
   - Vercel Edge Functions: Auto-scaling
   - Supabase: Proven tot 1M+ users
   - pgvector: Handles 100M+ vectors
   - Horizontal scaling possible

6. **Modern Best Practices** ✅
   - Unified database (PostgreSQL + pgvector)
   - Row Level Security (database-enforced isolation)
   - Type safety (catch errors at compile time)
   - CI/CD built-in (preview deploys, rollbacks)

---

## Implementatie Roadmap

### Fase 1: Foundation Setup (Week 1-2)

#### 1.1 Project Initialization
```bash
# Create Next.js project
npx create-next-app@latest kov-rag --typescript --tailwind --app --turbopack

# Install dependencies
npm install @clerk/nextjs @supabase/supabase-js @prisma/client
npm install llamaindex openai zod react-markdown
npm install -D prisma
```

#### 1.2 Supabase Setup
```bash
# Create Supabase project (via dashboard)
# Enable pgvector extension
# Configure RLS policies
```

**SQL Schema:**
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- Organizations (Projects)
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  settings JSONB DEFAULT '{}'::jsonb
);

-- Memberships (N:N users ↔ organizations)
CREATE TABLE memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL, -- Clerk user ID
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('admin', 'member', 'viewer')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, organization_id)
);

-- Documents
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  uploaded_by TEXT NOT NULL, -- Clerk user ID
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Embeddings (vector store)
CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  embedding VECTOR(3072), -- OpenAI text-embedding-3-large
  chunk_index INTEGER NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create HNSW index for vector search
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);

-- Chat sessions
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL, -- Clerk user ID
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  sources JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies (Row Level Security)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see organizations they're member of
CREATE POLICY "Users see their organizations"
ON organizations FOR SELECT
USING (
  id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.jwt() ->> 'sub'
  )
);

-- Policy: Users can only see documents in their organizations
CREATE POLICY "Users see org documents"
ON documents FOR SELECT
USING (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.jwt() ->> 'sub'
  )
);

-- Policy: Only admins/members can insert documents
CREATE POLICY "Admins/members can upload documents"
ON documents FOR INSERT
WITH CHECK (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.jwt() ->> 'sub'
    AND role IN ('admin', 'member')
  )
);

-- Similar policies for embeddings, chat_sessions, chat_messages
-- (zie volledige schema in implementation guide)
```

#### 1.3 Clerk Setup
```bash
# Create Clerk account
# Enable Organizations feature
# Configure JWT template to include org_id
# Set environment variables
```

**Clerk JWT Template:**
```json
{
  "sub": "{{user.id}}",
  "email": "{{user.primary_email_address}}",
  "org_id": "{{org.id}}",
  "org_role": "{{org.role}}",
  "org_slug": "{{org.slug}}"
}
```

#### 1.4 Prisma Setup
```typescript
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
  previewFeatures = ["postgresqlExtensions"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  extensions = [vector]
}

model Organization {
  id        String   @id @default(uuid())
  name      String
  slug      String   @unique
  createdAt DateTime @default(now()) @map("created_at")
  settings  Json     @default("{}")

  memberships    Membership[]
  documents      Document[]
  embeddings     Embedding[]
  chatSessions   ChatSession[]

  @@map("organizations")
}

model Membership {
  id             String   @id @default(uuid())
  userId         String   @map("user_id")
  organizationId String   @map("organization_id")
  role           Role
  createdAt      DateTime @default(now()) @map("created_at")

  organization Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)

  @@unique([userId, organizationId])
  @@map("memberships")
}

enum Role {
  admin
  member
  viewer
}

model Document {
  id             String   @id @default(uuid())
  organizationId String   @map("organization_id")
  filename       String
  fileType       String   @map("file_type")
  uploadedBy     String   @map("uploaded_by")
  createdAt      DateTime @default(now()) @map("created_at")
  metadata       Json     @default("{}")

  organization Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  embeddings   Embedding[]

  @@map("documents")
}

model Embedding {
  id             String                        @id @default(uuid())
  documentId     String                        @map("document_id")
  organizationId String                        @map("organization_id")
  chunkText      String                        @map("chunk_text")
  embedding      Unsupported("vector(3072)")?
  chunkIndex     Int                           @map("chunk_index")
  metadata       Json                          @default("{}")
  createdAt      DateTime                      @default(now()) @map("created_at")

  document     Document     @relation(fields: [documentId], references: [id], onDelete: Cascade)
  organization Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)

  @@map("embeddings")
}

// ChatSession, ChatMessage models...
```

```bash
# Generate Prisma client
npx prisma generate

# Push schema to database
npx prisma db push
```

### Fase 2: Authentication & Multi-Tenancy (Week 2-3)

#### 2.1 Clerk Integration
```typescript
// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs';

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html lang="nl">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

#### 2.2 Organization Context
```typescript
// lib/organization.ts
import { auth } from '@clerk/nextjs';

export async function getActiveOrganization() {
  const { orgId, orgRole } = auth();

  if (!orgId) {
    throw new Error('No active organization');
  }

  return {
    id: orgId,
    role: orgRole as 'admin' | 'member' | 'viewer',
  };
}

export function hasPermission(
  role: 'admin' | 'member' | 'viewer',
  action: 'read' | 'write' | 'admin'
) {
  const permissions = {
    admin: ['read', 'write', 'admin'],
    member: ['read', 'write'],
    viewer: ['read'],
  };

  return permissions[role].includes(action);
}
```

#### 2.3 RLS Helper (Supabase)
```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js';
import { auth } from '@clerk/nextjs';

export async function getSupabaseClient() {
  const { getToken } = auth();
  const token = await getToken({ template: 'supabase' });

  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      global: {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    }
  );
}
```

### Fase 3: RAG Pipeline (Week 3-5)

#### 3.1 Document Upload & Processing
```typescript
// app/api/documents/upload/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs';
import { prisma } from '@/lib/prisma';
import { OpenAI } from 'openai';

export async function POST(req: NextRequest) {
  const { userId, orgId, orgRole } = auth();

  if (!userId || !orgId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check permission
  if (!['admin', 'member'].includes(orgRole!)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const formData = await req.formData();
  const file = formData.get('file') as File;

  // Extract text (PDF/DOCX/XML)
  const text = await extractText(file);

  // Chunk text
  const chunks = chunkText(text, { size: 800, overlap: 100 });

  // Generate embeddings
  const openai = new OpenAI();
  const embeddings = await openai.embeddings.create({
    model: 'text-embedding-3-large',
    input: chunks,
  });

  // Store in database
  const document = await prisma.document.create({
    data: {
      organizationId: orgId,
      filename: file.name,
      fileType: file.type,
      uploadedBy: userId,
    },
  });

  await prisma.embedding.createMany({
    data: embeddings.data.map((emb, i) => ({
      documentId: document.id,
      organizationId: orgId,
      chunkText: chunks[i],
      embedding: `[${emb.embedding.join(',')}]`, // pgvector format
      chunkIndex: i,
    })),
  });

  return NextResponse.json({ document });
}
```

#### 3.2 Query Endpoint
```typescript
// app/api/query/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs';
import { prisma } from '@/lib/prisma';
import { OpenAI } from 'openai';

export async function POST(req: NextRequest) {
  const { userId, orgId } = auth();
  const { query, topK = 5 } = await req.json();

  // Generate query embedding
  const openai = new OpenAI();
  const queryEmbedding = await openai.embeddings.create({
    model: 'text-embedding-3-large',
    input: query,
  });

  // Vector search (using Prisma raw SQL for pgvector)
  const results = await prisma.$queryRaw`
    SELECT
      chunk_text,
      metadata,
      1 - (embedding <=> ${`[${queryEmbedding.data[0].embedding.join(',')}]`}::vector) as similarity
    FROM embeddings
    WHERE organization_id = ${orgId}
    ORDER BY embedding <=> ${`[${queryEmbedding.data[0].embedding.join(',')}]`}::vector
    LIMIT ${topK}
  `;

  // Build context
  const context = results
    .map((r, i) => `Context ${i + 1}: [${i + 1}]\n${r.chunk_text}`)
    .join('\n\n');

  // Generate answer
  const completion = await openai.chat.completions.create({
    model: 'gpt-4-turbo',
    messages: [
      {
        role: 'system',
        content: 'Je bent een expert in BBL regelgeving...',
      },
      {
        role: 'user',
        content: `Context:\n${context}\n\nVraag: ${query}`,
      },
    ],
  });

  return NextResponse.json({
    answer: completion.choices[0].message.content,
    sources: results,
  });
}
```

### Fase 4: Frontend UI (Week 5-7)

#### 4.1 Organization Selector
```typescript
// components/OrganizationSelector.tsx
'use client';

import { OrganizationSwitcher } from '@clerk/nextjs';

export function OrganizationSelector() {
  return (
    <OrganizationSwitcher
      appearance={{
        elements: {
          rootBox: 'flex items-center',
        },
      }}
      createOrganizationMode="navigation"
      createOrganizationUrl="/create-organization"
    />
  );
}
```

#### 4.2 Query Page
```typescript
// app/(dashboard)/query/page.tsx
import { QueryForm } from '@/components/QueryForm';
import { auth } from '@clerk/nextjs';
import { redirect } from 'next/navigation';

export default async function QueryPage() {
  const { userId, orgId } = auth();

  if (!userId) redirect('/sign-in');
  if (!orgId) redirect('/select-organization');

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">BBL Vragen Stellen</h1>
      <QueryForm />
    </div>
  );
}
```

### Fase 5: Advanced Features (Week 8-10)

#### 5.1 Hybrid Search (pgvector + Full-Text Search)
```sql
-- Add full-text search
ALTER TABLE embeddings ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (to_tsvector('dutch', chunk_text)) STORED;

CREATE INDEX ON embeddings USING gin(search_vector);
```

```typescript
// Hybrid search query
const results = await prisma.$queryRaw`
  WITH vector_results AS (
    SELECT id, 1 - (embedding <=> ${vectorQuery}::vector) as score
    FROM embeddings
    WHERE organization_id = ${orgId}
    ORDER BY score DESC
    LIMIT ${topK * 2}
  ),
  fts_results AS (
    SELECT id, ts_rank(search_vector, plainto_tsquery('dutch', ${query})) as score
    FROM embeddings
    WHERE organization_id = ${orgId}
      AND search_vector @@ plainto_tsquery('dutch', ${query})
    ORDER BY score DESC
    LIMIT ${topK * 2}
  )
  SELECT
    e.*,
    COALESCE(v.score, 0) * 0.7 + COALESCE(f.score, 0) * 0.3 as combined_score
  FROM embeddings e
  LEFT JOIN vector_results v ON e.id = v.id
  LEFT JOIN fts_results f ON e.id = f.id
  WHERE e.organization_id = ${orgId}
    AND (v.id IS NOT NULL OR f.id IS NOT NULL)
  ORDER BY combined_score DESC
  LIMIT ${topK}
`;
```

#### 5.2 Streaming Responses
```typescript
// app/api/query/stream/route.ts
import { OpenAIStream, StreamingTextResponse } from 'ai';

export async function POST(req: Request) {
  // ... query logic ...

  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo',
    messages: [...],
    stream: true,
  });

  const stream = OpenAIStream(response);
  return new StreamingTextResponse(stream);
}
```

```typescript
// Client component
'use client';

import { useChat } from 'ai/react';

export function StreamingQuery() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: '/api/query/stream',
  });

  return (
    <form onSubmit={handleSubmit}>
      <input value={input} onChange={handleInputChange} />
      <div>{messages.map(m => <div key={m.id}>{m.content}</div>)}</div>
    </form>
  );
}
```

### Fase 6: Testing & Deployment (Week 10-12)

#### 6.1 Testing Setup
```bash
npm install -D @testing-library/react @testing-library/jest-dom vitest
```

#### 6.2 Deployment (Vercel)
```bash
# Connect to GitHub
# Vercel auto-deploys on push

# Environment variables in Vercel dashboard:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
DATABASE_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
OPENAI_API_KEY=
```

---

## Migratie Strategie

### Scenario 1: Greenfield (Nieuwe App)

**Aanbeveling:** Start direct met moderne stack (Optie A)

**Timeline:** 10-12 weken tot MVP

**Approach:**
1. Week 1-2: Setup infrastructure (Next.js + Supabase + Clerk)
2. Week 3-5: Implementeer RAG pipeline (document upload, query, chat)
3. Week 5-7: Build UI (React components, pages)
4. Week 8-10: Advanced features (hybrid search, streaming, admin panel)
5. Week 10-12: Testing, polish, deployment

**Team:** 2-3 developers (1 full-stack + 1 frontend + 1 designer)

---

### Scenario 2: Migratie van Huidige App

**Aanbeveling:** Incremental migration naar Optie B (Next.js + FastAPI hybrid)

**Phase 1: Backend Migration (4-6 weken)**
1. Migrate SQLite → PostgreSQL (Supabase)
2. Migrate Qdrant → pgvector
3. Add Organizations table + RLS policies
4. Update FastAPI auth to support Clerk JWTs
5. Add organization_id to all queries

**Phase 2: Frontend Migration (6-8 weken)**
1. Setup Next.js project
2. Integrate Clerk (Organizations)
3. Rebuild pages (Query, Chat, Documents, Admin)
4. Migrate Streamlit components → React components
5. Connect to FastAPI backend (existing endpoints)

**Phase 3: Optimization (2-4 weken)**
1. Implement hybrid search
2. Add streaming responses
3. Performance optimization
4. Testing & bug fixes

**Total Timeline:** 12-18 weken

**Parallel Development Strategy:**
- Keep Streamlit app running (oude versie)
- Build Next.js app parallel (nieuwe versie)
- Shared PostgreSQL + FastAPI backend
- Switch over wanneer Next.js app feature-complete

---

## Kosten Analyse

### Small Scale (MVP, <1000 gebruikers)

**Optie A: Full Next.js Stack**
| Service | Plan | Cost/month |
|---------|------|------------|
| Vercel | Hobby | $0 (free tier) |
| Supabase | Pro | $25 |
| Clerk | Free | $0 (tot 10K MAU) |
| OpenAI | Pay-as-go | $50-200 (depends on usage) |
| **Total** | | **$75-225/mo** |

**Optie B: Next.js + FastAPI Hybrid**
| Service | Plan | Cost/month |
|---------|------|------------|
| Vercel | Hobby | $0 |
| Railway (FastAPI) | Hobby | $5 |
| Supabase | Pro | $25 |
| Clerk | Free | $0 |
| OpenAI | Pay-as-go | $50-200 |
| **Total** | | **$80-230/mo** |

---

### Medium Scale (10K-100K gebruikers)

**Optie A: Full Next.js Stack**
| Service | Plan | Cost/month |
|---------|------|------------|
| Vercel | Pro | $20 |
| Supabase | Pro | $25 (+ overage) |
| Clerk | Pro | $200-400 (10K-20K MAU @ $0.02/MAU) |
| OpenAI | Pay-as-go | $500-2000 |
| **Total** | | **$745-2445/mo** |

---

### Large Scale (100K+ gebruikers)

**Optie B: Next.js + FastAPI Hybrid**
| Service | Plan | Cost/month |
|---------|------|------------|
| Vercel | Pro/Enterprise | $20-500 |
| Railway/AWS | Scale | $100-500 (FastAPI) |
| Supabase | Pro/Enterprise | $25-2000+ |
| Clerk | Pro/Enterprise | $2000+ |
| OpenAI | Pay-as-go | $2000-10000+ |
| **Total** | | **$4145-13000+/mo** |

**Note:** Bij deze schaal overweeg je waarschijnlijk custom infrastructure (Kubernetes, self-hosted PostgreSQL, etc.)

---

## Conclusie & Aanbevelingen

### 🏆 Winnende Architectuur: **Optie A (Full Next.js Stack)**

**Voor 80% van use cases is dit de beste keuze:**
- ✅ Snelste time-to-market (10-12 weken tot MVP)
- ✅ Laagste kosten ($75-225/mo small scale)
- ✅ Beste developer experience
- ✅ Built-in multi-tenancy (Clerk Organizations)
- ✅ Unified database (PostgreSQL + pgvector)
- ✅ Type safety (end-to-end TypeScript)
- ✅ Schaalbaar (tot 100K+ users)

### Wanneer **Optie B (Hybrid)** kiezen?

**Alleen als:**
- Je hebt **zeer complexe** RAG logic (custom NLP, spaCy, NLTK)
- Je team heeft **sterke Python expertise** en weinig TypeScript
- Je wilt **bestaande Python codebase** behouden

**Trade-offs:**
- ❌ Meer complexity (2 codebases)
- ❌ Langzamere development
- ❌ Hogere kosten (extra server)

### Roadmap Priority

**Phase 1 (Must Have):** Foundation
- ✅ Next.js + Supabase + Clerk setup
- ✅ Organizations (project-based permissions)
- ✅ Document upload (PDF, DOCX, XML)
- ✅ Basic RAG query

**Phase 2 (Should Have):** Core Features
- ✅ Chat interface (conversational RAG)
- ✅ Admin panel (invite users, manage projects)
- ✅ Hybrid search (vector + full-text)

**Phase 3 (Nice to Have):** Advanced
- ✅ Streaming responses
- ✅ BBL-specific metadata extraction
- ✅ Advanced reranking
- ✅ Analytics dashboard

### Volgende Stappen

**Voor Greenfield (nieuwe app):**
1. **Week 1:** Setup repositories, Supabase, Clerk accounts
2. **Week 2:** Implement schema, RLS policies, Prisma setup
3. **Week 3-4:** Build document upload + RAG pipeline
4. **Week 5-7:** Build frontend (query, chat, admin)
5. **Week 8-10:** Polish, test, deploy
6. **Week 10-12:** Beta launch, feedback, iterate

**Voor Migratie (bestaande app):**
1. **Week 1-2:** Migreer database (SQLite → PostgreSQL)
2. **Week 3-4:** Migreer vector store (Qdrant → pgvector)
3. **Week 5-6:** Add multi-tenancy (Organizations, RLS)
4. **Week 7-12:** Build Next.js frontend parallel
5. **Week 13-14:** Switch over, deprecate Streamlit
6. **Week 15-18:** Optimize, refine, scale

---

**Wil je dat ik een gedetailleerd implementation guide schrijf voor de gekozen architectuur? Of wil je dat ik direct begin met de implementatie?**
