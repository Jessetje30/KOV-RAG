# KOV-RAG Greenfield Implementation Plan
**Voor: Claude Code (AI Developer)**

Dit is een complete, stap-voor-stap implementation guide voor het bouwen van een moderne RAG applicatie voor BBL (Besluit Bouwwerken Leefomgeving) documenten met multi-project support en project-based permissions.

---

## 📋 Project Overview

### Wat gaan we bouwen?

Een **multi-tenant RAG (Retrieval-Augmented Generation) applicatie** waar:
- **Gebruikers** toegang hebben tot **meerdere projecten** (organizations)
- **Project Admins** andere users kunnen **uitnodigen** per project
- **BBL documenten** (PDF, DOCX, XML) kunnen worden **geüpload** per project
- **Intelligente queries** gesteld kunnen worden met **semantische zoekfunctie**
- **Chat interface** beschikbaar is met **conversationele RAG** en **inline citaties**
- **Data volledig geïsoleerd** is per project (multi-tenancy)

### Tech Stack

```yaml
Frontend:       Next.js 14 (App Router) + React 18 + TypeScript + Tailwind CSS
Backend:        Next.js API Routes (serverless functions)
Database:       PostgreSQL (Supabase managed)
ORM:            Prisma (type-safe queries)
Vector Store:   pgvector (PostgreSQL extension)
Auth:           Clerk (Organizations + Invitations)
LLM:            OpenAI GPT-4 + text-embedding-3-large
RAG Framework:  LangChain.js (optional: can be custom)
UI Components:  shadcn/ui (Radix UI + Tailwind)
Deployment:     Vercel (frontend + API routes)
```

### Project Structure

```
kov-rag/
├── .env.local                   # Environment variables (local)
├── .env.example                 # Environment template
├── next.config.js               # Next.js configuration
├── tailwind.config.ts           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies
│
├── prisma/
│   ├── schema.prisma           # Database schema
│   └── migrations/             # Database migrations
│
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout (Clerk provider)
│   │   ├── page.tsx            # Landing page
│   │   │
│   │   ├── (auth)/             # Auth routes
│   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   └── sign-up/[[...sign-up]]/page.tsx
│   │   │
│   │   ├── (dashboard)/        # Protected dashboard routes
│   │   │   ├── layout.tsx      # Dashboard layout (sidebar)
│   │   │   ├── page.tsx        # Dashboard home (redirect to query)
│   │   │   ├── query/page.tsx  # Query interface
│   │   │   ├── chat/page.tsx   # Chat interface
│   │   │   ├── documents/page.tsx  # Document management
│   │   │   └── admin/page.tsx  # Admin panel
│   │   │
│   │   └── api/                # API routes
│   │       ├── documents/
│   │       │   ├── upload/route.ts
│   │       │   ├── list/route.ts
│   │       │   └── [id]/delete/route.ts
│   │       ├── query/route.ts
│   │       ├── chat/
│   │       │   ├── sessions/route.ts
│   │       │   └── query/route.ts
│   │       └── webhook/
│   │           └── clerk/route.ts
│   │
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui components (Button, Input, etc.)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   ├── query/
│   │   │   ├── QueryForm.tsx
│   │   │   ├── QueryResults.tsx
│   │   │   ├── SourceCard.tsx
│   │   │   └── ExampleQuestions.tsx
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ChatSessions.tsx
│   │   ├── documents/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── DocumentCard.tsx
│   │   └── admin/
│   │       ├── InviteUser.tsx
│   │       └── MembersList.tsx
│   │
│   ├── lib/                    # Utilities and helpers
│   │   ├── prisma.ts           # Prisma client singleton
│   │   ├── openai.ts           # OpenAI client
│   │   ├── rag/
│   │   │   ├── embeddings.ts   # Embedding generation
│   │   │   ├── vectorSearch.ts # pgvector search
│   │   │   ├── chunking.ts     # Text chunking
│   │   │   ├── extraction.ts   # Document text extraction (PDF, DOCX, XML)
│   │   │   ├── bbl-parser.ts   # BBL XML specific parsing
│   │   │   └── query.ts        # RAG query pipeline
│   │   ├── permissions.ts      # Permission helpers
│   │   └── utils.ts            # Generic utilities
│   │
│   └── types/                  # TypeScript type definitions
│       ├── database.ts         # Database types
│       ├── api.ts              # API request/response types
│       └── rag.ts              # RAG-specific types
│
└── public/                     # Static assets
    └── images/
```

### Timeline

**Total: 10-12 weken (2-3 maanden)**

- **Phase 1:** Project Setup (Week 1) - 1 week
- **Phase 2:** Database & Auth (Week 2) - 1 week
- **Phase 3:** Document Processing (Week 3-4) - 2 weken
- **Phase 4:** RAG Pipeline (Week 5-6) - 2 weken
- **Phase 5:** Frontend UI (Week 7-9) - 3 weken
- **Phase 6:** Advanced Features (Week 10-11) - 2 weken
- **Phase 7:** Testing & Deployment (Week 12) - 1 week

---

## ✅ Prerequisites

### Vereiste Accounts (maak deze aan voordat je begint)

1. **Vercel Account** (https://vercel.com)
   - Gratis tier is voldoende voor development
   - Connecteer met GitHub voor auto-deployment

2. **Supabase Account** (https://supabase.com)
   - Maak een nieuw project aan
   - Noteer: `Project URL` en `anon/public key`
   - Enable pgvector extension (zie Phase 2)

3. **Clerk Account** (https://clerk.com)
   - Maak een nieuwe application aan
   - Enable Organizations feature
   - Noteer: `Publishable Key` en `Secret Key`

4. **OpenAI Account** (https://openai.com)
   - API key met credits
   - Toegang tot `gpt-4` en `text-embedding-3-large`

### Local Development Tools

```bash
# Node.js 18+ (LTS recommended)
node --version  # Should be >= 18.17.0

# npm or pnpm
npm --version   # Should be >= 9.0.0

# Git
git --version

# Code editor (VS Code recommended)
# VS Code extensions:
# - Prisma
# - Tailwind CSS IntelliSense
# - ESLint
# - Prettier
```

---

## 🚀 Phase 1: Project Setup

**Doel:** Initialiseer Next.js project met alle dependencies en configuraties

**Acceptatie Criteria:**
- ✅ Next.js 14 project draait op localhost:3000
- ✅ Tailwind CSS werkt
- ✅ TypeScript strict mode enabled
- ✅ ESLint en Prettier geconfigureerd
- ✅ Environment variables setup

### Stap 1.1: Initialiseer Next.js Project

```bash
# Maak nieuwe Next.js project met TypeScript, Tailwind, App Router
npx create-next-app@latest kov-rag \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-npm

# Navigeer naar project directory
cd kov-rag

# Open in VS Code
code .
```

**Verwachte output:** Next.js project is aangemaakt in `kov-rag/` directory

### Stap 1.2: Installeer Dependencies

```bash
# Core dependencies
npm install @clerk/nextjs @prisma/client @supabase/supabase-js openai
npm install zod react-markdown rehype-sanitize
npm install lucide-react class-variance-authority clsx tailwind-merge

# Dev dependencies
npm install -D prisma @types/node
npm install -D eslint-config-prettier prettier

# shadcn/ui CLI (voor UI components)
npx shadcn-ui@latest init -d
```

**Beantwoord shadcn prompts:**
- Style: `Default`
- Base color: `Slate`
- CSS variables: `Yes`

```bash
# Installeer shadcn components die we nodig hebben
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add toast
```

### Stap 1.3: Configureer Environment Variables

**Maak `.env.local` bestand:**
```bash
# Database
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
DIRECT_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Supabase
NEXT_PUBLIC_SUPABASE_URL="https://[YOUR-PROJECT-REF].supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="[YOUR-ANON-KEY]"

# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."
NEXT_PUBLIC_CLERK_SIGN_IN_URL="/sign-in"
NEXT_PUBLIC_CLERK_SIGN_UP_URL="/sign-up"
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL="/query"
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL="/query"

# OpenAI
OPENAI_API_KEY="sk-..."

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

**Maak `.env.example` bestand** (zonder values, voor git):
```bash
cp .env.local .env.example
# Open .env.example en verwijder alle values (behoud alleen keys)
```

**Update `.gitignore`:**
```bash
# Add to .gitignore if not already there
.env.local
.env*.local
```

### Stap 1.4: Configureer TypeScript (Strict Mode)

**Update `tsconfig.json`:**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    },
    "forceConsistentCasingInFileNames": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### Stap 1.5: Configureer Prettier

**Maak `.prettierrc` bestand:**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "printWidth": 100,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

**Maak `.prettierignore` bestand:**
```
.next
node_modules
dist
build
*.lock
package-lock.json
```

### Stap 1.6: Test Basis Setup

```bash
# Start development server
npm run dev
```

**Open browser:** http://localhost:3000

**Verwachte output:** Next.js welkomstpagina met Tailwind styling

**Acceptatie test:**
- ✅ Pagina laadt zonder errors
- ✅ Tailwind CSS werkt (tekst is gestijld)
- ✅ TypeScript compilation werkt (geen errors in terminal)

---

## 🗄️ Phase 2: Database & Authentication Setup

**Doel:** Setup PostgreSQL database met pgvector, Prisma ORM, en Clerk authentication

**Acceptatie Criteria:**
- ✅ Supabase PostgreSQL database is aangemaakt
- ✅ pgvector extension is enabled
- ✅ Prisma schema is gedefinieerd
- ✅ Database tabellen zijn aangemaakt (via Prisma migrate)
- ✅ Clerk authentication werkt (sign in/sign up)
- ✅ Clerk Organizations zijn enabled

### Stap 2.1: Supabase Setup

**In Supabase Dashboard:**

1. **Maak nieuw project:**
   - Project name: `kov-rag`
   - Database password: (genereer sterke password)
   - Region: West Europe (Amsterdam)

2. **Enable pgvector extension:**
   - Ga naar `Database` → `Extensions`
   - Zoek `vector`
   - Click `Enable`

3. **Haal connection string op:**
   - Ga naar `Settings` → `Database`
   - Copy `Connection string` (Pooler - Transaction mode)
   - Replace `[YOUR-PASSWORD]` met je database password
   - Plak in `.env.local` als `DATABASE_URL`

### Stap 2.2: Prisma Setup

**Initialiseer Prisma:**
```bash
npx prisma init
```

Dit maakt `prisma/schema.prisma` aan.

**Update `prisma/schema.prisma`:**

```prisma
// This is your Prisma schema file
generator client {
  provider = "prisma-client-js"
  previewFeatures = ["postgresqlExtensions"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
  extensions = [vector]
}

// ============================================
// MODELS
// ============================================

// Organizations (Projects)
model Organization {
  id        String   @id @default(cuid())
  name      String
  slug      String   @unique
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")
  settings  Json     @default("{}")

  // Relations
  memberships   Membership[]
  documents     Document[]
  embeddings    Embedding[]
  chatSessions  ChatSession[]

  @@map("organizations")
}

// Memberships (Users in Organizations with roles)
model Membership {
  id             String   @id @default(cuid())
  userId         String   @map("user_id") // Clerk user ID
  organizationId String   @map("organization_id")
  role           Role     @default(MEMBER)
  createdAt      DateTime @default(now()) @map("created_at")

  // Relations
  organization Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)

  @@unique([userId, organizationId])
  @@index([userId])
  @@index([organizationId])
  @@map("memberships")
}

enum Role {
  ADMIN
  MEMBER
  VIEWER
}

// Documents
model Document {
  id             String   @id @default(cuid())
  organizationId String   @map("organization_id")
  filename       String
  fileType       String   @map("file_type") // pdf, docx, txt, xml
  fileSize       Int      @map("file_size") // bytes
  uploadedBy     String   @map("uploaded_by") // Clerk user ID
  createdAt      DateTime @default(now()) @map("created_at")
  metadata       Json     @default("{}")

  // Relations
  organization Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  embeddings   Embedding[]

  @@index([organizationId])
  @@map("documents")
}

// Embeddings (Vector store)
model Embedding {
  id             String                        @id @default(cuid())
  documentId     String                        @map("document_id")
  organizationId String                        @map("organization_id")
  chunkText      String                        @map("chunk_text") @db.Text
  embedding      Unsupported("vector(3072)")?  // pgvector type
  chunkIndex     Int                           @map("chunk_index")
  metadata       Json                          @default("{}")
  createdAt      DateTime                      @default(now()) @map("created_at")

  // Relations
  document     Document     @relation(fields: [documentId], references: [id], onDelete: Cascade)
  organization Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)

  @@index([organizationId])
  @@index([documentId])
  @@map("embeddings")
}

// Chat Sessions
model ChatSession {
  id             String   @id @default(cuid())
  organizationId String   @map("organization_id")
  userId         String   @map("user_id") // Clerk user ID
  title          String   @default("Nieuwe chat")
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")

  // Relations
  organization Organization  @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  messages     ChatMessage[]

  @@index([organizationId])
  @@index([userId])
  @@map("chat_sessions")
}

// Chat Messages
model ChatMessage {
  id        String   @id @default(cuid())
  sessionId String   @map("session_id")
  role      MessageRole
  content   String   @db.Text
  sources   Json?    // Array of citation objects for assistant messages
  createdAt DateTime @default(now()) @map("created_at")

  // Relations
  session ChatSession @relation(fields: [sessionId], references: [id], onDelete: Cascade)

  @@index([sessionId])
  @@map("chat_messages")
}

enum MessageRole {
  USER
  ASSISTANT
}
```

**Generate Prisma Client:**
```bash
npx prisma generate
```

**Create initial migration:**
```bash
npx prisma migrate dev --name init
```

**Verwachte output:**
```
✔ Generated Prisma Client
✔ Applied migration 20240101000000_init to database
```

### Stap 2.3: Setup Prisma Client Singleton

**Maak `src/lib/prisma.ts`:**
```typescript
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
});

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}
```

### Stap 2.4: Setup Supabase RLS Policies

**Via Supabase SQL Editor**, run deze SQL:

```sql
-- Enable Row Level Security on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Helper function: Extract user_id from Clerk JWT
CREATE OR REPLACE FUNCTION auth.user_id() RETURNS text AS $$
  SELECT NULLIF(current_setting('request.jwt.claims', true)::json->>'sub', '')::text;
$$ LANGUAGE sql STABLE;

-- Policy: Users can only see organizations they're member of
CREATE POLICY "Users see their organizations"
ON organizations FOR SELECT
USING (
  id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
  )
);

-- Policy: Users can only see their own memberships
CREATE POLICY "Users see their memberships"
ON memberships FOR SELECT
USING (user_id = auth.user_id());

-- Policy: Users can see documents in their organizations
CREATE POLICY "Users see org documents"
ON documents FOR SELECT
USING (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
  )
);

-- Policy: Only ADMIN and MEMBER can insert documents
CREATE POLICY "Admins and members can upload documents"
ON documents FOR INSERT
WITH CHECK (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
    AND role IN ('ADMIN', 'MEMBER')
  )
);

-- Policy: Only uploader or ADMIN can delete documents
CREATE POLICY "Uploader or admin can delete documents"
ON documents FOR DELETE
USING (
  uploaded_by = auth.user_id()
  OR organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
    AND role = 'ADMIN'
  )
);

-- Policy: Users can see embeddings in their organizations
CREATE POLICY "Users see org embeddings"
ON embeddings FOR SELECT
USING (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
  )
);

-- Policy: System can insert embeddings (for document upload)
CREATE POLICY "System can insert embeddings"
ON embeddings FOR INSERT
WITH CHECK (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
    AND role IN ('ADMIN', 'MEMBER')
  )
);

-- Policy: Users can see chat sessions in their organizations
CREATE POLICY "Users see org chat sessions"
ON chat_sessions FOR SELECT
USING (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
  )
);

-- Policy: Users can create chat sessions in their organizations
CREATE POLICY "Users can create chat sessions"
ON chat_sessions FOR INSERT
WITH CHECK (
  organization_id IN (
    SELECT organization_id FROM memberships
    WHERE user_id = auth.user_id()
  )
);

-- Policy: Users can see messages in their sessions
CREATE POLICY "Users see their chat messages"
ON chat_messages FOR SELECT
USING (
  session_id IN (
    SELECT id FROM chat_sessions
    WHERE user_id = auth.user_id()
  )
);

-- Policy: Users can insert messages in their sessions
CREATE POLICY "Users can insert chat messages"
ON chat_messages FOR INSERT
WITH CHECK (
  session_id IN (
    SELECT id FROM chat_sessions
    WHERE user_id = auth.user_id()
  )
);

-- Create HNSW index for vector similarity search
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Create GIN index for full-text search
ALTER TABLE embeddings ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (to_tsvector('dutch', chunk_text)) STORED;

CREATE INDEX embeddings_search_idx ON embeddings USING gin(search_vector);
```

**Note:** Deze RLS policies zorgen ervoor dat data automatisch gefilterd wordt op organization level. Users kunnen alleen data zien van organizations waar ze lid van zijn.

### Stap 2.5: Clerk Setup

**In Clerk Dashboard:**

1. **Maak nieuwe application:**
   - Application name: `KOV-RAG`
   - Sign in/up options: Email, Google (optioneel)

2. **Enable Organizations:**
   - Ga naar `Organizations` in sidebar
   - Enable Organizations
   - Set permissions:
     - `org:admin` - Can manage members and settings
     - `org:member` - Can create content
     - `org:viewer` - Read-only access

3. **Configure JWT Template:**
   - Ga naar `JWT Templates`
   - Click `+ New template`
   - Name: `supabase`
   - Claims:
     ```json
     {
       "sub": "{{user.id}}",
       "email": "{{user.primary_email_address}}",
       "org_id": "{{org.id}}",
       "org_role": "{{org.role}}",
       "org_slug": "{{org.slug}}"
     }
     ```

4. **Copy API keys:**
   - Publishable key → `.env.local` als `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - Secret key → `.env.local` als `CLERK_SECRET_KEY`

### Stap 2.6: Integrate Clerk in Next.js

**Update `src/app/layout.tsx`:**
```typescript
import { ClerkProvider } from '@clerk/nextjs';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'KOV-RAG - BBL Kennisbank',
  description: 'Intelligente zoekfunctie voor BBL regelgeving',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="nl">
        <body className={inter.className}>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

**Maak auth pages:**

```bash
# Create directories
mkdir -p src/app/\(auth\)/sign-in/\[\[...sign-in\]\]
mkdir -p src/app/\(auth\)/sign-up/\[\[...sign-up\]\]
```

**Create `src/app/(auth)/sign-in/[[...sign-in]]/page.tsx`:**
```typescript
import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn />
    </div>
  );
}
```

**Create `src/app/(auth)/sign-up/[[...sign-up]]/page.tsx`:**
```typescript
import { SignUp } from '@clerk/nextjs';

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp />
    </div>
  );
}
```

### Stap 2.7: Test Authentication

```bash
npm run dev
```

**Test flow:**
1. Navigate to http://localhost:3000/sign-up
2. Maak test account aan
3. Verify email (in Clerk dashboard: disable email verification voor development)
4. Login werkt

**Acceptatie test:**
- ✅ Sign up page laadt
- ✅ Account kan worden aangemaakt
- ✅ Login werkt
- ✅ Session wordt bewaard (refresh werkt)

---

## 📄 Phase 3: Document Processing Pipeline

**Doel:** Implementeer document upload, text extraction, chunking, en embedding generation

**Acceptatie Criteria:**
- ✅ PDF, DOCX, TXT, XML files kunnen worden geüpload
- ✅ Text wordt correct geëxtraheerd
- ✅ Text wordt gechunked (800 chars, 100 overlap)
- ✅ Embeddings worden gegenereerd (OpenAI)
- ✅ Embeddings worden opgeslagen in pgvector
- ✅ Documents zijn zichtbaar per organization

### Stap 3.1: Installeer Document Processing Dependencies

```bash
npm install pdf-parse mammoth jsdom
npm install @types/pdf-parse --save-dev
```

### Stap 3.2: Setup OpenAI Client

**Maak `src/lib/openai.ts`:**
```typescript
import OpenAI from 'openai';

if (!process.env.OPENAI_API_KEY) {
  throw new Error('OPENAI_API_KEY is not set');
}

export const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Constants
export const EMBEDDING_MODEL = 'text-embedding-3-large';
export const EMBEDDING_DIMENSIONS = 3072;
export const LLM_MODEL = 'gpt-4-turbo-preview';
```

### Stap 3.3: Implement Text Extraction

**Maak `src/lib/rag/extraction.ts`:**
```typescript
import pdf from 'pdf-parse';
import mammoth from 'mammoth';
import { JSDOM } from 'jsdom';

export type SupportedFileType = 'pdf' | 'docx' | 'txt' | 'xml';

export async function extractText(file: File): Promise<string> {
  const fileType = getFileType(file.name);
  const buffer = await file.arrayBuffer();

  switch (fileType) {
    case 'pdf':
      return extractPDF(buffer);
    case 'docx':
      return extractDOCX(buffer);
    case 'txt':
      return extractTXT(buffer);
    case 'xml':
      return extractXML(buffer);
    default:
      throw new Error(`Unsupported file type: ${fileType}`);
  }
}

function getFileType(filename: string): SupportedFileType {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (!ext || !['pdf', 'docx', 'txt', 'xml'].includes(ext)) {
    throw new Error(`Unsupported file extension: ${ext}`);
  }
  return ext as SupportedFileType;
}

async function extractPDF(buffer: ArrayBuffer): Promise<string> {
  const data = await pdf(Buffer.from(buffer));
  return data.text;
}

async function extractDOCX(buffer: ArrayBuffer): Promise<string> {
  const result = await mammoth.extractRawText({ buffer: Buffer.from(buffer) });
  return result.value;
}

async function extractTXT(buffer: ArrayBuffer): Promise<string> {
  return new TextDecoder('utf-8').decode(buffer);
}

async function extractXML(buffer: ArrayBuffer): Promise<string> {
  const xmlString = new TextDecoder('utf-8').decode(buffer);
  // Parse XML and extract text (simplified - you can enhance with BBL-specific parsing)
  const dom = new JSDOM(xmlString, { contentType: 'text/xml' });
  return dom.window.document.documentElement.textContent || '';
}
```

### Stap 3.4: Implement Text Chunking

**Maak `src/lib/rag/chunking.ts`:**
```typescript
export interface ChunkOptions {
  chunkSize?: number;      // Default: 800 characters
  chunkOverlap?: number;   // Default: 100 characters
}

export interface Chunk {
  text: string;
  index: number;
  start: number;
  end: number;
}

export function chunkText(text: string, options: ChunkOptions = {}): Chunk[] {
  const chunkSize = options.chunkSize ?? 800;
  const chunkOverlap = options.chunkOverlap ?? 100;

  // Clean text
  const cleanedText = text.replace(/\s+/g, ' ').trim();

  if (cleanedText.length <= chunkSize) {
    return [{ text: cleanedText, index: 0, start: 0, end: cleanedText.length }];
  }

  const chunks: Chunk[] = [];
  let start = 0;
  let chunkIndex = 0;

  while (start < cleanedText.length) {
    const end = Math.min(start + chunkSize, cleanedText.length);
    const chunkText = cleanedText.slice(start, end);

    chunks.push({
      text: chunkText,
      index: chunkIndex,
      start,
      end,
    });

    chunkIndex++;
    start += chunkSize - chunkOverlap;
  }

  return chunks;
}

// Split text by sentences (alternative chunking strategy)
export function chunkBySentences(
  text: string,
  maxChunkSize: number = 800
): Chunk[] {
  // Simple sentence splitter (can be enhanced with NLP library)
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];

  const chunks: Chunk[] = [];
  let currentChunk = '';
  let chunkIndex = 0;
  let start = 0;

  for (const sentence of sentences) {
    if (currentChunk.length + sentence.length > maxChunkSize && currentChunk) {
      chunks.push({
        text: currentChunk.trim(),
        index: chunkIndex,
        start,
        end: start + currentChunk.length,
      });
      chunkIndex++;
      start += currentChunk.length;
      currentChunk = '';
    }
    currentChunk += sentence + ' ';
  }

  if (currentChunk) {
    chunks.push({
      text: currentChunk.trim(),
      index: chunkIndex,
      start,
      end: start + currentChunk.length,
    });
  }

  return chunks;
}
```

### Stap 3.5: Implement Embedding Generation

**Maak `src/lib/rag/embeddings.ts`:**
```typescript
import { openai, EMBEDDING_MODEL } from '../openai';

export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  // OpenAI allows max 2048 inputs per request
  const batchSize = 2048;
  const allEmbeddings: number[][] = [];

  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);

    const response = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: batch,
    });

    const embeddings = response.data.map((item) => item.embedding);
    allEmbeddings.push(...embeddings);
  }

  return allEmbeddings;
}

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: text,
  });

  return response.data[0].embedding;
}

// Format embedding for pgvector (PostgreSQL)
export function formatEmbeddingForDB(embedding: number[]): string {
  return `[${embedding.join(',').}]`;
}
```

### Stap 3.6: Implement Document Upload API

**Maak `src/app/api/documents/upload/route.ts`:**
```typescript
import { auth } from '@clerk/nextjs';
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { extractText } from '@/lib/rag/extraction';
import { chunkText } from '@/lib/rag/chunking';
import { generateEmbeddings, formatEmbeddingForDB } from '@/lib/rag/embeddings';

export const runtime = 'nodejs';
export const maxDuration = 300; // 5 minutes (for large files)

export async function POST(req: NextRequest) {
  try {
    // Check authentication
    const { userId, orgId, orgRole } = auth();

    if (!userId || !orgId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check permission (only ADMIN and MEMBER can upload)
    if (!orgRole || !['org:admin', 'org:member'].includes(orgRole)) {
      return NextResponse.json(
        { error: 'Insufficient permissions' },
        { status: 403 }
      );
    }

    // Parse form data
    const formData = await req.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return NextResponse.json(
        { error: 'File too large (max 10MB)' },
        { status: 400 }
      );
    }

    // Validate file type
    const allowedTypes = ['pdf', 'docx', 'txt', 'xml'];
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    if (!fileExt || !allowedTypes.includes(fileExt)) {
      return NextResponse.json(
        { error: 'Invalid file type. Allowed: PDF, DOCX, TXT, XML' },
        { status: 400 }
      );
    }

    // Extract text from file
    console.log('Extracting text from file:', file.name);
    const text = await extractText(file);

    if (!text || text.trim().length === 0) {
      return NextResponse.json(
        { error: 'No text could be extracted from file' },
        { status: 400 }
      );
    }

    // Chunk text
    console.log('Chunking text...');
    const chunks = chunkText(text, { chunkSize: 800, chunkOverlap: 100 });

    if (chunks.length === 0) {
      return NextResponse.json(
        { error: 'No chunks generated' },
        { status: 400 }
      );
    }

    // Generate embeddings
    console.log(`Generating embeddings for ${chunks.length} chunks...`);
    const chunkTexts = chunks.map((c) => c.text);
    const embeddings = await generateEmbeddings(chunkTexts);

    // Store in database
    console.log('Storing in database...');
    const document = await prisma.document.create({
      data: {
        organizationId: orgId,
        filename: file.name,
        fileType: fileExt,
        fileSize: file.size,
        uploadedBy: userId,
        metadata: {
          chunkCount: chunks.length,
          textLength: text.length,
        },
      },
    });

    // Store embeddings (batch insert)
    const embeddingData = chunks.map((chunk, i) => ({
      documentId: document.id,
      organizationId: orgId,
      chunkText: chunk.text,
      chunkIndex: chunk.index,
      metadata: {
        start: chunk.start,
        end: chunk.end,
      },
    }));

    // Use raw SQL for pgvector insertion
    for (let i = 0; i < embeddingData.length; i++) {
      const data = embeddingData[i];
      const embedding = formatEmbeddingForDB(embeddings[i]);

      await prisma.$executeRaw`
        INSERT INTO embeddings (
          id, document_id, organization_id, chunk_text, embedding, chunk_index, metadata, created_at
        ) VALUES (
          gen_random_uuid()::text,
          ${data.documentId},
          ${data.organizationId},
          ${data.chunkText},
          ${embedding}::vector,
          ${data.chunkIndex},
          ${JSON.stringify(data.metadata)}::jsonb,
          NOW()
        )
      `;
    }

    console.log('Upload complete!');

    return NextResponse.json({
      success: true,
      document: {
        id: document.id,
        filename: document.filename,
        chunksCount: chunks.length,
      },
    });
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Stap 3.7: Implement Document List API

**Maak `src/app/api/documents/list/route.ts`:**
```typescript
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const { userId, orgId } = auth();

    if (!userId || !orgId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get documents for current organization
    const documents = await prisma.document.findMany({
      where: {
        organizationId: orgId,
      },
      orderBy: {
        createdAt: 'desc',
      },
      include: {
        _count: {
          select: { embeddings: true },
        },
      },
    });

    const formattedDocuments = documents.map((doc) => ({
      id: doc.id,
      filename: doc.filename,
      fileType: doc.fileType,
      fileSize: doc.fileSize,
      uploadedBy: doc.uploadedBy,
      createdAt: doc.createdAt,
      chunksCount: doc._count.embeddings,
    }));

    return NextResponse.json({ documents: formattedDocuments });
  } catch (error) {
    console.error('List documents error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Stap 3.8: Test Document Upload

**Maak een test component** `src/app/test/upload/page.tsx`:
```typescript
'use client';

import { useState } from 'react';

export default function TestUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function handleUpload() {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      setResult({ error: 'Upload failed' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Test Document Upload</h1>

      <input
        type="file"
        accept=".pdf,.docx,.txt,.xml"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="mb-4"
      />

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? 'Uploading...' : 'Upload'}
      </button>

      {result && (
        <pre className="mt-4 p-4 bg-gray-100 rounded">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
```

**Test:**
1. Navigate to http://localhost:3000/test/upload
2. Upload een test PDF
3. Check console logs
4. Verify in Supabase database: `documents` en `embeddings` tables

**Acceptatie test:**
- ✅ File upload werkt
- ✅ Text wordt geëxtraheerd
- ✅ Chunks worden aangemaakt
- ✅ Embeddings worden gegenereerd
- ✅ Data staat in database

---

## 🔍 Phase 4: RAG Query Pipeline

**Doel:** Implementeer vector search, hybrid search, en RAG query met LLM

**Acceptatie Criteria:**
- ✅ Vector similarity search werkt
- ✅ Hybrid search (vector + full-text) werkt
- ✅ RAG pipeline genereert relevante antwoorden
- ✅ Citations/bronnen worden teruggegeven
- ✅ Queries zijn organization-scoped

### Stap 4.1: Implement Vector Search

**Maak `src/lib/rag/vectorSearch.ts`:**
```typescript
import { prisma } from '../prisma';
import { generateEmbedding } from './embeddings';

export interface SearchResult {
  id: string;
  chunkText: string;
  similarity: number;
  metadata: any;
  document: {
    id: string;
    filename: string;
  };
}

export async function vectorSearch(
  query: string,
  organizationId: string,
  topK: number = 5
): Promise<SearchResult[]> {
  // Generate query embedding
  const queryEmbedding = await generateEmbedding(query);
  const embeddingString = `[${queryEmbedding.join(',')}]`;

  // Vector similarity search using pgvector
  const results = await prisma.$queryRaw<SearchResult[]>`
    SELECT
      e.id,
      e.chunk_text as "chunkText",
      1 - (e.embedding <=> ${embeddingString}::vector) as similarity,
      e.metadata,
      json_build_object('id', d.id, 'filename', d.filename) as document
    FROM embeddings e
    JOIN documents d ON e.document_id = d.id
    WHERE e.organization_id = ${organizationId}
    ORDER BY e.embedding <=> ${embeddingString}::vector
    LIMIT ${topK}
  `;

  return results;
}

export async function hybridSearch(
  query: string,
  organizationId: string,
  topK: number = 5
): Promise<SearchResult[]> {
  // Generate query embedding
  const queryEmbedding = await generateEmbedding(query);
  const embeddingString = `[${queryEmbedding.join(',')}]`;

  // Hybrid search: combine vector similarity + full-text search
  const results = await prisma.$queryRaw<SearchResult[]>`
    WITH vector_results AS (
      SELECT
        id,
        chunk_text,
        1 - (embedding <=> ${embeddingString}::vector) as vector_score,
        document_id,
        metadata
      FROM embeddings
      WHERE organization_id = ${organizationId}
      ORDER BY embedding <=> ${embeddingString}::vector
      LIMIT ${topK * 3}
    ),
    fts_results AS (
      SELECT
        id,
        chunk_text,
        ts_rank(search_vector, plainto_tsquery('dutch', ${query})) as fts_score,
        document_id,
        metadata
      FROM embeddings
      WHERE organization_id = ${organizationId}
        AND search_vector @@ plainto_tsquery('dutch', ${query})
      ORDER BY fts_score DESC
      LIMIT ${topK * 3}
    )
    SELECT
      e.id,
      e.chunk_text as "chunkText",
      COALESCE(v.vector_score, 0) * 0.7 + COALESCE(f.fts_score, 0) * 0.3 as similarity,
      e.metadata,
      json_build_object('id', d.id, 'filename', d.filename) as document
    FROM embeddings e
    JOIN documents d ON e.document_id = d.id
    LEFT JOIN vector_results v ON e.id = v.id
    LEFT JOIN fts_results f ON e.id = f.id
    WHERE e.organization_id = ${organizationId}
      AND (v.id IS NOT NULL OR f.id IS NOT NULL)
    ORDER BY similarity DESC
    LIMIT ${topK}
  `;

  return results;
}
```

### Stap 4.2: Implement RAG Query Pipeline

**Maak `src/lib/rag/query.ts`:**
```typescript
import { openai, LLM_MODEL } from '../openai';
import { hybridSearch, SearchResult } from './vectorSearch';

export interface RAGResponse {
  answer: string;
  sources: SearchResult[];
  processingTime: number;
}

export async function queryRAG(
  query: string,
  organizationId: string,
  topK: number = 5
): Promise<RAGResponse> {
  const startTime = Date.now();

  // 1. Retrieve relevant chunks
  const sources = await hybridSearch(query, organizationId, topK);

  if (sources.length === 0) {
    return {
      answer: 'Ik kan geen relevante informatie vinden in de geüploade documenten. Probeer een andere vraag of upload meer documenten.',
      sources: [],
      processingTime: Date.now() - startTime,
    };
  }

  // 2. Build context with citations
  const context = sources
    .map((source, i) => {
      return `[${i + 1}] ${source.chunkText}\nBron: ${source.document.filename}`;
    })
    .join('\n\n');

  // 3. Generate answer with LLM
  const systemPrompt = `Je bent een expert assistent voor het Besluit Bouwwerken Leefomgeving (BBL).

Je taak is om vragen te beantwoorden over bouwregelgeving op basis van de verstrekte context.

Belangrijke richtlijnen:
- Geef alleen antwoorden die gebaseerd zijn op de verstrekte context
- Verwijs naar bronnen met [1], [2], etc.
- Als de context het antwoord niet bevat, geef dat eerlijk aan
- Wees precies en specifiek in je antwoorden
- Gebruik Nederlandse taal en terminologie

Context:
${context}`;

  const completion = await openai.chat.completions.create({
    model: LLM_MODEL,
    messages: [
      {
        role: 'system',
        content: systemPrompt,
      },
      {
        role: 'user',
        content: query,
      },
    ],
    temperature: 0.3, // Lower temperature for factual answers
    max_tokens: 1000,
  });

  const answer = completion.choices[0].message.content || 'Geen antwoord gegenereerd.';

  return {
    answer,
    sources,
    processingTime: Date.now() - startTime,
  };
}
```

### Stap 4.3: Implement Query API Endpoint

**Maak `src/app/api/query/route.ts`:**
```typescript
import { auth } from '@clerk/nextjs';
import { NextRequest, NextResponse } from 'next/server';
import { queryRAG } from '@/lib/rag/query';
import { z } from 'zod';

const QuerySchema = z.object({
  query: z.string().min(1).max(500),
  topK: z.number().min(1).max(20).optional().default(5),
});

export async function POST(req: NextRequest) {
  try {
    const { userId, orgId } = auth();

    if (!userId || !orgId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Parse and validate request body
    const body = await req.json();
    const validation = QuerySchema.safeParse(body);

    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid request', details: validation.error.errors },
        { status: 400 }
      );
    }

    const { query, topK } = validation.data;

    // Execute RAG query
    const result = await queryRAG(query, orgId, topK);

    return NextResponse.json(result);
  } catch (error) {
    console.error('Query error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Stap 4.4: Test RAG Query

**Maak test component** `src/app/test/query/page.tsx`:
```typescript
'use client';

import { useState } from 'react';

export default function TestQueryPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function handleQuery() {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, topK: 5 }),
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      setResult({ error: 'Query failed' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Test RAG Query</h1>

      <div className="mb-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Stel een vraag over BBL..."
          className="w-full p-2 border rounded min-h-[100px]"
        />
      </div>

      <button
        onClick={handleQuery}
        disabled={!query.trim() || loading}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? 'Zoeken...' : 'Stel vraag'}
      </button>

      {result && (
        <div className="mt-8">
          {result.error ? (
            <div className="p-4 bg-red-100 text-red-700 rounded">
              {result.error}
            </div>
          ) : (
            <>
              <div className="mb-4 p-4 bg-blue-50 rounded">
                <h2 className="font-bold mb-2">Antwoord:</h2>
                <p className="whitespace-pre-wrap">{result.answer}</p>
                <p className="text-sm text-gray-500 mt-2">
                  Processing time: {result.processingTime}ms
                </p>
              </div>

              <div>
                <h2 className="font-bold mb-2">Bronnen:</h2>
                {result.sources.map((source: any, i: number) => (
                  <div key={i} className="mb-2 p-3 bg-gray-50 rounded text-sm">
                    <p className="font-semibold">[{i + 1}] {source.document.filename}</p>
                    <p className="text-gray-600 mt-1">{source.chunkText.slice(0, 200)}...</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Similarity: {(source.similarity * 100).toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

**Test:**
1. Upload eerst een document via test upload page
2. Navigate to http://localhost:3000/test/query
3. Stel een vraag over het document
4. Verify antwoord is relevant

**Acceptatie test:**
- ✅ Query retourneert antwoord
- ✅ Bronnen worden getoond
- ✅ Citations [1], [2] zijn correct
- ✅ Antwoord is relevant voor query

---

**(CONTINUED IN NEXT PART - Dit is deel 1 van het implementation plan)**

**Status:** Phase 1-4 compleet (Setup, Auth, Documents, RAG Query)
**Remaining:** Phase 5-7 (Frontend UI, Chat, Advanced Features, Deployment)

**Wil je dat ik doorga met Phase 5-7?** Dit wordt een zeer groot document (waarschijnlijk 5000+ regels totaal). Ik kan ook kiezen om per phase een apart document te maken voor betere leesbaarheid.

**Optie A:** Eén groot document (IMPLEMENTATION_PLAN.md) - compleet maar zeer lang
**Optie B:** Gesplitste documents (PHASE_1_2.md, PHASE_3_4.md, PHASE_5_7.md) - beter leesbaar

Wat is jouw voorkeur?
