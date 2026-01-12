---
name: async-sqlmodel
description: |
  Build async database integration into FastAPI applications using SQLModel and async SQLAlchemy.
  This skill should be used when users want to create async-first database layers with SQLModel models,
  async sessions, relationships (with joinedload/selectinload), migrations, and production-grade patterns.
  Covers model definition, async CRUD operations, relationship eager loading, connection pooling,
  and Alembic migrations with async support.
  Always fetches latest SQLModel and SQLAlchemy async documentation before implementation.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

## Before Implementation

Gather context to ensure successful async database integration:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing models, database setup, Python version, FastAPI structure |
| **Conversation** | Database type (PostgreSQL/SQLite), async driver (asyncpg/aiosqlite), environment (dev/prod) |
| **Skill References** | Database patterns from `references/` (setup, models, operations, relationships) |
| **Fetch Docs** | Use `fetch-library-docs` skill to get latest SQLModel/SQLAlchemy async documentation |

Ensure all required context is gathered before implementing database layer.

---

## Skill Triggers & Use Cases

| Trigger | Skill Action |
|---------|--------------|
| "Create SQLModel database layer for FastAPI" | Generate async engine, session, models, and CRUD operations |
| "Define models with relationships" | Create SQLModel with foreign keys and eager loading patterns |
| "Access relationship data" | Provide selectinload/joinedload patterns for lazy relationship loading |
| "Setup async database connection" | Configure create_async_engine with pooling and async driver |
| "Create CRUD operations" | Generate ServiceBase for reusable async CRUD with eager loading |
| "Create model-specific service" | Extend ServiceBase for UserService, TeamService, etc. |
| "Setup advanced filtering" | Implement filter operators (gt, lt, ilike, in, between, etc.) |
| "Setup database migrations" | Configure Alembic with async template and autogenerate |
| "Use database in FastAPI endpoints" | Create async dependency for session and service injection |
| "Handle async transactions" | Setup rollback/commit patterns with error handling |

---

## Required Clarifications

Before implementing, ask the user these questions:

### 1. **Database & Driver** ❓
   - Which database? (PostgreSQL, MySQL, SQLite?)
   - Which async driver? (asyncpg for PostgreSQL, aiosqlite for SQLite, aiomysql for MySQL?)
   - **Affects**: Connection string and async engine configuration

### 2. **Model Complexity** ❓
   - Simple models (no relationships) or with relationships?
   - Types of relationships: One-to-many, many-to-many, self-referential?
   - Need JSONB columns or special types?
   - **Affects**: Model definition and eager loading strategy

### 3. **Operations Scope** ❓
   - What operations: CRUD, filtering, aggregations, bulk operations?
   - Need transactions or simple operations?
   - Batch insert/update patterns needed?
   - **Affects**: Session and operation patterns

### 4. **FastAPI Integration** ❓
   - Use as dependency for endpoints? (recommended)
   - Need connection pooling for production?
   - How many concurrent connections expected?
   - **Affects**: Session lifecycle and connection pool configuration

### 5. **Migrations & Deployment** ❓
   - Use Alembic for migrations?
   - Automatic schema creation (dev) or manual migrations (prod)?
   - Track all models in migrations?
   - **Affects**: Alembic setup and migration strategy

---

## User Input Not Required For

These are inferred or handled flexibly; don't ask unless user mentions them:
- ORM choice (it's SQLModel—this skill is SQLModel-specific)
- Async/await support (this skill assumes async-first)
- Session management pattern (follows SQLAlchemy best practices)
- Relationship eager loading (will use selectinload/joinedload patterns)

---

## Core Workflows

### 1. Async Database Setup

```
User Request → Identify Database Type & Driver
  ├─ PostgreSQL + asyncpg
  ├─ SQLite + aiosqlite
  └─ MySQL + aiomysql
         ↓
Fetch Official Docs (SQLAlchemy async)
  ├─ create_async_engine patterns
  ├─ AsyncSession configuration
  └─ Connection pooling options
         ↓
Setup Async Engine (see database-setup.md)
  ├─ Create engine with async driver
  ├─ Configure connection pooling
  ├─ Setup AsyncSession factory
  └─ Create session dependency
         ↓
Create Base Tables
  ├─ Create all tables on startup (dev)
  ├─ Use Alembic migrations (prod)
  └─ Test connection
```

### 2. Model Definition

```
Identify Models & Relationships
  ├─ Data structure for each model
  ├─ Primary keys and fields
  ├─ Foreign key relationships
  └─ Special types (JSONB, etc.)
         ↓
Fetch Official Docs (SQLModel)
  └─ Model patterns, field types, relationships
         ↓
Define SQLModel Classes (see models.md)
  ├─ Base model with SQLModel
  ├─ Fields with types and constraints
  ├─ Foreign keys and relationships
  ├─ Indexes if needed
  └─ Response models (plain Pydantic)
         ↓
Validate Models
  └─ Check type compatibility with async operations
```

### 3. Service Layer with ServiceBase

```
Identify CRUD Needs
  ├─ Create (insert new records)
  ├─ Read (query existing records)
  ├─ Update (modify records)
  └─ Delete (remove records)
         ↓
Create ServiceBase (see servicebase.md)
  ├─ Define generic ServiceBase[Model, Create, Update]
  ├─ Implement CRUD methods with eager loading support
  ├─ Add advanced filtering (gt, lt, ilike, in, etc.)
  └─ Configure transaction management
         ↓
Create Model-Specific Services (see servicebase.md)
  ├─ UserService(ServiceBase[User, UserCreate, UserUpdate])
  ├─ TeamService(ServiceBase[Team, TeamCreate, TeamUpdate])
  └─ Add custom methods beyond CRUD
         ↓
Test Service Operations
  └─ Verify async/await patterns and eager loading
```

### 4. Relationship Eager Loading

```
Identify Relationship Access Patterns
  ├─ Which relationships need eager loading?
  ├─ One-to-many or many-to-many?
  └─ Access frequency in endpoints?
         ↓
Fetch Official Docs (SQLAlchemy selectinload/joinedload)
  └─ Eager loading strategies
         ↓
Setup Eager Loading (see relationships.md)
  ├─ Use selectinload() for collections
  ├─ Use joinedload() for single relationships
  ├─ Avoid N+1 query problems
  └─ Response models control exposure
         ↓
Test Relationship Access
  └─ Verify relationships load without implicit IO
```

### 5. Migrations Setup

```
Decide Migration Strategy
  ├─ Development: Create all on startup
  └─ Production: Use Alembic
         ↓
Fetch Official Docs (Alembic async support)
  └─ Async migration patterns
         ↓
Setup Alembic (see migrations.md)
  ├─ Initialize Alembic repo
  ├─ Configure async template
  ├─ Import all models
  ├─ Auto-generate migrations
  └─ Apply migrations
         ↓
Track Migrations
  └─ Version control all migration files
```

### 6. FastAPI Integration

```
Identify Integration Points
  ├─ Session dependency for endpoints
  ├─ Connection lifecycle
  └─ Error handling
         ↓
Fetch Official Docs (FastAPI dependencies)
  └─ Async dependency patterns
         ↓
Create FastAPI Integration (see fastapi-integration.md)
  ├─ Async session dependency
  ├─ Use in endpoints
  ├─ Error handling and rollback
  └─ Lifespan events for setup/teardown
         ↓
Test Integration
  └─ Verify endpoints work with async database
```

---

## Decision Trees

### Database & Driver Decision

```
What database do you use?
├─ PostgreSQL → Use asyncpg driver
├─ SQLite (development) → Use aiosqlite driver
├─ MySQL → Use aiomysql driver
└─ Unsure? → Start with SQLite + aiosqlite (easiest)
```

### Relationship Eager Loading Decision

```
How to access related data?
├─ Single related object → Use joinedload()
├─ Collection of related objects → Use selectinload()
├─ Multiple levels deep → Combine strategies
└─ Unsure? → Default to selectinload()
```

### Model Complexity Decision

```
Do your models have relationships?
├─ NO → Use simple model definition (models.md)
├─ YES, simple (one-to-many) → Use relationships section (models.md)
└─ YES, complex (self-ref, many-to-many) → See relationships.md patterns
```

---

## Key Patterns (Reference in references/)

### Database Setup
- **`database-setup.md`** - Async engine, connection pooling, AsyncSession, session dependency

### Model Definition
- **`models.md`** - SQLModel basics, fields, types, constraints, indexes
- **`relationships.md`** - Foreign keys, relationships, eager loading with selectinload/joinedload

### Service Layer (CRUD Operations)
- **`servicebase.md`** - Generic ServiceBase class for CRUD, filtering, pagination, eager loading support
- **`async-operations.md`** - Async CRUD patterns, select/update/delete, transactions, error handling

### FastAPI Integration
- **`fastapi-integration.md`** - Using ServiceBase with FastAPI endpoints and dependency injection

### Production & Migrations
- **`migrations.md`** - Alembic async setup, autogenerate, upgrade workflows
- **`production-patterns.md`** - Connection pooling, monitoring, error handling, scaling
- **`best-practices.md`** - Model organization, naming, testing, performance

---

## Error Handling in Skill

When implementing database layer:
- ✅ Fetch official docs BEFORE writing models
- ✅ Use established async patterns from `references/`
- ✅ Always use eager loading for relationships (selectinload/joinedload)
- ✅ Handle SQLAlchemy errors with proper rollback
- ✅ Test async/await patterns work correctly
- ✅ Configure connection pooling for production

When uncertain:
- Use `fetch-library-docs` to get latest SQLModel/SQLAlchemy patterns
- Check `references/database-setup.md` for common patterns
- Ask user for specific context (database, driver, relationships)

---

## What This Skill Does

✅ Setup async database engine with create_async_engine
✅ Configure AsyncSession for concurrent requests
✅ Define SQLModel models with relationships
✅ Implement ServiceBase for generic CRUD operations
✅ Create model-specific services (UserService, TeamService, etc.)
✅ Support advanced filtering (gt, lt, ilike, in, between, etc.)
✅ Setup eager loading (selectinload/joinedload) in CRUD operations
✅ Configure connection pooling for production
✅ Create Alembic migrations with async support
✅ Integrate async database with FastAPI endpoints
✅ Handle transactions and error scenarios
✅ Optimize queries with proper eager loading strategies

## What This Skill Does NOT Do

❌ Manage production deployment infrastructure
❌ Perform database backups or recovery
❌ Create non-SQLModel ORMs (Tortoise, Piccolo, etc.)
❌ Provide synchronous database patterns (use SQLModel documentation for that)
❌ Handle sharding or read replicas (beyond basic setup)
❌ Generate test data fixtures (that's pytest-testing skill)
