# Todo API with Authentication

A production-grade Todo API built with FastAPI, SQLModel, and async Postgres. Features OAuth2 JWT-based authentication, async database operations, and comprehensive error handling.

## Features

- ✅ User registration and login with OAuth2 JWT authentication
- ✅ Full CRUD operations for todo items
- ✅ Data privacy - users only see their own todos
- ✅ Async database operations with Postgres/Neon
- ✅ Token refresh mechanism with automatic expiration
- ✅ Comprehensive error handling with error codes
- ✅ Structured JSON logging
- ✅ 100% test coverage with 78+ tests
- ✅ Docker & Docker Compose support
- ✅ Remote database (Postgres/Neon) support

## Tech Stack

- **Framework**: FastAPI >= 0.104.0
- **ORM**: SQLModel >= 0.0.14 with async SQLAlchemy
- **Database**: PostgreSQL/Neon with asyncpg driver
- **Migrations**: Alembic >= 1.12.0
- **Authentication**: OAuth2 JWT (HS256) with python-jose
- **Password Hashing**: Argon2 password hashing
- **Testing**: pytest + pytest-asyncio (78+ tests, 100% passing)
- **Container**: Docker & Docker Compose
- **Code Quality**: Black, Ruff, mypy, isort

## Project Structure

```
todo-api/
├── src/todo_api/
│   ├── __init__.py           # Application factory
│   ├── main.py               # Uvicorn entry point
│   ├── config.py             # Configuration & environment
│   ├── database.py           # Database setup & session management
│   ├── security.py           # JWT & password hashing utilities
│   ├── exceptions.py         # Custom exception classes
│   ├── error_handler.py      # Standardized error responses
│   ├── middleware.py         # Request/response middleware
│   ├── logging_config.py     # Structured JSON logging
│   ├── dependencies.py       # FastAPI dependencies (auth, session)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py          # Base model with timestamps
│   │   ├── user.py          # User entity with roles
│   │   ├── todo.py          # Todo entity
│   │   └── token.py         # RefreshToken & TokenBlacklist
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth request/response schemas
│   │   ├── todo.py          # Todo schemas
│   │   └── pagination.py    # Pagination parameters
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py  # User operations
│   │   ├── auth_service.py  # Authentication logic
│   │   ├── token_service.py # Token management
│   │   └── todo_service.py  # Todo CRUD operations
│   └── routes/
│       ├── __init__.py      # Route registration
│       ├── auth.py          # OAuth2 authentication endpoints
│       ├── todos.py         # Todo CRUD endpoints
│       └── health.py        # Health check endpoints
├── tests/
│   ├── conftest.py          # Pytest configuration & fixtures
│   ├── test_api_routes.py   # API integration tests (39 tests)
│   ├── test_auth.py         # Authentication & service tests (39 tests)
│   └── test_todos_service.py # Todo service tests
├── migrations/              # Alembic schema migrations
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   └── 002_add_is_admin_to_users.py
│   └── env.py
├── .env.example             # Environment variables template
├── .env.test                # Test environment configuration
├── .gitignore               # Git ignore patterns
├── .dockerignore             # Docker ignore patterns
├── Dockerfile               # Multi-stage Docker image
├── docker-compose.yml       # Local development with Postgres
├── docker-compose.prod.yml  # Production setup
├── pyproject.toml           # Project dependencies & config
└── README.md                # This file
```

## Quick Start

### Option 1: Local Development (with uv)

**Prerequisites:**
- Python 3.13+
- uv package manager
- PostgreSQL 14+ (or use Docker Compose)

**Setup:**

1. Clone repository
   ```bash
   git clone <repository-url>
   cd todo-api
   ```

2. Create environment file
   ```bash
   cp .env.example .env
   ```

3. Install dependencies
   ```bash
   uv sync
   ```

4. Run with local SQLite (for quick testing)
   ```bash
   uv run todo-api
   ```
   API available at `http://localhost:8000`

### Option 2: Docker (Recommended for Development)

**Prerequisites:**
- Docker
- Docker Compose

**Setup with Local Postgres:**

```bash
# Build and start with docker-compose
docker-compose up -d

# Wait for services to start
sleep 5

# Run migrations
docker-compose exec api uv run alembic upgrade head

# View logs
docker-compose logs -f api

# API available at http://localhost:8000
```

Stop services:
```bash
docker-compose down
```

### Option 3: Docker with Remote Neon Postgres

**Prerequisites:**
- Docker
- Neon Postgres account (neon.tech)

**Setup:**

1. Get your Neon connection string
   ```
   postgres://user:password@ep-xxxxx.us-east-1.neon.tech/dbname?sslmode=require
   ```

2. Create `.env` file
   ```bash
   cat > .env << EOF
   DATABASE_URL=postgres://user:password@ep-xxxxx.us-east-1.neon.tech/dbname?sslmode=require
   JWT_SECRET_KEY=your-secret-key-at-least-32-chars
   EOF
   ```

3. Build and run Docker image
   ```bash
   docker build -t todo-api:latest .

   docker run -d \
     --name todo-api \
     -p 8000:8000 \
     --env-file .env \
     todo-api:latest
   ```

4. View logs
   ```bash
   docker logs -f todo-api
   ```

5. API available at `http://localhost:8000`

## Setup Instructions

### Remote Database (Neon Postgres)

**Step 1: Create Neon Account**
- Go to [neon.tech](https://neon.tech)
- Sign up and create a new project
- Copy your connection string

**Step 2: Configure Environment**
```bash
# Edit .env
DATABASE_URL=postgres://user:password@ep-xxxxx.us-east-1.neon.tech/dbname?sslmode=require
JWT_SECRET_KEY=your-secret-key-generate-a-strong-one
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Step 3: Apply Migrations**
```bash
uv run alembic upgrade head
```

**Step 4: Run Server**
```bash
# Using uv
uv run todo-api

# Or with uvicorn
uv run uvicorn src.todo_api.main:app --reload
```

### Local PostgreSQL

**Option A: Install Postgres Locally**
```bash
# macOS
brew install postgresql
brew services start postgresql

# Linux (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

**Option B: PostgreSQL Docker Container**
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=todo_api \
  -p 5432:5432 \
  postgres:15-alpine
```

**Step 2: Configure .env**
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/todo_api
JWT_SECRET_KEY=your-secret-key-at-least-32-chars
```

**Step 3: Apply Migrations and Run**
```bash
uv sync
uv run alembic upgrade head
uv run todo-api
```

### Docker Compose (Recommended for Development)

**Includes:** Postgres 15, PgAdmin for database management

**Setup:**
```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api uv run alembic upgrade head

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

**Access:**
- API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- PgAdmin: `http://localhost:5050` (admin@admin.com / admin)

### Production Deployment (Docker)

**Build multi-stage image:**
```bash
docker build -t todo-api:prod -f Dockerfile.prod .
```

**Run with environment variables:**
```bash
docker run -d \
  --name todo-api-prod \
  -p 8000:8000 \
  -e DATABASE_URL='postgres://user:pass@host/db?sslmode=require' \
  -e JWT_SECRET_KEY='your-production-secret-key' \
  -e ENVIRONMENT='production' \
  todo-api:prod
```

## API Endpoints

### Authentication (OAuth2)

All login requests use OAuth2 `application/x-www-form-urlencoded` format:

- `POST /api/v1/auth/register` - Register new user (JSON)
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"user@example.com","password":"Test@1234"}'
  ```

- `POST /api/v1/auth/login` - OAuth2 login (Form data)
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -d 'username=user@example.com&password=Test@1234'
  ```

- `POST /api/v1/auth/refresh` - Refresh access token
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/refresh \
    -H "Content-Type: application/json" \
    -d '{"refresh_token":"eyJ..."}'
  ```

- `POST /api/v1/auth/logout` - Logout (blacklist token)
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/logout \
    -H "Content-Type: application/json" \
    -d '{"refresh_token":"eyJ..."}'
  ```

- `POST /api/v1/auth/change-password` - Change password
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/change-password \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{"current_password":"Old@1234","new_password":"New@1234"}'
  ```

### Todos

All todo endpoints require `Authorization: Bearer <access_token>` header

- `POST /api/v1/todos` - Create todo
  ```bash
  curl -X POST http://localhost:8000/api/v1/todos \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"title":"My Todo","description":"Details"}'
  ```

- `GET /api/v1/todos` - List todos (paginated)
  ```bash
  curl http://localhost:8000/api/v1/todos?skip=0&limit=20 \
    -H "Authorization: Bearer <token>"
  ```

- `GET /api/v1/todos/{todo_id}` - Get specific todo

- `PUT /api/v1/todos/{todo_id}` - Update todo

- `DELETE /api/v1/todos/{todo_id}` - Delete todo

### Health & Monitoring

- `GET /health` - Health check (no auth required)
- `GET /ready` - Readiness check (database connection)
- `GET /metrics` - Prometheus metrics

## Testing

**Run all tests:**
```bash
uv run pytest tests/ -v
```

**With coverage:**
```bash
uv run pytest tests/ --cov=src/todo_api --cov-report=html
```

**Specific test file:**
```bash
uv run pytest tests/test_api_routes.py -v
```

**Watch mode:**
```bash
uv run pytest-watch tests/ -v
```

**Expected output:**
```
78 passed in 10.21s (100% pass rate)
```

## Code Quality

**Format code:**
```bash
uv run black src/ tests/
```

**Lint with Ruff:**
```bash
uv run ruff check src/ tests/
```

**Type checking:**
```bash
uv run mypy src/
```

**Import sorting:**
```bash
uv run isort src/ tests/
```

**All at once:**
```bash
uv run black src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run isort src/ tests/ && \
uv run mypy src/
```

## Database Migrations

**Create new migration:**
```bash
uv run alembic revision --autogenerate -m "description of changes"
```

**Apply migrations:**
```bash
uv run alembic upgrade head
```

**Rollback one migration:**
```bash
uv run alembic downgrade -1
```

**View migration history:**
```bash
uv run alembic history
```

**Generate SQL without applying:**
```bash
uv run alembic upgrade head --sql
```

## Error Handling

All API endpoints return standardized error responses:

```json
{
  "error_code": "AUTH_001",
  "message": "Invalid email or password",
  "details": null,
  "timestamp": "2026-01-13T10:30:00Z"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| AUTH_001 | 401 | Invalid credentials |
| VALIDATION_001 | 422 | Email format invalid |
| VALIDATION_002 | 422 | Password too weak |
| NOT_FOUND_002 | 404 | Todo not found |
| SERVER_001 | 500 | Internal server error |

## Security Features

- **OAuth2 JWT**: Access (1hr) + Refresh (7 days) tokens
- **Password**: Argon2 hashing (resistant to GPU attacks)
- **User Isolation**: All queries filter by authenticated user_id
- **Token Blacklist**: Logout immediately invalidates tokens
- **CORS**: Configurable cross-origin requests
- **HTTPS**: Required in production
- **Rate Limiting**: Available via middleware

## Troubleshooting

### Database Connection Issues

```bash
# Test Postgres connection
uv run python << 'EOF'
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect('postgres://user:pass@host/db')
    print("Connected!")
    await conn.close()

asyncio.run(test())
EOF

# Check connection string format
# Should be: postgresql://user:password@host:port/dbname
# For Neon: postgres://user:password@ep-xxxx.us-east-1.neon.tech/dbname?sslmode=require
```

### Docker Build Issues

```bash
# Clear Docker cache and rebuild
docker-compose build --no-cache

# Check Docker logs
docker logs <container-id>

# Verify image exists
docker images | grep todo-api
```

### Test Failures

```bash
# Run with verbose output
uv run pytest tests/ -vv -s

# Run specific test
uv run pytest tests/test_api_routes.py::TestAuthenticationRoutes::test_login_success -v

# Reset test database
rm -f test.db  # if using SQLite for tests
```

### JWT Errors

```bash
# Verify JWT secret is set
echo $JWT_SECRET_KEY

# Check token expiration
python -c "from datetime import datetime, timedelta; print((datetime.utcnow() + timedelta(hours=1)).isoformat())"
```

## Performance Tips

1. **Connection Pooling**: Configured for 20 connections by default
2. **Query Optimization**: Use `selectinload()` to prevent N+1 queries
3. **Pagination**: Always paginate large result sets (limit=20 default)
4. **Caching**: Implement Redis for session/token caching (future enhancement)
5. **Async**: All database operations are non-blocking

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test locally: `uv run pytest tests/ -v`
4. Run code quality checks: `uv run black src/ && uv run ruff check src/`
5. Commit with clear messages: `git commit -m "feat: add new feature"`
6. Push: `git push origin feature/new-feature`
7. Create pull request with description

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review API docs at `/docs` (Swagger UI)