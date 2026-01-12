# async-sqlmodel Skill - Navigation & Index

Welcome to the comprehensive async-sqlmodel skill for FastAPI database integration. This skill provides everything you need to build async-first database layers from basic to production-grade patterns.

## Quick Start

**Are you new to SQLModel?** Start here:
1. Read `SKILL.md` (overview and workflows)
2. Check `database-setup.md` (async engine and session setup)
3. Look at `models.md` (defining SQLModel classes)
4. Follow the examples in `async-operations.md`

**Are you using relationships?** Go here:
1. `relationships.md` (defining and loading relationships)
2. `fastapi-integration.md` (using relationships in endpoints)
3. `async-operations.md` (eager loading patterns)

**Do you need production patterns?** Check:
1. `production-patterns.md` (scaling, caching, monitoring)
2. `best-practices.md` (professional organization)
3. `migrations.md` (managing schema changes)

---

## Complete Reference Guide

### Foundational References

| Reference | Purpose | Time | Key Topics |
|-----------|---------|------|------------|
| **[database-setup.md](database-setup.md)** | Configure async engine & sessions | 15 min | `create_async_engine`, `AsyncSession`, pooling, FastAPI integration |
| **[models.md](models.md)** | Define SQLModel classes | 20 min | Models, fields, relationships, response models |
| **[async-operations.md](async-operations.md)** | Implement CRUD operations | 25 min | Create, read, update, delete, transactions |

### Advanced Patterns

| Reference | Purpose | Time | Key Topics |
|-----------|---------|------|------------|
| **[relationships.md](relationships.md)** | Define & load relationships | 25 min | One-to-many, many-to-many, eager loading, selectinload, joinedload |
| **[migrations.md](migrations.md)** | Manage database schema | 20 min | Alembic, auto-generate, upgrade/downgrade |
| **[fastapi-integration.md](fastapi-integration.md)** | Use database in FastAPI | 20 min | Session dependency, CRUD endpoints, error handling |

### Production & Best Practices

| Reference | Purpose | Time | Key Topics |
|-----------|---------|------|------------|
| **[best-practices.md](best-practices.md)** | Professional patterns | 15 min | Organization, service layer, testing, security |
| **[performance.md](performance.md)** | Query & infrastructure optimization | 30 min | Query profiling, N+1 prevention, pool tuning, benchmarking, caching |
| **[production-patterns.md](production-patterns.md)** | Scaling & reliability | 20 min | Connection pooling, caching, backups, monitoring |

---

## Learning Paths

### Path 1: Hello World to First Endpoint (1 hour)

```
1. database-setup.md (10 min)
   └─ Create async engine with SQLite

2. models.md (15 min)
   └─ Define User model

3. async-operations.md (15 min)
   └─ Implement create_user function

4. fastapi-integration.md (15 min)
   └─ Create POST /users endpoint
   └─ Use session dependency

5. Test the endpoint
```

**Outcome**: Working FastAPI endpoint with async SQLModel

---

### Path 2: Relationships & Complex Data (2 hours)

```
1. Complete Path 1 (1 hour)

2. relationships.md (30 min)
   └─ Define Team and User with one-to-many
   └─ Understand lazy loading problem
   └─ Learn selectinload/joinedload

3. fastapi-integration.md (15 min)
   └─ Load related data in endpoints
   └─ Handle circular references

4. best-practices.md (15 min)
   └─ Organize models and services
```

**Outcome**: Complex data models with proper relationship loading

---

### Path 3: Production Deployment (3+ hours)

```
1. Complete Paths 1 & 2 (2 hours)

2. migrations.md (30 min)
   └─ Setup Alembic
   └─ Create auto-generated migrations

3. best-practices.md (20 min)
   └─ Service layer pattern
   └─ Error handling
   └─ Testing setup

4. production-patterns.md (30 min)
   └─ Connection pooling optimization
   └─ Caching strategy
   └─ Monitoring & backups

5. Deploy and monitor
```

**Outcome**: Production-ready database layer with proper scaling

---

## Topic-Based Navigation

### By Database Type

#### PostgreSQL
- **Start**: `database-setup.md` (use asyncpg driver)
- **Advanced**: `production-patterns.md` (read replicas, backups)
- **Migrations**: `migrations.md` (Alembic async support)

#### SQLite (Development)
- **Start**: `database-setup.md` (use aiosqlite driver)
- **Migrations**: `migrations.md` (Alembic with SQLite)
- **Note**: No production use recommended

#### MySQL
- **Start**: `database-setup.md` (use aiomysql driver)
- **Connection pooling**: `production-patterns.md`

### By Task Type

#### Defining Models
1. `models.md` - Basic model definition
2. `relationships.md` - Add relationships (one-to-many, many-to-many)
3. `best-practices.md` - Model organization

#### CRUD Operations
1. `async-operations.md` - Create, read, update, delete patterns
2. `relationships.md` - Eager loading for relationships
3. `fastapi-integration.md` - Using in FastAPI endpoints

#### FastAPI Integration
1. `database-setup.md` - Setup and session dependency
2. `fastapi-integration.md` - Endpoints and error handling
3. `best-practices.md` - Service layer pattern

#### Relationships & Loading
1. `relationships.md` - Define relationships
2. `relationships.md` - Eager loading (selectinload/joinedload)
3. `fastapi-integration.md` - Prevent circular references

#### Testing
1. `best-practices.md` - Test fixtures with in-memory database
2. `fastapi-integration.md` - Dependency overrides

#### Production Scaling
1. `production-patterns.md` - Connection pooling
2. `production-patterns.md` - Caching and monitoring
3. `production-patterns.md` - Backups and disaster recovery

### By Problem Type

#### "How do I setup async database?"
→ `database-setup.md`

#### "How do I define models with relationships?"
→ `models.md` + `relationships.md`

#### "How do I access relationship data?"
→ `relationships.md` (selectinload/joinedload section)

#### "How do I use database in FastAPI endpoints?"
→ `fastapi-integration.md`

#### "How do I prevent N+1 queries?"
→ `relationships.md` (eager loading section)

#### "How do I manage database migrations?"
→ `migrations.md`

#### "How do I organize code professionally?"
→ `best-practices.md`

#### "How do I scale to production?"
→ `production-patterns.md`

#### "How do I handle errors properly?"
→ `fastapi-integration.md` (error handling) + `best-practices.md` (consistent patterns)

#### "How do I test my database code?"
→ `best-practices.md` (testing section)

---

## Key Concepts

### Async/Await
- **All database operations must use `await`**
- **Every `session.execute()`, `session.commit()`, `session.refresh()` needs `await`**
- See: `async-operations.md`

### Eager Loading (Critical!)
- **Always eager load relationships before accessing them**
- **Use `selectinload()` for collections (List[...])**
- **Use `joinedload()` for single objects (Optional[...])**
- **Never lazy load in async code (will error)**
- See: `relationships.md`

### Session Lifecycle
- **Session provided as FastAPI dependency**
- **Automatic rollback on errors**
- **Automatic cleanup on request completion**
- See: `database-setup.md`, `fastapi-integration.md`

### Connection Pooling
- **Reuse connections across requests (not create new each time)**
- **Configure pool_size and max_overflow for expected load**
- **Use pool_pre_ping to detect stale connections**
- See: `database-setup.md`, `production-patterns.md`

### Migrations
- **Use Alembic to track schema changes**
- **Auto-generate migrations from model changes**
- **Version control all migration files**
- **Test migrations in staging before production**
- See: `migrations.md`

---

## File Reference

### Core Skill
- **SKILL.md** (340 lines) - Skill definition with workflows and clarifications

### Database Setup
- **database-setup.md** (280 lines) - Async engine, pooling, session configuration

### Models & Data
- **models.md** (380 lines) - SQLModel definition, fields, relationships, response models
- **relationships.md** (420 lines) - Relationship types, eager loading, N+1 prevention
- **async-operations.md** (400 lines) - CRUD operations, transactions, error handling

### FastAPI Integration
- **fastapi-integration.md** (350 lines) - Endpoints, session dependency, error handling

### DevOps & Administration
- **migrations.md** (380 lines) - Alembic setup, auto-generation, applying migrations
- **production-patterns.md** (320 lines) - Connection pooling, caching, monitoring, backups
- **performance.md** (450 lines) - Query profiling, N+1 detection, pool tuning, benchmarking, caching
- **best-practices.md** (380 lines) - Organization, service layer, testing, security

**Total**: 10+ reference files, 3,500+ lines of professional documentation

---

## Common Scenarios

### Scenario 1: Create User with Team

```
1. Define models (models.md)
   └─ User with team_id foreign key
   └─ Team with players relationship

2. Create CRUD service (best-practices.md)
   └─ UserService.create_user()

3. Add FastAPI endpoint (fastapi-integration.md)
   └─ POST /users with team_id

4. Test (best-practices.md)
   └─ Override session in tests
```

### Scenario 2: List Teams with Players

```
1. Load teams with eager loading (relationships.md)
   └─ Use selectinload(Team.players)

2. Create endpoint (fastapi-integration.md)
   └─ GET /teams with pagination

3. Handle circular references (fastapi-integration.md)
   └─ Use response models without player.team
```

### Scenario 3: Deploy to Production

```
1. Optimize connection pooling (production-patterns.md)
   └─ Calculate pool_size from expected load

2. Setup migrations (migrations.md)
   └─ Test with staging database

3. Configure monitoring (production-patterns.md)
   └─ Log slow queries
   └─ Monitor pool health

4. Implement caching (production-patterns.md)
   └─ Redis for frequently accessed data
```

---

## Production Readiness Checklist

### Before Going Live

- [ ] Async engine created with correct driver (asyncpg, aiosqlite, aiomysql)
- [ ] AsyncSession configured with expire_on_commit=False
- [ ] Connection pooling tuned for expected load
- [ ] All relationships eagerly loaded (selectinload/joinedload)
- [ ] Response models prevent circular references
- [ ] Error handling with proper rollback
- [ ] Migrations tested and verified
- [ ] Tests use in-memory database
- [ ] Monitoring and alerting configured
- [ ] Backups automated and tested
- [ ] Database credentials in environment variables
- [ ] Slow query logging enabled
- [ ] Health check endpoint implemented

---

## Important Reminders

### ⚠️ Critical: Always Eager Load Relationships!

```python
# ❌ WILL FAIL
async def get_teams(session):
    teams = await session.execute(select(Team))
    # Accessing teams[0].players causes error in async context
    print(teams[0].players)

# ✅ CORRECT
async def get_teams(session):
    from sqlalchemy.orm import selectinload
    stmt = select(Team).options(selectinload(Team.players))
    result = await session.execute(stmt)
    teams = result.scalars().all()
    # Now .players is available
    print(teams[0].players)
```

### ⚠️ Critical: Use await on All Database Operations!

```python
# ❌ INCOMPLETE (missing await)
async def create_user(session):
    user = User(username="john")
    session.add(user)
    session.commit()  # ERROR: forgot await!

# ✅ CORRECT
async def create_user(session):
    user = User(username="john")
    session.add(user)
    await session.commit()  # ✅ await
    await session.refresh(user)  # ✅ await
```

---

## Support & Resources

### Official Documentation
- [SQLModel docs](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy async docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI dependency injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

### Key Libraries
- **sqlmodel** - SQL models with Pydantic
- **sqlalchemy** - Core async support
- **alembic** - Database migrations
- **asyncpg** - Async PostgreSQL driver
- **aiosqlite** - Async SQLite driver

---

## Tips for Success

1. **Start with SQLite** - Easier for development and learning
2. **Use response models** - Separate database models from API responses
3. **Always eager load** - Prevent N+1 query problems
4. **Test in-memory** - Fast, isolated database for unit tests
5. **Monitor queries** - Log slow queries in production
6. **Backup regularly** - Automate backups for production
7. **Document models** - Add docstrings explaining each model
8. **Version control migrations** - Git commit all Alembic files
9. **Use service layer** - Encapsulate business logic
10. **Measure coverage** - Test both happy path and errors

---

## Cross-Skill Integration

### Testing Your Database Layer
For comprehensive testing of SQLModel with pytest, see the **pytest-testing skill** documentation: `fastapi-sqlmodel-testing.md` covers async fixtures, relationship testing, endpoint integration tests, and mocking patterns.

### FastAPI Best Practices
For routing, authentication, and API design patterns, see the **fastapi-builder skill** documentation.

---

## Version Information

- **Tested with**: Python 3.9+, SQLModel 0.0.14+, SQLAlchemy 2.0+
- **Async drivers**: asyncpg, aiosqlite, aiomysql
- **Last Updated**: 2026-01-12
- **Status**: Production-ready

---

**Ready to build your async database layer?** Pick your learning path above and dive in!
