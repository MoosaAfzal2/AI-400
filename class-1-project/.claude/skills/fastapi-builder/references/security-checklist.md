# FastAPI Security Best Practices

Comprehensive security guide covering authentication, data protection, and attack prevention.

## OWASP Top 10 Coverage

### 1. Authentication & Session Management

#### Password Storage

**RECOMMENDED: Argon2 (Modern Best Practice)**
```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Use Argon2 (winner of Password Hashing Competition)
password_hash = PasswordHash((Argon2Hasher(),))

# Hash before storing
hashed_password = password_hash.hash(user_password)

# Verify during login
if not password_hash.verify(provided_password, hashed_password):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

**LEGACY ALTERNATIVE: Bcrypt**
```python
from passlib.context import CryptContext

# Use bcrypt if you have existing compatibility needs
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Hash before storing
hashed_password = pwd_context.hash(user_password)

# Verify during login
if not pwd_context.verify(provided_password, hashed_password):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

✅ **Do:**
- Use Argon2 (pwdlib) for new projects - more resistant to GPU/ASIC attacks
- Use bcrypt only if maintaining existing hashes
- Enforce strong passwords (min 12 characters, complexity rules)
- Implement password history (prevent reuse)
- Force password reset every 90 days

❌ **Don't:**
- Store passwords in plain text
- Use fast hashing (MD5, SHA1)
- Hardcode passwords
- Log passwords anywhere
- Use bcrypt for new projects (unless legacy compatibility needed)

#### JWT Token Security
```python
from datetime import datetime, timedelta
from jose import jwt

# Short expiry (15-30 minutes for access tokens)
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

✅ **Do:**
- Use short expiry (15-30 minutes for access tokens)
- Rotate refresh tokens on each use
- Store refresh tokens in HTTP-only cookies
- Include token issued-at (`iat`) and expiry (`exp`) claims
- Validate token signature on every request

❌ **Don't:**
- Use long-lived tokens
- Store tokens in localStorage (XSS vulnerable)
- Skip signature validation
- Use weak SECRET_KEY

### 2. SQL Injection Prevention

SQLAlchemy handles SQL injection automatically via parameterized queries:

```python
# ✅ Safe: Parameterized query (SQLAlchemy does this automatically)
result = await db.execute(
    select(User).where(User.username == username)
)

# ❌ NEVER do string concatenation:
# result = db.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

✅ **Do:**
- Always use ORM methods (SQLAlchemy)
- Use parameterized queries for raw SQL
- Validate input types with Pydantic

❌ **Don't:**
- Concatenate user input into SQL strings
- Use `.format()` or f-strings with user data

### 3. Cross-Site Scripting (XSS) Prevention

FastAPI automatically escapes response data in JSON:

```python
# ✅ Safe: JSON response automatically escaped
@app.get("/items/")
async def get_items():
    return {"name": user_input}  # Safely escaped

# XSS attempt: <script>alert('xss')</script>
# Returned as: {"name": "&lt;script&gt;...&lt;/script&gt;"}
```

✅ **Do:**
- Let FastAPI handle JSON escaping
- Use Pydantic for input validation
- Set Content-Security-Policy headers

❌ **Don't:**
- Return HTML with raw user input
- Use `.format()` or f-strings in HTML templates

### 4. Cross-Site Request Forgery (CSRF) Protection

CSRF is less relevant for JSON APIs but still important for form submission:

```python
from fastapi.middleware.csrf import CSRFMiddleware

# For APIs with session-based auth, add CSRF protection
app.add_middleware(CSRFMiddleware, secret_key=SECRET_KEY)

# For token-based auth (JWT), CSRF is less critical
# (tokens not sent automatically with cross-site requests)
```

✅ **Do:**
- Use HTTPS (prevents token interception)
- Use SameSite cookies (`SameSite=Strict` or `SameSite=Lax`)
- Validate origin headers for state-changing requests

❌ **Don't:**
- Use cookies for state-changing operations without CSRF token
- Send tokens in GET parameters

### 5. Broken Access Control

Implement proper authorization checks:

```python
from fastapi import Depends, HTTPException

async def verify_item_owner(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Item:
    item = await db.get(Item, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return item

@app.delete("/items/{item_id}")
async def delete_item(
    item: Item = Depends(verify_item_owner)
):
    # Only reached if current_user owns the item
    return await db.delete(item)
```

✅ **Do:**
- Check ownership/permissions on every operation
- Use dependency injection for auth checks
- Implement role-based access control (RBAC)
- Log access control failures

❌ **Don't:**
- Trust user IDs from request parameters
- Skip authorization on "internal" endpoints
- Allow users to modify others' data

### 6. Security Misconfiguration

#### CORS Configuration
```python
# ❌ DON'T use this in production:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Too permissive!
    allow_credentials=True,
)

# ✅ DO specify allowed origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",
        "https://www.example.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

#### Security Headers
```python
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### 7. Sensitive Data Exposure

#### Never Log Sensitive Data
```python
import logging

logger = logging.getLogger(__name__)

# ❌ DON'T log sensitive data:
logger.info(f"User login: {username} with password {password}")

# ✅ DO log safely:
logger.info(f"User login attempt: {username}")
```

#### Encrypt Sensitive Fields
```python
from cryptography.fernet import Fernet

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    ssn_encrypted = Column(String)  # Never plain text

    @property
    def ssn(self):
        cipher = Fernet(ENCRYPTION_KEY)
        return cipher.decrypt(self.ssn_encrypted)

    @ssn.setter
    def ssn(self, value):
        cipher = Fernet(ENCRYPTION_KEY)
        self.ssn_encrypted = cipher.encrypt(value.encode())
```

### 8. Rate Limiting

Prevent brute force and DoS attacks:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/token")
@limiter.limit("5/minute")  # Max 5 attempts per minute
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # Login logic
    pass
```

✅ **Do:**
- Limit login attempts (5 per minute)
- Limit API endpoints (100 per hour)
- Return 429 Too Many Requests
- Implement exponential backoff for clients

❌ **Don't:**
- Allow unlimited login attempts
- No rate limiting on public endpoints

### 9. Input Validation

Pydantic validates all inputs automatically:

```python
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=12)  # Min 12 chars

# ❌ Invalid request rejected automatically:
# {"username": "ab", "email": "invalid", "password": "short"}
# Returns 422 Unprocessable Entity with validation errors
```

### 10. Dependency & Version Management

```bash
# ✅ Pin versions for security
fastapi==0.109.0
sqlalchemy==2.0.23
pydantic==2.5.0

# ✅ Regularly scan for vulnerabilities
pip-audit

# ✅ Update dependencies
pip list --outdated
pip install --upgrade fastapi
```

---

## Secrets Management

### Environment Variables
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str  # Required, loaded from .env
    DATABASE_URL: str
    API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### .env File (Never commit to git)
```bash
SECRET_KEY=generate-random-32-char-string-here
DATABASE_URL=postgresql+asyncpg://user:password@localhost/db
API_KEY=your-api-key-here
```

### .gitignore
```
.env
.env.local
.env.*.local
```

---

## Security Audit Checklist

- [ ] All passwords hashed with bcrypt/Argon2
- [ ] JWT tokens expire within 30 minutes
- [ ] HTTPS enforced (no HTTP in production)
- [ ] CORS restricted to known origins
- [ ] Secrets not in version control
- [ ] SQL injection prevented (using ORM)
- [ ] Access control implemented (ownership checks)
- [ ] Rate limiting on login/sensitive endpoints
- [ ] Error messages don't expose internals
- [ ] Security headers configured
- [ ] Dependencies scanned for vulnerabilities
- [ ] Sensitive data not logged
- [ ] Input validation with Pydantic

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8949)
- [Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
