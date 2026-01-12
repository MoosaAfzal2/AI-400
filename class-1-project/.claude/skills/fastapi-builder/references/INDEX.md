# FastAPI Builder Skill - Knowledge Index

This document provides an overview of all the domain expertise embedded in the fastapi-builder skill.

## Organization

The skill is structured with progressive disclosure:

```
SKILL.md (primary - workflows and decision trees)
├── references/ (domain expertise - fetch when needed)
│   ├── PROJECT ARCHITECTURE
│   │   ├── project-structure.md         - Layered architecture, all layers with examples
│   │   ├── database-patterns.md         - Async setup, connection pooling, CRUD, transactions
│   │   ├── jwt-security-patterns.md     - RS256 JWT, token lifecycle, password security
│   │   ├── api-design-patterns.md       - RESTful endpoints, HTTP status codes, pagination
│   │   ├── testing-architecture.md      - Pytest fixtures, unit/integration tests
│   │   └── deployment-architecture.md   - Docker, K8s, Vercel, health checks, logging
│   │
│   ├── CORE PATTERNS
│   │   ├── routing.md                   - Route types, parameters, documentation
│   │   ├── validation.md                - Pydantic validation, error handling
│   │   ├── authentication.md            - API Keys, JWT, OAuth2
│   │   ├── dependencies.md              - Dependency injection patterns
│   │   ├── middleware-errors.md         - CORS, logging, error standardization
│   │   ├── common-errors.md             - Troubleshooting and solutions
│   │
│   └── QUALITY & DEPLOYMENT
│       ├── production-checklist.md      - Pre-deployment verification (40+ items)
│       └── security-checklist.md        - OWASP Top 10, best practices
│
├── assets/ (project templates)
│   ├── template-minimal.md     - Simple hello-world project
│   └── template-modular.md     - Production project with auth+DB
│
└── scripts/ (executable helpers)
    └── scaffold.py             - Generate new projects

```

## Reference Quick Links

### ⭐ Production Architecture (START HERE)
These files encode real-world patterns and are essential for building professional-grade FastAPI applications:

- **Project Structure** (references/project-structure.md): Complete guide to layered architecture (API → Core → DB → Models → Services) with code examples, async database setup, SQLModel patterns, dependency injection, authentication flow
- **Database Patterns** (references/database-patterns.md): Production async setup, connection pooling (pool_size=10, max_overflow=5), CRUD operations, transactions, query optimization, performance tips
- **JWT Security** (references/jwt-security-patterns.md): RS256 asymmetric JWT, token lifecycle (15-min access / 7-day refresh), token rotation, single-session enforcement, password hashing, JWKS endpoint
- **API Design** (references/api-design-patterns.md): RESTful conventions (/api/v1/...), HTTP status codes (201, 204, 401, 403, 404, 409), schemas, pagination, filtering, sorting
- **Testing** (references/testing-architecture.md): Pytest setup, async fixtures, in-memory SQLite, unit/integration tests, coverage reporting
- **Deployment** (references/deployment-architecture.md): Multi-stage Docker, docker-compose, Kubernetes manifests, Vercel, health checks, environment management

### Core Concepts
- **Routing** (references/routing.md): Path/query parameters, HTTP methods, OpenAPI docs
- **Validation** (references/validation.md): Pydantic models, field validators, error responses

### Additional Features
- **Authentication** (references/authentication.md): API keys, JWT, OAuth2, scopes, refresh tokens
- **Dependencies** (references/dependencies.md): Dependency injection, authentication chains, caching

### Operations
- **Middleware & Errors** (references/middleware-errors.md): CORS, logging, standardized errors
- **Deployment** (references/deployment.md): Docker, Kubernetes, Nginx, health checks
- **Testing** (references/testing.md): pytest fixtures, async tests, mocking

### Troubleshooting & Production
- **Common Errors** (references/common-errors.md): 422 validation, database, auth, async issues
- **Production Checklist** (references/production-checklist.md): Pre-deployment verification, monitoring, incident response
- **Security Checklist** (references/security-checklist.md): OWASP Top 10, password hashing, JWT security, secrets management

## Key Patterns Covered

### Production Architecture Patterns
✅ **Layered Architecture**: API layer (routes) → Core layer (config, security) → Database layer → Models layer → Services layer
✅ **Async Database**: SQLAlchemy with asyncpg, connection pooling (10 base + 5 overflow), pool recycling (1 hour)
✅ **SQLModel Patterns**: UUID primary keys, server-side timestamps, soft-delete (is_active), cascade deletes, proper indexes
✅ **JWT Security**: RS256 asymmetric keys, short-lived access tokens (15 min), long-lived refresh tokens (7 days)
✅ **Authentication Flow**: Single-session enforcement (revoke all on login), token rotation (delete old on refresh), JWKS endpoint
✅ **RESTful API**: Versioned endpoints (/api/v1/), correct status codes, pagination with skip/limit, proper error responses
✅ **Testing**: Pytest with async fixtures, in-memory SQLite, separate unit and integration tests
✅ **Deployment**: Multi-stage Docker, docker-compose for dev, Kubernetes manifests for production, health checks

### Scaffolding (from SKILL.md workflows)
1. **Minimal project**: Hello-world in single file
2. **Modular project**: Multi-file structure with routers, auth, database

### Features Implemented
| Feature | Reference | Pattern |
|---------|-----------|---------|
| Layered architecture | project-structure.md | API/Core/DB/Models/Services layers |
| Async database | database-patterns.md | SQLAlchemy + asyncpg with connection pooling |
| SQLModel setup | project-structure.md | UUID keys, timestamps, soft-delete, indexes |
| Path/Query params | routing.md | FastAPI type hints + validation |
| Request validation | validation.md | Pydantic BaseModel + Field constraints |
| Response models | routing.md | response_model parameter |
| API Keys | authentication.md | APIKeyHeader/Query/Cookie |
| JWT Tokens | jwt-security-patterns.md | RS256, access+refresh tokens, rotation |
| OAuth2 | authentication.md | authlib integration |
| CRUD operations | database-patterns.md | Async session + sqlalchemy.select |
| Transactions | database-patterns.md | Session commit/rollback |
| Relationships | project-structure.md | SQLAlchemy ForeignKey + relationship() |
| Dependency injection | dependencies.md | Depends() with chains |
| Error handling | api-design-patterns.md | Exception handlers + HTTP status codes |
| CORS | middleware-errors.md | CORSMiddleware configuration |
| Testing | testing-architecture.md | pytest + TestClient + async fixtures |
| Docker | deployment-architecture.md | Multi-stage Dockerfile optimization |
| Kubernetes | deployment-architecture.md | Deployment manifests + probes |
| Health checks | deployment-architecture.md | Liveness & readiness probes |
| Environment mgmt | deployment-architecture.md | .env files, secrets, ConfigMaps |
| Production Checklist | production-checklist.md | Pre-deployment verification (40+ items) |
| Security | security-checklist.md | OWASP Top 10, password hashing, JWT, secrets |

## Domain Coverage

✅ **Production Architecture (MUST KNOW):**
- Layered project structure (API/Core/DB/Models/Services)
- Async database with connection pooling (real production config)
- JWT security with RS256 asymmetric keys
- Token lifecycle and rotation patterns
- Single-session enforcement
- RESTful API design with correct status codes
- Authentication flow (sign-up, login, logout, refresh)
- Testing with pytest and async fixtures
- Deployment (Docker, Kubernetes, Vercel)
- Health checks and monitoring
- Environment management

✅ **Covered comprehensively:**
- FastAPI routing and parameters
- Pydantic validation
- SQLAlchemy async integration with SQLModel
- Proper index strategy and relationship handling
- Error handling and standardization
- Dependency injection
- Testing patterns (unit + integration)
- Docker/Kubernetes deployment
- Security best practices (OWASP Top 10)

✅ **Covered with patterns:**
- API keys
- OAuth2
- CORS
- Middleware
- Transactions
- Migrations (Alembic)

✅ **Mentioned but no deep patterns:**
- Streaming responses
- Background tasks
- WebSockets
- GraphQL (not standard)

## When to Use Each Reference

| Task | Reference |
|------|-----------|
| **Understanding project structure** | project-structure.md ⭐ START HERE |
| **Setting up database** | database-patterns.md + project-structure.md |
| **Implementing authentication** | jwt-security-patterns.md + testing-architecture.md |
| **Designing API endpoints** | api-design-patterns.md + validation.md |
| **Adding a new route** | routing.md + api-design-patterns.md |
| **Request validation** | validation.md |
| **Handling errors** | api-design-patterns.md + common-errors.md |
| **Writing tests** | testing-architecture.md |
| **Deploying to production** | deployment-architecture.md + production-checklist.md |
| **Security review** | security-checklist.md + jwt-security-patterns.md |
| **Performance optimization** | database-patterns.md (query optimization, indexes) |
| **Debugging problems** | common-errors.md |
| **Local development setup** | deployment-architecture.md (docker-compose section) |
| **Kubernetes deployment** | deployment-architecture.md (Kubernetes section) |

## Next Steps After Skill Creation

1. **Start with project structure** (reference: project-structure.md)
   - Understand the layered architecture: API → Core → DB → Models → Services
   - Study how each layer works with code examples

2. **Choose database setup** (reference: database-patterns.md)
   - Learn production connection pooling configuration
   - Understand async patterns and CRUD operations

3. **Plan authentication** (reference: jwt-security-patterns.md)
   - Understand RS256 JWT vs HS256
   - Learn token lifecycle and rotation

4. **Design API endpoints** (reference: api-design-patterns.md)
   - Follow RESTful naming conventions
   - Use correct HTTP status codes

5. **Write tests** (reference: testing-architecture.md)
   - Setup pytest with async fixtures
   - Use in-memory SQLite for fast tests

6. **Deploy** (reference: deployment-architecture.md)
   - Build Docker image with multi-stage approach
   - Configure Kubernetes or other deployment targets

7. **Pre-deployment verification** (reference: production-checklist.md)
   - Run 40+ pre-deployment checks
   - Verify security configuration

8. **Final security review** (reference: security-checklist.md)
   - Audit OWASP Top 10 items
   - Verify secrets management

## Official Documentation Links

The skill does NOT hardcode docs (they change). Instead:
- Fetches latest FastAPI docs when implementing (via fetch-library-docs skill)
- References are time-tested patterns that transcend version changes
- Common errors reference official troubleshooting approaches

To add new patterns or update existing ones:
1. Research official FastAPI documentation
2. Test pattern in real project
3. Update corresponding reference file
4. Include version note if version-specific

---

## Cross-Skill Integration

### Database Integration with Async SQLModel
For comprehensive async database patterns beyond basic CRUD, see the **async-sqlmodel skill** documentation including connection pool tuning, relationship eager loading with selectinload/joinedload, N+1 query prevention, query performance profiling, and production optimization patterns in `performance.md`.

### Testing FastAPI Applications
For pytest setup with FastAPI, async fixtures, endpoint testing with dependencies, and SQLModel database testing, see the **pytest-testing skill** documentation including `fastapi-testing.md` for endpoint testing patterns and `fastapi-sqlmodel-testing.md` for database integration tests.

### Migrating from Sync to Async
For existing FastAPI applications using synchronous patterns, see the **fastapi-builder skill** reference: `sync-to-async-migration.md` covers 12-phase migration strategy from route handlers to database to testing.

---

**Skill Created**: 2026-01-12
**Production Architecture Enhancement**: Phase 3 (2026-01-12)
  - Added 6 new comprehensive production pattern files based on auth-service project
  - Integrated real-world patterns into core skill workflows
  - Enhanced from generic guide to production-grade reference
**FastAPI Knowledge Base**: Comprehensive coverage from hello-world to enterprise production
**Update Frequency**: As needed when new patterns emerge or best practices change

## What Changed in Phase 3

The skill was enhanced from a general FastAPI guide to a **production-architecture reference** by:

1. **Added 6 New Production Files** (2,500+ lines of real patterns):
   - `project-structure.md` - Complete layered architecture guide
   - `database-patterns.md` - Async DB with connection pooling
   - `jwt-security-patterns.md` - RS256 JWT with token lifecycle
   - `api-design-patterns.md` - RESTful design with HTTP status codes
   - `testing-architecture.md` - Pytest setup with async fixtures
   - `deployment-architecture.md` - Docker, K8s, Vercel deployment

2. **Updated Core Skill Workflows** to reference production patterns
   - New Project Scaffolding now includes architecture overview
   - Database Integration references pooling configuration (pool_size=10, max_overflow=5)
   - Authentication Setup details RS256, token rotation, single-session enforcement
   - Deployment Workflow includes health checks, logging, env management

3. **Updated INDEX.md** for better navigation
   - Clear "START HERE" pointer to project-structure.md
   - Organized references into: Production Architecture, Core Patterns, Quality & Deployment
   - Enhanced "When to Use" table with 14 practical scenarios
   - New "Next Steps" section with 8 progressive learning steps

The skill now encodes **"MUST KNOW"** production patterns rather than generic best practices.

