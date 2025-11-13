# KOV-RAG Implementation Guide - Part 1: Backend Foundation
**Voor: Claude Code (AI Developer)**

Dit is een **specification-based implementation guide** voor het bouwen van de backend foundation van een moderne RAG applicatie. Je krijgt **requirements en architecture decisions**, maar **geen code**. Het is jouw taak om de beste moderne implementatie te kiezen.

---

## ⚠️ KRITISCHE INSTRUCTIES

### 1. Package Versioning
- **ALTIJD**: `npm install <package>` zonder versienummer
- **NOOIT**: `npm install <package@1.2.3>` met specifieke versie
- Laat package managers de **laatste compatibele versie** kiezen
- Dit houdt het project toekomstbestendig en veilig

### 2. Implementation Philosophy
- **Je krijgt REQUIREMENTS**, geen code
- **Jij kiest** de beste moderne implementatie
- **Gebruik** de nieuwste patterns en best practices
- **Denk kritisch** over architecture decisions
- **Test** alles wat je bouwt
- **Document** belangrijke beslissingen

### 3. Quality Standards
- ✅ **Type Safety**: Gebruik TypeScript strict mode
- ✅ **Testing**: Write tests voor kritieke functionaliteit
- ✅ **Security**: Apply OWASP best practices
- ✅ **Performance**: Optimize voor production gebruik
- ✅ **Maintainability**: Code moet leesbaar en onderhoudbaar zijn
- ✅ **Scalability**: Design voor groei (1 user → 100K users)

---

## 📋 Project Overview

### Mission Statement
Bouw een **enterprise-grade, multi-tenant RAG applicatie** voor BBL (Besluit Bouwwerken Leefomgeving) documenten die:
- Schaalbaar is van 10 tot 100,000+ gebruikers
- Volledige data-isolatie garandeert per project/organization
- Moderne security best practices volgt
- Excellent developer experience biedt
- Production-ready is vanaf dag 1

### Core Requirements

**Functional Requirements:**
1. **Multi-Tenancy**: Gebruikers kunnen lid zijn van meerdere "projects" (organizations)
2. **Project-Based Permissions**: Per project kunnen admins users uitnodigen met verschillende roles (Admin, Member, Viewer)
3. **Document Management**: Upload en verwerk BBL documenten (PDF, DOCX, TXT, XML)
4. **Intelligent Search**: Semantic vector search met relevantie ranking
5. **Chat Interface**: Conversational RAG met conversation history en inline citations
6. **Real-time Collaboration**: Meerdere users kunnen tegelijkertijd in hetzelfde project werken

**Non-Functional Requirements:**
1. **Security**: Enterprise-grade authentication, authorization, en data isolation
2. **Performance**: Query response time < 3 seconden, document upload < 30 seconden
3. **Scalability**: Horizontaal schaalbaar, stateless waar mogelijk
4. **Reliability**: 99.9% uptime, graceful error handling
5. **Maintainability**: Clean code, well-documented, testable
6. **Cost-Efficiency**: Optimize voor serverless/managed services

### Tech Stack Decisions (With Rationale)

**Frontend Framework: Next.js 14+ (App Router)**
- **Why**: React Server Components, streaming, built-in API routes, excellent DX
- **Alternative Considered**: Separate React app - rejected (extra complexity)
- **Critical**: Use App Router (not Pages Router) for modern patterns

**Database: PostgreSQL with pgvector**
- **Why**: ACID compliance, proven scale, pgvector extension for unified data storage
- **Alternative Considered**: Separate vector DB (Qdrant/Pinecone) - rejected (sync issues)
- **Critical**: Use managed service (Supabase) for ops simplicity

**Authentication: Clerk**
- **Why**: Organizations feature = multi-tenancy out-of-the-box, excellent DX
- **Alternative Considered**: Supabase Auth - valid alternative (cheaper, more work)
- **Critical**: Must support project-based permissions natively

**ORM: Prisma**
- **Why**: Type-safe queries, excellent DX, auto-migrations
- **Alternative Considered**: Drizzle - valid alternative (lighter)
- **Critical**: TypeScript-first, must generate types from schema

**LLM Provider: OpenAI**
- **Why**: Best-in-class GPT-4, reliable API, good rate limits
- **Alternative Considered**: Anthropic Claude - valid alternative
- **Critical**: Must support streaming responses

**Deployment: Vercel**
- **Why**: Zero-config Next.js deployment, edge functions, preview deploys
- **Alternative Considered**: AWS/Railway - valid alternatives
- **Critical**: Must support serverless functions with reasonable timeout

---

## 🏗️ Architecture Principles

### 1. Multi-Tenancy Architecture

**Pattern: Row-Level Security (RLS)**
- Database enforces data isolation, NOT application code
- Every table has `organization_id` foreign key
- PostgreSQL RLS policies automatically filter queries
- JWT contains `org_id` claim for auth context

**Why This Matters:**
- Security: Impossible to leak data across organizations (DB enforces it)
- Performance: Indexes on `organization_id` ensure fast queries
- Simplicity: Application code doesn't need tenant filtering logic

**Implementation Requirements:**
1. Design database schema with `organization_id` on all tenant-specific tables
2. Create RLS policies that filter based on JWT claims
3. Ensure JWT template includes `org_id` and `org_role`
4. Add indexes on `organization_id` columns
5. Test cross-tenant data access (should fail)

### 2. Vector Search Architecture

**Pattern: Hybrid Search (Vector + Full-Text)**
- Combine semantic similarity (pgvector) with keyword matching (PostgreSQL FTS)
- Weight: 70% vector, 30% full-text (tune based on testing)
- Both searches filter by `organization_id` first

**Why This Matters:**
- Accuracy: Hybrid search improves recall by 20-30% vs pure vector
- Flexibility: Catches exact matches (artikel numbers, legal terms)
- Performance: Single database query, no separate vector DB

**Implementation Requirements:**
1. Create `vector(3072)` column for embeddings (OpenAI text-embedding-3-large)
2. Create HNSW index on embedding column for fast similarity search
3. Add `tsvector` generated column for full-text search (Dutch language)
4. Create GIN index on tsvector column
5. Write query that combines both search methods with weighted scoring
6. Benchmark: Compare pure vector vs hybrid on test queries

**Critical Decision Point: Vector Dimensions**
- OpenAI text-embedding-3-large = 3072 dimensions
- Consider: Can reduce to 1536 if storage is concern (test impact on accuracy)
- Monitor: Index size vs query performance trade-off

### 3. RAG Pipeline Architecture

**Pattern: Retrieval → Rerank → Generate**
1. **Retrieve**: Get top 15 candidates via hybrid search
2. **Rerank**: Filter by relevance threshold (0.65 high, 0.40 fallback)
3. **Generate**: Build context, call LLM with structured prompt

**Why This Matters:**
- Quality: Filtering low-relevance chunks improves answer quality
- Cost: Fewer tokens sent to LLM = lower cost
- Speed: Smaller context = faster LLM response

**Implementation Requirements:**
1. Design retrieval to get 3x topK candidates
2. Apply relevance scoring (similarity + metadata matching)
3. Filter based on threshold (configurable)
4. Build context with citation markers [1], [2], [3]
5. Structure prompt: System (role) → Context → Query
6. Handle edge cases: No results, low relevance results

**Critical Considerations:**
- **Chunking Strategy**: 800 chars with 100 char overlap (tune for BBL)
- **Context Window**: Max 8K tokens for GPT-4 (monitor token usage)
- **Citation Accuracy**: Ensure [1] references match returned sources
- **Hallucination Prevention**: Instruct LLM to only use provided context

### 4. Authentication & Authorization Architecture

**Pattern: JWT + Organizations + RLS**
- Clerk issues JWT with `org_id` and `org_role` claims
- Application passes JWT to Supabase in Authorization header
- Supabase extracts `org_id` from JWT and applies RLS policies
- No application-level permission checks needed (DB handles it)

**Why This Matters:**
- Security: Single source of truth (database)
- Performance: No extra queries to check permissions
- Simplicity: Application code is cleaner

**Implementation Requirements:**
1. Configure Clerk JWT template with required claims
2. Configure Supabase to trust Clerk JWTs (JWKS URL)
3. Create SQL function to extract `user_id` from JWT
4. Write RLS policies using extracted `user_id`
5. Test: Verify users can only see their org's data

**Role Definitions:**
- **ADMIN**: Full access, can invite/remove members, manage settings
- **MEMBER**: Can create content (upload docs, query, chat)
- **VIEWER**: Read-only access (query and chat only)

---

## 📦 Phase 1: Project Initialization

**Goal**: Setup modern Next.js project with all required tooling

### Requirements

**1.1 Initialize Next.js Project**
- Use `create-next-app` with latest Next.js version
- Enable TypeScript (strict mode)
- Enable Tailwind CSS
- Use App Router (not Pages Router)
- Set up src directory structure
- Configure import alias `@/*`

**1.2 Install Core Dependencies**
- Authentication: Clerk SDK
- Database: Prisma ORM, Supabase client
- LLM: OpenAI SDK
- UI: shadcn/ui components (or similar modern component library)
- Validation: Zod for runtime type checking
- Utilities: date-fns, clsx, tailwind-merge

**1.3 Configure Development Environment**
- Setup ESLint with strict rules
- Setup Prettier with consistent formatting
- Configure TypeScript with strict mode
- Setup environment variables (.env.local, .env.example)
- Configure Git ignore (node_modules, .env.local, .next)

**1.4 Setup Project Structure**
```
src/
├── app/                    # Next.js App Router
├── components/             # React components
├── lib/                    # Business logic, utilities
├── types/                  # TypeScript type definitions
└── prisma/                 # Database schema
```

### Acceptance Criteria
- ✅ `npm run dev` starts development server without errors
- ✅ TypeScript compilation succeeds with strict mode
- ✅ Tailwind CSS classes work in components
- ✅ Environment variables can be loaded
- ✅ Hot reload works for code changes

### Critical Checkpoints
1. **TypeScript Strict Mode**: Verify `strict: true` in tsconfig.json
2. **Import Aliases**: Test that `@/components/...` imports work
3. **Build Success**: Run `npm run build` to verify production build works

---

## 🗄️ Phase 2: Database & Authentication

**Goal**: Setup PostgreSQL with pgvector, Prisma ORM, and Clerk authentication

### 2.1 Supabase PostgreSQL Setup

**Requirements:**
1. Create Supabase project (managed PostgreSQL)
2. Enable pgvector extension
3. Configure connection pooling
4. Get connection strings (direct and pooled)

**Critical Decisions:**
- **Region**: Choose closest to users (West Europe for Netherlands)
- **Plan**: Start with Pro ($25/mo) for sufficient resources
- **Pooler Mode**: Use Transaction mode for Prisma

**Security Checklist:**
- ✅ Store connection strings in `.env.local`, never commit
- ✅ Use different databases for development/staging/production
- ✅ Rotate passwords periodically

### 2.2 Database Schema Design

**Core Entities:**

**Organizations** (Projects)
- Represents a "project" or "team"
- Has name, slug (URL-friendly), settings (JSON)
- Relationships: members, documents, embeddings, chat sessions

**Memberships** (User-Organization junction)
- Links users to organizations with roles
- Has user_id (Clerk ID), organization_id, role (ADMIN/MEMBER/VIEWER)
- Unique constraint on (user_id, organization_id)

**Documents**
- Represents uploaded files
- Has filename, file_type, file_size, uploaded_by, metadata (JSON)
- Belongs to organization
- Relationships: embeddings

**Embeddings** (Vector Store)
- Represents text chunks with embeddings
- Has chunk_text (TEXT), embedding (vector(3072)), chunk_index
- Belongs to document and organization
- Has metadata (JSON) for BBL-specific info

**ChatSessions**
- Represents conversation threads
- Has title, created_at, updated_at
- Belongs to user and organization
- Relationships: messages

**ChatMessages**
- Represents individual messages
- Has role (USER/ASSISTANT), content (TEXT), sources (JSON)
- Belongs to chat session

**Schema Requirements:**
1. All tenant-specific tables MUST have `organization_id`
2. Add indexes on `organization_id` for performance
3. Add indexes on frequently queried columns
4. Use `cuid()` for IDs (better than UUID for sorting)
5. Use `@map()` for snake_case database column names

**Critical Considerations:**
- **Vector Column Type**: Use `Unsupported("vector(3072)")` in Prisma
- **JSON Columns**: Use `Json` type for flexible metadata
- **Timestamps**: Use `@default(now())` and `@updatedAt`
- **Cascading Deletes**: Configure `onDelete: Cascade` for cleanup

### 2.3 Row Level Security (RLS) Policies

**Requirements:**

**Enable RLS on all tables**
- Organizations, memberships, documents, embeddings, chat_sessions, chat_messages

**Create helper function**
- SQL function to extract `user_id` from JWT: `auth.user_id()`
- Uses `current_setting('request.jwt.claims')` to parse JWT

**Create policies for each table:**

**Organizations:**
- SELECT: Users can see organizations they're member of
- Subquery: `WHERE id IN (SELECT organization_id FROM memberships WHERE user_id = auth.user_id())`

**Documents:**
- SELECT: Users can see documents in their organizations
- INSERT: Only ADMIN and MEMBER can upload
- DELETE: Only uploader or ADMIN can delete

**Embeddings:**
- SELECT: Users can see embeddings in their organizations
- INSERT: Only ADMIN and MEMBER (during document upload)

**Chat Sessions:**
- SELECT: Users can see sessions in their organizations
- INSERT: All members can create sessions
- DELETE: Only session owner can delete

**Chat Messages:**
- SELECT: Users can see messages in their sessions
- INSERT: All members can add messages

**Testing Requirements:**
1. Test as different users with different roles
2. Verify cross-organization access is blocked
3. Test permission boundaries (VIEWER can't upload, etc.)

### 2.4 Prisma ORM Setup

**Requirements:**
1. Create `prisma/schema.prisma` with models matching design
2. Configure PostgreSQL provider with pgvector extension
3. Use `directUrl` for migrations (bypasses pooler)
4. Generate Prisma Client: `npx prisma generate`
5. Create initial migration: `npx prisma migrate dev --name init`

**Prisma Client Singleton Pattern:**
- Create `lib/prisma.ts` with singleton instance
- Prevent multiple instances in development (hot reload issue)
- Log queries in development, errors only in production

**Testing Requirements:**
- ✅ Prisma Studio connects: `npx prisma studio`
- ✅ Can create records via Prisma Client
- ✅ Generated types work in TypeScript

### 2.5 Clerk Authentication Setup

**Requirements:**

**Create Clerk Application:**
1. Enable Organizations feature
2. Configure sign-in/sign-up options (Email required, optional: Google OAuth)
3. Set up JWT template with custom claims
4. Configure redirect URLs

**JWT Template Configuration:**
```json
{
  "sub": "{{user.id}}",
  "email": "{{user.primary_email_address}}",
  "org_id": "{{org.id}}",
  "org_role": "{{org.role}}",
  "org_slug": "{{org.slug}}"
}
```

**Next.js Integration:**
1. Wrap root layout with `<ClerkProvider>`
2. Create sign-in/sign-up pages using Clerk components
3. Protect routes using `auth()` helper
4. Access organization context via `auth()` in Server Components

**Webhook Setup (Optional but Recommended):**
- Sync user creation to your database
- Handle organization membership changes
- Endpoint: `/api/webhook/clerk`

**Testing Requirements:**
- ✅ Sign up flow works (create account)
- ✅ Sign in flow works (login with existing account)
- ✅ Session persists after page refresh
- ✅ Logout works (clears session)
- ✅ Organization context available in auth()

**Critical Security Checks:**
1. Verify JWT signature validation works
2. Test expired token handling
3. Verify organization context is correct
4. Test permission checks (ADMIN vs MEMBER vs VIEWER)

### 2.6 Integration Testing

**Test Scenarios:**

**Scenario 1: New User Journey**
1. User signs up
2. User creates organization
3. User becomes admin of organization
4. User can access organization data
5. RLS policies allow access

**Scenario 2: Multi-Organization Access**
1. User A is member of Org 1 and Org 2
2. Switch active organization
3. Verify data filtering changes
4. Confirm cannot see Org 3 data

**Scenario 3: Permission Boundaries**
1. VIEWER cannot upload documents (403 error)
2. MEMBER can upload documents (success)
3. ADMIN can delete other's documents (success)
4. MEMBER cannot delete other's documents (403 error)

**Write Automated Tests:**
- Use testing library of choice (Jest, Vitest)
- Test database queries with test database
- Mock Clerk auth in tests

---

## 📄 Phase 3: Document Processing Pipeline

**Goal**: Implement document upload, text extraction, chunking, and embedding generation

### 3.1 Document Upload API

**Endpoint:** `POST /api/documents/upload`

**Requirements:**

**Input Validation:**
1. Accept multipart/form-data with file
2. Validate file type: PDF, DOCX, TXT, XML only
3. Validate file size: Max 10MB (configurable)
4. Sanitize filename (prevent path traversal)
5. Check user has ADMIN or MEMBER role in organization

**File Storage Strategy:**
- **Option A**: Store file blob in PostgreSQL (simple but not ideal for large files)
- **Option B**: Upload to Supabase Storage, store URL in database (recommended)
- **Critical**: Choose based on expected file sizes and access patterns

**Security Checklist:**
- ✅ Validate Content-Type header matches file extension
- ✅ Sanitize filename (remove special characters, path separators)
- ✅ Scan for malware (optional: use third-party service)
- ✅ Rate limit upload endpoint (max 10 uploads per minute per user)

### 3.2 Text Extraction

**Requirements:**

**Implement extractors for each file type:**

**PDF Extraction:**
- Library choice: pdf-parse, pdfjs-dist, or similar
- Extract text page by page
- Preserve structure where possible
- Handle scanned PDFs (warn if no text extracted)

**DOCX Extraction:**
- Library choice: mammoth, docx, or similar
- Extract paragraphs and tables
- Preserve formatting hints (bold, headings) in metadata

**TXT Extraction:**
- Simple: read file as UTF-8 text
- Handle different encodings if needed (UTF-8, Latin-1)

**XML Extraction (BBL-Specific):**
- Parse BWB XML structure
- Extract articles (artikelen) with hierarchy
- Preserve legal structure (hoofdstuk, paragraaf, artikel)
- Extract metadata: artikel number, title, content

**Critical Considerations:**
- **Error Handling**: What if extraction fails? Return 400 with clear error
- **Performance**: Use streaming for large files
- **Memory**: Don't load entire file in memory (buffer/stream)
- **Timeouts**: Set reasonable timeout (5 minutes for large files)

**Testing Requirements:**
1. Test with sample files of each type
2. Test with corrupted files (should fail gracefully)
3. Test with empty files (should return error)
4. Test with very large files (should handle or reject with size limit)

### 3.3 Text Chunking Strategy

**Requirements:**

**Chunking Algorithm:**
- **Default Strategy**: Fixed-size chunks with overlap
  - Chunk size: 800 characters
  - Overlap: 100 characters
  - Rationale: Balance between context and granularity

- **Alternative Strategy**: Sentence-based chunking
  - Keep sentences intact
  - Max chunk size: 800 characters
  - Combine sentences until limit reached

- **BBL-Specific Strategy**: Article-based chunking
  - 1 artikel = 1 chunk
  - Preserves legal structure
  - Better for citation accuracy

**Chunk Metadata:**
- Store chunk index (order in document)
- Store character offset (start, end)
- For BBL: Store artikel number, chapter, section

**Critical Decisions:**
- **Chunk Size Tuning**: Test with 400, 800, 1200 chars - measure accuracy
- **Overlap Necessity**: Test with 0, 100, 200 char overlap - measure recall
- **Language-Specific**: Dutch text may have different optimal chunk size

**Implementation Requirements:**
1. Create chunking function with configurable parameters
2. Return chunks with metadata
3. Handle edge cases: Text shorter than chunk size
4. Preserve enough context for meaningful search

### 3.4 Embedding Generation

**Requirements:**

**OpenAI Embeddings API:**
- Model: `text-embedding-3-large` (3072 dimensions)
- Batch processing: Up to 2048 texts per request
- Handle rate limits (retry with exponential backoff)
- Cache embeddings to avoid regeneration

**Embedding Pipeline:**
1. Take array of chunk texts
2. Split into batches of 2048
3. Call OpenAI API for each batch
4. Combine results
5. Return array of embedding vectors

**Error Handling:**
- API rate limit: Retry with exponential backoff (2s, 4s, 8s, 16s)
- API failure: Return error to user, don't save partial embeddings
- Network timeout: Set 60s timeout, retry once

**Cost Optimization:**
- **Embedding Cache**: Store hash of text → embedding mapping
- Check cache before calling API
- Avoid regenerating for identical text

**Implementation Requirements:**
1. Create embedding generation function
2. Implement batching logic
3. Add retry mechanism
4. Format embeddings for pgvector (array → `[1,2,3...]` string)

**Testing Requirements:**
- Test with single text
- Test with 3000 texts (multiple batches)
- Test error handling (mock API failure)
- Measure cost: Log token usage

### 3.5 Database Storage

**Requirements:**

**Transaction Handling:**
- Wrap entire operation in transaction
- If any step fails, rollback everything
- Steps: Create document → Create embeddings → Commit

**Batch Insert Optimization:**
- Use `$executeRaw` for bulk insert of embeddings
- Insert in batches of 1000 for performance
- Use prepared statements to prevent SQL injection

**Implementation:**
1. Create document record (get document_id)
2. For each chunk:
   - Insert embedding record with document_id
   - Use RAW SQL for pgvector column: `embedding::vector`
3. Commit transaction

**Testing Requirements:**
- Test successful upload (verify all embeddings inserted)
- Test failed extraction (verify no partial data)
- Test database constraint violations

### 3.6 API Response

**Success Response:**
```typescript
{
  success: true,
  document: {
    id: string,
    filename: string,
    chunksCount: number,
    processingTime: number (ms)
  }
}
```

**Error Responses:**
- 400: Invalid file type, file too large, extraction failed
- 401: Unauthorized (not logged in)
- 403: Forbidden (wrong role)
- 500: Internal server error (unexpected failure)

**Implementation Requirements:**
- Use Zod for response schema validation
- Include processing time for monitoring
- Log errors with context (user_id, org_id, filename)

### 3.7 List Documents API

**Endpoint:** `GET /api/documents`

**Requirements:**
1. Return all documents for current organization
2. Order by created_at DESC (newest first)
3. Include chunk count for each document
4. Paginate if needed (optional for MVP)

**Response Schema:**
```typescript
{
  documents: [{
    id: string,
    filename: string,
    fileType: string,
    fileSize: number,
    uploadedBy: string,
    createdAt: string (ISO8601),
    chunksCount: number
  }]
}
```

**Performance Optimization:**
- Use `include: { _count: { select: { embeddings: true } } }` for count
- Add index on (organization_id, created_at)

### 3.8 Delete Document API

**Endpoint:** `DELETE /api/documents/:id`

**Requirements:**
1. Verify user has permission (ADMIN or document owner)
2. Delete document record (cascading delete handles embeddings)
3. Return success confirmation

**Security Checks:**
- Verify document belongs to current organization
- Verify user is ADMIN or uploaded the document
- RLS policies provide additional safety layer

---

## 🔍 Phase 4: RAG Query Pipeline

**Goal**: Implement intelligent search with hybrid vector+full-text search and LLM answer generation

### 4.1 Query API Design

**Endpoint:** `POST /api/query`

**Input Schema:**
```typescript
{
  query: string,      // User's question (1-500 chars)
  topK?: number       // Number of sources to return (1-20, default: 5)
}
```

**Output Schema:**
```typescript
{
  answer: string,           // LLM-generated answer
  sources: [{               // Retrieved source chunks
    id: string,
    text: string,
    similarity: number,     // 0-1 relevance score
    metadata: object,       // Chunk metadata
    document: {
      id: string,
      filename: string
    }
  }],
  processingTime: number    // Total time in ms
}
```

**Requirements:**
1. Validate input (query not empty, topK in range)
2. Check user authentication and organization context
3. Execute RAG pipeline
4. Return structured response
5. Log query for analytics (optional)

### 4.2 Vector Similarity Search

**Requirements:**

**pgvector Cosine Similarity:**
- Operator: `<=>` (cosine distance, lower = more similar)
- Convert to similarity: `1 - (embedding <=> query_embedding)`
- Filter by organization_id FIRST (use index)
- Order by similarity DESC
- Limit to topK * 3 (get more candidates for reranking)

**SQL Query Structure:**
```sql
SELECT
  id, chunk_text, document_id, metadata,
  1 - (embedding <=> [query_embedding]::vector) as similarity
FROM embeddings
WHERE organization_id = ?
ORDER BY embedding <=> [query_embedding]::vector
LIMIT ?
```

**Performance Optimization:**
- Ensure HNSW index exists on embedding column
- Index parameters: `m = 16, ef_construction = 64` (tune based on data size)
- Monitor query time (should be < 100ms for 10K embeddings)

**Implementation Requirements:**
1. Generate query embedding (OpenAI API)
2. Format embedding for pgvector (`[1,2,3...]::vector`)
3. Execute raw SQL query via Prisma
4. Parse results into TypeScript types

### 4.3 Full-Text Search (Dutch)

**Requirements:**

**PostgreSQL FTS Configuration:**
- Language: Dutch ('dutch' config)
- Operator: `@@` (matches)
- Ranking: `ts_rank()` for scoring
- Query: `plainto_tsquery('dutch', query)` (simple query parsing)

**Implementation:**
1. Add `tsvector` generated column (if not already added in Phase 2)
2. Create GIN index on tsvector column
3. Query: Match on search_vector, rank by ts_rank()
4. Filter by organization_id

**SQL Query Structure:**
```sql
SELECT
  id, chunk_text, document_id, metadata,
  ts_rank(search_vector, plainto_tsquery('dutch', ?)) as fts_score
FROM embeddings
WHERE organization_id = ?
  AND search_vector @@ plainto_tsquery('dutch', ?)
ORDER BY fts_score DESC
LIMIT ?
```

### 4.4 Hybrid Search Combination

**Requirements:**

**Combine vector and FTS results:**
- Vector weight: 0.7 (70%)
- FTS weight: 0.3 (30%)
- Combined score: `vector_score * 0.7 + fts_score * 0.3`

**SQL Implementation (CTE pattern):**
```sql
WITH vector_results AS (...),
     fts_results AS (...)
SELECT
  e.*,
  COALESCE(v.vector_score, 0) * 0.7 +
  COALESCE(f.fts_score, 0) * 0.3 as combined_score
FROM embeddings e
LEFT JOIN vector_results v ON e.id = v.id
LEFT JOIN fts_results f ON e.id = f.id
WHERE organization_id = ?
  AND (v.id IS NOT NULL OR f.id IS NOT NULL)
ORDER BY combined_score DESC
LIMIT ?
```

**Critical Decisions:**
- **Weight Tuning**: Test different ratios (0.5/0.5, 0.6/0.4, 0.7/0.3, 0.8/0.2)
- **Performance**: Hybrid search adds ~50ms vs pure vector, worth it for accuracy
- **Fallback**: If FTS returns no results, fall back to pure vector

**Implementation Requirements:**
1. Implement both search methods
2. Combine with weighted scoring
3. Return top K results after scoring
4. Include join with documents table for metadata

### 4.5 Relevance Filtering

**Requirements:**

**Two-Tier Thresholding:**
- **High Relevance**: similarity >= 0.65 (confident results)
- **Medium Relevance**: similarity >= 0.40 (fallback)

**Logic:**
1. Get all results with similarity >= 0.40
2. Prefer high relevance (>= 0.65)
3. If < topK high relevance results, include medium relevance (up to topK total)
4. If no results >= 0.40, return "no relevant documents found" message

**Edge Cases:**
- Zero results: Return message, don't call LLM
- Only low-relevance results: Warn user "limited confidence in results"
- Very high relevance (> 0.90): Highlight as "exact match"

**Testing Requirements:**
- Test with queries that should match (high similarity)
- Test with queries that shouldn't match (low similarity)
- Test threshold boundaries (0.64, 0.65, 0.66)

### 4.6 Context Building

**Requirements:**

**Format for LLM:**
```
[1] {chunk_text}
Bron: {filename}

[2] {chunk_text}
Bron: {filename}

...
```

**Context Limits:**
- GPT-4 context window: 128K tokens
- Target: Use ~4K tokens for context (leave room for response)
- Calculate: ~3 chars per token, 800 chars per chunk → ~5-6 chunks safe

**Implementation Requirements:**
1. Take top K results from hybrid search
2. Format each with citation number [1], [2], etc.
3. Include source metadata (filename, artikel number if BBL)
4. Concatenate with double newline separator
5. Calculate token count (rough estimate)

**Metadata Inclusion:**
For BBL documents, include:
- Artikel number
- Chapter/section
- Document filename

### 4.7 LLM Answer Generation

**Requirements:**

**System Prompt Design:**
```
Je bent een expert assistent voor het Besluit Bouwwerken Leefomgeving (BBL).

Taak:
- Beantwoord vragen over bouwregelgeving op basis van de verstrekte context
- Verwijs naar bronnen met [1], [2], etc.
- Als context het antwoord niet bevat, geef dat eerlijk aan
- Wees precies en specifiek
- Gebruik Nederlandse taal en BBL-terminologie

Context:
{formatted_context}
```

**LLM Parameters:**
- Model: `gpt-4-turbo-preview` or `gpt-4`
- Temperature: 0.3 (low for factual answers)
- Max tokens: 1000 (allow detailed answers)
- Top_p: 1.0
- Stop: null

**Message Structure:**
1. System message: Role definition + context
2. User message: Query

**Critical Considerations:**
- **Hallucination Prevention**: Emphasize "only use provided context"
- **Citation Accuracy**: Verify LLM uses correct citation numbers
- **Dutch Language**: Explicitly request Dutch responses
- **Tone**: Professional, helpful, precise

**Error Handling:**
- LLM API failure: Return error, don't show partial response
- Rate limit: Retry with exponential backoff
- Timeout: Set 30s timeout

### 4.8 Response Formatting

**Requirements:**

**Parse LLM Response:**
- Extract answer text
- Verify citations [1], [2] exist in answer
- Match citations to source chunks

**Build Response Object:**
```typescript
{
  answer: string,          // LLM response
  sources: [{              // Mapped sources
    id: string,
    text: string,          // Original chunk text
    similarity: number,
    metadata: {...},
    document: {...}
  }],
  processingTime: number   // End-to-end time
}
```

**Implementation Requirements:**
1. Time entire operation (start to finish)
2. Return sources in order of citation [1], [2], ...
3. Include processing time for monitoring
4. Log slow queries (> 5 seconds) for optimization

### 4.9 Testing & Validation

**Test Scenarios:**

**Scenario 1: Exact Match Query**
- Query: "Wat is artikel 3.44?"
- Expected: High similarity (> 0.85), article 3.44 text returned

**Scenario 2: Semantic Query**
- Query: "Wat zijn de eisen voor brandveiligheid in woningen?"
- Expected: Multiple relevant articles, properly ranked

**Scenario 3: No Match Query**
- Query: "Hoe maak ik een goede koffie?"
- Expected: "Geen relevante informatie gevonden" message

**Scenario 4: Multi-Organization Isolation**
- Org A has document X
- Org B queries for content in document X
- Expected: No results (RLS blocks cross-org access)

**Automated Tests:**
1. Unit test: Vector search function
2. Unit test: FTS search function
3. Unit test: Hybrid combination logic
4. Integration test: Full RAG pipeline
5. Performance test: Query response time < 3s

**Metrics to Track:**
- Query latency (p50, p95, p99)
- Relevance accuracy (manual evaluation)
- Citation accuracy (citations match sources)
- Token usage (OpenAI cost tracking)

---

## ✅ Phase Completion Checklist

### Phase 1: Project Initialization
- [ ] Next.js project created with TypeScript + Tailwind
- [ ] All dependencies installed (latest versions)
- [ ] ESLint + Prettier configured
- [ ] Environment variables setup
- [ ] Development server runs without errors
- [ ] Production build succeeds

### Phase 2: Database & Authentication
- [ ] Supabase project created
- [ ] pgvector extension enabled
- [ ] Prisma schema defined with all models
- [ ] RLS policies created and tested
- [ ] Clerk authentication integrated
- [ ] JWT template configured with org claims
- [ ] Sign-in/sign-up flows work
- [ ] Multi-organization access tested
- [ ] Permission boundaries tested

### Phase 3: Document Processing
- [ ] Document upload API endpoint works
- [ ] Text extraction for all file types (PDF, DOCX, TXT, XML)
- [ ] Text chunking implemented and tested
- [ ] Embedding generation works (OpenAI)
- [ ] Embeddings stored in pgvector
- [ ] Document list API works
- [ ] Document delete API works
- [ ] End-to-end upload test succeeds
- [ ] Performance acceptable (< 30s for typical document)

### Phase 4: RAG Query
- [ ] Query API endpoint works
- [ ] Vector similarity search returns results
- [ ] Full-text search works (Dutch)
- [ ] Hybrid search combines both methods
- [ ] Relevance filtering applied
- [ ] Context building formats correctly
- [ ] LLM generates relevant answers
- [ ] Citations accurate
- [ ] Response time acceptable (< 3s)
- [ ] Multi-organization isolation works

---

## 🚨 Critical Success Factors

### Must-Haves for Production
1. **Security**: RLS policies prevent data leakage
2. **Performance**: Query response < 3s, upload < 30s
3. **Accuracy**: Hybrid search + relevance filtering
4. **Reliability**: Error handling, retries, logging
5. **Type Safety**: TypeScript strict mode, Zod validation

### Nice-to-Haves (Can be Phase 5-7)
- Streaming LLM responses
- Query caching
- Advanced BBL metadata extraction
- Reranking with LLM
- Analytics dashboard

### What NOT to Build (Yet)
- Admin analytics (Phase 5)
- User management UI (Phase 5)
- Chat interface (Phase 6)
- Advanced features (Phase 7)

---

## 📊 Success Metrics

**Track These KPIs:**
1. **Query Accuracy**: Manual evaluation of answer quality (target: > 85% helpful)
2. **Query Latency**: P95 response time (target: < 3 seconds)
3. **Upload Success Rate**: % of successful uploads (target: > 95%)
4. **Search Recall**: % of relevant documents retrieved (target: > 80%)
5. **Cost Efficiency**: $ per query (OpenAI + infrastructure)

**Monitoring Requirements:**
- Log all API requests with timing
- Track OpenAI token usage
- Monitor database query performance
- Alert on error rate > 5%

---

## 📝 Documentation Requirements

**Document These Decisions:**
1. Why hybrid search over pure vector?
2. Why Clerk over Supabase Auth?
3. Why pgvector over separate Qdrant?
4. Chunk size choice (800 chars) - rationale
5. Relevance threshold choice (0.65/0.40) - rationale

**Code Documentation:**
- Add JSDoc comments to all public functions
- Document complex algorithms (hybrid search query)
- Add README with setup instructions
- Document environment variables

---

## 🎯 Next Steps

**After Part 1 Completion:**
- You'll have a working backend with document upload and RAG query
- Part 2 will cover: Frontend UI, Chat interface, Advanced features, Deployment

**Before Starting Part 2:**
1. Test all Phase 1-4 functionality thoroughly
2. Deploy to staging environment
3. Get feedback on query quality
4. Tune parameters (chunk size, thresholds, weights)

---

**Ready to start implementing? Begin with Phase 1!**
