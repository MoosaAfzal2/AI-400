# FastAPI Routing Patterns

## Basic Route Types

### Path Parameters

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}
```

FastAPI automatically validates `item_id` as an integer. Path parameters are required.

### Query Parameters

```python
@app.get("/items/")
async def list_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

Query parameters are optional if they have default values.

### Request Body (POST/PUT)

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

Pydantic automatically validates the request body and returns 422 Unprocessable Entity if invalid.

### Multiple Body Parameters

```python
class Item(BaseModel):
    name: str
    price: float

class User(BaseModel):
    username: str

@app.post("/offers/")
async def create_offer(item: Item, user: User):
    return {"item": item, "user": user}
```

FastAPI sends `item` and `user` as separate JSON objects in the request.

## Advanced Patterns

### HTTP Methods

```python
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Retrieve an item"""
    pass

@app.post("/items/")
async def create_item(item: Item):
    """Create a new item"""
    pass

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    """Replace an entire item"""
    pass

@app.patch("/items/{item_id}")
async def partial_update(item_id: int, item: Item):
    """Partially update an item"""
    pass

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item"""
    pass
```

### Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    pass
```

### Response Models

```python
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return {"id": item_id, "name": "Widget", "price": 9.99}
```

FastAPI filters the response to only include fields in `ItemResponse`.

### Multiple Response Models

```python
@app.get("/items/{item_id}", responses={
    200: {"model": ItemResponse},
    404: {"description": "Item not found"},
})
async def get_item(item_id: int):
    pass
```

### OpenAPI Documentation

```python
@app.get(
    "/items/{item_id}",
    summary="Get item by ID",
    description="Retrieve a specific item from the database",
    tags=["items"]
)
async def get_item(item_id: int):
    pass
```

Accessible at `/docs` (Swagger UI) or `/redoc` (ReDoc).

## Routing Organization

### Flat Structure (Simple Projects)

```
myproject/
├── main.py           # All routes
├── schemas.py        # Pydantic models
├── database.py       # Database setup
└── requirements.txt
```

### Modular Structure (Larger Projects)

```
myproject/
├── main.py           # App creation, startup/shutdown
├── config.py         # Configuration
├── database.py       # Database setup
├── routers/
│   ├── items.py      # Item routes
│   ├── users.py      # User routes
│   └── auth.py       # Authentication routes
├── schemas/
│   ├── item.py
│   └── user.py
├── models/
│   ├── item.py       # SQLAlchemy models
│   └── user.py
├── dependencies.py   # Shared dependencies
├── exceptions.py     # Custom exceptions
└── tests/
```

Import and include routers in main:

```python
from fastapi import FastAPI
from routers import items, users, auth

app = FastAPI()
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
```
