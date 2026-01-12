# Minimal FastAPI Project

## File Structure
```
my_app/
├── main.py
├── requirements.txt
└── test_main.py
```

## main.py

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="My FastAPI App",
    description="A simple FastAPI application",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

@app.post("/items/")
async def create_item(item: Item):
    """Create a new item"""
    return {"item": item, "created": True}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get an item by ID"""
    return {"item_id": item_id, "name": "Widget"}
```

## requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

## Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Visit http://localhost:8000/docs for interactive API documentation
```
