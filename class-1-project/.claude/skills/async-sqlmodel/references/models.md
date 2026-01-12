# SQLModel Definition - Models and Fields

Define SQLModel classes with proper types, constraints, relationships, and validation. This guide covers basic models, field types, relationships, and response models.

## Basic SQLModel

### Simple Model

```python
# src/models.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# ============================================================================
# BASIC MODEL
# ============================================================================

class User(SQLModel, table=True):
    """User model with database table"""
    __tablename__ = "users"

    # Primary key (auto-increment)
    id: Optional[int] = Field(default=None, primary_key=True)

    # Required fields
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(index=True, unique=True)

    # Optional fields
    full_name: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Boolean flags
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
```

### Field Types

```python
from sqlmodel import Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

class Product(SQLModel, table=True):
    """Product with various field types"""
    __tablename__ = "products"

    # Integer types
    id: Optional[int] = Field(default=None, primary_key=True)
    quantity: int = Field(ge=0)  # >= 0 (Pydantic validation)

    # String types
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    sku: str = Field(unique=True, index=True)

    # Decimal (for money)
    price: Decimal = Field(decimal_places=2, max_digits=10)

    # Float
    rating: float = Field(ge=0.0, le=5.0)

    # Boolean
    is_available: bool = Field(default=True)

    # DateTime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    release_date: Optional[date] = Field(default=None)

    # Text (large strings)
    details: Optional[str] = Field(default=None, sa_column_kwargs={"type": "TEXT"})
```

---

## Foreign Keys & Basic Relationships

### One-to-Many Relationship

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# ============================================================================
# PARENT MODEL
# ============================================================================

class Team(SQLModel, table=True):
    """Team with multiple members"""
    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # Relationship (virtual, not in database)
    members: List["User"] = Relationship(back_populates="team")

# ============================================================================
# CHILD MODEL
# ============================================================================

class User(SQLModel, table=True):
    """User that belongs to a Team"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)

    # Foreign key to team
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id")

    # Relationship (virtual, not in database)
    team: Optional[Team] = Relationship(back_populates="members")
```

### Many-to-Many Relationship

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# ============================================================================
# ASSOCIATION TABLE (junction table)
# ============================================================================

class StudentCourse(SQLModel, table=True):
    """Junction table for Student-Course relationship"""
    __tablename__ = "student_courses"

    student_id: Optional[int] = Field(
        default=None,
        foreign_key="students.id",
        primary_key=True,
    )
    course_id: Optional[int] = Field(
        default=None,
        foreign_key="courses.id",
        primary_key=True,
    )

# ============================================================================
# MODELS WITH MANY-TO-MANY
# ============================================================================

class Student(SQLModel, table=True):
    """Student that enrolls in many Courses"""
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Relationship to courses
    courses: List["Course"] = Relationship(
        back_populates="students",
        link_model=StudentCourse,
    )

class Course(SQLModel, table=True):
    """Course with many Students"""
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    # Relationship to students
    students: List[Student] = Relationship(
        back_populates="courses",
        link_model=StudentCourse,
    )
```

---

## Advanced Field Configuration

### Field Constraints

```python
from sqlmodel import Field
from typing import Optional

class Product(SQLModel, table=True):
    """Product with various constraints"""

    id: Optional[int] = Field(default=None, primary_key=True)

    # String length constraints
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Product name",
    )

    # Numeric constraints
    price: float = Field(
        gt=0,      # greater than
        le=99999,  # less than or equal
    )

    rating: float = Field(
        ge=0.0,    # greater than or equal
        le=5.0,    # less than or equal
    )

    stock: int = Field(
        ge=0,      # can't be negative
    )

    # Unique and index
    sku: str = Field(unique=True, index=True)
    category: str = Field(index=True)

    # Nullable with default
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    # Database column name different from field
    is_published: bool = Field(
        default=False,
        sa_column_kwargs={"name": "published"},
    )
```

### Custom Database Column Configuration

```python
from sqlmodel import Field
from sqlalchemy import Column, String, Text, Integer

class Article(SQLModel, table=True):
    """Article with custom column configuration"""
    __tablename__ = "articles"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Custom column type
    title: str = Field(
        sa_column=Column(String(500), nullable=False, unique=True)
    )

    # Text column (large)
    content: str = Field(
        sa_column=Column(Text, nullable=False)
    )

    # Custom column name
    author_name: str = Field(
        sa_column=Column("author", String(255))
    )

    # With default at database level
    view_count: int = Field(
        default=0,
        sa_column=Column(Integer, server_default="0"),
    )
```

---

## Special Field Types

### JSON/JSONB Fields

```python
from sqlmodel import Field
from sqlalchemy import JSON
from typing import Optional, Dict, Any
import json

class Config(SQLModel, table=True):
    """Store arbitrary JSON data"""
    __tablename__ = "configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # JSON field (serialized as JSON in database)
    settings: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON),
    )

    # Example usage:
    # config = Config(
    #     name="app-config",
    #     settings={
    #         "theme": "dark",
    #         "notifications": True,
    #         "language": "en"
    #     }
    # )
```

### Enum Fields

```python
from enum import Enum
from sqlmodel import Field
from typing import Optional

class StatusEnum(str, Enum):
    """Status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class Account(SQLModel, table=True):
    """Account with enum status"""
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    # Enum field
    status: StatusEnum = Field(
        default=StatusEnum.PENDING,
        sa_column_kwargs={"type": "VARCHAR"},
    )
```

---

## Response Models (No Database)

### Pydantic Only (No Table)

```python
from sqlmodel import SQLModel
from typing import Optional

# ============================================================================
# DATABASE MODEL
# ============================================================================

class UserDB(SQLModel, table=True):
    """User stored in database"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    hashed_password: str  # Never expose in response

# ============================================================================
# RESPONSE MODELS (No table=True)
# ============================================================================

class UserPublic(SQLModel):
    """User data returned to client (no password)"""
    id: int
    username: str
    email: str

class UserPublicWithTeam(SQLModel):
    """User with related team data"""
    id: int
    username: str
    email: str
    team: Optional["TeamPublic"] = None

class TeamPublic(SQLModel):
    """Team data without members (prevents recursion)"""
    id: int
    name: str

# ============================================================================
# CIRCULAR RELATIONSHIP SOLUTION
# ============================================================================

# Define models in correct order to avoid forward references
# or use string quotes: "ModelName"

class Hero(SQLModel, table=True):
    """Hero stored in database"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id")

class HeroPublic(SQLModel):
    """Hero response (no team to prevent recursion)"""
    id: int
    name: str

class HeroPublicWithTeam(SQLModel):
    """Hero with team (team has no heroes to prevent recursion)"""
    id: int
    name: str
    team: Optional["TeamPublic"] = None

class TeamPublic(SQLModel):
    """Team response (no heroes)"""
    id: int
    name: str

class TeamPublicWithHeroes(SQLModel):
    """Team with heroes (heroes have no team)"""
    id: int
    name: str
    heroes: List[HeroPublic] = []
```

---

## Model Best Practices

### ✅ Good Model Design

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    """Well-designed User model"""
    __tablename__ = "users"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Core fields with constraints
    username: str = Field(
        index=True,
        unique=True,
        min_length=3,
        max_length=50,
    )
    email: str = Field(unique=True, index=True)

    # Optional fields
    full_name: Optional[str] = None
    bio: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Status flags
    is_active: bool = Field(default=True)

    # Relationship (not in database)
    posts: List["Post"] = Relationship(back_populates="author")
```

### ❌ Common Mistakes

```python
# ❌ Don't: Missing primary key
class User(SQLModel, table=True):
    username: str
    # SQLModel requires id field

# ❌ Don't: Store relationships as fields
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    posts_list: str  # Don't store list as string
    # Use Relationship instead

# ❌ Don't: Expose sensitive data in model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str  # ❌ Never expose to client
    # Use separate response model

# ❌ Don't: Circular relationships without care
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    members: List["User"] = Relationship()  # Fine
    # But response models should not have circular references

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team: Optional[Team] = Relationship()  # Fine
    # Response models should have separate definitions
```

---

## Model Organization

### File Structure

```
src/
├── models/
│   ├── __init__.py
│   ├── base.py              # Base model
│   ├── user.py              # User models
│   ├── product.py           # Product models
│   ├── team.py              # Team models
│   └── schemas.py           # Response models (no table=True)
└── database.py
```

### Base Model for Common Fields

```python
# src/models/base.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class BaseModel(SQLModel):
    """Base model with common fields"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Inherit from BaseModel
class User(BaseModel, table=True):
    """User inherits id, created_at, updated_at from BaseModel"""
    __tablename__ = "users"
    username: str
    email: str
```

---

## Model Validation

### Pydantic Validators

```python
from sqlmodel import SQLModel, Field
from pydantic import field_validator
from typing import Optional

class User(SQLModel, table=True):
    """User with validation"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, max_length=50)
    email: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Username must be alphanumeric"""
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        """Simple email validation"""
        if "@" not in v:
            raise ValueError("Invalid email")
        return v
```

---

## Model Checklist

Before using models in production:

- [ ] All database models have `table=True`
- [ ] All database models have primary key (id field)
- [ ] Foreign keys use correct table references
- [ ] Relationships use `back_populates` for bidirectional
- [ ] Response models don't have `table=True`
- [ ] Sensitive data (passwords) not in response models
- [ ] Circular relationships handled in response models
- [ ] Field constraints defined (min_length, max_length, etc.)
- [ ] Indexes created for frequently queried fields
- [ ] Timestamps use `default_factory=datetime.utcnow`
- [ ] All imports from sqlmodel are correct

---

## Summary

SQLModel models should:
1. **Have proper primary key** (id field with Optional[int])
2. **Define all fields with types** (no dynamic attributes)
3. **Use Relationship for navigating to related models**
4. **Use Field for constraints and configuration**
5. **Separate database models from response models**
6. **Use back_populates for bidirectional relationships**
7. **Apply validation with Pydantic validators**
