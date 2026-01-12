---
name: fastapi-builder
description: |
  Build and extend FastAPI applications from hello-world to production-grade APIs.
  This skill should be used when users want to create new FastAPI projects, add features
  (routing, validation, auth, database integration, middleware), debug FastAPI-specific
  issues, or deploy applications to Docker/Kubernetes. Always fetches latest official
  FastAPI documentation before implementation to ensure correct API patterns and best practices.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing FastAPI structure, patterns, conventions, Python version, async setup |
| **Conversation** | Specific requirements: features, endpoints, auth needs, deployment target |
| **Skill References** | Domain patterns from `references/` (routing, validation, auth, database, deployment) |
| **Fetch Docs** | Use `fetch-library-docs` skill to get latest FastAPI documentation before implementation |

Ensure all required context is gathered before implementing.

---

## Skill Triggers & Use Cases

| Trigger | Skill Action |
|---------|--------------|
| "Create a new FastAPI project" | Scaffold project with hello-world → extensible structure |
| "Add an endpoint that does X" | Generate route with validation, docs, tests |
| "Set up authentication" | Implement JWT/OAuth2/API keys from official patterns |
| "Integrate with database" | Add SQLAlchemy async setup with CRUD operations |
| "Add middleware/error handling" | Implement exception handlers, middleware chains |
| "Deploy to Docker/Kubernetes" | Generate Dockerfile, docker-compose, K8s manifests |
| "FastAPI error: X" | Debug using skill knowledge + fetch latest docs |

---

## Required Clarifications

Before implementing, ask the user these questions (gather upfront before starting work):

### 1. **Project Type & Scale** ❓
   - Are you building a new project from scratch, or adding features to an existing one?
   - Will this have multiple domains/features, or is it a simple single-purpose API?
   - **Affects**: Choosing between minimal (flat) vs modular (routers) structure

### 2. **Authentication Needs** ❓
   - Does your API need authentication? If yes, which method?
     - **API Keys** (simple, header/query based, no login flow)
     - **JWT** (stateless tokens, suitable for single-page apps and mobile)
     - **OAuth2** (third-party authentication, federated identity)
     - **No auth** (public API)
   - **Affects**: security.py and auth routing setup

### 3. **Database Requirement** ❓
   - Do you need persistent data storage?
   - If yes: SQL (PostgreSQL/MySQL/SQLite) or NoSQL (MongoDB)?
   - Will you have complex relationships and transactions?
   - **Affects**: models.py, database.py, and CRUD patterns

### 4. **Deployment Target** ❓
   - Where will this run in production?
     - **Docker + Kubernetes** (recommended, orchestrated scaling)
     - **Docker only** (single server containerization)
     - **Traditional servers** (systemd/supervisord, VPS)
   - **Affects**: Dockerfile, docker-compose, or traditional deployment files

### 5. **Python & Environment** ❓
   - What Python version are you targeting? (3.9+, 3.10+, 3.11+?)
   - Any existing constraints (packages already in use, etc.)?
   - **Affects**: requirements.txt versions and syntax (e.g., `str | None` vs `Optional[str]`)

---

## User Input Not Required For

These are inferred or handled flexibly; don't ask unless user mentions them:
- Framework choice (it's FastAPI—this skill is framework-specific)
- Async/await (all code is async by default)
- Testing framework (pytest is standard)
- Code style (follows modern Python conventions)

---

## Core Workflows

### 1. New Project Scaffolding

```
User Request → Gather Requirements
  ├─ Project name, structure preference (flat, modular)
  ├─ Features needed (auth, database, async, validation)
  ├─ Python version & environment
  └─ Deployment target
         ↓
Fetch Official Docs (fetch-library-docs)
  ├─ Core concepts (Starlette, Pydantic integration)
  ├─ Project structure best practices
  └─ ASGI application setup
         ↓
Understand Production Architecture (see project-structure.md)
  ├─ Layered architecture: API → Core → DB → Models → Services
  ├─ Async database setup with connection pooling
  ├─ Dependency injection patterns
  ├─ Authentication flow (single-session, token rotation)
  └─ Error handling with privacy-focused responses
         ↓
Generate Scaffolding
  ├─ pyproject.toml (dependencies, metadata)
  ├─ main.py (application entry point with lifespan)
  ├─ Configuration module (settings, environment)
  ├─ Database setup (if requested, see database-patterns.md)
  ├─ Auth setup (if requested, see jwt-security-patterns.md)
  ├─ Docker/K8s files (if requested, see deployment-architecture.md)
  ├─ API routes with correct status codes (see api-design-patterns.md)
  └─ Basic tests (pytest with fixtures, see testing-architecture.md)
         ↓
Provide Next Steps
  └─ How to extend, test, deploy
```

### 2. Add Feature to Existing Project

```
User Request → Analyze Codebase
  ├─ Read main.py and project structure (compare with project-structure.md)
  ├─ Identify existing patterns (dependency injection, error handling)
  ├─ Check configuration setup
  └─ Understand database layer (if present)
         ↓
Fetch Official Docs (for specific feature)
  └─ Get correct patterns for requested feature
         ↓
Generate Implementation
  ├─ Match existing code patterns
  ├─ Follow layered architecture (API → Core → DB → Models)
  ├─ Add to appropriate module using correct HTTP status codes
  ├─ Include validation & error handling with privacy
  └─ Add tests (unit + integration, see testing-architecture.md)
         ↓
Integrate & Validate
  └─ Show modified files with line references
```

### 3. Authentication Setup

```
Determine Auth Type (from user requirements)
  ├─ API Keys (simple, header-based)
  ├─ JWT (stateless tokens, refresh tokens) ⭐ Recommended
  └─ OAuth2 (third-party integration)
         ↓
Fetch Official Docs (fetch-library-docs)
  └─ Get latest FastAPI security patterns
         ↓
Implement Security Scheme (see jwt-security-patterns.md)
  ├─ RS256 asymmetric JWT (not HS256)
  ├─ Load RSA keys from environment (production) or file path (dev)
  ├─ Access tokens: 15 minutes expiry (short-lived)
  ├─ Refresh tokens: 7 days expiry (long-lived)
  ├─ Token type field for validation (access vs refresh)
  └─ Bcrypt password hashing with cost factor 12
         ↓
Implement Token Management (see jwt-security-patterns.md)
  ├─ Single-session enforcement: DELETE all tokens on login
  ├─ Token rotation: DELETE old refresh token before issuing new pair
  ├─ Refresh token whitelist in database (for revocation)
  └─ JWKS endpoint at /.well-known/jwks.json for distributed verification
         ↓
Add to Endpoints (see api-design-patterns.md)
  ├─ /api/v1/auth/sign-up (POST, 201 Created)
  ├─ /api/v1/auth/login (POST, OAuth2PasswordRequestForm)
  ├─ /api/v1/auth/refresh (POST, with token rotation)
  ├─ /api/v1/auth/logout (POST, revoke refresh token)
  └─ Apply bearer token to protected endpoints via Depends()
         ↓
Test & Document (see testing-architecture.md)
  ├─ Generate test fixtures (test_user, auth_headers)
  ├─ Test token creation, validation, expiration
  ├─ Test single-session enforcement
  └─ Test token rotation on refresh
```

### 4. Database Integration

```
Determine Database Type
  ├─ SQLAlchemy + PostgreSQL/MySQL/SQLite
  └─ (Other NoSQL patterns in references)
         ↓
Fetch Official Docs (fetch-library-docs)
  └─ Get latest SQLAlchemy async patterns
         ↓
Setup Database Layer (see database-patterns.md)
  ├─ Async engine with connection pooling (pool_size=10, max_overflow=5)
  ├─ AsyncSession factory with expire_on_commit=False
  ├─ pool_recycle=3600 & pool_pre_ping=True for production
  └─ get_session dependency for FastAPI injection
         ↓
Create Models & Schemas (see project-structure.md)
  ├─ SQLModel ORM models with proper indexes
  ├─ UUID primary keys & server-side timestamps
  ├─ Soft-delete pattern (is_active field)
  ├─ Pydantic schemas for API layer
  └─ Cascade deletes for relationships
         ↓
Implement CRUD Operations (see database-patterns.md)
  ├─ Create (INSERT with validation)
  ├─ Read (SELECT with eager loading to prevent N+1)
  ├─ Update (UPDATE with partial updates using setattr)
  ├─ Delete (soft delete via is_active or hard delete)
  └─ Pagination with skip/limit parameters
         ↓
Add Dependency for DB Session
  ├─ Create async context for session management
  └─ Inject into route handlers via Depends(get_session)
         ↓
Test with In-Memory SQLite (see testing-architecture.md)
  └─ Use StaticPool for isolated, fast tests
```

### 5. Error Handling & Middleware

```
Identify Error Types (see api-design-patterns.md)
  ├─ Validation errors (Pydantic) → 422 Unprocessable Entity
  ├─ Database errors (integrity, connection) → 409 Conflict or 503 Service Unavailable
  ├─ Authentication errors (401, 403)
  └─ Business logic errors → 400 Bad Request
         ↓
Create Exception Classes
  ├─ Custom exception hierarchy
  ├─ Exception handlers with proper HTTP status codes
  └─ Privacy-focused error messages (no internal details in responses)
         ↓
Add Middleware (if needed)
  ├─ Request/response logging (structured JSON format)
  ├─ CORS handling (see security-checklist.md)
  ├─ Request ID tracking (for debugging)
  └─ Compression
         ↓
Implement Error Responses (see api-design-patterns.md)
  ├─ Standardized error format with error codes
  ├─ Include request_id for server-side lookup
  ├─ Include timestamp for correlation
  └─ Do NOT expose internal exceptions to clients
         ↓
Security Verification (see security-checklist.md)
  ├─ Verify error responses don't leak sensitive data
  ├─ Check authentication error format (401 with WWW-Authenticate header)
  └─ Test authorization error format (403 Forbidden)
```

### 6. Deployment

```
Determine Target Environment
  ├─ Docker + Kubernetes (recommended, see deployment-architecture.md)
  ├─ Docker only (single server, see deployment-architecture.md)
  └─ Traditional servers (systemd/supervisord)
         ↓
Fetch Official Docs (fetch-library-docs)
  └─ Get latest deployment patterns
         ↓
Generate Deployment Files (see deployment-architecture.md)
  ├─ Dockerfile: multi-stage (builder + runtime), non-root user
  ├─ docker-compose.yml: PostgreSQL, Redis, API with health checks
  ├─ Kubernetes manifests:
  │   ├─ Deployment (3 replicas, resource limits, probes)
  │   ├─ Service (LoadBalancer or ClusterIP)
  │   ├─ ConfigMap (non-secret config)
  │   └─ Secrets (sensitive data)
  ├─ .dockerignore & .gitignore (exclude large/sensitive files)
  └─ Environment configuration (.env, .env.production)
         ↓
Configure for Production (see deployment-architecture.md)
  ├─ Uvicorn with worker process configuration
  ├─ Health check endpoints (/api/v1/health, /api/v1/ready)
  ├─ Database migrations with Alembic on startup
  ├─ Structured logging (JSON format for cloud ingestion)
  ├─ Readiness probe: check database connectivity
  ├─ Liveness probe: simple health endpoint
  └─ Graceful shutdown with pre-stop sleep
         ↓
Environment Variables (see deployment-architecture.md)
  ├─ Development: DATABASE_URL, SECRET_KEY, DEBUG=True
  ├─ Production: DATABASE_URL (external), RSA_PRIVATE_KEY_CONTENT (base64)
  ├─ All secrets from environment (never hardcoded)
  └─ Kubernetes Secrets for sensitive data
         ↓
Provide Deployment Steps (see deployment-architecture.md)
  ├─ Build: docker build -t app:latest .
  ├─ Local testing: docker-compose up -d
  ├─ Kubernetes: kubectl apply -f *.yaml
  └─ Scaling: kubectl scale deployment app --replicas=5
```

---

## Decision Trees

### Project Structure Decision

```
Does project need multiple domains/features?
├─ YES → Use modular structure (routers in separate modules)
└─ NO → Use flat structure (simple_main.py + schemas.py + db.py)

Does project need configuration management?
├─ YES → settings.py with Pydantic BaseSettings
└─ NO → Inline configuration in main.py
```

### Authentication Decision

```
Need to authenticate users externally?
├─ YES → Use OAuth2/OpenID (see authentication.md: OAuth2 section)
├─ NO → Need token-based stateless auth?
│   ├─ YES → Use JWT (see authentication.md: JWT Tokens section)
│   └─ NO → Use API Keys (see authentication.md: API Keys section)
```

### Database Decision

```
Have relational data with transactions?
├─ YES → Use SQLAlchemy + PostgreSQL (see database.md: Async Setup section)
└─ NO → Consider lightweight options:
    ├─ SQLite (for development/testing) (see database.md: Async Setup section)
    └─ Mention: MongoDB patterns not included; see common-errors.md for troubleshooting

Need migrations?
├─ YES → Setup Alembic with SQLAlchemy (see deployment.md: Alembic setup)
└─ NO → Use sqlalchemy.event for schema management (see database.md: Startup/Shutdown)
```

---

## Key Patterns (Reference in references/)

### Production Architecture (MUST Know)

These reference files encode production-grade patterns extracted from real-world applications:

- **`project-structure.md`** ⭐ **START HERE** - Complete layered architecture (API, Core, DB, Models, Services layers) with code examples for each layer. Covers async database setup with connection pooling, SQLModel patterns, dependency injection, and authentication flow.

- **`database-patterns.md`** - Production async database setup (SQLAlchemy + asyncpg), connection pooling (pool_size=10, max_overflow=5), CRUD operations, transactions, query optimization, and in-memory SQLite for testing.

- **`jwt-security-patterns.md`** - RS256 asymmetric JWT implementation, token lifecycle (15-min access tokens, 7-day refresh tokens), token rotation, single-session enforcement, password hashing with bcrypt, and JWKS endpoint for distributed verification.

- **`api-design-patterns.md`** - RESTful endpoint naming (/api/v1/...), correct HTTP status codes (201, 204, 401, 403, 404, 409), request/response schemas with Pydantic, pagination, filtering, sorting, and error response formatting.

- **`testing-architecture.md`** - Pytest setup with async fixtures, in-memory SQLite for isolated tests, unit and integration test patterns, auth fixtures, and coverage reporting.

- **`deployment-architecture.md`** - Multi-stage Docker, docker-compose for local development, Kubernetes manifests, Vercel deployment, health checks (liveness/readiness probes), environment management, and complete deployment checklist.

### Core Framework Patterns

- **Routing**: Path parameters, query parameters, request bodies
- **Validation**: Pydantic models, custom validators, error responses
- **Dependency Injection**: Database sessions, authentication, shared resources
- **Async**: Event loops, async/await, sync operations in async context
- **Security**: CORS, HTTPS, CSRF (when applicable), rate limiting, authentication
- **Monitoring**: Logging, request tracing, health checks

### Quality & Deployment Checklists

- **`production-checklist.md`** - 40+ pre-deployment verification items (security config, database setup, containers, operations)
- **`security-checklist.md`** - OWASP Top 10 coverage, secrets management, security audit checklist

---

## Error Handling in Skill

When implementing:
- ✅ Fetch official docs BEFORE writing code
- ✅ Use established patterns from `references/`
- ✅ Include error handling for database, validation, auth
- ✅ Add tests for happy path + error cases
- ✅ Provide clear error messages in API responses

When uncertain:
- Use `fetch-library-docs` to get latest patterns
- Check `references/common-errors.md` for solutions
- Ask user for specific context (existing code, requirements)

---

## What This Skill Does

✅ Scaffold new FastAPI projects (hello-world → production)
✅ Generate individual features (routes, auth, database)
✅ Provide deployment configurations (Docker, Kubernetes)
✅ Debug FastAPI-specific issues with latest documentation
✅ Match existing project patterns when extending
✅ Include validation, error handling, and testing

## What This Skill Does NOT Do

❌ Deploy or manage live infrastructure
❌ Modify database in production
❌ Change project structure after initial scaffolding (requires planning)
❌ Create domain-specific business logic (beyond CRUD)
❌ Optimize already-running systems (use profiling first)
