# FastAPI Middleware & Error Handling

## Middleware Basics

### Adding Middleware

```python
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Define middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(middleware=middleware)

# Or add after creation
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

## Common Middleware

### CORS (Cross-Origin Resource Sharing)

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### Request/Response Logging

```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### Request ID Tracking

```python
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### Gzip Compression

```python
from starlette.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

### Custom Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Before request
        request.state.start_time = time.time()

        response = await call_next(request)

        # After response
        process_time = time.time() - request.state.start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(CustomMiddleware)
```

## Exception Handling

### Global Exception Handler

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )
```

### Custom Exceptions

```python
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
        self.detail = f"Item {item_id} not found"

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": exc.detail, "item_id": exc.item_id}
    )

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in [1, 2, 3]:
        raise ItemNotFoundError(item_id)
    return {"item_id": item_id}
```

### Exception Hierarchy

```python
class APIError(Exception):
    """Base exception for all API errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class ValidationError(APIError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)

class NotFoundError(APIError):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class UnauthorizedError(APIError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ForbiddenError(APIError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)

@app.exception_handler(APIError)
async def api_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )
```

## Error Response Standardization

### Standard Error Format

```python
from pydantic import BaseModel
from enum import Enum

class ErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    SERVER_ERROR = "server_error"

class ErrorDetail(BaseModel):
    type: ErrorType
    message: str
    field: str | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str | None = None
    timestamp: str
```

### Using Standard Response

```python
from datetime import datetime

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    request_id = getattr(request.state, "request_id", None)
    error_response = ErrorResponse(
        error=ErrorDetail(
            type=ErrorType.SERVER_ERROR,
            message="An unexpected error occurred"
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )
```

## Dependency-Based Error Handling

### Conditional Error Handling

```python
from fastapi import Depends, HTTPException

async def check_admin(current_user: str = Depends(verify_token)) -> str:
    if current_user != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.delete("/admin/items/{item_id}")
async def delete_item_admin(
    item_id: int,
    admin: str = Depends(check_admin)
):
    return {"deleted": True}
```

## Best Practices

1. **Use HTTP status codes correctly**: 400 (client), 401/403 (auth), 404 (not found), 500 (server)
2. **Standardize error responses**: Include error type, message, request ID
3. **Don't expose internal errors**: Log internally, return generic messages to client
4. **Validate early**: Use Pydantic for input validation
5. **Use middleware for cross-cutting concerns**: Logging, CORS, compression
6. **Handle database errors gracefully**: Don't return raw SQL errors
7. **Implement retry logic**: For transient failures
8. **Log exceptions with full context**: Stack trace, request details, user info
