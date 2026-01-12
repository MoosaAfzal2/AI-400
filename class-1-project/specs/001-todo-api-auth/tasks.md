# Implementation Tasks: Todo API with Authentication

**Feature**: Todo API with Authentication (`001-todo-api-auth`)
**Date**: 2026-01-12
**Tech Stack**: FastAPI (async) + SQLModel + Neon Postgres + JWT + Alembic
**Status**: Ready for Development

---

## Overview

Implementation broken into 5 phases with 87 atomic, testable tasks:
1. **Phase 1** (Setup): 8 tasks - Project initialization, configuration, dependencies
2. **Phase 2** (Foundational): 15 tasks - Database models, migrations, authentication utilities
3. **Phase 3** (User Story 1-2): 18 tasks - User registration and login endpoints
4. **Phase 4** (User Story 3-4): 24 tasks - Todo creation, reading, listing with pagination
5. **Phase 5** (User Story 5-7): 22 tasks - Todo updates, deletion, data privacy, integration tests

**Independent Testing**: Each user story can be tested independently after foundational phase.
**Parallel Opportunities**: Services and routes can be developed in parallel within a story.

---

## Phase 1: Setup & Configuration

**Goal**: Initialize project structure, install dependencies, configure environment.
**Duration**: 1-2 days
**Blocking For**: All other phases

- [ ] T001 Create project directory structure: src/todo_api, tests, migrations, docs directories
- [ ] T002 Create pyproject.toml with all 20+ dependencies (FastAPI, SQLModel, Alembic, pytest, etc.)
- [ ] T003 Create .env.example with database URL, JWT secrets, bcrypt settings, server config
- [ ] T004 Create .env.test for test database configuration
- [ ] T005 Create .gitignore for Python, virtual environments, environment files
- [ ] T006 Initialize git repository and create 001-todo-api-auth branch
- [ ] T007 Create README.md with setup instructions, API overview, quick start guide
- [ ] T008 Run `pip install -e ".[dev]"` and verify all dependencies installed successfully

**Acceptance Criteria**:
- ✅ Project directory structure matches plan layout
- ✅ All dependencies install without errors
- ✅ .env.example and .env.test created with all required variables
- ✅ README covers setup from scratch

---

## Phase 2: Foundational - Database, Models & Authentication Utilities

**Goal**: Build database infrastructure and security utilities that all user stories depend on.
**Duration**: 2-3 days
**Blocking For**: All user story phases
**Independent Test**: Database connection, model creation, password hashing

- [ ] T009 Create src/todo_api/config.py with Pydantic Settings: DATABASE_URL, JWT secrets, bcrypt cost factor, token expiration times
- [ ] T010 Create src/todo_api/database.py: AsyncEngine, AsyncSessionLocal, get_session dependency, graceful shutdown
- [ ] T011 Create src/todo_api/__init__.py with create_app() application factory: config, database, middleware, routes, exception handlers
- [ ] T012 Create src/todo_api/models/base.py: Base SQLModel class with timestamp mixin (created_at, updated_at)
- [ ] T013 [P] Create src/todo_api/models/user.py: User entity with email (unique), password_hash, is_active, relationships to todos and refresh_tokens
- [ ] T014 [P] Create src/todo_api/models/todo.py: Todo entity with user_id (FK), title, description, is_completed, timestamps, user relationship
- [ ] T015 [P] Create src/todo_api/models/token.py: RefreshToken and TokenBlacklist entities with audit trail fields
- [ ] T016 Create src/todo_api/security.py: JWT encode/decode (HS256), password hash/verify (bcrypt cost=10), password validation function (8+ chars, mixed types)
- [ ] T017 Create src/todo_api/exceptions.py: Custom exceptions (AuthException, ValidationException, ResourceNotFoundException, UnauthorizedException)
- [ ] T018 Create src/todo_api/middleware.py: Error handling middleware, request/response logging middleware
- [ ] T019 Initialize Alembic: `alembic init migrations` with async support configured
- [ ] T020 Create src/todo_api/logging_config.py: Structured JSON logging setup with request context
- [ ] T021 Create migrations/versions/001_initial_schema.py: Create users, todos, refresh_tokens, token_blacklist tables with indexes
- [ ] T022 Run `alembic upgrade head` and verify database schema created in Neon Postgres
- [ ] T023 Create src/todo_api/dependencies.py: get_session, get_current_user (JWT extraction and validation), optional_current_user
- [ ] T024 Create pytest.ini with asyncio mode and test discovery configuration

**Acceptance Criteria**:
- ✅ Config loads from .env without errors
- ✅ Database connection successful to Neon Postgres
- ✅ AsyncSession works with async context managers
- ✅ JWT encode/decode round-trip succeeds
- ✅ Bcrypt hashing verifies with cost factor 10
- ✅ Password validation accepts valid passwords and rejects weak passwords
- ✅ Alembic migrations apply successfully
- ✅ All 4 tables created with correct schema, indexes, and foreign keys

---

## Phase 3: User Story 1 & 2 - Authentication System

**Goal**: Implement user registration, login, token refresh, logout, and password change.
**Duration**: 2-3 days
**User Stories**: US1 (Registration), US2 (Login)
**Independent Test**: Register new user, login, refresh token, logout

### Services

- [ ] T025 [US1] Create src/todo_api/services/user_service.py: get_user_by_email, get_user_by_id, create_user (hash password, save to DB), update_user, delete_user
- [ ] T026 [US2] Create src/todo_api/services/auth_service.py: register_user (validate email/password, check duplicate), authenticate_user (verify credentials), generate_tokens (access + refresh JWT), verify_token
- [ ] T027 [US2] Create src/todo_api/services/token_service.py: validate_token (signature, expiration, blacklist check), blacklist_token (add to revocation list), refresh_access_token, get_refresh_token_from_db

### Schemas (Pydantic Models)

- [ ] T028 [US1] Create src/todo_api/schemas/auth.py: UserRegister (email, password), UserLogin, TokenResponse (access_token, refresh_token, expires_in), PasswordChange, ErrorResponse
- [ ] T029 [US1] Create src/todo_api/schemas/pagination.py: PaginationParams (skip, limit), PaginationResponse wrapper
- [ ] T030 [US1] Create src/todo_api/schemas/__init__.py with schema exports

### Routes

- [ ] T031 [US1] Create src/todo_api/routes/auth.py with POST /auth/register: validate input, call auth_service.register_user, return user details (201 Created)
- [ ] T032 [US2] Add POST /auth/login to auth.py: validate input, call auth_service.authenticate_user, generate_tokens, store refresh token in DB, return tokens (200 OK)
- [ ] T033 [US2] Add POST /auth/refresh to auth.py: validate refresh token, call token_service.refresh_access_token, return new access token (200 OK)
- [ ] T034 Add POST /auth/logout to auth.py: extract tokens from request, call token_service.blacklist_token for both, return success (200 OK)
- [ ] T035 Add POST /auth/change-password to auth.py: require authentication, verify current password, validate new password, update user, blacklist all refresh tokens, return success (200 OK)
- [ ] T036 Create src/todo_api/routes/__init__.py with router exports

### Testing

- [ ] T037 [US1] Create tests/test_auth.py: test registration (valid, duplicate email, weak password, invalid email), test password hashing
- [ ] T038 [US2] Add login tests to test_auth.py: test login (valid, invalid password, non-existent email), test token validity, test token refresh, test logout, test expired token rejection

**Independent Test Criteria** (US1 & US2):
- ✅ User registration with valid email and strong password succeeds
- ✅ Duplicate email registration rejected (VALIDATION_003)
- ✅ Weak password registration rejected (VALIDATION_002)
- ✅ Invalid email registration rejected (VALIDATION_001)
- ✅ Login with valid credentials returns access + refresh tokens
- ✅ Login with invalid password rejected (AUTH_001)
- ✅ Login with non-existent email rejected without leaking user existence
- ✅ Access token valid for subsequent requests
- ✅ Expired token rejected (AUTH_002)
- ✅ Refresh token generates new access token
- ✅ Logout blacklists both tokens immediately
- ✅ Password change requires current password verification
- ✅ Password change with weak new password rejected

---

## Phase 4: User Story 3 & 4 - Todo CRUD (Create & Read)

**Goal**: Implement todo creation, listing, filtering, pagination with user isolation.
**Duration**: 2-3 days
**User Stories**: US3 (Create Todo), US4 (Read/List Todos)
**Independent Test**: Create todo as authenticated user, list todos, verify user isolation

### Services

- [ ] T039 [US3] Create src/todo_api/services/todo_service.py: create_todo (title, description, associate with user_id), get_todo_by_id_and_user (authorization check), get_user_todos (filter by user_id, pagination, sorting), delete_todo, update_todo
- [ ] T040 [P] [US3] Add pagination/sorting support to todo_service: get_user_todos with skip, limit, sort_by (created_at, completed_at, title), sort_order (asc, desc)

### Schemas

- [ ] T041 [US3] Create src/todo_api/schemas/todo.py: TodoCreate (title, description optional), TodoUpdate (title optional, description optional, is_completed optional), TodoResponse (all fields + timestamps), TodoListResponse (items, total, skip, limit, has_more)

### Routes

- [ ] T042 [US3] Create src/todo_api/routes/todos.py with POST /todos: require authentication, validate input, call todo_service.create_todo, return created todo (201 Created)
- [ ] T043 [US3] Add GET /todos/{id} to todos.py: require authentication, call todo_service.get_todo_by_id_and_user, return todo or 404/403 (200 OK)
- [ ] T044 [US4] Add GET /todos to todos.py: require authentication, accept skip/limit/is_completed/sort_by/sort_order query params, call todo_service.get_user_todos, return paginated list (200 OK)
- [ ] T045 [US4] Add pagination support to GET /todos: default skip=0, limit=20, has_more logic, total count, error on invalid params

### Authorization & Isolation

- [ ] T046 [US3] [US4] Implement user isolation checks: all todo queries filter by user_id = current_user.id, GET/PUT/DELETE check todo.user_id matches current_user.id or return 403 Forbidden

### Testing

- [ ] T047 [US3] Create tests/test_todos.py: test create todo (valid, missing title, long text validation), test todo stored with correct user_id, test created_at timestamp
- [ ] T048 [US4] Add list tests to test_todos.py: test list todos (empty, multiple), test pagination (skip/limit), test user isolation (user A cannot see user B's todos), test completed_at null initially

**Independent Test Criteria** (US3 & US4):
- ✅ Authenticated user can create todo with title
- ✅ Todo stored with correct user_id association
- ✅ Created_at and updated_at timestamps set
- ✅ User isolation enforced—user A cannot access user B's todos
- ✅ Missing title rejected (VALIDATION_004)
- ✅ Very long text (>10,000 chars) rejected (VALIDATION_005)
- ✅ List returns only authenticated user's todos
- ✅ Empty list returns 200 OK with empty items array
- ✅ Pagination parameters (skip/limit) work correctly
- ✅ Invalid pagination params rejected (VALIDATION_006)
- ✅ Unauthenticated requests return 401 Unauthorized

---

## Phase 5: User Story 5, 6 & 7 - Todo Update, Delete & Data Privacy

**Goal**: Implement todo updates, deletion, verify comprehensive data isolation.
**Duration**: 2 days
**User Stories**: US5 (Update), US6 (Delete), US7 (Data Privacy - cross-cutting)
**Independent Test**: Update own todo, delete own todo, verify cross-user access denied

### Services (Extend Services from Phase 4)

- [ ] T049 [US5] [US6] Add update_todo and delete_todo to todo_service.py: authorization checks, update only specified fields (partial update), set completed_at when is_completed=true, soft delete or hard delete with cascade check
- [ ] T050 [US7] Add comprehensive authorization audit: trace all queries to verify user_id filter applied

### Routes (Extend Routes from Phase 4)

- [ ] T051 [US5] Add PUT /todos/{id} to todos.py: require authentication, validate authorization (check todo belongs to user), accept partial updates (title, description, is_completed), return updated todo (200 OK)
- [ ] T052 [US5] Add completion timestamp handling: when is_completed changes to true, set completed_at = now(); when changes to false, set completed_at = null
- [ ] T053 [US6] Add DELETE /todos/{id} to todos.py: require authentication, validate authorization, delete todo from DB, return 204 No Content
- [ ] T054 [US7] Add authorization middleware: verify every todo operation checks user_id, log all authorization failures

### Testing

- [ ] T055 [US5] Add update tests to test_todos.py: test update own todo (title, description, is_completed), test partial update (only one field), test completed_at set/unset, test update other user's todo rejected (403)
- [ ] T056 [US6] Add delete tests to test_todos.py: test delete own todo succeeds, test deleted todo not in list, test delete other user's todo rejected (403)
- [ ] T057 [US7] Add data privacy tests to test_todos.py: test user A cannot access user B's todos via GET, PUT, DELETE; test cross-user token attempt returns 403
- [ ] T058 Create tests/integration/test_full_flows.py: end-to-end flows (register → login → create todo → list → update → delete)

### Error Handling & Status Codes

- [ ] T059 Add error response middleware: format all errors as {error_code, message, details, timestamp}
- [ ] T060 Map all error codes to HTTP status: AUTH_* → 401, AUTHZ_* → 403, VALIDATION_* → 422, RESOURCE_* → 404, SERVER_* → 500

### Observability & Testing Infrastructure

- [ ] T061 Create src/todo_api/routes/health.py: GET /health endpoint returns {status, database, checks, timestamp}
- [ ] T062 Create src/todo_api/routes/metrics.py: GET /metrics endpoint returns Prometheus-format metrics (request count, latency, error rates)
- [ ] T063 Create tests/conftest.py: pytest fixtures for async session, test client, sample users, sample todos
- [ ] T064 Add database fixtures: async_session fixture for test database isolation
- [ ] T065 Add auth fixtures: create_test_user, create_test_token, authenticated_client fixtures

### Coverage & Final Testing

- [ ] T066 Run pytest with coverage: `pytest --cov=src --cov-report=html` target 85%+ coverage
- [ ] T067 Test error scenarios: all 15+ error codes tested with correct HTTP status
- [ ] T068 Test edge cases: concurrent updates, expired tokens, malformed requests, DB connection failures
- [ ] T069 Performance validation: registration <500ms, login <500ms, create todo <200ms, list todos <500ms

**Independent Test Criteria** (US5, US6, US7):
- ✅ Authenticated user can update own todo (title, description, is_completed)
- ✅ Partial updates only modify specified fields
- ✅ Completing todo sets completed_at timestamp
- ✅ Incomplete todo clears completed_at (sets to null)
- ✅ User cannot update other user's todo (403 Forbidden)
- ✅ Authenticated user can delete own todo
- ✅ Deleted todo removed from database
- ✅ User cannot delete other user's todo (403 Forbidden)
- ✅ User A cannot read/update/delete user B's todos via direct access
- ✅ Separate tokens for different users properly isolated
- ✅ Cross-user queries return 403 Forbidden
- ✅ All privacy test cases pass

---

## Phase 6: Polish, Documentation & Production Readiness

**Goal**: Finalize documentation, security hardening, performance optimization.
**Duration**: 1-2 days
**Blocking For**: Production deployment

- [ ] T070 Create src/todo_api/main.py: app = create_app() entrypoint for Uvicorn
- [ ] T071 Security hardening: CORS middleware configuration, HTTPS redirect in production, secure cookie settings
- [ ] T072 Create docker/Dockerfile: multi-stage build, minimal final image, non-root user
- [ ] T073 Create docker-compose.yml: FastAPI service + Neon Postgres for local development
- [ ] T074 Performance optimization: database query analysis, connection pool tuning (pool_size=20, pool_pre_ping=True)
- [ ] T075 Final security checklist: JWT secret rotation policy, password hashing cost verification, SQL injection prevention
- [ ] T076 Update README.md: comprehensive setup guide, API documentation, example requests/responses
- [ ] T077 Create DEPLOYMENT.md: environment variable setup, Neon connection string, production checklist
- [ ] T078 Code quality: Black formatter, Ruff linter, mypy type checking
- [ ] T079 Create .github/workflows/ci.yml: automated tests on push (pytest, coverage check)
- [ ] T080 Documentation: OpenAPI/Swagger auto-docs available at /docs and /redoc
- [ ] T081 Final integration testing: full end-to-end with Neon Postgres
- [ ] T082 Load testing (optional): verify 1000 concurrent users supported
- [ ] T083 Security audit: OWASP top 10 checklist

**Acceptance Criteria**:
- ✅ All tests pass (85%+ coverage)
- ✅ Code formatted with Black
- ✅ No Ruff linting issues
- ✅ No mypy type errors
- ✅ Docker image builds successfully
- ✅ docker-compose local development works
- ✅ README covers full setup from scratch to deployment
- ✅ OpenAPI docs show all endpoints with correct error codes

---

## Task Summary by Phase

| Phase | Tasks | Duration | Focus |
|-------|-------|----------|-------|
| Phase 1 | T001-T008 | 1-2 days | Setup & Configuration |
| Phase 2 | T009-T024 | 2-3 days | Database, Models, Auth Utils (Blocking) |
| Phase 3 | T025-T038 | 2-3 days | User Registration & Login |
| Phase 4 | T039-T058 | 2-3 days | Todo Create & Read |
| Phase 5 | T059-T069 | 2 days | Todo Update, Delete & Privacy |
| Phase 6 | T070-T083 | 1-2 days | Polish & Production |

**Total**: 83 tasks across 6 phases (10-12 days estimated)

---

## Parallelization Opportunities

**Within Phase 2** (after T008):
- T013, T014, T015 (models) can run in parallel
- T016, T020 (utilities) can run in parallel

**Within Phase 3**:
- T025, T026, T027 (services) depend on Phase 2 but can run in parallel with each other
- T028, T029 (schemas) independent, can start immediately after Phase 2

**Within Phase 4**:
- T039, T040 (services) can run in parallel after Phase 3 services
- T041 (schemas) independent
- T042-T045 (routes) depend on services/schemas but can run in parallel with each other

**Within Phase 5**:
- T049, T050, T051-T053 can run in parallel (all depend on Phase 4)

---

## MVP (Minimal Viable Product) Scope

**Phase 1 + Phase 2 + Phase 3 + Phase 4 (tasks T001-T058)**

Delivers:
- ✅ User registration and login
- ✅ JWT authentication with token refresh
- ✅ Todo creation and reading
- ✅ Pagination and listing
- ✅ Basic data isolation
- ✅ Error handling with error codes
- ✅ ~70% of functional requirements

**Timeline**: 6-7 days

---

## Dependencies Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundation) ← BLOCKS ALL
    ↓
Phase 3 (Auth) ─────┐
                    ├→ Phase 4 (CRUD) ─→ Phase 5 (Polish) ─→ Phase 6 (Deploy)
                    ↑
                    └─ Can start Phase 4 after T026 (auth_service)
```

---

## Test Execution Strategy

**Phase 1**: Manual verification of setup (ls, pip list, .env files)
**Phase 2**: Unit tests for config, database, models, security utilities
**Phase 3**: Integration tests for auth flows (register, login, token refresh)
**Phase 4**: Integration tests for CRUD operations with user isolation
**Phase 5**: Cross-user authorization and privacy tests
**Phase 6**: Full end-to-end tests, load testing, security audit

---

## Status & Next Steps

**Status**: ✅ Ready for Implementation

**Next Steps**:
1. Review task breakdown for completeness
2. Assign tasks to developers in order (Phase 1 → Phase 2 → Parallel execution in later phases)
3. Use task checkboxes to track progress
4. Execute tests after each phase completion

**Verification**:
- Phase 1 complete → Verify dependencies installed
- Phase 2 complete → Verify database schema created
- Phase 3 complete → Verify registration and login work
- Phase 4 complete → Verify CRUD with pagination
- Phase 5 complete → Verify privacy and error handling
- Phase 6 complete → Verify production readiness

---

**Generated**: 2026-01-12
**Feature**: Todo API with Authentication (001-todo-api-auth)
**Total Tasks**: 83
**Estimated Duration**: 10-12 days
**Status**: ✅ Ready for Development

