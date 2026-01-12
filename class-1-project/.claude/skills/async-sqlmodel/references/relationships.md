# Relationships & Eager Loading - SQLModel Patterns

Master relationship definitions, lazy loading issues, and eager loading strategies with selectinload and joinedload to avoid N+1 query problems.

**Cross-Skill References**: See **pytest-testing skill** `fastapi-sqlmodel-testing.md` for testing relationship eager loading; see **async-sqlmodel skill** `performance.md` for N+1 query detection and optimization.

## Relationship Fundamentals

### One-to-Many (Most Common)

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# ============================================================================
# PARENT (One side)
# ============================================================================

class Team(SQLModel, table=True):
    """Team with multiple players"""
    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Collection of related objects
    players: List["Player"] = Relationship(
        back_populates="team",
        cascade_delete=True,  # Delete players when team deleted
    )

# ============================================================================
# CHILD (Many side)
# ============================================================================

class Player(SQLModel, table=True):
    """Player belongs to one Team"""
    __tablename__ = "players"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Foreign key to Team
    team_id: Optional[int] = Field(
        foreign_key="teams.id",
        ondelete="CASCADE",
    )

    # Back reference to single object
    team: Optional[Team] = Relationship(back_populates="players")
```

### Many-to-Many

```python
from sqlmodel import SQLModel, Field, Relationship

# ============================================================================
# JUNCTION TABLE (Maps many-to-many relationship)
# ============================================================================

class StudentCourseLink(SQLModel, table=True):
    """Maps Students to Courses"""
    __tablename__ = "student_courses"

    student_id: Optional[int] = Field(
        foreign_key="students.id",
        primary_key=True,
    )
    course_id: Optional[int] = Field(
        foreign_key="courses.id",
        primary_key=True,
    )
    # Can add extra data here (grade, enrollment_date, etc.)
    grade: Optional[str] = None

# ============================================================================
# MANY-TO-MANY MODELS
# ============================================================================

class Student(SQLModel, table=True):
    """Student takes many Courses"""
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    courses: List["Course"] = Relationship(
        back_populates="students",
        link_model=StudentCourseLink,
    )

class Course(SQLModel, table=True):
    """Course has many Students"""
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    students: List[Student] = Relationship(
        back_populates="courses",
        link_model=StudentCourseLink,
    )
```

---

## The Lazy Loading Problem

### Understanding Lazy Loading

Lazy loading happens when you access a relationship attribute that hasn't been loaded yet:

```python
# ❌ PROBLEM: Lazy Loading

async def get_teams_with_lazy_loading(session: AsyncSession) -> List[Team]:
    """This causes N+1 query problem"""
    statement = select(Team)
    result = await session.execute(statement)
    teams = result.scalars().all()

    # Problem: Accessing .players here causes additional queries!
    # Query 1: SELECT * FROM teams
    # Query N: SELECT * FROM players WHERE team_id = ?  (for each team)
    # Total: 1 + N queries!

    for team in teams:
        print(f"{team.name}: {len(team.players)} players")
        # ↑ This access triggers lazy loading (implicit query)

    return teams
```

### Why Lazy Loading Fails in Async

```python
# ❌ In async code, lazy loading raises an error:

async def get_team_fails(session: AsyncSession):
    """This will fail!"""
    statement = select(Team)
    result = await session.execute(statement)
    team = result.scalar_one()

    # ❌ This raises an error in async context:
    # "Emit.await_() not being awaited" or similar
    # Lazy loading tries to make a synchronous query in async code

    print(team.players)  # ERROR! Can't lazy load in async
```

### Solution: Eager Load Before Using

Always eager load relationships before accessing them:

```python
# ✅ SOLUTION: Eager Loading

async def get_team_with_eager_loading(
    session: AsyncSession,
    team_id: int,
) -> Optional[Team]:
    """Load team with all players eagerly"""
    # Use joinedload to eager load the relationship
    statement = (
        select(Team)
        .where(Team.id == team_id)
        .options(joinedload(Team.players))
    )
    result = await session.execute(statement)
    team = result.unique().scalar_one_or_none()

    # Now .players is available (loaded in the query)
    if team:
        print(f"{team.name}: {len(team.players)} players")
        # ✅ No lazy loading, already loaded!

    return team
```

---

## Eager Loading Strategies

### selectinload (For Collections/Lists)

Use `selectinload` for loading a collection of related objects:

```python
from sqlalchemy.orm import selectinload

async def get_teams_with_players(session: AsyncSession) -> List[Team]:
    """Load all teams with all their players"""
    # selectinload makes 2 queries:
    # Query 1: SELECT * FROM teams
    # Query 2: SELECT * FROM players WHERE team_id IN (...)
    statement = (
        select(Team)
        .options(selectinload(Team.players))
    )
    result = await session.execute(statement)
    teams = result.scalars().all()

    # Now we can access .players without additional queries
    for team in teams:
        print(f"{team.name}: {[p.name for p in team.players]}")

    return teams
```

**When to use selectinload:**
- Loading a collection (List[...])
- Need all related items
- Expecting multiple parent records

### joinedload (For Single Objects)

Use `joinedload` for loading a single related object (not a collection):

```python
from sqlalchemy.orm import joinedload

async def get_player_with_team(
    session: AsyncSession,
    player_id: int,
) -> Optional[Player]:
    """Load player with their team using JOIN"""
    # joinedload uses a SQL JOIN to load the relationship
    # Query: SELECT players.*, teams.* FROM players
    #        JOIN teams ON players.team_id = teams.id
    #        WHERE players.id = ?
    statement = (
        select(Player)
        .where(Player.id == player_id)
        .options(joinedload(Player.team))
    )
    result = await session.execute(statement)
    player = result.unique().scalar_one_or_none()

    # Now .team is available
    if player:
        print(f"{player.name} plays for {player.team.name}")

    return player
```

**When to use joinedload:**
- Loading a single related object (not List)
- Want a single JOIN query
- Loading just 1-2 parent records

### Comparison: selectinload vs joinedload

```python
# SELECTINLOAD (recommended for lists)
# Query 1: SELECT * FROM teams
# Query 2: SELECT * FROM players WHERE team_id IN (1, 2, 3, ...)
# Result: 2 queries (scales well with many parents)
statement = select(Team).options(selectinload(Team.players))

# JOINEDLOAD (for single objects)
# Query: SELECT teams.*, players.* FROM teams
#        LEFT JOIN players ON ...
#        WHERE teams.id = 1
# Result: 1 query with JOIN (best for single parent)
statement = select(Team).where(Team.id == 1).options(joinedload(Team.players))
```

---

## Multiple Relationships

### Loading Multiple Relationships

```python
async def get_player_full(
    session: AsyncSession,
    player_id: int,
) -> Optional[Player]:
    """Load player with team and stats"""
    statement = (
        select(Player)
        .where(Player.id == player_id)
        .options(
            joinedload(Player.team),           # Single object
            selectinload(Player.match_stats),  # Collection
        )
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()
```

### Nested Relationships

```python
async def get_team_with_full_data(
    session: AsyncSession,
    team_id: int,
) -> Optional[Team]:
    """Load team with players and each player's stats"""
    from sqlalchemy.orm import contains_eager

    statement = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            # selectinload for team.players collection
            selectinload(Team.players).options(
                # selectinload for each player's stats
                selectinload(Player.match_stats)
            )
        )
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()
```

---

## Contains Eager (Advanced)

Use `contains_eager` when filtering by relationship:

```python
from sqlalchemy.orm import contains_eager

async def get_teams_with_scoring_players(
    session: AsyncSession,
) -> List[Team]:
    """Get teams with only players that have scored"""
    statement = (
        select(Team)
        .join(Team.players)
        .where(Player.goals > 0)
        .options(contains_eager(Team.players))
    )
    result = await session.execute(statement)
    teams = result.unique().scalars().all()

    # teams[i].players only contains players with goals > 0
    # (not all players of the team)
    return teams
```

---

## Self-Referential Relationships

### Hierarchy (Parent-Child)

```python
class Employee(SQLModel, table=True):
    """Employee with manager (self-referential)"""
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Foreign key to another employee
    manager_id: Optional[int] = Field(
        foreign_key="employees.id",
        nullable=True,
    )

    # Relationships
    manager: Optional["Employee"] = Relationship(
        back_populates="subordinates",
        sa_relationship_kwargs={"remote_side": "Employee.id"},
    )
    subordinates: List["Employee"] = Relationship(
        back_populates="manager"
    )
```

### Using Self-Referential

```python
async def get_employee_with_manager(
    session: AsyncSession,
    employee_id: int,
) -> Optional[Employee]:
    """Load employee with manager"""
    statement = (
        select(Employee)
        .where(Employee.id == employee_id)
        .options(joinedload(Employee.manager))
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()

async def get_manager_with_team(
    session: AsyncSession,
    manager_id: int,
) -> Optional[Employee]:
    """Load manager with all subordinates"""
    statement = (
        select(Employee)
        .where(Employee.id == manager_id)
        .options(selectinload(Employee.subordinates))
    )
    result = await session.execute(statement)
    return result.unique().scalar_one_or_none()
```

---

## Circular Dependencies & Response Models

### Problem: Infinite Recursion

```python
# ❌ PROBLEM: Circular relationships cause infinite recursion

class Team(SQLModel):
    id: int
    name: str
    players: List["Player"]  # Has players

class Player(SQLModel):
    id: int
    name: str
    team: Optional["Team"]  # Has team

# When serializing:
# Team → players → [Player → team → Team → players → ...]
# Infinite loop!
```

### Solution: Response Models

```python
# ✅ SOLUTION: Use separate response models without circular references

# Database models (can have circular references)
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    players: List["Player"] = Relationship(back_populates="team")

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(foreign_key="teams.id")
    team: Optional[Team] = Relationship(back_populates="players")

# ============================================================================
# RESPONSE MODELS (No circular dependencies)
# ============================================================================

class PlayerPublic(SQLModel):
    """Player without team (prevents recursion)"""
    id: int
    name: str

class TeamPublic(SQLModel):
    """Team without players (prevents recursion)"""
    id: int
    name: str

# Use separate models for relationships:

class PlayerWithTeam(SQLModel):
    """Player with team (team has no players)"""
    id: int
    name: str
    team: Optional[TeamPublic] = None

class TeamWithPlayers(SQLModel):
    """Team with players (players have no team)"""
    id: int
    name: str
    players: List[PlayerPublic] = []
```

### Using Response Models in Endpoints

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/teams/{team_id}", response_model=TeamWithPlayers)
async def get_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get team with all players"""
    team = await get_team_with_eager_loading(session, team_id)
    return team  # Pydantic validates against TeamWithPlayers schema

@router.get("/players/{player_id}", response_model=PlayerWithTeam)
async def get_player(
    player_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get player with team"""
    player = await get_player_with_team(session, player_id)
    return player  # Pydantic validates against PlayerWithTeam schema
```

---

## Relationship Patterns

### Always Use back_populates

```python
# ✅ Good: Bidirectional with back_populates
class Team(SQLModel, table=True):
    players: List["Player"] = Relationship(back_populates="team")

class Player(SQLModel, table=True):
    team: Optional[Team] = Relationship(back_populates="players")

# ❌ Avoid: One-way relationships
class Team(SQLModel, table=True):
    players: List["Player"] = Relationship()  # No back_populates

class Player(SQLModel, table=True):
    # Can't access player.team!
    pass
```

### Always Eager Load Before Accessing

```python
# ❌ DON'T
async def bad_access(session: AsyncSession):
    statement = select(Team)
    result = await session.execute(statement)
    team = result.scalar_one()
    # Access relationship without eager loading - ERROR!
    print(team.players)

# ✅ DO
async def good_access(session: AsyncSession):
    statement = (
        select(Team)
        .options(selectinload(Team.players))
    )
    result = await session.execute(statement)
    team = result.scalar_one()
    # Relationship is eagerly loaded
    print(team.players)
```

---

## Relationship Checklist

Before using relationships in production:

- [ ] All relationships have `back_populates`
- [ ] Foreign keys use correct table references
- [ ] Relationships are eager loaded (selectinload or joinedload)
- [ ] No lazy loading in async code
- [ ] Response models prevent circular references
- [ ] N+1 query problems identified and fixed
- [ ] `contains_eager` used when filtering by relationship
- [ ] Self-referential relationships use correct `sa_relationship_kwargs`
- [ ] Cascade delete options set appropriately
- [ ] Tests verify relationships load correctly

---

## Summary

Relationships in async SQLModel:
1. **Define with Relationship()** using back_populates
2. **Always eager load** with selectinload/joinedload
3. **Never lazy load** in async code (will error)
4. **Use selectinload** for collections/lists
5. **Use joinedload** for single objects
6. **Prevent circular references** in response models
7. **Avoid N+1 queries** with proper eager loading
