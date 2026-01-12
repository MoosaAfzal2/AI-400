---
id: "004"
title: "Todo API Technical Implementation Plan"
stage: "plan"
date: "2026-01-12"
surface: "agent"
model: "claude-haiku-4.5"
feature: "001-todo-api-auth"
branch: "001-todo-api-auth"
user: "user"
command: "/sp.plan"
labels: ["architecture", "implementation-plan", "fastapi", "async-sqlmodel", "jwt-authentication"]
links:
  spec: "specs/001-todo-api-auth/spec.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - specs/001-todo-api-auth/plan.md
tests: []
---

## Prompt

```
Generate a technical implementation plan using the following modern tech stack:
- Framework: FastAPI (Async)
- Database: Neon Postgres
- ORM: SQLModel (with Async engine)
- Migrations: Alembic
- Auth: JWT-based authentication (OAuth2 with PasswordRequestForm)

Architecture Requirements:
- Use an application factory pattern.
- Implement strictly async database sessions.
- Define a One-to-Many relationship between Users and Todos.
- Ensure all environment variables (DB URL, Secret Keys) are managed via .env.
```

## Response snapshot

Generated comprehensive 14-section technical implementation plan for Todo API with Authentication. Plan covers: (1) Executive summary with key deliverables; (2) Architecture overview with technology stack rationale; (3) Data model with SQLModel definitions, relationships, indexes, validation rules; (4) Authentication system with dual-token strategy (access 1h + refresh 7d), token flows, security decisions; (5) API endpoints with complete request/response contracts for 5 auth endpoints + 5 todo endpoints + 2 operational endpoints; (6) Error handling taxonomy with 15+ error codes across 5 categories with HTTP mappings; (7) Project structure with complete directory layout and dependencies; (8) 8-phase implementation plan (10-12 days) with dependency ordering and verification steps; (9) Skill usage strategy for async-sqlmodel, fastapi-builder, pytest-testing; (10) Critical files matrix; (11) Verification and acceptance criteria (unit, integration, performance, security, coverage); (12) Risk mitigation; (13) Environment configuration; (14) Success criteria and next steps.

## Outcome

- ✅ Impact: Comprehensive implementation blueprint ready for execution. Plan includes 1,079 lines of detailed specifications covering all aspects from architecture through production hardening. All 41+ functional requirements from specification mapped to implementation phases with explicit deliverables and verification checkpoints.
- 🧪 Tests: Plan includes 85%+ coverage target with specific test categories (unit, integration, performance, security). All 15+ error codes explicitly testable via test matrix. Performance benchmarks defined (register <500ms, login <500ms, create todo <200ms).
- 📁 Files: specs/001-todo-api-auth/plan.md (1,079 lines); all critical files listed with phase assignments and dependencies.
- 🔁 Next prompts: Ready for `/sp.tasks` to generate dependency-ordered implementation tasks. Implementation can begin with Phase 1 (Foundation).
- 🧠 Reflection: Plan demonstrates alignment between specification requirements and technical implementation. Application factory pattern clearly defined. Async-first architecture throughout (AsyncSession, AsyncEngine, async routes, async services). Error handling comprehensive with 15+ distinct codes. All user stories directly mapped to endpoints and test scenarios. No ambiguities remain for implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None. All architectural decisions justified and alternatives considered. Risk mitigation section addresses all identified risks.
- Graders run and results (PASS/FAIL): Architecture Completeness: PASS (all layers defined). API Contract Clarity: PASS (all endpoints specified with request/response examples). Data Model Completeness: PASS (all entities, relationships, indexes defined). Testing Strategy: PASS (coverage targets and test categories specified). Security Posture: PASS (dual-token system, bcrypt cost factor, token blacklist, error handling).
- Prompt variant (if applicable): N/A (first planning iteration)
- Next experiment: Execute Phase 1 with fastapi-builder and async-sqlmodel skills. Create tasks.md from phase breakdown.

---

## Plan Structure Summary

### Architecture Decisions
- **Web Framework**: FastAPI (native async/await, automatic OpenAPI documentation)
- **Database ORM**: SQLModel (type-safe, async-first, Pydantic v2 integration)
- **Database**: Neon Postgres (serverless, async-ready, managed)
- **Async Driver**: asyncpg (high-performance async Postgres)
- **Authentication**: JWT (HS256) with dual-token pattern
- **Password Hashing**: bcrypt cost factor 10 (~100ms per hash)
- **Migrations**: Alembic with async support
- **Logging**: Structured JSON (machine-parseable, audit-ready)
- **Metrics**: Prometheus-compatible format

### Key Architectural Patterns
1. **Application Factory**: Single `create_app()` function for all initialization
2. **Async Throughout**: AsyncSession, AsyncEngine, async routes, async services
3. **Layered Architecture**: Routes → Schemas → Services → Models → Database
4. **One-to-Many Relationships**: User→Todos, User→RefreshTokens
5. **Dependency Injection**: FastAPI `Depends()` for request-scoped dependencies

### Data Model
**4 Tables**:
- Users (id, email UNIQUE, password_hash, timestamps, is_active)
- Todos (id, user_id FK, title, description, is_completed, timestamps)
- RefreshTokens (id, user_id FK, token_jti UNIQUE, issued_at, expires_at, revoked_at, ip_address)
- TokenBlacklist (id, user_id FK, token_jti UNIQUE, token_type, revoked_at, reason, expires_at)

**Indexes**: users(email), todos(user_id, created_at), refresh_tokens(user_id, token_jti), token_blacklist(token_jti, expires_at)

### Authentication Strategy
- **Access Token**: Short-lived (1 hour), JWT HS256, stateless, claims: sub, email, iat, exp, jti, type
- **Refresh Token**: Long-lived (7 days), JWT HS256, database-backed, claims: sub, iat, exp, jti, type
- **Security**: bcrypt cost 10, password validation (8+ chars with mixed types), token blacklist on logout

### API Endpoints (13 total)
**Authentication (5)**:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- POST /auth/change-password

**Todos (5)**:
- GET /todos (with pagination)
- POST /todos
- GET /todos/{id}
- PUT /todos/{id}
- DELETE /todos/{id}

**Operations (2)**:
- GET /health
- GET /metrics

### Error Handling (15+ codes)
- AUTH_001-007 (Authentication errors, 401)
- AUTHZ_001-002 (Authorization errors, 403)
- VALIDATION_001-008 (Validation errors, 422)
- RESOURCE_001-002 (Not found, 404)
- SERVER_001-004 (Server errors, 500)

### Implementation Phases (8 phases, 10-12 days)
1. **Foundation** (Days 1-2): Config, database, environment
2. **Models & Migrations** (Days 2-4): SQLModel definitions, Alembic
3. **Authentication** (Days 4-6): JWT, bcrypt, auth services
4. **Auth Routes** (Days 6-7): /auth/* endpoints
5. **Todo Routes** (Days 7-9): /todos/* endpoints with authorization
6. **Observability** (Days 9-10): Health, metrics, logging
7. **Testing** (Days 10-11): 85%+ coverage
8. **Hardening** (Days 11-12): Security, performance, docs

### Project Structure
```
todo-api/
├── src/todo_api/
│   ├── __init__.py (app factory)
│   ├── config.py (settings)
│   ├── database.py (AsyncEngine, AsyncSessionLocal)
│   ├── models/ (base, user, todo, token)
│   ├── schemas/ (auth, todo, error, pagination)
│   ├── routes/ (auth, todos, health, metrics)
│   ├── services/ (auth, user, todo, token)
│   ├── security.py (JWT, bcrypt)
│   ├── dependencies.py (DI)
│   ├── exceptions.py
│   └── middleware.py
├── migrations/ (Alembic)
├── tests/ (conftest, test_auth, test_todos, integration)
├── .env.example
├── pyproject.toml
└── README.md
```

### Dependencies (20+ packages)
FastAPI, uvicorn, SQLAlchemy[asyncio], sqlmodel, alembic, asyncpg, python-jose, passlib, pydantic, email-validator, prometheus-client, python-json-logger, pytest, pytest-asyncio, httpx

### Verification Checklist
**Unit Tests**: JWT sign/verify, bcrypt cost=10, password validation, token expiration
**Integration Tests**: Full auth flow, CRUD operations, data isolation, token revocation
**Performance**: Register <500ms, login <500ms, create todo <200ms, list todos <500ms
**Security**: No password logging, JWT signature verification, token expiration enforced, blacklist prevents reuse
**Coverage**: Overall ≥85%, security ≥95%, auth routes ≥90%, todo routes ≥85%

---

## Alignment with Specification

**All 41+ Requirements Addressed**:
- FR-001-008: Auth requirements → /auth/* endpoints + auth_service
- FR-009-020: Todo CRUD requirements → /todos/* endpoints + todo_service
- FR-021-024: Data persistence → SQLModel + Postgres
- FR-003a: Password validation → security.py validation functions
- FR-004a: Bcrypt cost 10 → config.BCRYPT_COST_FACTOR = 10
- FR-006a-b: Dual-token system → token refresh endpoint
- FR-008a-e: Token expiration + blacklist → token_service
- FR-025-27: Password change → /auth/change-password endpoint
- FR-028-29: API schemas → All request/response schemas in plan
- FR-030-32: Tech stack → FastAPI + async-sqlmodel + Pydantic v2
- FR-033-36: Observability → logging_config.py + /health + /metrics
- FR-037-39: Token storage → RefreshToken + TokenBlacklist tables
- FR-040-41: Error handling → 15+ error codes with HTTP mappings

---

## Production Readiness

✅ Environment configuration (DATABASE_URL, JWT_SECRET_KEY, etc.)
✅ Database connection pooling (AsyncEngine pool_size=20)
✅ CORS middleware configuration
✅ Rate limiting (optional enhancement)
✅ HTTPS enforcement (production only)
✅ Bcrypt cost factor 10 configured
✅ JWT secret ≥256 bits required
✅ Token blacklist cleanup job (daily)
✅ Structured JSON logging to stdout
✅ Prometheus metrics endpoint (/metrics)
✅ Health check endpoint (/health)
✅ Graceful shutdown for database
✅ Comprehensive API documentation (FastAPI auto-docs)
✅ README covers setup and deployment

