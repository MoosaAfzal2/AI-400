#!/usr/bin/env python3
"""
Generate a new FastAPI project scaffold.
Usage: python scaffold.py --name my_project --template minimal|modular
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

MINIMAL_FILES = {
    "main.py": """from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="{project_name}",
    description="A FastAPI application",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.get("/health")
async def health():
    return {{"status": "healthy"}}

@app.post("/items/")
async def create_item(item: Item):
    return {{"item": item, "created": True}}

@app.get("/items/{{item_id}}")
async def get_item(item_id: int):
    return {{"item_id": item_id}}
""",
    "requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
pytest==7.4.3
httpx==0.25.2
""",
    ".gitignore": """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.env
.venv
venv/
ENV/
.vscode/
.idea/
""",
}

MODULAR_STRUCTURE = {
    "main.py": """from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import items, users, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="{project_name}",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])

@app.get("/health")
async def health():
    return {{"status": "healthy"}}
""",
    "config.py": """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
""",
    "database.py": """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
""",
    "requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.23
aiosqlite==0.19.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
""",
    ".gitignore": """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.env
.venv
venv/
ENV/
.vscode/
.idea/
*.db
""",
    ".env.example": """DATABASE_URL=sqlite+aiosqlite:///./app.db
SECRET_KEY=your-secret-key-here-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
""",
}

def scaffold_project(name: str, template: str = "minimal"):
    """Generate a new FastAPI project"""
    project_path = Path(name)

    if project_path.exists():
        raise ValueError(f"Project directory {name} already exists")

    project_path.mkdir()

    if template == "minimal":
        for filename, content in MINIMAL_FILES.items():
            (project_path / filename).write_text(content.format(project_name=name))
        print(f"✓ Created minimal FastAPI project: {name}/")

    elif template == "modular":
        # Create subdirectories
        (project_path / "routers").mkdir()
        (project_path / "tests").mkdir()

        for filename, content in MODULAR_FILES.items():
            (project_path / filename).write_text(content.format(project_name=name))

        # Create empty __init__.py files
        (project_path / "routers" / "__init__.py").write_text("")

        print(f"✓ Created modular FastAPI project: {name}/")

    print(f"Next steps:")
    print(f"  1. cd {name}")
    print(f"  2. python -m venv venv")
    print(f"  3. source venv/bin/activate  # or .\\venv\\Scripts\\activate on Windows")
    print(f"  4. pip install -r requirements.txt")
    print(f"  5. uvicorn main:app --reload")
    print(f"  6. Visit http://localhost:8000/docs")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastAPI Project Scaffolder")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--template", default="minimal", choices=["minimal", "modular"])

    args = parser.parse_args()
    scaffold_project(args.name, args.template)
