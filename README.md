# AI Code Review & Repository Intelligence Platform

A full-stack web application that indexes Git repositories using vector embeddings to enable semantic code search and AI-powered code reviews via LLM.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Features](#4-features)
5. [Data Models](#5-data-models)
6. [API Reference](#6-api-reference)
7. [Backend Deep Dive](#7-backend-deep-dive)
8. [Frontend Deep Dive](#8-frontend-deep-dive)
9. [AI & ML Pipeline](#9-ai--ml-pipeline)
10. [Database Design](#10-database-design)
11. [Authentication & Authorization](#11-authentication--authorization)
12. [Infrastructure & Deployment](#12-infrastructure--deployment)
13. [CI/CD Pipeline](#13-cicd-pipeline)
14. [Configuration Reference](#14-configuration-reference)
15. [Local Development Setup](#15-local-development-setup)
16. [Known Limitations & TODOs](#16-known-limitations--todos)
17. [Interview Prep: Key Talking Points](#17-interview-prep-key-talking-points)

---

## 1. Project Overview

This platform solves two core problems developers face with large codebases:

1. **Finding relevant code** — traditional `grep`-style search requires exact keyword matches. This platform lets you ask "where is authentication handled?" or "show me database connection logic" and get semantically relevant results.
2. **Code quality feedback** — instead of manually reviewing files, you can trigger an LLM-powered review that returns structured issues with severity levels and suggested fixes.

### User Journey

```
Register / Login
       ↓
Add a GitHub (or any Git) repository URL
       ↓
Platform clones it, chunks files, generates embeddings, stores in pgvector
       ↓
Search codebase with natural language queries
       ↓
Trigger AI review on a specific file or the whole repo
       ↓
View issues sorted by severity with suggested fixes
```

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (React SPA)                       │
│   Dashboard │ Repositories │ Search │ Reviews               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS REST  /api/v1  (JWT Bearer)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI (Python 3.12)                      │
│                                                              │
│  /auth ──────────────► JWT create/validate                   │
│                                                              │
│  /repositories ───────► IndexingService (BackgroundTask)     │
│                              │                               │
│                              ├─ GitPython shallow clone      │
│                              ├─ file_utils walk + chunk      │
│                              └─ EmbeddingService → pgvector  │
│                                                              │
│  /search ─────────────► SearchService                        │
│                              ├─ EmbeddingService             │
│                              ├─ pgvector cosine ANN          │
│                              └─ InMemoryCache (120s TTL)     │
│                                                              │
│  /reviews ────────────► ReviewService                        │
│                              ├─ Reconstruct file from chunks │
│                              ├─ LangChain ChatOpenAI         │
│                              └─ Structured JSON parse → DB   │
└───────────────┬──────────────────────────┬───────────────────┘
                │                          │
                ▼                          ▼
┌───────────────────────┐    ┌─────────────────────────────┐
│  PostgreSQL 16        │    │  Redis 7 (configured,        │
│  + pgvector           │    │  not yet wired)              │
│                       │    └─────────────────────────────┘
│  Tables:              │
│  • users              │    ┌─────────────────────────────┐
│  • repositories       │    │  Local disk                  │
│  • repo_files         │    │  /tmp/ai_code_review_repos/  │
│  • code_chunks        │    │  {repo_id}/  (cloned repos)  │
│    (384-dim vector)   │    └─────────────────────────────┘
│  • review_history     │
└───────────────────────┘
```

### Deployment Architecture (AWS)

```
GitHub Actions (CI/CD)
       │
       ├─ Build Docker images
       ├─ Push to AWS ECR
       └─ Update ECS task definition → rolling deploy

ECS Fargate Cluster
  ├─ backend task  (Dockerfile.backend)
  └─ frontend task (Dockerfile.frontend → nginx)
       nginx reverse proxy:
         /api/* → backend container
         /*     → static React build
```

---

## 3. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend language | Python 3.12 | Strong async support, rich ML ecosystem |
| Web framework | FastAPI 0.115 + Uvicorn | Auto-generated OpenAPI docs, async-first, dependency injection |
| ORM | SQLAlchemy 2 (async) | Async sessions, type-safe queries |
| DB migrations | Alembic | Schema version control |
| Database | PostgreSQL 16 + pgvector | ACID + vector similarity search in one place |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` | 384-dim, runs locally, no API cost |
| LLM | LangChain 0.3 + OpenAI SDK | Structured prompting, swappable model backend |
| Auth | python-jose (HS256 JWT) + passlib (bcrypt) | Industry-standard JWT auth |
| Git | GitPython | Programmatic clone with branch fallback |
| Frontend | React 18 + TypeScript 5 | Type safety, component reuse |
| Build tool | Vite 6 | Fast HMR in dev, optimized prod builds |
| HTTP client | Axios 1.7 | Interceptors for JWT injection |
| Containerization | Docker + Docker Compose | Reproducible dev environment |
| CI | GitHub Actions | Lint, type-check, test on every PR |
| Deployment | AWS ECS Fargate + ECR | Serverless containers, no EC2 management |

---

## 4. Features

### 4.1 Repository Management
- Add any public Git repository by URL, name, and branch
- Background indexing with status polling (`pending → cloning → indexing → ready | error`)
- Reindex a repository to pick up new commits
- Delete a repository (removes all associated files, chunks, and reviews)
- View all repositories with status badges

### 4.2 Semantic Code Search
- Natural language query encoded to a 384-dim embedding
- Cosine similarity ANN search via pgvector IVFFlat index
- Filter results by repository
- Returns: matching code snippet, file path, line range, similarity score
- Results cached in-memory for 120 seconds

### 4.3 AI Code Review
- **File review**: send a specific file path for review
- **Repository review**: sample up to 5 files from a repository for batch review
- LLM returns structured JSON array of issues with:
  - `issue` — short title
  - `severity` — `critical | high | medium | low | info`
  - `description` — detailed explanation
  - `suggested_fix` — concrete fix recommendation
  - `line_range` — affected lines
- All review results stored in `review_history` table

### 4.4 Authentication
- Register with email + password (bcrypt hashed)
- Login returns a JWT (configurable expiry)
- All protected endpoints require `Authorization: Bearer <token>`
- Role field (`user` / `admin`) exists for future RBAC expansion

### 4.5 Dashboard
- Aggregate stats: total repositories, indexed files, code chunks, reviews run
- Recent repositories table with status

---

## 5. Data Models

### User
```python
class User(Base):
    id: UUID
    email: str          # unique
    hashed_password: str
    role: str           # "user" | "admin"
    is_active: bool
    created_at: datetime
```

### Repository
```python
class Repository(Base):
    id: UUID
    name: str
    url: str
    branch: str         # default "main"
    status: str         # "pending" | "cloning" | "indexing" | "ready" | "error"
    error_message: str  # set on failure
    file_count: int
    chunk_count: int
    owner_id: UUID      # FK → users
    created_at: datetime
    updated_at: datetime
```

### RepoFile
```python
class RepoFile(Base):
    id: UUID
    repository_id: UUID # FK → repositories
    file_path: str      # relative path within repo
    language: str       # detected from extension
    size_bytes: int
    line_count: int
    created_at: datetime
```

### CodeChunk
```python
class CodeChunk(Base):
    id: UUID
    repo_file_id: UUID  # FK → repo_files
    repository_id: UUID # denormalized for fast vector search filtering
    content: str        # raw code text
    start_line: int
    end_line: int
    chunk_index: int
    embedding: Vector(384)  # pgvector column
    created_at: datetime
```

### ReviewHistory
```python
class ReviewHistory(Base):
    id: UUID
    repository_id: UUID
    file_path: str      # None = whole-repo review
    review_type: str    # "file" | "repository"
    results: JSON       # list of ReviewIssue dicts
    created_at: datetime
    requested_by: UUID  # FK → users
```

---

## 6. API Reference

Base URL: `/api/v1`

All endpoints except `/auth/register` and `/auth/login` require `Authorization: Bearer <token>`.

### Auth

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account `{email, password}` |
| `POST` | `/auth/login` | Get JWT `{email, password}` → `{access_token, token_type}` |
| `GET` | `/auth/me` | Current user info |

### Repositories

| Method | Path | Description |
|---|---|---|
| `GET` | `/repositories` | List all repos for current user |
| `POST` | `/repositories` | Add repo `{name, url, branch}` — triggers background indexing |
| `GET` | `/repositories/{id}` | Get single repo with stats |
| `GET` | `/repositories/{id}/status` | Poll indexing status |
| `POST` | `/repositories/{id}/reindex` | Re-clone and re-index |
| `DELETE` | `/repositories/{id}` | Delete repo + all data |

### Search

| Method | Path | Description |
|---|---|---|
| `POST` | `/search` | Semantic search `{query, repository_id?, limit?}` |

### Reviews

| Method | Path | Description |
|---|---|---|
| `POST` | `/reviews/file` | File review `{repository_id, file_path}` |
| `POST` | `/reviews/repository` | Repo review `{repository_id}` (samples 5 files) |
| `GET` | `/reviews/{id}` | Get review result |
| `GET` | `/reviews?repository_id=` | List reviews for a repo |

---

## 7. Backend Deep Dive

### Entry Point — `main.py`
- Creates the FastAPI app
- Configures CORS from `settings.ALLOWED_ORIGINS`
- Mounts all routers under `/api/v1`
- On startup, runs `Base.metadata.create_all()` (Alembic handles prod migrations)

### Configuration — `config/settings.py`
- Uses `pydantic-settings` reading from `.env` file
- Single `Settings` instance imported everywhere
- All secrets injected via environment variables (no hardcoded values)

### Dependency Injection — `api/dependencies.py`
- Factory functions return service instances with DB sessions
- `get_db()` — yields an async SQLAlchemy session (auto-committed/rolled-back)
- `get_embedding_service()` — returns singleton (model loaded once via LRU cache)
- `get_current_user()` — decodes JWT, fetches user from DB

### Indexing Pipeline — `services/indexing_service.py`

```
index_repository(repo_id, url, branch)
    │
    ├─ 1. Update status → "cloning"
    ├─ 2. git_utils.clone_repository(url, branch, target_dir)
    │       └─ GitPython.Repo.clone_from(depth=1)
    │          fallback: clone default branch if branch not found
    │
    ├─ 3. Update status → "indexing"
    ├─ 4. file_utils.walk_repository_files(cloned_dir)
    │       └─ os.walk, skip: .git, node_modules, __pycache__, venv, dist
    │          filter by supported_extensions (30+ file types)
    │          skip files > MAX_FILE_SIZE_KB
    │
    ├─ 5. For each file:
    │       a. detect_language(extension) → "python" | "javascript" | ...
    │       b. chunk_code(content, chunk_size=512, overlap=64)
    │              └─ line-based sliding window
    │       c. embedding_service.encode(chunk_text) → np.array [384]
    │       d. INSERT repo_file + code_chunks (batch)
    │
    └─ 6. Update status → "ready", set file_count, chunk_count
         (on any exception → status = "error", error_message set)
```

### Embedding Service — `services/embedding_service.py`
- Wraps `SentenceTransformer("all-MiniLM-L6-v2")`
- Model loaded once and cached with `functools.lru_cache`
- `encode(text: str) → np.ndarray[float32, 384]`
- Called for both indexing (chunk text) and search (query text)

### Search Service — `services/search_service.py`
- Encodes the query to a 384-dim vector
- Runs raw SQL with pgvector `<=>` (cosine distance) operator:
  ```sql
  SELECT cc.*, (cc.embedding <=> '[...]'::vector) AS distance
  FROM code_chunks cc
  JOIN repo_files rf ON cc.repo_file_id = rf.id
  WHERE cc.repository_id = :repo_id   -- optional filter
  ORDER BY distance
  LIMIT :limit
  ```
- Wraps result in `InMemoryCache` with 120s TTL (cache key = hash of query + filters)

### Review Service — `services/review_service.py`
- Reconstructs file content by joining all CodeChunk.content for that file path (ordered by chunk_index)
- Truncates to 8000 chars to stay within token limits
- Builds LangChain chain: `ChatOpenAI` + system prompt demanding JSON output
- System prompt specifies exact JSON schema: `[{issue, severity, description, suggested_fix, line_range}]`
- Parses LLM response, validates severity values, saves to `review_history`
- Falls back to placeholder issues if LLM call fails

### File Utilities — `utils/file_utils.py`
- `SUPPORTED_EXTENSIONS`: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.rb`, `.php`, `.cs`, `.cpp`, `.c`, `.h`, `.swift`, `.kt`, `.scala`, `.r`, `.m`, `.sh`, `.yaml`, `.yml`, `.json`, `.md`, `.sql`, `.html`, `.css`, `.scss`, `.vue`, `.svelte`, and more
- `chunk_code(content, size, overlap)`: splits by lines, creates overlapping windows so context isn't lost at chunk boundaries

---

## 8. Frontend Deep Dive

### Routing — `App.tsx`
All routes except `/login` and `/register` are wrapped in `<ProtectedRoute>` which checks `AuthContext` for a valid token and redirects to `/login` if absent.

```
/login          → LoginPage
/register       → RegisterPage
/               → DashboardPage (protected)
/repositories   → RepositoriesPage (protected)
/search         → SearchPage (protected)
/reviews        → ReviewsPage (protected)
```

### Auth Context — `context/AuthContext.tsx`
- Stores JWT in `localStorage` (`ai_review_token`)
- On mount, reads token from storage and attempts `/auth/me` to validate it
- `login(token)` — stores token, sets user state
- `logout()` — clears token, redirects to `/login`
- Axios interceptors inject `Authorization: Bearer <token>` on every request

### Key Pages

**DashboardPage**: fetches aggregate counts (total repos, files, chunks, reviews) and recent repositories list. Shows status badges color-coded by state.

**RepositoriesPage**: add form (name, URL, branch), list with delete and reindex actions, polls status every 3 seconds for repos in `pending/cloning/indexing` state.

**SearchPage**: text input for query, optional repository filter dropdown, displays result cards with file path, line range, similarity score, and code snippet.

**ReviewsPage**: select repository → select review type (file or repo) → optionally enter file path → trigger review → display issues as cards with SeverityBadge.

### API Modules — `src/api/`
Each module (`auth.ts`, `repositories.ts`, `search.ts`, `reviews.ts`) exports typed async functions that call the corresponding REST endpoints and return typed responses matching `src/types/index.ts`.

---

## 9. AI & ML Pipeline

### Embedding Model: `all-MiniLM-L6-v2`
- A distilled BERT model from the sentence-transformers library
- Output: 384-dimensional dense float32 vectors
- Runs entirely on CPU locally — no external API needed for indexing/search
- Typical encode time: ~5ms per chunk on CPU
- Why this model: good semantic quality-to-size ratio, widely benchmarked, free

### Vector Storage: pgvector
- PostgreSQL extension adding a `vector` column type
- Supports exact KNN and approximate ANN via IVFFlat or HNSW indexes
- This project uses **IVFFlat** with `lists=100`:
  - Divides vectors into 100 clusters (Voronoi cells)
  - At query time, probes the nearest `nprobe` clusters (default 10)
  - Trade-off: faster than exact KNN, slight accuracy loss
- Cosine similarity via `<=>` operator (1 - cosine_similarity = cosine distance)

### LLM Integration: LangChain + OpenAI
- Uses `ChatOpenAI` from `langchain-openai`
- Model configurable via `LLM_MODEL` env var (default: `gpt-4o-mini`)
- System prompt engineering:
  - Instructs the model to act as a senior code reviewer
  - Demands strict JSON array output (no markdown fences)
  - Specifies exact field names and allowed severity enum values
- Response parsing uses `json.loads()` on the raw LLM output
- Any OpenAI-compatible endpoint (Azure OpenAI, local Ollama, etc.) works via `OPENAI_API_BASE`

### Indexing Numbers (estimates)
- A 1000-file repo with avg 200 lines/file = ~200k lines
- At 512-line chunks with 64-line overlap: ~450 chunks
- Each embedding call: ~5ms → ~2.25 seconds per repo for embedding alone
- PostgreSQL insert with pgvector: ~0.1ms/row at small scale

---

## 10. Database Design

### Why PostgreSQL + pgvector Instead of a Dedicated Vector DB?
- Avoids introducing a separate vector database (Pinecone, Weaviate, Qdrant) as another infrastructure dependency
- Single source of truth: relational metadata + vector embeddings in one system
- ACID transactions: indexing either fully succeeds or is rolled back
- pgvector IVFFlat index is sufficient for tens of millions of vectors

### Schema Decisions
- `code_chunks.repository_id` is **denormalized** (also accessible via `repo_files`) to avoid a JOIN in the hot search query path
- `review_history.results` stored as JSON (not normalized rows) because review issue schemas may evolve without migrations
- All primary keys are UUIDs (not auto-increment integers) for distributed-safe ID generation

### Migration
Alembic is used for all schema changes. The initial migration (`0001_initial_schema.py`) creates:
1. `CREATE EXTENSION IF NOT EXISTS vector`
2. All five tables
3. IVFFlat index: `CREATE INDEX ON code_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)`

---

## 11. Authentication & Authorization

### JWT Flow
```
POST /auth/login {email, password}
   → bcrypt.verify(password, hashed_password)
   → python-jose creates HS256 JWT:
       payload: {sub: user_id, exp: now + ACCESS_TOKEN_EXPIRE_MINUTES}
       signed with SECRET_KEY
   → returns {access_token: "eyJ...", token_type: "bearer"}

Subsequent requests:
   Authorization: Bearer eyJ...
   → python-jose decodes + verifies signature + checks exp
   → DB lookup: SELECT * FROM users WHERE id = payload.sub
   → inject user into route handler via FastAPI Depends()
```

### RBAC
- `User.role` field: `"user"` or `"admin"`
- `require_admin` dependency in `auth/rbac.py` raises 403 if role != "admin"
- Currently no routes use `require_admin` — scaffolded for future admin features (e.g., managing all users' repositories)

---

## 12. Infrastructure & Deployment

### Docker Compose (local/dev)
```yaml
services:
  db:       # ankane/pgvector:pg16 — postgres with pgvector pre-installed
  redis:    # redis:7-alpine
  backend:  # built from docker/Dockerfile.backend
  frontend: # built from docker/Dockerfile.frontend (multi-stage: node build → nginx serve)
```

### Dockerfile.backend
- Base: `python:3.12-slim`
- Installs system deps (git for GitPython, libpq for psycopg2)
- Copies `requirements.txt`, runs `pip install`
- Copies source, runs `uvicorn main:app --host 0.0.0.0 --port 8000`

### Dockerfile.frontend
- Stage 1: `node:20-alpine` — `npm ci && npm run build` → `dist/`
- Stage 2: `nginx:alpine` — copies `dist/` to nginx webroot
- `nginx.conf` proxies `/api/*` to `http://backend:8000/api/*` and serves all other routes as `index.html` (SPA fallback)

### AWS ECS Fargate Deployment
- No EC2 instances to manage — containers run on AWS-managed compute
- Images stored in ECR (Elastic Container Registry)
- Task definition in `docs/ecs-task-definition.json` defines CPU/memory, env vars from Secrets Manager, and container dependencies
- GitHub Actions deploys via OIDC (no long-lived AWS keys in repo):
  1. Authenticate to AWS using OIDC web identity
  2. `docker build && docker push` to ECR
  3. Register new ECS task definition revision
  4. `ecs update-service --force-new-deployment` triggers rolling deploy

---

## 13. CI/CD Pipeline

### `.github/workflows/ci.yml` (runs on every PR and push to main)

```
Backend checks:
  ├─ ruff check .                    (linting)
  ├─ mypy .                          (type checking)
  └─ pytest --asyncio-mode=auto      (unit + integration tests)
       DATABASE_URL=sqlite+aiosqlite:///:memory:
       (no real PostgreSQL needed in CI)

Frontend checks:
  ├─ npm ci
  ├─ tsc --noEmit                    (TypeScript type checking)
  └─ npm run build                   (Vite production build)
```

### `.github/workflows/deploy.yml` (runs on push to `main` only)

```
1. Configure AWS credentials (OIDC)
2. Login to ECR
3. Build & push backend image:  $ECR_REGISTRY/backend:$SHA
4. Build & push frontend image: $ECR_REGISTRY/frontend:$SHA
5. Update ECS task definition with new image tags
6. Deploy to ECS service (rolling update, zero downtime)
```

---

## 14. Configuration Reference

Copy `.env.example` to `.env` and fill in values:

| Variable | Default | Required | Description |
|---|---|---|---|
| `SECRET_KEY` | — | Yes | JWT signing secret (use `openssl rand -hex 32`) |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/ai_review` | Yes | Async PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | No | Redis connection (not yet active) |
| `OPENAI_API_KEY` | — | Yes | OpenAI API key for LLM reviews |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | No | Override for Azure/local LLM |
| `LLM_MODEL` | `gpt-4o-mini` | No | OpenAI model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | No | sentence-transformers model |
| `EMBEDDING_DIMENSION` | `384` | No | Must match model output dim |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | No | JWT expiry |
| `CHUNK_SIZE` | `512` | No | Lines per code chunk |
| `CHUNK_OVERLAP` | `64` | No | Overlap lines between chunks |
| `MAX_FILE_SIZE_KB` | `500` | No | Skip files larger than this |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | No | CORS origins |

---

## 15. Local Development Setup

### Prerequisites
- Docker + Docker Compose
- (Optional) Python 3.12 + Node 20 for running outside Docker

### With Docker Compose
```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and a generated SECRET_KEY

docker compose up --build
# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs  (FastAPI auto-generated Swagger UI)
```

### Backend Only (for development)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev  # Vite dev server on :5173, proxies /api to :8000
```

### Running Tests
```bash
cd backend
DATABASE_URL=sqlite+aiosqlite:///:memory: pytest -v
```

---

## 16. Known Limitations & TODOs

| Area | Issue | Notes |
|---|---|---|
| **Redis cache** | `InMemoryCache` used everywhere — Redis is configured but never connected | `cache.py` has `# TODO: implement RedisCacheBackend using aioredis` |
| **SQL injection risk** | `search_service.py` string-interpolates `repository_id` into a raw SQL `text()` query | Should use bound parameters |
| **LLM truncation** | Review content truncated to 8000 chars hardcoded | No retry logic; large files get incomplete reviews |
| **Admin RBAC** | `require_admin` dependency exists but applied to zero routes | Admin features (user management, cross-user repos) not yet built |
| **Disk cleanup** | Cloned repos in `/tmp/ai_code_review_repos/` are never deleted after indexing | Will fill disk on a busy server |
| **No streaming** | LLM reviews block until full response received | Could stream tokens for better UX |
| **In-memory cache** | Lost on restart; not shared across multiple backend instances | Redis integration needed for horizontal scaling |
| **No pagination** | List endpoints return all results | Needs cursor/offset pagination for large datasets |
| **Single embedding model** | Model is hardcoded at startup; changing requires restart | Could support per-repo embedding model selection |

---

## 17. Interview Prep: Key Talking Points

### "Walk me through the indexing pipeline"
When a user adds a repository, the backend kicks off a `BackgroundTask` (FastAPI's async background job system). It transitions the repository's status through `pending → cloning → indexing → ready`. First, GitPython shallow-clones the repo (depth=1 to keep it fast). Then `file_utils.walk_repository_files` recursively walks the directory, skipping irrelevant folders and files above the size limit. Each file is read and split into overlapping 512-line chunks (64-line overlap so context isn't lost at chunk boundaries). Each chunk is encoded to a 384-dimensional vector by `sentence-transformers` running locally, then persisted to PostgreSQL as a `code_chunks` row with a `vector(384)` column managed by pgvector.

### "Why pgvector instead of Pinecone/Weaviate?"
Simplicity and consistency. pgvector lets us store relational metadata (users, repos, files) and vector embeddings in the same PostgreSQL instance, with full ACID guarantees. A repository either indexes fully or not at all. For the scale of a typical codebase (tens of thousands of chunks), IVFFlat approximate nearest-neighbor search is fast enough without an additional infrastructure component to operate.

### "How does semantic search work?"
The user's query string is run through the same `all-MiniLM-L6-v2` sentence-transformers model as the indexed chunks. This produces a 384-dim vector. We then run a pgvector cosine distance query (`<=>` operator) across all `code_chunks`, filtered optionally by repository. The IVFFlat index makes this sub-millisecond at scale. Results are ranked by cosine similarity, and the top N chunks (with their file path and line range) are returned.

### "How does the AI code review work?"
We reconstruct the file's full content from stored code chunks (ordered by `chunk_index`), truncate to 8000 chars, and send it to the LLM via LangChain's `ChatOpenAI`. The system prompt tells the model to act as a senior reviewer and return a strict JSON array of issues. Each issue has `severity` (critical/high/medium/low/info), a `description`, and a `suggested_fix`. We parse the JSON response and store it in `review_history`.

### "How is authentication handled?"
Standard JWT with bcrypt. On registration, passwords are hashed with bcrypt via passlib. On login, we verify the password against the stored hash, then issue an HS256 JWT signed with `SECRET_KEY`, containing the user's UUID as the `sub` claim. FastAPI's dependency injection system decodes the token on every protected request, fetches the user from the database, and injects it into route handlers. The frontend stores the token in `localStorage` and Axios interceptors attach it to every request.

### "How does the frontend handle protected routes?"
`AuthContext` wraps the app and exposes a `useAuth()` hook. On mount, it reads the token from `localStorage` and validates it by calling `GET /auth/me`. If valid, the user is set in context. `ProtectedRoute` is a wrapper component that checks `useAuth()` and redirects to `/login` if no user is present. React Router's nested routes ensure all app pages go through this guard.

### "What would you improve?"
1. Wire up Redis for a shared cache so the app can scale horizontally
2. Fix the SQL injection risk in `search_service.py` by using SQLAlchemy bound parameters
3. Add streaming LLM responses for better review UX
4. Delete cloned repo directories after indexing to reclaim disk space
5. Add cursor-based pagination to all list endpoints
6. Implement the admin RBAC routes (user management, cross-user repository visibility)
