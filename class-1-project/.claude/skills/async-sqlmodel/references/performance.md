# Performance Optimization - Query Profiling & Infrastructure

Comprehensive performance optimization strategies covering query profiling, infrastructure tuning, monitoring, and benchmarking patterns for production async SQLModel applications.

**Cross-Skill References**: See **pytest-testing skill** for performance testing patterns and benchmarking; see **fastapi-builder skill** for production deployment and monitoring infrastructure.

---

## Part 1: Query Performance Analysis

### Query Profiling with SQLAlchemy Echo

```python
# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool
import logging

# Enable SQL logging to see all queries
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Create engine with echo enabled (development only)
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/db",
    echo=True,  # ⚠️ ONLY in development - high overhead
    pool_size=20,
)
```

### Query Execution Time Measurement

```python
# src/utils/profiling.py

import time
import asyncio
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

def profile_query(func):
    """Decorator to measure query execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(f"{func.__name__} took {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper

# Usage in services
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @profile_query
    async def get_user_with_posts(self, user_id: int):
        """Get user with all posts - will show query time"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from src.models import User

        statement = select(User).where(User.id == user_id).options(selectinload(User.posts))
        result = await self.session.execute(statement)
        return result.unique().scalar_one_or_none()
```

### N+1 Query Detection

```python
# src/utils/n_plus_one_detector.py

from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)

class N_Plus_OneDetector:
    """Detect N+1 query patterns"""

    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self.query_log = []
        self.current_request_queries = []

    def setup_listener(self, engine: Engine):
        """Setup SQLAlchemy event listener"""
        @event.listens_for(engine, "before_cursor_execute")
        def log_query(conn, cursor, statement, parameters, context, executemany):
            self.current_request_queries.append({
                'statement': statement,
                'params': parameters,
                'timestamp': time.time()
            })

    def check_for_n_plus_one(self):
        """Check if similar queries appear many times"""
        if len(self.current_request_queries) > self.threshold:
            stmt_patterns = {}
            for query in self.current_request_queries:
                # Normalize query (remove specific IDs)
                pattern = query['statement'].split('WHERE')[0]
                stmt_patterns[pattern] = stmt_patterns.get(pattern, 0) + 1

            suspicious = {p: c for p, c in stmt_patterns.items() if c > 2}
            if suspicious:
                logger.warning(f"Potential N+1 queries detected: {suspicious}")

        self.current_request_queries = []

# Usage in middleware
from contextlib import asynccontextmanager
from fastapi import FastAPI

detector = N_Plus_OneDetector(threshold=10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    detector.setup_listener(engine)
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def detect_n_plus_one(request, call_next):
    response = await call_next(request)
    detector.check_for_n_plus_one()
    return response
```

### Slow Query Logging

```python
# src/utils/slow_query_logger.py

import time
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

def log_slow_queries(engine: Engine, threshold_ms: float = 100.0):
    """Log queries slower than threshold"""

    @event.listens_for(engine, "before_cursor_execute")
    def before_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def after_execute(conn, cursor, statement, parameters, context, executemany):
        start = conn.info['query_start_time'].pop(-1)
        elapsed_ms = (time.time() - start) * 1000

        if elapsed_ms > threshold_ms:
            logger.warning(
                f"SLOW QUERY ({elapsed_ms:.1f}ms): {statement[:100]}..."
            )

# Setup in database module
log_slow_queries(engine, threshold_ms=100.0)
```

### Query Analysis with EXPLAIN

```python
# src/utils/query_analysis.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def analyze_query(session: AsyncSession, query_str: str) -> dict:
    """Analyze query execution plan"""
    explain_query = f"EXPLAIN ANALYZE {query_str}"

    result = await session.execute(text(explain_query))
    rows = result.fetchall()

    return {
        'plan': [row[0] for row in rows],
        'analysis': '\n'.join(row[0] for row in rows)
    }

# Usage
async def analyze_user_query(session: AsyncSession):
    """Analyze SELECT performance"""
    query = "SELECT * FROM user WHERE id = 1"
    analysis = await analyze_query(session, query)
    print(analysis['analysis'])
    # Shows query plan, rows examined, time estimate, index usage

# Example output:
# Seq Scan on "user" (cost=0.00..35.00 rows=1)
#   Filter: (id = 1)
# →Better: Add index on id column
```

---

## Part 2: Query Optimization Patterns

### Batch Operations (Reduce Queries)

```python
# ❌ INEFFICIENT: N separate INSERT queries
async def create_many_users_slow(session: AsyncSession, users: list[dict]):
    """Creates N database roundtrips"""
    for user_data in users:
        user = User(**user_data)
        session.add(user)
        await session.commit()  # Each iteration commits separately

# ✅ EFFICIENT: Batch INSERT
async def create_many_users_fast(session: AsyncSession, users: list[dict]):
    """Single batch insert"""
    user_objects = [User(**data) for data in users]
    session.add_all(user_objects)
    await session.commit()  # One roundtrip for all

# ✅ ULTRA-EFFICIENT: Bulk insert (SQLAlchemy Core)
from sqlalchemy import insert

async def create_many_users_ultra_fast(session: AsyncSession, users: list[dict]):
    """Fastest bulk insert using Core"""
    stmt = insert(User).values(users)
    await session.execute(stmt)
    await session.commit()
    # Example: 10,000 records in ~500ms vs minutes with individual inserts

# ✅ EFFICIENT: Batch UPDATE
async def update_user_statuses(session: AsyncSession, user_statuses: dict):
    """Update multiple users in one query"""
    from sqlalchemy import update

    for user_id, status in user_statuses.items():
        stmt = update(User).where(User.id == user_id).values(status=status)
        await session.execute(stmt)
    await session.commit()

# ✅ ULTRA-EFFICIENT: Bulk update
from sqlalchemy.dialects.postgresql import update as pg_update

async def update_user_statuses_bulk(session: AsyncSession, updates: list[tuple]):
    """Bulk update: list of (id, status) tuples"""
    for user_id, status in updates:
        stmt = update(User).where(User.id == user_id).values(status=status)
        await session.execute(stmt)
    await session.commit()
```

### Proper Eager Loading Strategies

```python
# ❌ WORST: Lazy loading (causes N+1)
async def get_team_with_players_lazy(session: AsyncSession, team_id: int):
    """Causes multiple queries"""
    team = await session.get(Team, team_id)
    # Every time we access team.players, it triggers a query
    print(len(team.players))  # Query 1: SELECT * FROM player WHERE team_id=?

# ⚠️ BETTER: Single selectinload (two queries total)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_team_with_players_better(session: AsyncSession, team_id: int):
    """Two total queries: 1 for team, 1 for all players"""
    stmt = select(Team).where(Team.id == team_id).options(selectinload(Team.players))
    result = await session.execute(stmt)
    team = result.unique().scalar_one()
    print(len(team.players))  # No new query (already loaded)

# ✅ BEST: joinedload (single query, LEFT JOIN)
from sqlalchemy.orm import joinedload

async def get_team_with_players_best(session: AsyncSession, team_id: int):
    """Single query with LEFT JOIN"""
    stmt = select(Team).where(Team.id == team_id).options(joinedload(Team.players))
    result = await session.execute(stmt)
    team = result.unique().scalar_one()
    print(len(team.players))  # No new query (already joined)

# ✅ BEST: Multiple relationships
async def get_team_full(session: AsyncSession, team_id: int):
    """Load team with players and coaches in single query"""
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            joinedload(Team.players),
            joinedload(Team.coach)
        )
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one()
```

### Pagination (Limit Data Transfer)

```python
# ❌ INEFFICIENT: Load everything
async def get_all_users_bad(session: AsyncSession):
    """Loads entire table into memory"""
    stmt = select(User)
    result = await session.execute(stmt)
    return result.scalars().all()  # If table has 1M rows, loads all

# ✅ EFFICIENT: Paginate
async def get_users_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 10
) -> dict:
    """Load one page at a time"""
    skip = (page - 1) * page_size

    # Get total count
    count_stmt = select(func.count()).select_from(User)
    count = await session.scalar(count_stmt)

    # Get paginated results
    stmt = select(User).offset(skip).limit(page_size)
    result = await session.execute(stmt)
    users = result.scalars().all()

    return {
        'items': users,
        'total': count,
        'page': page,
        'page_size': page_size,
        'pages': (count + page_size - 1) // page_size
    }

# Usage in endpoint
@app.get("/users/")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    return await get_users_paginated(session, page, page_size)
```

### Filtering with Index Usage

```python
# Database setup with indexes
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)  # Index on email
    status: str = Field(index=True)  # Index on status
    created_at: datetime = Field(index=True)  # Index on creation

# ✅ USE INDEXED FIELDS
async def find_user_by_email(session: AsyncSession, email: str):
    """Uses email index"""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# ✅ COMPOUND INDEX
class User(SQLModel, table=True):
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
    )
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    status: str
    created_at: datetime

# This query uses compound index
async def get_recent_active_users(session: AsyncSession, days: int = 7):
    """Uses idx_status_created index"""
    since = datetime.now() - timedelta(days=days)
    stmt = select(User).where(
        (User.status == 'active') &
        (User.created_at >= since)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
```

---

## Part 3: Infrastructure Optimization

### Connection Pool Tuning

```python
# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine
import os

def get_pool_config(environment: str, concurrent_requests: int) -> dict:
    """Calculate optimal pool configuration"""

    if environment == "development":
        return {
            'pool_size': 5,
            'max_overflow': 5,
            'pool_pre_ping': True,  # Test connections
            'pool_recycle': 3600,   # Recycle every hour
        }

    elif environment == "staging":
        return {
            'pool_size': 10,
            'max_overflow': 10,
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }

    elif environment == "production":
        # Formula: pool_size = sqrt(concurrent_requests)
        base_pool = int(concurrent_requests ** 0.5)
        pool_size = max(20, min(base_pool, 50))  # Between 20-50
        max_overflow = pool_size // 2

        return {
            'pool_size': pool_size,
            'max_overflow': max_overflow,
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'echo_pool': False,
        }

# Usage
config = get_pool_config(
    environment=os.getenv("ENVIRONMENT", "development"),
    concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "100"))
)

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/db",
    **config
)

# Example production scenarios:
# 100 requests/sec → pool_size=20, max_overflow=10
# 400 requests/sec → pool_size=30, max_overflow=15
# 900 requests/sec → pool_size=40, max_overflow=20
```

### Monitoring Pool Health

```python
# src/monitoring/pool_monitor.py

from sqlalchemy.pool import QueuePool
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class PoolHealthMonitor:
    """Monitor and log connection pool metrics"""

    def __init__(self, engine, check_interval: int = 60):
        self.engine = engine
        self.check_interval = check_interval
        self.metrics_history = []

    async def monitor(self):
        """Continuously monitor pool health"""
        while True:
            try:
                metrics = self.get_metrics()
                self.metrics_history.append(metrics)

                # Keep only last 1440 entries (24 hours at 1-min intervals)
                if len(self.metrics_history) > 1440:
                    self.metrics_history.pop(0)

                self._log_warnings(metrics)
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Pool monitoring error: {e}")
                await asyncio.sleep(self.check_interval)

    def get_metrics(self) -> dict:
        """Get current pool metrics"""
        pool = self.engine.pool
        if not isinstance(pool, QueuePool):
            return {}

        size = pool.size()
        checked_out = pool.checkedout()
        queue_size = size - checked_out
        overflow = pool.overflow()

        return {
            'timestamp': datetime.now().isoformat(),
            'pool_size': size,
            'checked_out': checked_out,
            'available': queue_size,
            'overflow': overflow,
            'utilization_pct': (checked_out / size * 100) if size > 0 else 0,
            'total_connections': size + overflow,
        }

    def _log_warnings(self, metrics: dict):
        """Log warnings for unhealthy pool state"""
        utilization = metrics['utilization_pct']
        overflow = metrics['overflow']

        if utilization > 90:
            logger.warning(
                f"Pool utilization high: {utilization:.1f}% "
                f"({metrics['checked_out']}/{metrics['pool_size']})"
            )

        if overflow > metrics['pool_size'] // 2:
            logger.warning(
                f"Excessive overflow connections: {overflow} "
                f"(pool_size={metrics['pool_size']})"
            )

    def get_stats(self) -> dict:
        """Get average metrics over history"""
        if not self.metrics_history:
            return {}

        avg_utilization = sum(m['utilization_pct'] for m in self.metrics_history) / len(self.metrics_history)
        max_overflow = max(m['overflow'] for m in self.metrics_history)

        return {
            'avg_utilization_pct': avg_utilization,
            'max_overflow': max_overflow,
            'samples': len(self.metrics_history),
        }

# Usage in FastAPI app
from contextlib import asynccontextmanager

monitor = PoolHealthMonitor(engine, check_interval=60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(monitor.monitor())
    yield
    # Shutdown
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/admin/pool-stats")
async def get_pool_stats():
    """Check pool health (admin endpoint)"""
    return {
        'current': monitor.get_metrics(),
        'stats': monitor.get_stats()
    }
```

### Query Result Caching

```python
# src/cache/query_cache.py

from typing import Any, Callable, TypeVar
import hashlib
import json
import asyncio
from datetime import datetime, timedelta

T = TypeVar('T')

class QueryCache:
    """Simple in-memory query result cache"""

    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.default_ttl = default_ttl

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Create cache key from function and args"""
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def set(self, key: str, value: Any, ttl: int | None = None):
        """Cache value with TTL"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=ttl)
        }

    def get(self, key: str) -> Any | None:
        """Get cached value if not expired"""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if datetime.now() > entry['expires']:
            del self.cache[key]
            return None

        return entry['value']

    def clear(self):
        """Clear entire cache"""
        self.cache.clear()

# Usage with query caching
query_cache = QueryCache(default_ttl=600)  # 10 minutes

async def get_active_teams(session: AsyncSession):
    """Get active teams with caching"""
    cache_key = query_cache._make_key('get_active_teams', (), {})

    # Try cache first
    cached = query_cache.get(cache_key)
    if cached is not None:
        return cached

    # Execute query
    stmt = select(Team).where(Team.is_active == True)
    result = await session.execute(stmt)
    teams = result.scalars().all()

    # Cache result
    query_cache.set(cache_key, teams, ttl=600)
    return teams

# ✅ WITH REDIS (production-grade)
import redis.asyncio as redis

class RedisQueryCache:
    """Redis-backed query cache (distributed)"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = None
        self.redis_url = redis_url

    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url(self.redis_url)

    async def get(self, key: str) -> Any | None:
        """Get from Redis"""
        if not self.redis:
            return None
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = 600):
        """Set in Redis with TTL"""
        if not self.redis:
            return
        await self.redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str):
        """Delete from Redis"""
        if not self.redis:
            return
        await self.redis.delete(key)

# Usage in lifespan
redis_cache = RedisQueryCache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_cache.connect()
    yield
    if redis_cache.redis:
        await redis_cache.redis.close()

app = FastAPI(lifespan=lifespan)
```

### Read-Write Separation

```python
# src/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Primary database (writes)
write_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@primary-db:5432/myapp",
    pool_size=20,
    echo=False,
)

# Read replica (reads)
read_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@replica-db:5432/myapp",
    pool_size=30,  # More capacity for reads
    pool_pre_ping=True,
)

write_session_maker = async_sessionmaker(
    write_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

read_session_maker = async_sessionmaker(
    read_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_write_session() -> AsyncSession:
    """Dependency for write operations"""
    async with write_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_read_session() -> AsyncSession:
    """Dependency for read operations"""
    async with read_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Usage in endpoints
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_read_session)  # Read replica
):
    """Use read replica for queries"""
    user = await session.get(User, user_id)
    return user

@app.post("/users/")
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_write_session)  # Primary
):
    """Use primary for writes"""
    user = User(**user_data.dict())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

---

## Part 4: Benchmarking & Metrics

### Benchmarking Query Performance

```python
# scripts/benchmark_queries.py

import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from src.models import Team, Player

async def benchmark_eager_loading_strategies():
    """Compare selectinload vs joinedload performance"""

    engine = create_async_engine("postgresql+asyncpg://...")
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

    iterations = 100
    team_id = 1

    # Benchmark 1: selectinload (collection)
    start = time.perf_counter()
    for _ in range(iterations):
        async with async_session_maker() as session:
            stmt = select(Team).where(Team.id == team_id).options(
                selectinload(Team.players)
            )
            result = await session.execute(stmt)
            team = result.unique().scalar_one()
            _ = len(team.players)
    selectinload_time = time.perf_counter() - start

    # Benchmark 2: joinedload (collection)
    start = time.perf_counter()
    for _ in range(iterations):
        async with async_session_maker() as session:
            stmt = select(Team).where(Team.id == team_id).options(
                joinedload(Team.players)
            )
            result = await session.execute(stmt)
            team = result.unique().scalar_one()
            _ = len(team.players)
    joinedload_time = time.perf_counter() - start

    print(f"Iterations: {iterations}")
    print(f"selectinload: {selectinload_time:.3f}s ({selectinload_time/iterations*1000:.1f}ms each)")
    print(f"joinedload:   {joinedload_time:.3f}s ({joinedload_time/iterations*1000:.1f}ms each)")
    print(f"Winner: {'selectinload' if selectinload_time < joinedload_time else 'joinedload'}")
```

### Metrics Collection

```python
# src/metrics/query_metrics.py

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json

@dataclass
class QueryMetrics:
    """Record query performance metrics"""
    operation: str  # 'select', 'insert', 'update', 'delete'
    table: str
    duration_ms: float
    rows_affected: int
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_json(self) -> str:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data)

class MetricsCollector:
    """Collect and aggregate query metrics"""

    def __init__(self):
        self.metrics = []

    def record(self, metric: QueryMetrics):
        """Record a query metric"""
        self.metrics.append(metric)

    def get_summary(self) -> dict:
        """Get aggregated metrics"""
        if not self.metrics:
            return {}

        operations = {}
        for metric in self.metrics:
            key = f"{metric.operation}_{metric.table}"
            if key not in operations:
                operations[key] = {
                    'count': 0,
                    'total_ms': 0.0,
                    'avg_ms': 0.0,
                    'max_ms': 0.0,
                    'rows_total': 0
                }

            op = operations[key]
            op['count'] += 1
            op['total_ms'] += metric.duration_ms
            op['max_ms'] = max(op['max_ms'], metric.duration_ms)
            op['rows_total'] += metric.rows_affected

        # Calculate averages
        for op in operations.values():
            op['avg_ms'] = op['total_ms'] / op['count']

        return operations

# Usage
metrics_collector = MetricsCollector()

# In service layer
async def create_user(session: AsyncSession, user_data: dict):
    """Record metrics for user creation"""
    start = time.perf_counter()
    user = User(**user_data)
    session.add(user)
    await session.commit()
    elapsed = (time.perf_counter() - start) * 1000

    metrics_collector.record(QueryMetrics(
        operation='insert',
        table='user',
        duration_ms=elapsed,
        rows_affected=1
    ))
    return user

# Periodic reporting
@app.get("/admin/metrics/queries")
async def get_query_metrics():
    """Get aggregated query metrics"""
    return metrics_collector.get_summary()
```

---

## Performance Optimization Checklist

### Query Optimization
- [ ] Use eager loading (selectinload/joinedload) for relationships
- [ ] Add indexes on frequently filtered columns
- [ ] Use compound indexes for multi-column WHERE clauses
- [ ] Implement pagination for large result sets
- [ ] Use batch operations for inserts/updates (add_all, bulk_insert)
- [ ] Profile slow queries with EXPLAIN ANALYZE
- [ ] Monitor N+1 query patterns
- [ ] Cache frequently accessed data (Redis or in-memory)

### Connection Pool
- [ ] Calculate pool_size based on concurrent requests (√n formula)
- [ ] Set appropriate max_overflow (typically pool_size // 2)
- [ ] Enable pool_pre_ping for stale connection detection
- [ ] Configure pool_recycle to recycle old connections (3600s)
- [ ] Monitor pool utilization metrics (target 60-80%)
- [ ] Alert when utilization exceeds 90%
- [ ] Adjust pool settings based on production metrics

### Infrastructure
- [ ] Implement connection pooling (QueuePool for production)
- [ ] Use read replicas for read-heavy workloads
- [ ] Monitor slow queries (>100ms threshold)
- [ ] Set up query result caching (Redis for production)
- [ ] Track query execution time in metrics
- [ ] Use proper indexes (covering indexes if applicable)
- [ ] Regular database maintenance (ANALYZE, VACUUM)

### Monitoring & Observability
- [ ] Log all slow queries with full stack trace
- [ ] Monitor pool health (checked_out, available, overflow)
- [ ] Track query metrics (count, duration, rows affected)
- [ ] Set up alerting for anomalies (sudden latency increase)
- [ ] Regular performance benchmarking (before/after optimizations)
- [ ] Track connection retry rates
- [ ] Monitor database CPU and memory usage

---

## Summary

Production async SQLModel performance optimization requires:
1. **Query Analysis**: Profile with slow query logs and EXPLAIN ANALYZE
2. **Eager Loading**: Always use selectinload/joinedload for relationships
3. **Batch Operations**: Use bulk insert/update instead of individual operations
4. **Connection Pooling**: Tune pool_size, max_overflow based on load
5. **Caching**: Implement Redis caching for frequently accessed data
6. **Monitoring**: Continuous metrics collection and alerting
7. **Infrastructure**: Read replicas for scaling read-heavy workloads
8. **Regular Analysis**: Benchmark queries, analyze execution plans, adjust as needed
