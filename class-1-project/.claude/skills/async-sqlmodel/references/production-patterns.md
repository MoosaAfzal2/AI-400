# Production Patterns - Scaling & Reliability

Advanced patterns for production deployments including scaling, monitoring, disaster recovery, and optimization strategies.

## Connection Pool Optimization

### Monitor Pool Health

```python
# src/monitoring.py

from sqlalchemy.pool import QueuePool
import time

class PoolMonitor:
    """Monitor connection pool health"""

    def __init__(self, engine):
        self.engine = engine

    def get_metrics(self) -> dict:
        """Get current pool metrics"""
        pool = self.engine.pool
        if not isinstance(pool, QueuePool):
            return {}

        return {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "queue_size": pool.size() - pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "timestamp": time.time(),
        }

    async def log_metrics(self):
        """Log metrics periodically"""
        metrics = self.get_metrics()
        logger.info(f"Pool metrics: {metrics}")
```

### Dynamic Pool Adjustment

```python
# src/database.py

def get_pool_size(expected_requests_per_sec: int) -> tuple[int, int]:
    """Calculate optimal pool size based on load"""
    # Rule of thumb: pool_size = sqrt(requests_per_sec)
    base_size = int(expected_requests_per_sec ** 0.5)

    # Minimum 5, maximum 30
    pool_size = max(5, min(base_size, 30))
    max_overflow = max(5, pool_size // 2)

    return pool_size, max_overflow

# Use in configuration
expected_rps = int(os.getenv("EXPECTED_REQUESTS_PER_SEC", "100"))
pool_size, max_overflow = get_pool_size(expected_rps)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=pool_size,
    max_overflow=max_overflow,
)
```

---

## Read Replicas

### Primary-Replica Pattern

```python
# src/database.py

# Primary (writes)
primary_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@primary:5432/db",
    pool_size=20,
)

# Replica (reads)
replica_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@replica:5432/db",
    pool_size=30,  # Can handle more read load
    pool_pre_ping=True,
)

async def get_read_session() -> AsyncSession:
    """Get session for read-only operations"""
    async with async_sessionmaker(replica_engine)() as session:
        yield session

async def get_write_session() -> AsyncSession:
    """Get session for write operations"""
    async with async_sessionmaker(primary_engine)() as session:
        yield session
```

### Using Read Replicas

```python
# src/api/users.py

# Use replica for reads (faster, distributed)
@router.get("/users/")
async def list_users(
    session: AsyncSession = Depends(get_read_session),
):
    """Read from replica"""
    pass

# Use primary for writes (consistency)
@router.post("/users/")
async def create_user(
    session: AsyncSession = Depends(get_write_session),
):
    """Write to primary"""
    pass
```

---

## Caching Strategy

### Cache Frequently Accessed Data

```python
# src/cache.py

from redis.asyncio import Redis
import json

class DatabaseCache:
    """Cache layer for database queries"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get_user(self, user_id: int):
        """Get user from cache or database"""
        cache_key = f"user:{user_id}"

        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Fall back to database
        from src.services.user import UserService
        user = await UserService.get_user(session, user_id)

        if user:
            # Cache for 1 hour
            await self.redis.setex(
                cache_key,
                3600,
                json.dumps({"id": user.id, "username": user.username}),
            )

        return user

    async def invalidate_user(self, user_id: int):
        """Invalidate cache when user changes"""
        cache_key = f"user:{user_id}"
        await self.redis.delete(cache_key)
```

### Cache Invalidation on Updates

```python
@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_session),
    cache: DatabaseCache = Depends(get_cache),
):
    """Update user and invalidate cache"""
    user = await UserService.update_user(session, user_id, user_in)

    # Invalidate cache
    await cache.invalidate_user(user_id)

    return user
```

---

## Transactions & ACID

### Serializable Transaction

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event

async def transfer_credits(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    amount: float,
) -> bool:
    """Transfer credits (atomic operation)"""
    try:
        # Start serializable transaction
        await session.begin()

        # Lock both users
        from_user = await session.get(
            User,
            from_user_id,
            with_for_update=True,  # Exclusive lock
        )
        to_user = await session.get(
            User,
            to_user_id,
            with_for_update=True,
        )

        # Verify balance
        if not from_user or from_user.credits < amount:
            await session.rollback()
            return False

        # Update balances
        from_user.credits -= amount
        to_user.credits += amount

        session.add(from_user)
        session.add(to_user)

        await session.commit()
        return True

    except Exception:
        await session.rollback()
        raise
```

---

## Backup & Recovery

### Automated Backups

```python
# src/backup.py

import subprocess
from datetime import datetime

async def backup_database(backup_dir: str) -> str:
    """Create database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.sql"

    # PostgreSQL
    subprocess.run([
        "pg_dump",
        "-h", "localhost",
        "-U", "postgres",
        "myapp",
        "-f", backup_file,
    ])

    return backup_file

async def restore_database(backup_file: str) -> bool:
    """Restore from backup"""
    try:
        subprocess.run([
            "psql",
            "-h", "localhost",
            "-U", "postgres",
            "myapp",
            "-f", backup_file,
        ])
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False
```

---

## Query Optimization

### Identify Slow Queries

```python
# src/monitoring.py

import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time"""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    total_time = time.time() - conn.info['query_start_time'].pop(-1)

    # Log queries taking > 100ms
    if total_time > 0.1:
        logger.warning(
            f"Slow query ({total_time:.3f}s): {statement}",
            extra={"parameters": parameters},
        )
```

### Index Analysis

```sql
-- Find missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## High Availability

### Connection Failover

```python
# src/database.py

from sqlalchemy.engine import URL

def get_database_url_with_failover() -> str:
    """Get database URL with failover hosts"""
    primary = os.getenv("DATABASE_URL")
    failover = os.getenv("DATABASE_FAILOVER_URL", "")

    if failover:
        # SQLAlchemy supports multiple hosts for PostgreSQL
        return f"{primary},{failover}"

    return primary

engine = create_async_engine(
    get_database_url_with_failover(),
    pool_pre_ping=True,  # Detect failed connections
)
```

### Health Check

```python
# src/health.py

async def database_health_check() -> bool:
    """Check if database is healthy"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

@app.get("/health/db")
async def health_db():
    """Health check endpoint"""
    healthy = await database_health_check()
    status = "healthy" if healthy else "unhealthy"
    return {"status": status}
```

---

## Cost Optimization

### Query Pagination for Large Datasets

```python
# ✅ Good: Paginated queries
async def get_all_users_paginated(
    session: AsyncSession,
    batch_size: int = 1000,
):
    """Get all users in batches (memory efficient)"""
    skip = 0
    while True:
        statement = (
            select(User)
            .offset(skip)
            .limit(batch_size)
        )
        result = await session.execute(statement)
        users = result.scalars().all()

        if not users:
            break

        yield from users
        skip += batch_size

# ❌ Bad: Load all at once
async def get_all_users_bad(session):
    statement = select(User)
    result = await session.execute(statement)
    return result.scalars().all()  # Could be millions of rows!
```

### Connection Pooling Reduces Cost

```
Without pooling:
├─ Create connection: 100ms overhead
├─ Execute query: 10ms
├─ Close connection: 50ms
└─ Total per request: 160ms

With pooling (reuse):
├─ Get from pool: 1ms
├─ Execute query: 10ms
├─ Return to pool: 1ms
└─ Total per request: 12ms

Benefit: 13x faster = Lower latency & infrastructure costs
```

---

## Disaster Recovery

### Data Validation

```python
# src/integrity.py

async def validate_database_integrity(session: AsyncSession) -> dict:
    """Validate database integrity"""
    issues = []

    # Check for orphaned records
    orphaned_users = await session.execute(
        select(User).where(User.team_id.notin_(
            select(Team.id)
        ))
    )
    if orphaned_users.scalars().all():
        issues.append("Orphaned user records found")

    # Check for duplicate unique keys
    duplicates = await session.execute(
        select(User.email, func.count())
        .group_by(User.email)
        .having(func.count() > 1)
    )
    if duplicates.scalars().all():
        issues.append("Duplicate email addresses found")

    return {"valid": len(issues) == 0, "issues": issues}
```

---

## Production Deployment Checklist

Before production:

- [ ] Connection pooling configured and tested
- [ ] Read replicas setup if high traffic expected
- [ ] Caching strategy implemented
- [ ] Backups automated and tested
- [ ] Query performance optimized
- [ ] Health checks configured
- [ ] Monitoring and alerting setup
- [ ] Database credentials in environment variables
- [ ] Migrations tested and verified
- [ ] Disaster recovery plan documented
- [ ] Database logs enabled
- [ ] Slow query logging enabled

---

## Summary

Production SQLModel deployment requires:
1. **Connection pooling** properly configured
2. **Read replicas** for scale
3. **Caching** for performance
4. **Backups** automated and tested
5. **Monitoring** and alerting
6. **Health checks** for availability
7. **Query optimization** for cost
8. **Disaster recovery** plan
