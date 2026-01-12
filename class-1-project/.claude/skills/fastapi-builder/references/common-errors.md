# Common FastAPI Errors & Solutions

## Request Validation Errors

### Error: "422 Unprocessable Entity"

**Causes:**
- Missing required field in request body
- Invalid data type (e.g., string instead of number)
- Field value violates validation constraints

**Solution:**
```python
# Check error details
response = client.post("/items/", json={"name": "Widget"})  # Missing price
print(response.json())
# {
#   "detail": [
#     {
#       "loc": ["body", "price"],
#       "msg": "Field required",
#       "type": "missing"
#     }
#   ]
# }

# Fix: Provide all required fields
response = client.post("/items/", json={"name": "Widget", "price": 9.99})
```

## Database Connection Errors

### Error: "sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file"

**Cause:** Database path doesn't exist or permissions issue

**Solution:**
```python
# Use absolute path or ensure directory exists
import os
from pathlib import Path

db_dir = Path("./data")
db_dir.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{db_dir}/app.db"
```

### Error: "Connection pool timeout"

**Cause:** Database connections exhausted, queries taking too long

**Solution:**
```python
# Adjust pool size and overflow
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Test connections before use
    connect_args={"timeout": 10}
)
```

## Authentication Errors

### Error: "401 Unauthorized - Invalid token"

**Cause:** Token expired, malformed, or wrong secret key

**Solution:**
```python
# Verify token structure
from jose import jwt, JWTError

try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(payload)  # Debug: check content
except JWTError as e:
    print(f"Token error: {e}")

# Ensure SECRET_KEY is same for encoding/decoding
SECRET_KEY = "your-consistent-secret-key"  # Don't change mid-session
```

### Error: "403 Forbidden - Not enough permissions"

**Cause:** Token doesn't have required scopes

**Solution:**
```python
# Ensure token includes required scopes
def create_access_token(username: str, scopes: list[str]):
    payload = {"sub": username, "scopes": scopes}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# And verify them in dependency
async def verify_token_with_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
):
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403)
```

## Async/Await Issues

### Error: "RuntimeError: Event loop is closed"

**Cause:** Mixing sync and async code incorrectly

**Solution:**
```python
# Always use async for database operations
@app.get("/items/")
async def list_items(db: AsyncSession = Depends(get_db)):  # async!
    result = await db.execute(select(Item))
    return result.scalars().all()

# Don't do this:
@app.get("/items/")  # Missing async!
def list_items(db: AsyncSession = Depends(get_db)):
    result = db.execute(select(Item))  # Missing await!
```

### Error: "greenlet_spawn has not been called"

**Cause:** Using sync SQLAlchemy with async FastAPI

**Solution:**
```python
# Use async SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Correct
engine = create_async_engine("postgresql+asyncpg://...")

# Wrong
engine = create_engine("postgresql://...")  # No async support
```

## CORS Errors

### Error: "Access to XMLHttpRequest blocked by CORS policy"

**Cause:** Frontend can't access API due to CORS settings

**Solution:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# For development (allow all):
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Dependency Injection Issues

### Error: "Could not determine how to get dependant"

**Cause:** Circular dependency or incorrect dependency type

**Solution:**
```python
# Circular: A depends on B, B depends on A
# Break cycle by using Request directly
from fastapi import Request

async def get_user_from_request(request: Request):
    return request.state.user

# Or restructure dependencies

# Type mismatch
# Wrong:
async def my_route(db: str = Depends(get_db)):  # Type should be AsyncSession
    pass

# Right:
async def my_route(db: AsyncSession = Depends(get_db)):
    pass
```

## Startup/Shutdown Errors

### Error: "Event loop is already running"

**Cause:** Using synchronous context managers with async startup

**Solution:**
```python
# Use lifespan parameter instead of @app.on_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## Debugging Tips

1. **Enable SQL logging**: `create_async_engine(DATABASE_URL, echo=True)`
2. **Print to console**: Use `print()` in routes for debugging
3. **Check request/response**: Use `response.json()` and `response.status_code`
4. **Enable CORS for localhost**: Useful during development
5. **Test with curl**: `curl -X POST http://localhost:8000/items/ -H "Content-Type: application/json" -d '{"name": "test", "price": 9.99}'`
6. **Check dependencies**: Verify `get_db()` returns correct type
7. **Watch logs**: Run with `--log-level debug` flag
