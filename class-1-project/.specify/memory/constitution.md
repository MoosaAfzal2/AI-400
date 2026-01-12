# Todo API with Authentication Constitution

## Core Principles

### I. Security First

Authentication and data isolation are non-negotiable. Every API endpoint must enforce user-level data access controls.

**Rules**:
- OAuth2 with JWT (HS256) required for all protected endpoints
- JWT tokens MUST include: sub (user_id), email, iat, exp, jti, type
- Access tokens expire in 1 hour; refresh tokens expire in 7 days
- Argon2 password hashing (minimum cost factor 10 = ~100ms per operation)
- All user passwords MUST be hashed before storage; zero passwords in plain text
- Token blacklist/revocation on logout MUST prevent token reuse
- Every database query filtering by user_id; MUST enforce at service layer
- Cross-user access attempts return 403 Forbidden (not 401)
- No sensitive data in error messages (no user existence leaks)

**Rationale**: Data breaches and auth failures directly undermine user trust. Security failures are non-recoverable.

---

### II. Asynchronous Performance (Non-Blocking I/O)

All database and I/O operations MUST be fully async using AsyncSession and asyncpg driver.

**Rules**:
- AsyncEngine with asyncpg driver configured for Neon Postgres
- AsyncSession for all database operations (no synchronous I/O)
- Async context managers for resource cleanup
- FastAPI routes MUST be async functions
- Middleware MUST support async request/response handling
- Connection pooling: pool_size=20, pool_pre_ping=True
- No blocking operations in request handlers (password hashing offloaded to service layer)
- Graceful error handling on connection failures (circuit breaker pattern)

**Rationale**: Async-first enables high concurrency (1000+ concurrent users) without thread pools. Non-blocking improves latency and resource efficiency.

---

### III. Maintainability Through Type Safety & Clear Architecture

All code MUST use strict type hints and follow layered architecture (Routes → Schemas → Services → Models → Database).

**Rules**:
- Python 3.12+ required
- Pydantic v2 models for all request/response validation
- SQLModel for type-safe ORM with async support
- Every function MUST have type hints (parameters and return types)
- Layered architecture strictly enforced:
  - Routes: HTTP handling, input validation, dependency injection
  - Schemas: Pydantic request/response models
  - Services: Business logic, CRUD operations, authorization
  - Models: SQLModel database entities
  - Database: AsyncSession, AsyncEngine, migrations
- No circular imports between layers
- Maximum function length: 50 lines (encourage smaller, composable functions)
- Variable names MUST be self-documenting (no `u`, `t`, `x` for user/todo/index)

**Rationale**: Type safety catches errors early. Layered architecture enables parallel development, testing, and maintenance.

---

### IV. Reliability Through Comprehensive Testing

All features MUST include async tests using pytest + pytest-asyncio; minimum 85% coverage.

**Rules**:
- TDD mandatory: Tests written before implementation
- Unit tests for security, validation, business logic
- Integration tests for API endpoints and user flows
- End-to-end tests for complete user journeys (register → login → CRUD)
- Async tests MUST use pytest.mark.asyncio
- Test database isolation: separate .env.test configuration
- Fixtures for: async session, test users, test todos
- Every error code MUST have at least one test case
- Coverage minimum 85% (enforced in CI/CD)
- No test skips without explicit rationale (marked with TODO)

**Rationale**: Comprehensive tests prevent regressions, catch edge cases early, and enable confident refactoring.

---

### V. Observability & Operational Readiness

All errors, metrics, and health status MUST be observable in production.

**Rules**:
- Structured JSON logging for all auth events, errors, and request lifecycle
- Request/response logging with context (user_id, request_id, timestamp)
- Prometheus-compatible metrics endpoint (/metrics):
  - HTTP request count (by method, endpoint, status)
  - Request latency (p50, p95, p99)
  - Authentication success/failure rates
  - Database operation latency
- Health check endpoint (/health) returns system status:
  - Database connectivity
  - Token blacklist service availability
  - Timestamp
- All errors follow standardized format:
  ```json
  {
    "error_code": "AUTH_001",
    "message": "Invalid credentials",
    "details": {...},
    "timestamp": "ISO8601",
    "request_id": "uuid"
  }
  ```
- 15+ error codes with explicit HTTP status mapping (AUTH_* → 401, AUTHZ_* → 403, VALIDATION_* → 422, etc.)
- No sensitive data in logs (passwords, tokens, credit cards)

**Rationale**: Observability enables rapid incident detection, root cause analysis, and SLO compliance.

---

### VI. Database Integrity & Versioning

All schema changes MUST go through Alembic migrations; no direct database modifications allowed.

**Rules**:
- Alembic for all schema migrations (not manual SQL)
- Migration naming convention: XXX_descriptive_name.py
- Migration history preserved and version-controlled in git
- Migrations MUST be reversible (downgrade tested)
- Foreign key constraints enforced with CASCADE on user deletion
- All tables MUST have created_at, updated_at timestamps
- Indexes MUST be created for frequent query filters (user_id, email, token_jti)
- Connection string stored in .env (DATABASE_URL), never in code
- Backup strategy documented (Neon Postgres managed backups assumed)

**Rationale**: Alembic migrations enable safe schema evolution, rollback capability, and audit trails.

---

## Additional Constraints

### Technology Stack (Non-Negotiable)

- **Web Framework**: FastAPI >= 0.104.0 (native async, automatic OpenAPI docs)
- **Database ORM**: SQLModel >= 0.0.14 (async-first, type-safe)
- **Database**: Neon Postgres (serverless, async-ready, no version constraints)
- **Async Driver**: asyncpg >= 0.29.0 (high-performance async Postgres)
- **Authentication**: python-jose >= 3.3.0 (JWT), passlib >= 1.7.4 (bcrypt)
- **Validation**: Pydantic >= 2.0.0 (runtime validation, IDE support)
- **Migrations**: Alembic >= 1.12.0 (schema versioning)
- **Testing**: pytest >= 7.4.0, pytest-asyncio >= 0.21.0
- **Logging**: python-json-logger >= 2.0.0 (structured JSON)
- **Metrics**: prometheus-client >= 0.19.0 (Prometheus format)
- **Settings**: pydantic-settings >= 2.0.0 (environment-based config)

**Rationale**: This stack enables production-grade async APIs with type safety and comprehensive testing.

---

### API Standards

- **Format**: RESTful JSON API
- **Versioning**: /api/v1/ prefix for future compatibility
- **HTTP Methods**: GET (read), POST (create), PUT (update), DELETE (delete)
- **Status Codes**: 201 (created), 400 (validation error), 401 (auth), 403 (authz), 404 (not found), 500 (server error)
- **Pagination**: skip/limit parameters with has_more flag
- **Error Format**: Standardized JSON with error_code, message, details, timestamp
- **HTTPS**: Mandatory in production; enforced via middleware

**Rationale**: RESTful standards enable interoperability and predictable client implementations.

---

### Code Quality Standards

- **Formatter**: Black (line length 88)
- **Linter**: Ruff (strict, no exceptions without justification)
- **Type Checking**: mypy (strict mode enabled)
- **Import Organization**: isort (standard library → dependencies → local)
- **Docstrings**: Required for public APIs (one-liner minimum)
- **Comments**: Only for non-obvious logic; code should be self-documenting
- **No Magic Numbers**: Named constants for all configuration values
- **No Hardcoded Secrets**: .env file only; never commit credentials

**Rationale**: Consistent code quality improves maintainability and reduces onboarding time.

---

### Deployment & Operations

- **Containerization**: Dockerfile for containerized deployment (multi-stage build)
- **Local Development**: docker-compose.yml for local Neon Postgres simulation
- **Environment Management**: .env.example template provided; .env never committed
- **Secrets Management**: JWT_SECRET_KEY, DATABASE_URL, BCRYPT_COST_FACTOR in .env
- **Graceful Shutdown**: Database connections properly closed on shutdown
- **Horizontal Scaling**: Stateless design; sessions not tied to instances
- **Monitoring**: Ready for Datadog, New Relic, or cloud-native monitoring

**Rationale**: Container-ready and stateless design enable cloud-native deployment patterns.

---

## Governance

### Amendment Procedure

- Amendments require justification linking to identified gap or issue
- Proposed amendments MUST be reviewed by team lead before ratification
- Constitution changes MUST NOT affect in-flight tasks without explicit communication
- Each amendment MUST increment version per semantic versioning (see below)
- Amendment changelog MUST be maintained in git commit messages

### Versioning Policy

- **MAJOR bump**: Principle removals, backward-incompatible constraint changes, tech stack replacements
- **MINOR bump**: New principles added, materially expanded guidance, new constraint classes
- **PATCH bump**: Clarifications, typo fixes, non-semantic refinements, examples added

### Compliance Review

- Every PR MUST verify compliance with Core Principles (security, async, maintainability, testing, observability)
- Every task MUST reference applicable principles in acceptance criteria
- Pre-commit hooks SHOULD verify: type hints, linting, test coverage baseline
- Release gate: 85%+ test coverage, zero high-severity security issues, all tests passing

### Success Criteria (From User Request)

- ✅ Secure User Signup/Login flow (enforced by Principle I: Security First)
- ✅ Fully functional Todo CRUD with user-level data privacy (Principle I + Schema migrations)
- ✅ Successful end-to-end async database integration (Principle II: Async Performance)
- ✅ Passing test suite with 85%+ coverage (Principle IV: Comprehensive Testing)

---

**Version**: 1.0.0 | **Ratified**: 2026-01-12 | **Last Amended**: 2026-01-12

