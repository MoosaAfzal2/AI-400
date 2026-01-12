# FastAPI Authentication Patterns

## API Keys (Simple Token-Based)

### Implementation

```python
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader, APIKeyCookie, APIKeyQuery

app = FastAPI()

# Header-based API key
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    # In production: lookup in database
    valid_keys = {"sk-1234567890", "sk-0987654321"}
    if api_key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/protected/")
async def protected_route(api_key: str = Depends(verify_api_key)):
    return {"message": "Access granted", "api_key": api_key}
```

### Query Parameter API Key

```python
api_key_query = APIKeyQuery(name="api_key")

async def verify_api_key(api_key: str = Security(api_key_query)) -> str:
    if api_key != "sk-secret":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

### Cookie-Based API Key

```python
api_key_cookie = APIKeyCookie(name="api_key")

async def verify_api_key(api_key: str = Security(api_key_cookie)) -> str:
    if api_key != "sk-secret":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

## JWT Tokens (Stateless Authentication)

### Setup and Token Generation

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "your-secret-key-min-32-chars-long"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Login Endpoint

```python
from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # In production: lookup user in database, verify password
    if form_data.username != "user" or not verify_password(form_data.password, hash_password("password")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    expires_in = int(access_token_expires.total_seconds())
    return {"access_token": access_token, "token_type": "bearer", "expires_in": expires_in}
```

### Token Verification

```python
from jose import JWTError

async def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected/")
async def protected_route(current_user: str = Depends(verify_token)):
    return {"message": f"Hello {current_user}"}
```

### Refresh Tokens

```python
@app.post("/token/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme)) -> Token:
    current_user = await verify_token(token)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": current_user},
        expires_delta=access_token_expires
    )
    expires_in = int(access_token_expires.total_seconds())
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }
```

## OAuth2 with Third-Party Providers

### Google OAuth2

```python
from fastapi import FastAPI
from authlib.integrations.starlette_client import OAuth

app = FastAPI()
oauth = OAuth()

oauth.register(
    name='google',
    client_id='your-client-id',
    client_secret='your-client-secret',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token.get('userinfo')
    return {"user": user}
```

## Scopes & Permissions

```python
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

class TokenData(BaseModel):
    username: str
    scopes: list[str] = []

async def verify_token_with_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> TokenData:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    token_scopes = payload.get("scopes", [])

    # Check if required scopes are present
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return TokenData(username=username, scopes=token_scopes)

@app.get("/admin/")
async def admin_route(current_user: TokenData = Depends(verify_token_with_scopes(["admin"]))):
    return {"message": "Admin access granted"}
```

## Best Practices

1. **Never store passwords**: Hash with bcrypt or Argon2
2. **Use HTTPS in production**: Always encrypt in transit
3. **Short token expiry**: 15-30 minutes for access tokens
4. **Rotate secrets**: Change SECRET_KEY in production
5. **Store secrets in environment**: Use `.env` files or secrets management
6. **Log authentication events**: Track failed attempts
7. **Implement rate limiting**: Prevent brute force attacks
8. **Secure refresh tokens**: Store in HTTP-only cookies when possible
