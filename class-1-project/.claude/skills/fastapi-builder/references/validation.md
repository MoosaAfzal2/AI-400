# FastAPI Validation Patterns

## Pydantic Models (Core Validation)

### Basic Model

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None
```

### Field Validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, le=1000000)
    quantity: int = Field(default=1, ge=0)
    description: str | None = Field(default=None, max_length=500)
```

Common Field constraints:
- `min_length`, `max_length` - string length
- `gt`, `ge`, `lt`, `le` - numeric comparisons
- `regex` - pattern matching
- `description` - OpenAPI docs

### Custom Validators

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    username: str
    email: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
```

### Model Validators (Cross-field)

```python
from pydantic import BaseModel, model_validator

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode='after')
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise ValueError('New password and confirmation do not match')
        if self.current_password == self.new_password:
            raise ValueError('New password must be different from current')
        return self
```

## Request Validation in Routes

### Automatic Validation

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
async def create_item(item: Item):
    # item is automatically validated
    # FastAPI returns 422 if invalid
    return item
```

### Optional Fields with Defaults

```python
class Item(BaseModel):
    name: str
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

### Query String Validation

```python
from fastapi import Query

@app.get("/items/")
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return {"skip": skip, "limit": limit}
```

### Path Parameter Validation

```python
from fastapi import Path

@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(..., gt=0, description="The item ID must be positive")
):
    return {"item_id": item_id}
```

### Header Validation

```python
from fastapi import Header

@app.get("/items/")
async def get_items(
    user_agent: str | None = Header(None),
    x_token: str = Header(...)
):
    return {"user_agent": user_agent}
```

## Response Validation

```python
from pydantic import BaseModel

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    # Only fields in ItemResponse are included
    return {"id": item_id, "name": "Widget", "price": 9.99, "internal": "data"}
```

## Error Responses

FastAPI automatically generates standardized error responses:

```json
// 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

## Best Practices

1. **Use Field for documentation**: `Field(..., description="User's full name")`
2. **Validate at boundaries**: Validate user input, not internal code
3. **Use custom validators sparingly**: Keep validation logic in models
4. **Compose models**: Reuse Pydantic models across schemas
5. **Document error cases**: Use OpenAPI examples for error responses
