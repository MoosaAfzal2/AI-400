# Todo API with Authentication

A production-grade Todo API built with FastAPI, SQLModel, and Neon Postgres. Features JWT-based authentication, async database operations, and comprehensive error handling.

## Features

- ✅ User registration and login with JWT authentication
- ✅ Full CRUD operations for todo items
- ✅ Data privacy - users only see their own todos
- ✅ Async database operations with Neon Postgres
- ✅ Token refresh mechanism with automatic expiration
- ✅ Comprehensive error handling with error codes
- ✅ Structured JSON logging
- ✅ 85%+ test coverage with pytest

## Tech Stack

- **Framework**: FastAPI >= 0.104.0
- **ORM**: SQLModel >= 0.0.14 with async SQLAlchemy
- **Database**: Neon Postgres with asyncpg driver
- **Migrations**: Alembic >= 1.12.0
- **Authentication**: JWT (HS256) with python-jose
- **Password Hashing**: Bcrypt with cost factor 10
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: Black, Ruff, mypy, isort

## Project Structure

```
todo-api/
├── src/todo_api/
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration & environment
│   ├── database.py           # Database setup & session management
│   ├── security.py           # JWT & password hashing utilities
│   ├── exceptions.py         # Custom exception classes
│   ├── middleware.py         # Request/response middleware
│   ├── logging_config.py     # Structured JSON logging
│   ├── dependencies.py       # FastAPI dependencies (auth, session)
│   ├── models/
│   │   ├── base.py          # Base model with timestamps
│   │   ├── user.py          # User entity
│   │   ├── todo.py          # Todo entity
│   │   └── token.py         # RefreshToken & TokenBlacklist
│   ├── schemas/
│   │   ├── auth.py          # Authentication request/response schemas
│   │   ├── todo.py          # Todo request/response schemas
│   │   └── pagination.py    # Pagination parameters
│   ├── services/
│   │   ├── user_service.py  # User operations
│   │   ├── auth_service.py  # Authentication logic
│   │   ├── token_service.py # Token management
│   │   └── todo_service.py  # Todo CRUD operations
│   └── routes/
│       ├── __init__.py      # Route registration
│       ├── auth.py          # Authentication endpoints
│       └── todos.py         # Todo CRUD endpoints
├── tests/
│   ├── conftest.py          # Pytest configuration & fixtures
│   ├── test_auth.py         # Authentication tests
│   └── test_todos.py        # Todo CRUD tests
├── migrations/              # Alembic migrations
│   └── versions/
│       └── 001_initial_schema.py
├── docs/
├── .env.example             # Environment variables template
├── .env.test                # Test environment configuration
├── .gitignore               # Git ignore patterns
├── pyproject.toml           # Project dependencies & config
└── README.md                # This file
```

## Setup Instructions

### Prerequisites

- Python 3.12+
- uv (Python package manager)
- Neon Postgres account

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd todo-api
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   Then update `.env` with your Neon Postgres connection string and JWT secret key.

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Apply migrations**
   ```bash
   uv run alembic upgrade head
   ```

5. **Run the server**
   ```bash
   uv run uvicorn todo_api:create_app --reload
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (blacklist token)
- `POST /api/v1/auth/change-password` - Change password

### Todos

- `POST /api/v1/todos` - Create todo
- `GET /api/v1/todos` - List user's todos (paginated)
- `GET /api/v1/todos/{todo_id}` - Get specific todo
- `PUT /api/v1/todos/{todo_id}` - Update todo
- `DELETE /api/v1/todos/{todo_id}` - Delete todo

### Health & Monitoring

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Testing

Run all tests with coverage:
```bash
uv run pytest --cov=src/todo_api tests/
```

Run specific test file:
```bash
uv run pytest tests/test_auth.py -v
```

Run with asyncio debug:
```bash
uv run pytest tests/ -v --asyncio-mode=auto
```

## Code Quality

Format code with Black:
```bash
uv run black src/ tests/
```

Lint with Ruff:
```bash
uv run ruff check src/ tests/
```

Type check with mypy:
```bash
uv run mypy src/
```

Sort imports with isort:
```bash
uv run isort src/ tests/
```

## Database Migrations

Create a new migration:
```bash
uv run alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

Rollback one migration:
```bash
uv run alembic downgrade -1
```

## Error Handling

All API endpoints return standardized error responses with error codes:

```json
{
  "error_code": "AUTH_001",
  "message": "Invalid email or password",
  "details": null,
  "timestamp": "2026-01-12T10:30:00Z"
}
```

## Security Features

- **JWT Tokens**: Access tokens expire in 1 hour, refresh tokens in 7 days
- **Password Hashing**: Bcrypt with cost factor 10 (~100ms per operation)
- **User Isolation**: All queries enforce user_id filter at service layer
- **Token Blacklist**: Logout invalidates tokens immediately
- **HTTPS**: Required in production (enforced via middleware)

## Troubleshooting

### Database Connection Issues
- Verify Neon Postgres connection string in `.env`
- Check that asyncpg driver is installed: `uv run python -c "import asyncpg; print('OK')"`
- Test connection: `uv run python -c "from src.todo_api.database import engine; print('Connected')"`

### JWT Errors
- Ensure JWT_SECRET_KEY is at least 32 characters
- Check token expiration with: `python -c "from datetime import datetime, timedelta; print((datetime.utcnow() + timedelta(hours=1)).isoformat())"`

### Test Failures
- Ensure .env.test is properly configured
- Delete and recreate test database if migrations fail
- Run with `--asyncio-mode=auto` for async test compatibility

## Contributing

1. Create a feature branch: `git checkout -b feature/new-feature`
2. Make changes and test locally
3. Run code quality checks
4. Commit with clear messages
5. Push and create pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions, please open an issue on GitHub.