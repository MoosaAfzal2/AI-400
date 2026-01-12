# API Design and Endpoint Patterns - Production REST API

## RESTful Endpoint Naming

### Convention Pattern

```
/api/v{version}/{resource}/{sub-resource}/{action}
```

Examples:

```python
# Version your API for backward compatibility
/api/v1/...

# Users resource
GET    /api/v1/users                 # List all users
GET    /api/v1/users/{id}            # Get specific user
POST   /api/v1/users                 # Create user
PUT    /api/v1/users/{id}            # Replace user
PATCH  /api/v1/users/{id}            # Partial update
DELETE /api/v1/users/{id}            # Delete user

# Sub-resources (nested relationships)
GET    /api/v1/users/{id}/posts      # User's posts
POST   /api/v1/users/{id}/posts      # Create post for user
GET    /api/v1/users/{id}/posts/{post_id}

# Authentication endpoints
POST   /api/v1/auth/sign-up          # Registration
POST   /api/v1/auth/login            # Login
POST   /api/v1/auth/logout           # Logout
POST   /api/v1/auth/refresh          # Refresh token
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

# Current user (me)
GET    /api/v1/user/me               # Current user profile
PATCH  /api/v1/user/me               # Update profile
```

---

## HTTP Status Codes (Correct Usage)

### 2xx Success

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful request, returns data |
| 201 | Created | Resource successfully created |
| 202 | Accepted | Request accepted, processing async |
| 204 | No Content | Successful request, no data returned |

```python
# 200 OK - Return data
@router.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404)
    return user  # Returns 200 with user data

# 201 Created - Resource created
@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user  # Returns 201 with created user

# 204 No Content - No data returned
@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404)
    db.delete(user)
    db.commit()
    # Returns 204 with empty body
```

### 4xx Client Errors

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 | Bad Request | Invalid input, validation failure |
| 401 | Unauthorized | Missing/invalid credentials |
| 403 | Forbidden | Valid credentials but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (duplicate) |
| 422 | Unprocessable Entity | Validation error (FastAPI default) |

```python
# 400 Bad Request - Invalid input
if price < 0:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Price cannot be negative"
    )

# 401 Unauthorized - Missing/invalid token
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# 403 Forbidden - Valid auth but no permission
if not current_user.is_admin:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions"
    )

# 404 Not Found - Resource missing
user = db.query(User).filter(User.id == id).first()
if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

# 409 Conflict - Duplicate resource
existing = db.query(User).filter(User.email == email).first()
if existing:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Email already registered"
    )
```

### 5xx Server Errors

| Code | Meaning | Use Case |
|------|---------|----------|
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Temporary service issue (DB down, email service down) |

```python
# 500 - Unexpected error (usually automatic from uncaught exceptions)
# 503 - Service temporarily unavailable (fail gracefully)
try:
    await send_email(user.email)
except SMTPException:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Email service temporarily unavailable. Please try again later."
    )
```

---

## Request/Response Schemas

### Pydantic Schemas

```python
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime

# Request schemas (input validation)
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="At least 8 characters")
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

# Response schemas (output formatting)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy compatibility

# Authentication response
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Short-lived access token")
    refresh_token: str = Field(..., description="Longer-lived refresh token")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    token_type: str = Field(default="Bearer", description="Token type")
```

### Usage in Endpoints

```python
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user: UserCreate,  # Input validation
    db: Session = Depends(get_db)
) -> UserResponse:  # Output formatting
    """
    Create new user.

    Validates input using UserCreate schema.
    Returns UserResponse with filtered fields.
    """
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user  # Formatted as UserResponse
```

---

## Pagination

### Query Parameters

```python
@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(100, ge=1, le=1000, description="Limit"),
    db: Session = Depends(get_db)
):
    """
    List users with pagination.

    - skip: How many users to skip (offset)
    - limit: Maximum users to return (1-1000)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# Usage
# GET /api/v1/users?skip=0&limit=50  (first 50)
# GET /api/v1/users?skip=50&limit=50 (next 50)
```

### Paginated Response

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool = True

    @validator('has_more', pre=True, always=True)
    def calculate_has_more(cls, v, values):
        if 'total' in values and 'skip' in values and 'limit' in values:
            return (values['skip'] + values['limit']) < values['total']
        return v

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> PaginatedResponse[UserResponse]:
    """List users with pagination info"""
    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()

    return PaginatedResponse[UserResponse](
        items=users,
        total=total,
        skip=skip,
        limit=limit
    )
```

---

## Filtering and Searching

### Query Filters

```python
@router.get("/users")
async def search_users(
    email: Optional[str] = Query(None, description="Filter by email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    """
    Search/filter users.

    - email: Email contains (case-insensitive)
    - role: Exact role match
    - is_active: Active status
    """
    query = db.query(User)

    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))

    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.offset(skip).limit(limit).all()
    return users

# Usage
# GET /api/v1/users?email=john&role=admin
# GET /api/v1/users?is_active=true
```

---

## Sorting

```python
from enum import Enum

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortBy(str, Enum):
    EMAIL = "email"
    CREATED = "created_at"
    NAME = "first_name"

@router.get("/users")
async def list_users(
    sort_by: SortBy = Query(SortBy.CREATED),
    sort_order: SortOrder = Query(SortOrder.DESC),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    """List users with sorting"""
    query = db.query(User)

    # Build sort column
    sort_column = {
        SortBy.EMAIL: User.email,
        SortBy.CREATED: User.created_at,
        SortBy.NAME: User.first_name,
    }[sort_by]

    # Apply sort
    if sort_order == SortOrder.ASC:
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    users = query.offset(skip).limit(limit).all()
    return users

# Usage
# GET /api/v1/users?sort_by=email&sort_order=asc
```

---

## Error Response Format

### Standard Error Response

```python
from datetime import datetime
from typing import Optional

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                message=exc.detail,
                code="HTTP_ERROR",
            ),
            request_id=request.headers.get("X-Request-ID")
        ).model_dump()
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(ErrorDetail(
            field=".".join(str(x) for x in error["loc"][1:]),
            message=error["msg"],
            code=error["type"]
        ))

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "errors": [e.model_dump() for e in errors],
            "request_id": request.headers.get("X-Request-ID"),
            "timestamp": datetime.utcnow()
        }
    )
```

---

## API Documentation

### OpenAPI Integration

```python
@router.get("/users/{id}", tags=["users"])
async def get_user(
    id: int = Path(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.

    This endpoint retrieves a specific user's profile information.

    **Path Parameters:**
    - id: Unique user identifier (must be > 0)

    **Responses:**
    - 200: User found
    - 404: User not found
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404)
    return user

# Auto-generated documentation
# GET /docs (Swagger UI)
# GET /redoc (ReDoc)
```

---

## Summary: Production API Checklist

- ✅ Versioned endpoints (/api/v1/...)
- ✅ RESTful naming conventions
- ✅ Correct HTTP status codes (201, 204, 401, 403, 404, 409)
- ✅ Request validation with Pydantic
- ✅ Response schemas for consistent output
- ✅ Pagination with skip/limit
- ✅ Filtering and searching
- ✅ Sorting support
- ✅ Standard error response format
- ✅ OpenAPI documentation
- ✅ Proper authentication headers
- ✅ Request ID tracking
