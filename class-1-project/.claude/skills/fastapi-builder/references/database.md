# FastAPI Database Integration (SQLAlchemy + PostgreSQL)

## Async Setup

### Connection Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# PostgreSQL with asyncpg
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0,
    connect_args={"timeout": 10}
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()
```

### Database Session Dependency

```python
from typing import AsyncGenerator
from fastapi import Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Use in routes:
# async def get_items(db: AsyncSession = Depends(get_db)):
```

### Startup/Shutdown Events

```python
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
```

## Models & Schemas

### SQLAlchemy ORM Model

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="items")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)

    items = relationship("Item", back_populates="user", cascade="all, delete")
```

### Pydantic Schemas

```python
from pydantic import BaseModel
from datetime import datetime

class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    created_at: datetime

    class Config:
        from_attributes = True
```

## CRUD Operations

### Create

```python
from fastapi import FastAPI, Depends

app = FastAPI()

@app.post("/items/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
```

### Read Single

```python
from fastapi import HTTPException

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(Item, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
```

### Read Multiple (with Pagination)

```python
from sqlalchemy import select

@app.get("/items/", response_model=list[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    query = select(Item).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return items
```

### Update

```python
@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_item = await db.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
```

### Delete

```python
@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    db_item = await db.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(db_item)
    await db.commit()
    return {"deleted": True}
```

## Transactions & Bulk Operations

### Transactions

```python
@app.post("/transfer/")
async def transfer_funds(
    from_user_id: int,
    to_user_id: int,
    amount: float,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Entire operation in transaction
        from_user = await db.get(User, from_user_id)
        to_user = await db.get(User, to_user_id)

        from_user.balance -= amount
        to_user.balance += amount

        db.add(from_user)
        db.add(to_user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Transfer failed")
```

### Bulk Insert

```python
@app.post("/items/bulk/")
async def bulk_create_items(
    items: list[ItemCreate],
    db: AsyncSession = Depends(get_db)
):
    db_items = [Item(**item.model_dump()) for item in items]
    db.add_all(db_items)
    await db.commit()
    return {"created": len(db_items)}
```

## Relationships

### One-to-Many

```python
# Already shown in models above
# User has many Items

@app.get("/users/{user_id}/items/")
async def get_user_items(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    # Access related items
    return user.items
```

### Many-to-Many

```python
from sqlalchemy import Table

user_item_association = Table(
    'user_items',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('item_id', Integer, ForeignKey('items.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    items = relationship("Item", secondary=user_item_association)
```

## Migrations with Alembic

### Initialize

```bash
alembic init alembic
```

### Create Migration

```bash
alembic revision --autogenerate -m "Create tables"
```

### Apply Migration

```bash
alembic upgrade head
```

## Best Practices

1. **Use connection pooling**: Pool keeps connections open
2. **Use transactions**: Ensure data consistency
3. **Index foreign keys**: Improves query performance
4. **Lazy vs eager loading**: Be explicit about relationship loading
5. **Paginate results**: Avoid loading entire tables
6. **Use prepared statements**: SQL parameterization built-in
7. **Test with real database**: SQLite for development, PostgreSQL for production
8. **Handle connection timeouts**: Implement retry logic
