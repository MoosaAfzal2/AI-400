# Sync to Async Migration - FastAPI Patterns

Migrate existing synchronous FastAPI applications to async-first architecture. This guide covers identifying sync code, refactoring patterns, database migration, and production verification.

**Cross-Skill References**: See **async-sqlmodel skill** for comprehensive async database patterns and optimization; see **pytest-testing skill** for async test conversion patterns.

## Migration Overview

### Why Migrate to Async?

```
Sync FastAPI (Limited):
├─ Slower concurrent requests (threads block)
├─ Higher memory per request (one thread per request)
├─ Database waits block entire worker
└─ Limited scalability

Async FastAPI (Production):
├─ Efficient concurrent handling (non-blocking)
├─ Lower memory footprint
├─ Database/IO doesn't block
└─ Higher throughput, better scalability
```

---

## Phase 1: Audit Existing Code

### Identify Sync Code

```python
# ❌ Sync patterns to migrate
import requests
from sqlalchemy.orm import Session

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session):  # ❌ sync function
    # ❌ Sync database session
    user = db.query(User).filter(User.id == user_id).first()

    # ❌ Sync HTTP call
    response = requests.get(f"https://api.example.com/users/{user_id}")

    return user
```

### Sync Code Checklist

```
Before migration, identify:
- [ ] Sync route handlers (def, not async def)
- [ ] Sync database sessions (Session, not AsyncSession)
- [ ] Sync HTTP calls (requests, not httpx)
- [ ] Sync file operations (open(), not aiofiles)
- [ ] Sync external services (blocking calls)
- [ ] Threads/processes (threading, multiprocessing)
- [ ] Context managers without async support
```

---

## Phase 2: Dependency Preparation

### Install Async Alternatives

```bash
# Current async libraries for FastAPI
pip install sqlalchemy[asyncio]
pip install httpx  # Async HTTP client
pip install aiofiles  # Async file operations
pip install sqlmodel  # SQLModel with async support
pip install asyncpg  # Async PostgreSQL driver (or aiosqlite, aiomysql)
```

### Create Async Engine (if using SQLAlchemy/SQLModel)

```python
# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

# Async engine with proper pooling
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    """Provide async session for endpoints"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## Phase 3: Route Handler Migration

### Migrate Route Functions

```python
# ❌ BEFORE: Sync route
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return user

# ✅ AFTER: Async route
@app.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    # Await all async operations
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)
    return user
```

### Key Changes

1. **Add `async` keyword** to function definition
2. **Use `await`** on all async operations
3. **Switch dependencies** to async versions
4. **Update type hints** (Session → AsyncSession, etc.)

---

## Phase 4: Database Migration

### Migrate Database Sessions

```python
# ❌ BEFORE: Sync SQLAlchemy
from sqlalchemy.orm import Session, sessionmaker

# Sync engine
sync_engine = create_engine("postgresql://...")
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ✅ AFTER: Async SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Async engine
async_engine = create_async_engine("postgresql+asyncpg://...")
async_session_maker = async_sessionmaker(async_engine, class_=AsyncSession)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

@app.get("/users/")
async def list_users(session: AsyncSession = Depends(get_session)):
    statement = select(User)
    result = await session.execute(statement)
    return result.scalars().all()
```

### Migrate Query Patterns

```python
# ❌ BEFORE: Sync SQLAlchemy ORM
user = db.query(User).filter(User.id == 1).first()
users = db.query(User).limit(10).all()

# ✅ AFTER: Async SQLAlchemy Core
from sqlalchemy import select

user = await session.get(User, 1)
statement = select(User).limit(10)
result = await session.execute(statement)
users = result.scalars().all()

# ✅ Async SQLModel patterns
from sqlmodel import select

statement = select(User).limit(10)
result = await session.execute(statement)
users = result.scalars().all()
```

### Migrate Relationships (if using SQLAlchemy/SQLModel)

```python
# ❌ BEFORE: Sync lazy loading
team = db.query(Team).first()
# Access relationship (implicit query)
players = team.players

# ✅ AFTER: Async eager loading (REQUIRED)
from sqlalchemy.orm import selectinload

statement = select(Team).options(selectinload(Team.players))
result = await session.execute(statement)
team = result.unique().scalar_one()
# Now .players is available (no implicit queries)
players = team.players
```

---

## Phase 5: HTTP Client Migration

### Migrate External API Calls

```python
# ❌ BEFORE: Sync requests
import requests

@app.get("/external-data")
def get_external_data():
    response = requests.get("https://api.example.com/data")
    return response.json()

# ✅ AFTER: Async httpx
import httpx

@app.get("/external-data")
async def get_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### Reuse HTTP Client (Production Pattern)

```python
# src/http_client.py

import httpx

# Global client (connection pooling, performance)
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
)

# In endpoints
@app.get("/external-data")
async def get_external_data():
    response = await http_client.get("https://api.example.com/data")
    return response.json()

# Cleanup in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await http_client.aclose()
```

---

## Phase 6: File Operations Migration

### Migrate File Handling

```python
# ❌ BEFORE: Sync file operations
@app.post("/upload/")
def upload_file(file: UploadFile):
    contents = file.file.read()  # Blocks
    with open("uploads/file.txt", "w") as f:
        f.write(contents.decode())  # Blocks
    return {"filename": file.filename}

# ✅ AFTER: Async file operations
import aiofiles

@app.post("/upload/")
async def upload_file(file: UploadFile):
    contents = await file.read()  # Non-blocking
    async with aiofiles.open("uploads/file.txt", "w") as f:
        await f.write(contents.decode())  # Non-blocking
    return {"filename": file.filename}
```

---

## Phase 7: Service Layer Migration

### Migrate Business Logic

```python
# ❌ BEFORE: Sync service
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str) -> User:
        user = User(username=username, email=email)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

# Use in endpoint
@app.post("/users/")
def create_user(username: str, email: str, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(username, email)

# ✅ AFTER: Async service
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, email: str) -> User:
        user = User(username=username, email=email)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

# Use in endpoint
@app.post("/users/")
async def create_user(username: str, email: str, session: AsyncSession = Depends(get_session)):
    service = UserService(session)
    return await service.create_user(username, email)
```

---

## Phase 8: Middleware Migration

### Migrate Custom Middleware

```python
# ❌ BEFORE: Sync middleware
@app.middleware("http")
def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = call_next(request)  # Sync
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# ✅ AFTER: Async middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)  # Async
    response.headers["X-Request-ID"] = request.state.request_id
    return response
```

---

## Phase 9: Dependency Injection Migration

### Migrate Dependencies

```python
# ❌ BEFORE: Sync dependencies
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == token).first()
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return user

# ✅ AFTER: Async dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, int(token))
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user
```

---

## Phase 10: Testing Migration

### Migrate Tests to Async

```python
# ❌ BEFORE: Sync tests
def test_create_user(client: TestClient, db: Session):
    response = client.post("/users/", json={"username": "john", "email": "john@example.com"})
    assert response.status_code == 201
    user = db.query(User).filter(User.username == "john").first()
    assert user is not None

# ✅ AFTER: Async tests
@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient, session: AsyncSession):
    response = await async_client.post(
        "/users/",
        json={"username": "john", "email": "john@example.com"}
    )
    assert response.status_code == 201
    from sqlalchemy import select
    statement = select(User).where(User.username == "john")
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    assert user is not None
```

---

## Phase 11: Lifespan Events Migration

### Migrate Startup/Shutdown

```python
# ❌ BEFORE: Sync events
@app.on_event("startup")
def startup():
    # Sync initialization
    pass

@app.on_event("shutdown")
def shutdown():
    # Sync cleanup
    pass

# ✅ AFTER: Async lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup (async)
    print("Starting up...")
    yield
    # Shutdown (async)
    print("Shutting down...")
    await http_client.aclose()

app = FastAPI(lifespan=lifespan)
```

---

## Phase 12: Verification & Testing

### Pre-Migration Checklist

Before starting migration:
- [ ] All endpoints identified
- [ ] External dependencies (databases, APIs) support async
- [ ] Team familiar with async/await patterns
- [ ] Testing strategy decided
- [ ] Rollback plan created
- [ ] Staging environment available

### Post-Migration Verification

After migration:
- [ ] All route handlers are `async def`
- [ ] All database operations use `await`
- [ ] All HTTP calls use `httpx` with `await`
- [ ] All file operations use `aiofiles` with `await`
- [ ] No blocking operations in request path
- [ ] Relationships use eager loading (selectinload/joinedload)
- [ ] Tests run with `pytest.mark.asyncio`
- [ ] Load testing shows improved throughput
- [ ] No deadlocks or race conditions
- [ ] Error handling works correctly

---

## Common Migration Pitfalls

### ❌ Forgetting `await`

```python
# ❌ WRONG: Missing await
user = session.get(User, 1)  # Returns coroutine, not user

# ✅ CORRECT: With await
user = await session.get(User, 1)
```

### ❌ Lazy Loading in Async

```python
# ❌ WRONG: Accessing relationship causes error
user = await session.get(User, 1)
print(user.team.name)  # ERROR: Can't lazy load in async

# ✅ CORRECT: Eager load first
from sqlalchemy.orm import joinedload
statement = select(User).where(User.id == 1).options(joinedload(User.team))
result = await session.execute(statement)
user = result.unique().scalar_one()
print(user.team.name)  # OK: Already loaded
```

### ❌ Blocking Calls in Async

```python
# ❌ WRONG: Blocking call blocks entire async runtime
time.sleep(5)  # Blocks all requests
requests.get("https://api.example.com")  # Blocks all requests

# ✅ CORRECT: Use async alternatives
await asyncio.sleep(5)
await http_client.get("https://api.example.com")
```

### ❌ Sync Context Managers

```python
# ❌ WRONG: Sync context manager doesn't await
with open("file.txt") as f:
    data = f.read()

# ✅ CORRECT: Async context manager with await
async with aiofiles.open("file.txt") as f:
    data = await f.read()
```

---

## Migration Strategy

### Big Bang (Not Recommended)

```
❌ Migrate entire codebase at once
├─ High risk
├─ Difficult to test
└─ Hard to rollback
```

### Gradual Migration (Recommended)

```
✅ Migrate one feature/module at a time
├─ Test each change
├─ Easy to rollback
├─ Team learns gradually
└─ Reduces risk
```

**Suggested order:**
1. Database access layer
2. External API calls
3. Business logic services
4. Route handlers
5. Middleware
6. Tests

---

## Production Deployment

### Verify in Staging

```bash
# Load test to verify performance improvement
ab -n 10000 -c 100 https://staging.example.com/

# Monitor async tasks
python -c "import asyncio; asyncio.run(my_async_function())"

# Profile to ensure no blocking
python -m cProfile app.py
```

### Rollback Plan

Keep sync code available:
```bash
git branch sync-version  # Keep sync code as backup
git checkout async-migration  # Work on async version

# If issues arise:
git checkout sync-version  # Quick rollback
```

---

## Sync-to-Async Migration Checklist

Before considering migration complete:
- [ ] All endpoints are async
- [ ] All database calls await AsyncSession
- [ ] All external API calls use httpx with await
- [ ] All file operations use aiofiles with await
- [ ] Relationships use eager loading
- [ ] Tests updated to pytest.mark.asyncio
- [ ] Error handling verified
- [ ] Staging deployment successful
- [ ] Performance improved (throughput/latency)
- [ ] No async-related errors in logs
- [ ] Load testing passed
- [ ] Team trained on async patterns

---

## Summary

Successful sync→async migration requires:
1. **Identify** all sync code patterns
2. **Install** async alternatives
3. **Migrate** incrementally, starting with database layer
4. **Update** all route handlers to async
5. **Test** thoroughly with async patterns
6. **Verify** in staging before production
7. **Monitor** for performance improvements and errors
