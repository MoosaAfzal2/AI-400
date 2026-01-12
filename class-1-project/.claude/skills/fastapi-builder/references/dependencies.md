# FastAPI Dependency Injection Patterns

## Basic Dependencies

### Simple Dependency

```python
from fastapi import Depends

def common_parameters(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/items/")
async def list_items(commons: dict = Depends(common_parameters)):
    return commons
```

### Database Session Dependency

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

@app.get("/items/")
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

## Authentication Dependencies

### Current User Dependency

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    return username

@app.get("/protected/")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
```

### Current User with Database Lookup

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/profile/")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

### Optional Authentication

```python
async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme)
) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

@app.get("/public/")
async def public_route(user: str | None = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user}"}
    return {"message": "Hello guest"}
```

## Advanced Patterns

### Dependency with State

```python
class RequestContext:
    def __init__(self, user_id: int, request_id: str):
        self.user_id = user_id
        self.request_id = request_id

async def get_request_context(
    current_user: str = Depends(get_current_user),
    request: Request
) -> RequestContext:
    request_id = request.headers.get("X-Request-ID")
    return RequestContext(user_id=current_user.id, request_id=request_id)

@app.get("/context/")
async def use_context(ctx: RequestContext = Depends(get_request_context)):
    return {"user_id": ctx.user_id, "request_id": ctx.request_id}
```

### Conditional Dependencies

```python
async def verify_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(verify_admin)
):
    # Only admin can delete
    return {"deleted": user_id}
```

### Dependency Chains

```python
async def get_query_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
) -> Item:
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404)
    return item

async def verify_item_owner(
    item: Item = Depends(get_query_item),
    current_user: User = Depends(get_current_user)
) -> Item:
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not item owner")
    return item

@app.put("/items/{item_id}")
async def update_item(
    item_update: ItemUpdate,
    item: Item = Depends(verify_item_owner)
):
    # Item is already verified as owned by current user
    return item
```

## Sub-dependencies

### Multiple Levels

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
        await session.close()

async def get_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    result = await db.execute(select(User).where(User.username == payload["sub"]))
    return result.scalar_one()

async def verify_user_active(
    user: User = Depends(get_user_from_token)
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")
    return user

@app.get("/me/")
async def get_me(current_user: User = Depends(verify_user_active)):
    return current_user
```

## Caching Dependencies

### Use cache_key Parameter

```python
from fastapi import Depends

async def get_query(
    skip: int = 0,
    limit: int = 10
):
    return {"skip": skip, "limit": limit}

# Multiple dependencies with same params share one call
@app.get("/items/")
async def list_items(
    query1: dict = Depends(get_query),
    query2: dict = Depends(get_query)
):
    # get_query() called only once within request
    return {"query1": query1, "query2": query2}
```

## Best Practices

1. **Keep dependencies simple**: Each dependency does one thing
2. **Reuse dependencies**: Share common logic across routes
3. **Type hint dependencies**: FastAPI uses types for introspection
4. **Test dependencies independently**: Mock in tests
5. **Order matters**: Earlier dependencies available to later ones
6. **Avoid circular dependencies**: A → B → A is invalid
7. **Use FastAPI Security classes**: OAuth2PasswordBearer, APIKeyHeader, etc.
8. **Document security**: Use OpenAPI tags and documentation
