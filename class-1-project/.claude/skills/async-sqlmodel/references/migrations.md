# Database Migrations - Alembic with Async Support

Setup and manage database migrations using Alembic with async SQLAlchemy support. This guide covers initialization, autogeneration, and applying migrations.

## Alembic Setup

### Initialize Alembic in Project

```bash
# Install Alembic
pip install alembic

# Initialize Alembic repo in project
alembic init alembic

# Output:
# Creating directory /path/to/alembic ...
# Creating script alembic/env.py ...
# Creating template alembic/versions/ ...
# Done.
```

### Project Structure After Init

```
project/
├── alembic/
│   ├── env.py                 # Alembic environment configuration
│   ├── script.py.mako         # Migration template
│   ├── versions/              # Migration files go here
│   │   └── (empty initially)
│   └── alembic.ini            # Alembic configuration
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py            # SQLModel.metadata
│   ├── database.py
│   └── main.py
└── pyproject.toml
```

---

## Configure for Async

### env.py Configuration

```python
# alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool
from alembic import context
from src.models import SQLModel  # Import your models

# ============================================================================
# CONFIGURATION
# ============================================================================

config = context.config
fileConfig(config.config_file_name)

# Import all models here for autogenerate to detect them
# Import models BEFORE calling configure_mappers()
from src.models.user import User
from src.models.team import Team
from src.models.product import Product

# Target metadata for autogenerate
target_metadata = SQLModel.metadata

# ============================================================================
# RUN MIGRATIONS ASYNC
# ============================================================================

def run_migrations_online() -> None:
    """Run migrations with async engine"""

    # Get configuration
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = context.get_x_argument(default="")

    def process_revision_directives(context, revision, directives):
        """Process auto-generated migration directives"""
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []

    # Create async engine
    connectable = create_async_engine(
        configuration.get("sqlalchemy.url"),
        echo=False,
        future=True,
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            render_as_batch=True,  # For SQLite support
        )

        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline() -> None:
    """Run migrations offline (for CI/CD)"""
    url = context.get_x_argument(default="")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### alembic.ini Configuration

```ini
# alembic.ini

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names
file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# string value is passed to zoneinfo.ZoneInfo()
timezone =

[loggers]
keys = root,sqlalchemy.engine

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy.engine]
level = WARN
handlers =
qualname = sqlalchemy.engine

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

## Creating Migrations

### Auto-Generate Migration

```bash
# Create migration automatically from model changes
alembic revision --autogenerate -m "Add user model"

# Output:
# Generating /path/to/alembic/versions/abc123_add_user_model.py ...
# Done.
```

### Generated Migration File

```python
# alembic/versions/abc123_add_user_model.py

from alembic import op
import sqlalchemy as sa
from sqlmodel import SQLModel

def upgrade() -> None:
    """Apply this migration (forward)"""
    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )

    # Create indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'])
    op.create_index(op.f('ix_users_username'), 'users', ['username'])

def downgrade() -> None:
    """Revert this migration (backward)"""
    # Drop indexes
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')

    # Drop tables
    op.drop_table('users')
```

### Manual Migration (if autogenerate not enough)

```bash
# Create empty migration for manual edits
alembic revision -m "Add user email verification"

# Output:
# Generating /path/to/alembic/versions/def456_add_user_email_verification.py ...
# Done.
```

```python
# alembic/versions/def456_add_user_email_verification.py

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    """Add email verification column"""
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'users',
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
    )

def downgrade() -> None:
    """Remove email verification column"""
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
```

---

## Applying Migrations

### Apply Latest Migrations

```bash
# Apply all pending migrations to latest version
alembic upgrade head

# Output:
# INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO [alembic.runtime.migration] Will assume transactional DDL.
# INFO [alembic.runtime.migration] Running upgrade -> abc123, Add user model
# INFO [alembic.runtime.migration] Running upgrade abc123 -> def456, Add email verification
```

### Apply Specific Migration

```bash
# Apply migrations up to specific version
alembic upgrade abc123

# Roll back to specific version
alembic downgrade def456
```

### Check Current Version

```bash
# Show current revision
alembic current

# Output:
# def456 (head)
```

### View Migration History

```bash
# Show all revisions
alembic history

# Output:
# <base> -> abc123 (head), Add user model
# abc123 -> def456, Add email verification
```

---

## Common Migration Patterns

### Adding a Column

```python
def upgrade() -> None:
    """Add bio column to users"""
    op.add_column(
        'users',
        sa.Column('bio', sa.String(500), nullable=True),
    )

def downgrade() -> None:
    """Remove bio column"""
    op.drop_column('users', 'bio')
```

### Adding a Column with Default

```python
def upgrade() -> None:
    """Add is_admin column with default"""
    op.add_column(
        'users',
        sa.Column(
            'is_admin',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

def downgrade() -> None:
    op.drop_column('users', 'is_admin')
```

### Adding a Constraint

```python
def upgrade() -> None:
    """Add unique constraint to email"""
    op.create_unique_constraint(
        'uq_users_email',
        'users',
        ['email'],
    )

def downgrade() -> None:
    """Remove unique constraint"""
    op.drop_constraint('uq_users_email', 'users')
```

### Adding a Foreign Key

```python
def upgrade() -> None:
    """Add team_id foreign key"""
    op.add_column(
        'users',
        sa.Column('team_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_users_team_id',
        'users',
        'teams',
        ['team_id'],
        ['id'],
        ondelete='CASCADE',
    )

def downgrade() -> None:
    """Remove foreign key"""
    op.drop_constraint('fk_users_team_id', 'users')
    op.drop_column('users', 'team_id')
```

### Creating a Table with Foreign Key

```python
def upgrade() -> None:
    """Create posts table with user_id foreign key"""
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_posts_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )

def downgrade() -> None:
    """Drop posts table"""
    op.drop_table('posts')
```

---

## CI/CD Integration

### GitHub Actions Migration

```yaml
# .github/workflows/migrations.yml

name: Database Migrations

on:
  push:
    branches: [main, develop]

jobs:
  migrate:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run migrations
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/testdb
        run: |
          alembic upgrade head

      - name: Verify schema
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/testdb
        run: |
          alembic current
```

---

## Migration Best Practices

### ✅ Do

- **Auto-generate migrations** for schema changes
- **Review auto-generated migrations** before applying
- **Version control migrations** (git commit)
- **Test migrations** in staging before production
- **Keep migrations isolated** (one change per migration)
- **Add descriptive messages** to migration names

### ❌ Don't

- **Manually edit table definitions** - use migrations
- **Skip migrations** in production
- **Modify old migrations** - create new ones instead
- **Rename columns** with complex logic - use multiple migrations
- **Deploy code before migrations** - run migrations first

---

## Migration Testing

### Test Migration Upgrade

```bash
# Create test database
export DATABASE_URL="sqlite+aiosqlite:///./test_migrations.db"

# Apply all migrations
alembic upgrade head

# Verify schema (check with SQLite CLI)
sqlite3 test_migrations.db ".schema"
```

### Test Migration Rollback

```bash
# Go to previous version
alembic downgrade -1

# Go back to latest
alembic upgrade head
```

---

## Troubleshooting Migrations

### Autogenerate Detects No Changes

**Problem**: `alembic revision --autogenerate` creates empty migration

**Solution**: Ensure models are imported in `env.py`:

```python
# alembic/env.py
from src.models.user import User
from src.models.team import Team
# All models must be imported
```

### Migration Fails on Apply

**Problem**: `alembic upgrade head` fails with error

**Solution**:
1. Check database connection
2. Review migration file for errors
3. Try rolling back first: `alembic downgrade -1`
4. Manually fix database if needed

### Revision Conflicts

**Problem**: Multiple migrations with same parent

**Solution**: Merge conflicts in migration files:

```python
# In dependent migration, update the `down_revision`
down_revision = "abc123"  # Previous migration
revision = "xyz789"

# Recreate the migration file if needed
```

---

## Migration Checklist

Before deploying migrations:

- [ ] Migrations generated or written
- [ ] Auto-generated migrations reviewed manually
- [ ] Migrations tested in staging database
- [ ] No data loss in downgrade path (if applicable)
- [ ] All models imported in `alembic/env.py`
- [ ] Migration applied successfully with `alembic upgrade head`
- [ ] Database schema matches models
- [ ] Rollback tested with `alembic downgrade -1`
- [ ] Migrations committed to version control
- [ ] CI/CD pipeline verifies migrations run

---

## Summary

Alembic migrations for async SQLModel:
1. **Initialize** with `alembic init`
2. **Configure** `env.py` for async engine
3. **Import models** in `env.py` for autogenerate
4. **Create migrations** with `alembic revision --autogenerate`
5. **Review** generated files before applying
6. **Apply** with `alembic upgrade head`
7. **Version control** all migration files
8. **Test** upgrades and downgrades
