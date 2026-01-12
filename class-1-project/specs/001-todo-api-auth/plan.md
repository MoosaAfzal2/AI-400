# Technical Implementation Plan: Todo API with Authentication

**Feature**: Todo API with Authentication (`001-todo-api-auth`)
**Date**: 2026-01-12
**Status**: Ready for Implementation
**Tech Stack**: FastAPI (async) + SQLModel + Neon Postgres + JWT + Alembic

---

## 1. EXECUTIVE SUMMARY

This plan outlines the implementation of a production-grade Todo API with robust authentication. The implementation leverages modern async-first Python technologies to ensure high concurrency support, type safety, and maintainability.

**Key Deliverables**:
- ✅ Async FastAPI application with application factory pattern
- ✅ SQLModel ORM with async SQLAlchemy engine
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ Alembic migrations with async support
- ✅ Neon Postgres database with proper schema
- ✅ 85%+ test coverage with pytest-asyncio
- ✅ Structured JSON logging and Prometheus metrics
- ✅ Comprehensive error handling (15+ error codes)

**Estimated Duration**: 10-12 days (2-week sprint)
**Primary Skills**: async-sqlmodel, fastapi-builder, pytest-testing

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Web Framework | FastAPI | >=0.104.0 | Native async/await, automatic OpenAPI docs, built-in validation |
| Database ORM | SQLModel | >=0.0.14 | Type-safe, async-first, Pydantic v2 integration |
| Database | Neon Postgres | Latest | Serverless, async-ready, managed backups |
| Async Driver | asyncpg | >=0.29.0 | High-performance async Postgres driver |
| Authentication | JWT (HS256) | python-jose | Stateless, scalable, supports dual-token pattern |
| Password Hashing | bcrypt | passlib >=1.7.4 | Cost factor 10 = ~100ms per hash, GPU-resistant |
| Migrations | Alembic | >=1.12.0 | Version-controlled schema, rollback support, async support |
| Validation | Pydantic | >=2.0.0 | Runtime validation, IDE support, FastAPI native |
| Testing | pytest + pytest-asyncio | >=7.4.0, >=0.21.0 | Async test support, fixture flexibility |
| Logging | python-json-logger | >=2.0.0 | Structured JSON logs, machine-parseable |
| Metrics | prometheus-client | >=0.19.0 | Industry-standard, Grafana-ready |
| Settings | pydantic-settings | >=2.0.0 | Environment-based configuration |

### 2.2 Architectural Patterns

**Application Factory**
```
create_app() function initializes:
  - Config from environment
  - Database engine + session factory
  - Dependency injection container
  - Middleware stack
  - Route registration
  - Error handlers
```

**Async Throughout**
- AsyncEngine with asyncpg driver
- AsyncSession for all database operations
- Async context managers for resource cleanup
- No blocking I/O in request handlers

**Layered Architecture**
```
Routes (FastAPI endpoints)
  ↓
Schemas (Pydantic request/response models)
  ↓
Services (Business logic, CRUD operations)
  ↓
Models (SQLModel database entities)
  ↓
Database (AsyncSession, AsyncEngine)
```

**One-to-Many Relationships**
- User → Todos (One user owns many todos)
- User → RefreshTokens (One user has many refresh tokens)
- Database-level foreign keys for referential integrity

---

## 3. DATA MODEL & SCHEMA

### 3.1 Entity Definitions

**User** (SQLModel)
```python
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    is_active: bool = True

    # Relationships
    todos: List["Todo"] = Relationship(back_populates="user")
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
```

**Todo** (SQLModel)
```python
class Todo(SQLModel, table=True):
    __tablename__ = "todos"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    user: User = Relationship(back_populates="todos")
```

**RefreshToken** (SQLModel)
```python
class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_jti: str = Field(unique=True, index=True)
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None

    # Relationship
    user: User = Relationship(back_populates="refresh_tokens")
```

**TokenBlacklist** (SQLModel)
```python
class TokenBlacklist(SQLModel, table=True):
    __tablename__ = "token_blacklist"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(foreign_key="users.id", nullable=True)
    token_jti: str = Field(unique=True, index=True)
    token_type: str  # 'access' or 'refresh'
    revoked_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str  # 'logout', 'password_change', 'admin_revoke'
    expires_at: datetime
```

### 3.2 Database Indexes

```sql
-- Fast email lookups
CREATE INDEX idx_users_email ON users(email);

-- Fast user todo list retrieval
CREATE INDEX idx_todos_user_created ON todos(user_id, created_at DESC);

-- Fast token lookups
CREATE INDEX idx_refresh_tokens_user_jti ON refresh_tokens(user_id, token_jti);

-- Fast blacklist checks + cleanup
CREATE INDEX idx_token_blacklist_jti ON token_blacklist(token_jti);
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);
```

### 3.3 Validation Rules

| Field | Rules | Error Code |
|-------|-------|-----------|
| email | Valid format, unique, required | VALIDATION_001, VALIDATION_003 |
| password (register) | 8+ chars, uppercase, lowercase, number, special | VALIDATION_002 |
| password (change) | Not same as current, meets strength requirements | VALIDATION_008 |
| title | 1-255 chars, required | VALIDATION_004, VALIDATION_005 |
| description | 0-10000 chars, optional | VALIDATION_005 |

---

## 4. AUTHENTICATION SYSTEM

### 4.1 Token Strategy

**Access Token (1 hour lifetime)**
- Type: JWT (HS256)
- Claims: `sub` (user_id), `email`, `iat`, `exp`, `jti`, `type: "access"`
- Storage: Client-side (Authorization header)
- Validation: Signature, expiration, not blacklisted
- Use: Authorize API requests

**Refresh Token (7 days lifetime)**
- Type: JWT (HS256) + Database entry
- Claims: `sub` (user_id), `iat`, `exp`, `jti`, `type: "refresh"`
- Storage: Database (RefreshToken table) + Client-side (httpOnly cookie)
- Validation: Signature, expiration, database entry exists, not revoked
- Use: Obtain new access token without re-login

### 4.2 Authentication Flow

```
Register Flow:
  POST /auth/register
    ├─ Validate email format, password strength
    ├─ Check email not already registered (VALIDATION_003)
    ├─ Hash password with bcrypt (cost=10)
    ├─ Create User record
    └─ Return user_id, email, created_at

Login Flow:
  POST /auth/login
    ├─ Validate credentials exist (AUTH_001)
    ├─ Verify password hash
    ├─ Generate access token (HS256, exp=1h)
    ├─ Generate refresh token (HS256, exp=7d)
    ├─ Store refresh token in database
    ├─ Update last_login_at
    └─ Return access_token, refresh_token, expires_in

Token Refresh Flow:
  POST /auth/refresh
    ├─ Validate refresh token signature (AUTH_006)
    ├─ Check expiration (AUTH_003)
    ├─ Query database (RefreshToken exists and not revoked)
    ├─ Generate new access token
    └─ Return new access_token, expires_in

Logout Flow:
  POST /auth/logout
    ├─ Extract tokens from request
    ├─ Add both tokens to blacklist
    ├─ Delete refresh token from database
    └─ Return success

Password Change Flow:
  POST /auth/change-password
    ├─ Verify current password (VALIDATION_007)
    ├─ Validate new password strength (VALIDATION_002)
    ├─ Check not same as current (VALIDATION_008)
    ├─ Hash and update password
    ├─ Revoke all existing refresh tokens
    └─ Return success
```

### 4.3 Security Decisions

1. **Bcrypt Cost Factor 10**:
   - ~100ms per hash on modern hardware
   - Acceptable for register/login endpoints
   - GPU-resistant (bcrypt-specific algorithm)

2. **Server-Side Refresh Token Storage**:
   - Enables immediate revocation on logout
   - Allows audit trail (ip_address, timestamps)
   - Supports concurrent session management

3. **Token Blacklist on Logout**:
   - Both access and refresh tokens blacklisted
   - Prevents token reuse after logout
   - TTL = token expiration time (cleanup removes old entries)

4. **Dual-Token Pattern**:
   - Access tokens: short-lived, stateless
   - Refresh tokens: long-lived, database-backed
   - Balances scalability with security

---

## 5. API ENDPOINTS & CONTRACTS

### 5.1 Authentication Endpoints

**POST /auth/register**
```json
Request:
  {
    "email": "user@example.com",
    "password": "MyPassword123!"
  }

Response (201):
  {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2026-01-12T20:30:00Z"
  }

Errors:
  VALIDATION_001: Invalid email format
  VALIDATION_002: Password too weak
  VALIDATION_003: Email already registered
```

**POST /auth/login**
```json
Request:
  {
    "email": "user@example.com",
    "password": "MyPassword123!"
  }

Response (200):
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
  }

Errors:
  AUTH_001: Invalid credentials
  VALIDATION_001: Missing email or password
```

**POST /auth/refresh**
```json
Request:
  {
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }

Response (200):
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
  }

Errors:
  AUTH_003: Refresh token expired
  AUTH_004: Token revoked
  AUTH_005: Invalid token format
  AUTH_006: Token signature verification failed
```

**POST /auth/logout**
```json
Request:
  Authorization: Bearer <access_token>

Response (200):
  {
    "message": "Logout successful"
  }

Errors:
  AUTH_005: Missing or invalid token
```

**POST /auth/change-password**
```json
Request:
  Authorization: Bearer <access_token>
  {
    "current_password": "OldPassword123!",
    "new_password": "NewPassword456!"
  }

Response (200):
  {
    "message": "Password changed successfully"
  }

Errors:
  VALIDATION_002: New password too weak
  VALIDATION_007: Current password incorrect
  VALIDATION_008: New password same as current
```

### 5.2 Todo Endpoints

**GET /todos**
```json
Query Parameters:
  skip: int = 0
  limit: int = 20
  is_completed: bool = null (filter by completion status)
  sort_by: str = 'created_at' (created_at, completed_at, title)
  sort_order: str = 'desc' (asc, desc)

Response (200):
  {
    "items": [
      {
        "id": "uuid",
        "user_id": "uuid",
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "is_completed": false,
        "created_at": "2026-01-12T20:30:00Z",
        "completed_at": null,
        "updated_at": "2026-01-12T20:30:00Z"
      }
    ],
    "total": 50,
    "skip": 0,
    "limit": 20,
    "has_more": true
  }

Errors:
  AUTH_002: Access token expired
  AUTH_005: Missing or invalid token
```

**POST /todos**
```json
Request:
  Authorization: Bearer <access_token>
  {
    "title": "Buy groceries",
    "description": "Milk, eggs, bread"
  }

Response (201):
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "is_completed": false,
    "created_at": "2026-01-12T20:30:00Z",
    "completed_at": null,
    "updated_at": "2026-01-12T20:30:00Z"
  }

Errors:
  VALIDATION_004: Missing title
  VALIDATION_005: Description exceeds max length
  AUTH_005: Missing token
```

**GET /todos/{id}**
```json
Response (200):
  { full todo object }

Errors:
  RESOURCE_001: Todo not found
  AUTHZ_001: Cannot access other user's todo
```

**PUT /todos/{id}**
```json
Request:
  {
    "title": "Updated title",
    "description": "Updated description",
    "is_completed": true
  }

Response (200):
  { updated todo object }

Errors:
  RESOURCE_001: Todo not found
  AUTHZ_001: Cannot update other user's todo
  VALIDATION_002: Invalid field values
```

**DELETE /todos/{id}**
```json
Response (204): No content

Errors:
  RESOURCE_001: Todo not found
  AUTHZ_001: Cannot delete other user's todo
```

### 5.3 Operational Endpoints

**GET /health**
```json
Response (200):
  {
    "status": "healthy",
    "database": "connected",
    "checks": {
      "db_connection": true,
      "redis": null
    },
    "timestamp": "2026-01-12T20:30:00Z"
  }

Response (503): Service unavailable if database offline
```

**GET /metrics**
```
Response (200): text/plain Prometheus format
  # HELP http_requests_total Total HTTP requests
  # TYPE http_requests_total counter
  http_requests_total{method="GET",endpoint="/todos",status="200"} 150

  # HELP http_request_duration_seconds Request latency
  # TYPE http_request_duration_seconds histogram
  http_request_duration_seconds_bucket{endpoint="/todos",le="0.1"} 140
```

---

## 6. ERROR HANDLING TAXONOMY

### 6.1 Standard Error Response Format

```json
{
  "error_code": "AUTH_001",
  "message": "Invalid credentials provided",
  "details": {
    "field": "email",
    "expected": "valid email format"
  },
  "timestamp": "2026-01-12T20:30:00Z",
  "request_id": "req_abc123def456"
}
```

### 6.2 Error Code Mapping

| Code | Category | HTTP | Description |
|------|----------|------|-------------|
| AUTH_001 | Authentication | 401 | Invalid credentials (email not found or password incorrect) |
| AUTH_002 | Authentication | 401 | Access token expired |
| AUTH_003 | Authentication | 401 | Refresh token expired |
| AUTH_004 | Authentication | 401 | Token revoked/blacklisted |
| AUTH_005 | Authentication | 401 | Invalid token format or missing |
| AUTH_006 | Authentication | 401 | Token signature verification failed |
| AUTH_007 | Authentication | 401 | User account not found or disabled |
| AUTHZ_001 | Authorization | 403 | User lacks permission (cross-user access) |
| AUTHZ_002 | Authorization | 403 | User lacks permission (general) |
| VALIDATION_001 | Validation | 422 | Email format invalid or missing |
| VALIDATION_002 | Validation | 422 | Password does not meet strength requirements |
| VALIDATION_003 | Validation | 422 | Email already registered |
| VALIDATION_004 | Validation | 422 | Required field missing |
| VALIDATION_005 | Validation | 422 | Field value exceeds max length |
| VALIDATION_006 | Validation | 422 | Invalid enum value |
| VALIDATION_007 | Validation | 422 | Current password incorrect |
| VALIDATION_008 | Validation | 422 | New password same as current |
| RESOURCE_001 | Not Found | 404 | Todo item not found |
| RESOURCE_002 | Not Found | 404 | User not found |
| SERVER_001 | Server Error | 500 | Database connection failure |
| SERVER_002 | Server Error | 500 | Internal server error |
| SERVER_003 | Server Error | 500 | Token blacklist service unavailable |
| SERVER_004 | Server Error | 500 | Unexpected error during password hashing |

---

## 7. PROJECT STRUCTURE

### 7.1 Directory Layout

```
todo-api/
├── src/
│   └── todo_api/
│       ├── __init__.py                    # App factory: create_app()
│       ├── config.py                      # Settings (Pydantic)
│       ├── database.py                    # AsyncEngine, AsyncSessionLocal
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py                    # Base SQLModel, timestamps mixin
│       │   ├── user.py                    # User model + relationships
│       │   ├── todo.py                    # Todo model + relationships
│       │   └── token.py                   # RefreshToken, TokenBlacklist
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py                    # Register, Login, Refresh schemas
│       │   ├── todo.py                    # Todo CRUD schemas
│       │   ├── error.py                   # ErrorResponse schema
│       │   └── pagination.py              # PaginationParams, PaginationResponse
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py                    # /auth/* endpoints
│       │   ├── todos.py                   # /todos/* endpoints
│       │   ├── health.py                  # /health
│       │   └── metrics.py                 # /metrics
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py            # Register, login, token refresh logic
│       │   ├── user_service.py            # User CRUD operations
│       │   ├── todo_service.py            # Todo CRUD with authorization
│       │   └── token_service.py           # Token validation, blacklist
│       ├── dependencies.py                # FastAPI dependency injection
│       ├── exceptions.py                  # Custom exception classes
│       ├── middleware.py                  # Error handling, logging middleware
│       ├── security.py                    # JWT encode/decode, password utils
│       └── logging_config.py              # Structured JSON logging setup
├── migrations/
│   ├── env.py                             # Alembic configuration
│   ├── script.py.mako                     # Migration template
│   ├── versions/
│   │   ├── 001_initial_schema.py          # Initial users, todos tables
│   │   ├── 002_add_tokens.py              # Add refresh_tokens table
│   │   └── 003_add_blacklist.py           # Add token_blacklist table
├── tests/
│   ├── conftest.py                        # pytest fixtures, async session
│   ├── test_auth.py                       # Auth endpoint tests
│   ├── test_todos.py                      # Todo endpoint tests
│   ├── test_health.py                     # Health check tests
│   ├── integration/
│   │   └── test_full_flows.py             # E2E flows (register→login→todo)
│   └── services/
│       ├── test_auth_service.py           # Auth service unit tests
│       ├── test_token_service.py          # Token validation tests
│       └── test_security.py               # JWT, bcrypt tests
├── .env.example                           # Environment template
├── .env.test                              # Test database config
├── pyproject.toml                         # Dependencies and configuration
├── pytest.ini                             # Pytest configuration
├── alembic.ini                            # Alembic configuration (generated)
└── README.md                              # Setup and deployment guide
```

### 7.2 Python Dependencies

```toml
[project]
dependencies = [
  "fastapi>=0.104.0",
  "uvicorn[standard]>=0.24.0",
  "sqlalchemy[asyncio]>=2.0.0",
  "sqlmodel>=0.0.14",
  "alembic>=1.12.0",
  "asyncpg>=0.29.0",
  "python-jose[cryptography]>=3.3.0",
  "passlib[bcrypt]>=1.7.4",
  "python-multipart>=0.0.6",
  "pydantic>=2.0.0",
  "pydantic-settings>=2.0.0",
  "email-validator>=2.0.0",
  "prometheus-client>=0.19.0",
  "python-json-logger>=2.0.0",
  "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.4.0",
  "pytest-asyncio>=0.21.0",
  "pytest-cov>=4.1.0",
  "httpx>=0.25.0",
]
```

---

## 8. IMPLEMENTATION PHASES (Dependency-Ordered)

### Phase 1: Foundation & Configuration (Days 1-2)

**Deliverable**: Configuration system, database connection, environment setup

**Tasks**:
1. Create project directory structure
2. Setup pyproject.toml with all dependencies
3. Implement `config.py` (Pydantic Settings)
   - Database URL, JWT secret
   - Bcrypt cost factor, token expiration
   - Logging configuration
4. Implement `database.py`
   - AsyncEngine with asyncpg pool
   - AsyncSessionLocal factory
   - Session dependency
5. Create `.env.example` and `.env.test`
6. Initialize git repository and .gitignore

**Verification**:
- [ ] `pip install -e ".[dev]"` succeeds
- [ ] Database connection successful
- [ ] Environment variables loaded correctly

---

### Phase 2: Models & Migrations (Days 2-4)

**Deliverable**: SQLModel definitions, Alembic setup, initial schema

**Tasks**:
1. Create `models/base.py` with:
   - Base SQLModel class
   - Timestamp mixin (created_at, updated_at)
2. Implement `models/user.py`
   - User entity with relationships
3. Implement `models/todo.py`
   - Todo entity with user_id FK
4. Implement `models/token.py`
   - RefreshToken and TokenBlacklist models
5. Initialize Alembic with async support
6. Generate migration: `001_initial_schema.py`
7. Create migration: `002_add_tokens.py`
8. Run migrations: `alembic upgrade head`

**Verification**:
- [ ] `alembic upgrade head` succeeds
- [ ] Database schema matches data model
- [ ] Indexes created correctly
- [ ] Foreign keys enforced

---

### Phase 3: Authentication System (Days 4-6)

**Deliverable**: JWT, password hashing, auth services

**Tasks**:
1. Implement `security.py`
   - JWT encode/decode (HS256)
   - Password hashing/verification (bcrypt, cost=10)
   - Token JTI generation
2. Implement `services/auth_service.py`
   - Register user (validate, hash password, create)
   - Login (verify, generate tokens, store refresh)
   - Token refresh (validate, generate new access token)
3. Implement `services/token_service.py`
   - Token validation (signature, expiration, blacklist)
   - Token blacklist operations
4. Implement `dependencies.py`
   - Current user extraction from token
   - Token dependency injector
5. Write tests in `tests/services/test_security.py`
   - JWT sign/verify
   - Bcrypt cost factor verification
   - Password validation rules

**Verification**:
- [ ] JWT tokens sign and verify correctly
- [ ] Bcrypt cost=10 (verify with timing)
- [ ] Blacklist prevents token reuse
- [ ] Test coverage >= 95% on security module

---

### Phase 4: Auth Endpoints (Days 6-7)

**Deliverable**: /auth/* routes operational

**Tasks**:
1. Implement `schemas/auth.py`
   - UserRegister, UserLogin request schemas
   - TokenResponse schema
   - PasswordChange schema
2. Implement `routes/auth.py`
   - POST /auth/register
   - POST /auth/login
   - POST /auth/refresh
   - POST /auth/logout
   - POST /auth/change-password
3. Implement `exceptions.py`
   - Custom exception classes
4. Implement `middleware.py`
   - Error handling middleware (ExceptionHandler)
   - Request logging middleware
5. Write tests in `tests/test_auth.py`
   - Register success/error cases
   - Login success/error cases
   - Token refresh success/error cases
   - Logout revocation

**Verification**:
- [ ] All 5 auth endpoints respond correctly
- [ ] Error codes match specification
- [ ] Token expiration enforced
- [ ] Logout invalidates tokens

---

### Phase 5: Todo Endpoints (Days 7-9)

**Deliverable**: /todos/* routes operational with authorization

**Tasks**:
1. Implement `schemas/todo.py`
   - TodoCreate, TodoUpdate, TodoResponse
   - PaginationParams, PaginationResponse
2. Implement `services/todo_service.py`
   - Create todo (associate with user)
   - Read todo (check ownership)
   - Update todo (check ownership)
   - Delete todo (check ownership)
   - List todos (filter by user, pagination)
3. Implement `routes/todos.py`
   - All 5 endpoints (GET list, GET one, POST, PUT, DELETE)
   - Authorization checks
4. Write tests in `tests/test_todos.py`
   - Create, read, update, delete
   - Pagination
   - Cross-user access denied (403)
   - Data isolation (user A can't see user B's todos)

**Verification**:
- [ ] All CRUD operations work
- [ ] 403 Forbidden on cross-user access
- [ ] Pagination works correctly
- [ ] Data isolation enforced

---

### Phase 6: Observability (Days 9-10)

**Deliverable**: Health check, metrics, structured logging

**Tasks**:
1. Implement `logging_config.py`
   - JSON log formatter
   - Request/response logging
   - Error logging with context
2. Implement `routes/health.py`
   - GET /health endpoint
   - Database connectivity check
3. Implement `routes/metrics.py`
   - GET /metrics endpoint
   - Prometheus format
   - Request count, latency, error rates
4. Add middleware for metrics collection
5. Test endpoints

**Verification**:
- [ ] /health returns status
- [ ] /metrics returns valid Prometheus format
- [ ] Logs contain request_id, user_id, status
- [ ] No sensitive data in logs

---

### Phase 7: Testing & Coverage (Days 10-11)

**Deliverable**: 85%+ coverage, all scenarios tested

**Tasks**:
1. Create `tests/conftest.py`
   - Async test session
   - Database fixtures
   - User fixtures
2. Implement integration tests
   - Full flow: register → login → create todo → list todos
   - Token refresh flow
   - Logout revocation
3. Performance tests
   - Register < 500ms
   - Login < 500ms
   - Create todo < 200ms
4. Generate coverage report
   - `pytest --cov=src --cov-report=html`

**Verification**:
- [ ] Coverage >= 85%
- [ ] All user stories pass
- [ ] All error codes tested
- [ ] Performance targets met

---

### Phase 8: Production Hardening (Days 11-12)

**Deliverable**: Deployment-ready, security hardening complete

**Tasks**:
1. Security hardening
   - CORS middleware configuration
   - Rate limiting (if needed)
   - Input validation (Pydantic)
   - SQL injection prevention (SQLModel)
2. Performance optimization
   - Database query analysis
   - Connection pool tuning
   - Caching (if needed)
3. Documentation
   - API documentation (FastAPI auto-docs)
   - Setup guide (README.md)
   - Deployment guide
4. Optional: Docker support
   - Dockerfile
   - docker-compose.yml

**Verification**:
- [ ] Security checklist complete
- [ ] README covers setup and deployment
- [ ] All endpoints documented
- [ ] Docker build succeeds (if included)

---

## 9. SKILL USAGE STRATEGY

### Skill: async-sqlmodel
**Phases**: 2-3 (models, migrations)
**Approach**:
1. Fetch latest SQLAlchemy and SQLModel documentation
2. Define models with relationships and validations
3. Configure async CRUD in services
4. Set up Alembic for async migrations
5. Verify connection pooling

**Output**: Model definitions, migrations, CRUD operations

### Skill: fastapi-builder
**Phases**: 1, 4-6 (app factory, routing, observability)
**Approach**:
1. Fetch latest FastAPI documentation
2. Scaffold app factory with middleware
3. Implement routers with dependency injection
4. Add error handling middleware
5. Implement health and metrics endpoints

**Output**: FastAPI application, routers, middleware

### Skill: pytest-testing
**Phases**: 3, 7-8 (testing infrastructure)
**Approach**:
1. Fetch latest pytest and pytest-asyncio documentation
2. Create conftest.py with async fixtures
3. Implement unit and integration tests
4. Configure coverage thresholds
5. Generate coverage reports

**Output**: Test suite, fixtures, coverage reports

### Skill: fetch-library-docs
**Ongoing**: Before implementing any library code
**Libraries**: SQLAlchemy, python-jose, passlib, Prometheus

---

## 10. CRITICAL FILES TO CREATE

| File | Purpose | Phase | Priority |
|------|---------|-------|----------|
| `src/todo_api/__init__.py` | App factory | 1 | P0 |
| `src/todo_api/config.py` | Settings | 1 | P0 |
| `src/todo_api/database.py` | DB connection | 1 | P0 |
| `src/todo_api/models/base.py` | Base models | 2 | P0 |
| `src/todo_api/models/user.py` | User model | 2 | P0 |
| `src/todo_api/models/todo.py` | Todo model | 2 | P0 |
| `src/todo_api/models/token.py` | Token models | 2 | P0 |
| `src/todo_api/security.py` | JWT, bcrypt | 3 | P0 |
| `src/todo_api/services/auth_service.py` | Auth logic | 3 | P0 |
| `src/todo_api/services/token_service.py` | Token logic | 3 | P0 |
| `src/todo_api/routes/auth.py` | /auth/* | 4 | P0 |
| `src/todo_api/routes/todos.py` | /todos/* | 5 | P0 |
| `src/todo_api/routes/health.py` | /health | 6 | P1 |
| `src/todo_api/routes/metrics.py` | /metrics | 6 | P1 |
| `tests/conftest.py` | Test fixtures | 7 | P0 |
| `tests/test_auth.py` | Auth tests | 4 | P0 |
| `tests/test_todos.py` | Todo tests | 5 | P0 |
| `pyproject.toml` | Dependencies | 1 | P0 |
| `.env.example` | Environment template | 1 | P0 |
| `README.md` | Setup guide | 8 | P1 |

---

## 11. VERIFICATION & ACCEPTANCE CRITERIA

### Unit Tests
- [ ] JWT sign/verify with HS256
- [ ] Bcrypt cost=10 verification
- [ ] Password validation rules enforced
- [ ] Token expiration calculations
- [ ] All 15+ error codes have correct HTTP status

### Integration Tests
- [ ] Full auth flow: register → login → refresh → logout
- [ ] Todo CRUD: create → read → update → delete
- [ ] Data isolation: user A can't access user B's todos
- [ ] Token revocation prevents token reuse
- [ ] Pagination with skip/limit works

### Performance Tests
- [ ] Register endpoint: < 500ms (includes bcrypt ~100ms)
- [ ] Login endpoint: < 500ms
- [ ] Create todo: < 200ms
- [ ] List todos: < 500ms (with pagination)
- [ ] 1000 concurrent requests handled safely

### Security Validation
- [ ] Passwords never logged
- [ ] JWT signatures verified
- [ ] Token expiration enforced
- [ ] Blacklist prevents revoked tokens
- [ ] SQL injection prevented (SQLModel parameterization)
- [ ] No sensitive data in error responses
- [ ] CORS configured correctly

### Coverage Metrics
- [ ] Overall coverage >= 85%
- [ ] Security module coverage >= 95%
- [ ] Auth routes coverage >= 90%
- [ ] Todo routes coverage >= 85%

---

## 12. RISK MITIGATION

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Token blacklist grows unbounded | Medium | Daily cleanup job, TTL on rows |
| DB connection pool exhausted | Medium | Monitor pool size, set timeouts, graceful degradation |
| Bcrypt hashing slow | Low | Cost factor 10 = acceptable, async processing |
| Concurrent token updates | Medium | Database transactions, row-level locks |
| JWT key rotation | Medium | Maintain key version, gradual rollover |
| Neon Postgres downtime | High | Connection retry logic, graceful error handling |

---

## 13. ENVIRONMENT CONFIGURATION

### .env.example
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/todo_api
DATABASE_POOL_SIZE=20
DATABASE_ECHO=false

# JWT
JWT_SECRET_KEY=your-secret-key-min-256-bits
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Bcrypt
BCRYPT_COST_FACTOR=10

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Logging
LOG_LEVEL=INFO
JSON_LOGS=true

# Server
PORT=8000
HOST=0.0.0.0
```

---

## 14. SUCCESS CRITERIA & DELIVERABLES

**By End of Sprint:**
- ✅ All 8 phases completed
- ✅ 41+ functional requirements implemented
- ✅ 85%+ test coverage achieved
- ✅ All 5 user stories passing acceptance tests
- ✅ Production-ready code deployed
- ✅ Documentation complete (README, API docs)

**Post-Implementation Validation:**
- [ ] Load test with 1000 concurrent users
- [ ] Security audit (OWASP top 10)
- [ ] Performance profiling (latency p95, p99)
- [ ] User feedback on API usability

---

## NEXT STEPS

1. **Approval**: Review and approve this plan
2. **Task Breakdown**: Generate `tasks.md` with dependency-ordered tickets
3. **Execution**: Begin Phase 1 with FastAPI app factory
4. **Tracking**: Update task statuses as phases complete
5. **Documentation**: Maintain README with setup instructions
6. **Deployment**: Push to production Neon Postgres

**Estimated Duration**: 10-12 business days
**Team Size**: 1-2 developers
**Primary Skills**: async-sqlmodel, fastapi-builder, pytest-testing

---

*Plan created by Claude Code on 2026-01-12*
*Feature: Todo API with Authentication (001-todo-api-auth)*
*Status: Ready for Phase 1 Implementation*

