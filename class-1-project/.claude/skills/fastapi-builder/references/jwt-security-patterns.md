# JWT and Security Patterns - Production Authentication

This guide covers RS256 asymmetric JWT, token lifecycle, password security, and distributed verification based on auth-service patterns.

## RS256 Asymmetric Cryptography

### Why Asymmetric (RS256 vs HS256)?

| Aspect | HS256 (Symmetric) | RS256 (Asymmetric) |
|--------|-------------------|--------------------|
| **Keys** | One secret key (sign + verify) | Private key (sign), Public key (verify) |
| **Security** | Compromise = total failure | Public key safe to share |
| **Distribution** | Hard in microservices | JWKS endpoint for other services |
| **Use Case** | Single service | Microservices, OpenID Connect |
| **Best For** | Monoliths | Production systems |

### RS256 Implementation

```python
from jose import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from pathlib import Path
from base64 import b64decode
import os

ALGORITHM = "RS256"

def generate_rsa_keys():
    """Generate RSA-2048 key pair (production setup)"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Save private key (keep secure!)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Save public key (safe to distribute)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

def get_rsa_keys():
    """Load RSA keys from configured sources"""
    # Priority 1: Environment variable (for Vercel deployment)
    if settings.RSA_PRIVATE_KEY_CONTENT:
        # Base64-decoded from environment
        private_key_pem = b64decode(settings.RSA_PRIVATE_KEY_CONTENT)
        # Extract public key from private key
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_key_pem, public_pem

    # Priority 2: File path (for development)
    elif settings.RSA_PRIVATE_KEY_PATH:
        private_path = Path(settings.RSA_PRIVATE_KEY_PATH)
        public_path = Path(str(private_path) + ".pub")

        with open(private_path, 'rb') as f:
            private_key_pem = f.read()

        with open(public_path, 'rb') as f:
            public_pem = f.read()

        return private_key_pem, public_pem

    raise ValueError("No RSA keys configured")
```

---

## Token Lifecycle

### Token Types and Structure

```python
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Dict

class TokenPayload:
    """JWT token payload structure"""
    sub: str                # Subject (user ID)
    iat: int               # Issued at (timestamp)
    exp: int               # Expiration (timestamp)
    type: str              # "access" or "refresh"
    jti: Optional[str]     # JWT ID (for revocation)

def create_access_token(user_id: UUID) -> str:
    """
    Create short-lived access token (15 minutes).

    Used for immediate requests. Short expiry limits compromise window.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),               # User ID
        "type": "access",                  # Token type for validation
        "iat": int(now.timestamp()),       # Issued at
        "exp": int(expires.timestamp()),   # Expiration
    }

    private_key, _ = get_rsa_keys()
    token = jwt.encode(payload, private_key, algorithm=ALGORITHM)
    return token

def create_refresh_token(user_id: UUID) -> str:
    """
    Create long-lived refresh token (7 days).

    Used to get new access tokens. Stored in database whitelist
    for revocation capability.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "type": "refresh",                 # Token type for validation
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }

    private_key, _ = get_rsa_keys()
    token = jwt.encode(payload, private_key, algorithm=ALGORITHM)
    return token
```

### Token Validation

```python
from jose import JWTError, jwt as jose_jwt
from fastapi import HTTPException, status

def verify_token(token: str, token_type: str = "access") -> Dict:
    """
    Verify JWT signature, expiration, and type.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded payload if valid

    Raises:
        JWTError if invalid
    """
    try:
        _, public_key = get_rsa_keys()

        # Decode and verify signature
        payload = jose_jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM]
        )

        # Verify token type matches expectation
        if payload.get("type") != token_type:
            raise JWTError(f"Invalid token type: {payload.get('type')}")

        return payload

    except jose_jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jose_jwt.JWTClaimsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

---

## Password Security

### Argon2 Configuration (RECOMMENDED - Modern Best Practice)

```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Production configuration with Argon2 (winner of Password Hashing Competition)
password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    """
    Hash password with Argon2.

    Argon2 advantages over bcrypt:
    - Resistant to GPU/ASIC attacks (memory-hard)
    - Configurable time and space complexity
    - Automatically handles salt and iterations
    - Faster parallel hashing capability
    """
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against Argon2 hash.

    Uses constant-time comparison to prevent timing attacks
    that could reveal password information.
    """
    return password_hash.verify(plain_password, hashed_password)

# Testing hash_password behavior
if __name__ == "__main__":
    password = "SecurePassword123!"

    # Same password, different hashes (due to salt)
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2  # Different hashes
    assert verify_password(password, hash1)  # Both verify correctly
    assert verify_password(password, hash2)
```

### Bcrypt Configuration (Legacy Alternative)

```python
from passlib.context import CryptContext

# Production configuration with high cost factor
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 12 (CPU-intensive)
)

def hash_password(password: str) -> str:
    """
    Hash password with bcrypt (legacy).

    Bcrypt cost factor of 12:
    - Takes ~250ms to hash (CPU-bound)
    - Resistant to brute-force attacks
    - Different hash for same password (due to salt)
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password with constant-time comparison.

    Uses constant-time comparison to prevent timing attacks
    that could reveal password information.
    """
    return pwd_context.verify(plain_password, hashed_password)
```

**Recommendation**: Use Argon2 (pwdlib) for new projects. Use bcrypt only if you have existing bcrypt hashes to maintain compatibility.

### Password Requirements

```python
from pydantic import BaseModel, Field, field_validator

class PasswordValidator(BaseModel):
    """Password validation rules"""
    password: str = Field(
        ...,
        min_length=8,
        description="At least 8 characters"
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Validate password meets strength requirements.
        """
        if len(v) < 8:
            raise ValueError('At least 8 characters required')

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*" for c in v)

        # Require at least 3 of 4 categories
        strength = sum([has_upper, has_lower, has_digit, has_special])
        if strength < 3:
            raise ValueError(
                'Password must contain uppercase, lowercase, digits, and special characters'
            )

        return v

# Usage in registration
class UserRegister(BaseModel):
    email: str = Field(..., min_length=5)
    username: str = Field(..., min_length=3)
    password: str
    password_confirm: str

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        """Verify passwords match"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
```

---

## Single-Session Enforcement

### Logout from All Devices

```python
async def login(
    credentials: OAuth2PasswordRequestForm,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint with single-session enforcement.

    When user logs in:
    1. Verify credentials
    2. DELETE all existing refresh tokens (logout from other devices)
    3. Issue new token pair
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.username)
    )
    user = result.scalar()

    # Verify password
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # SINGLE-SESSION: Revoke all existing tokens
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    await db.commit()

    # Issue new token pair
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Store refresh token in whitelist
    token_obj = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )
    db.add(token_obj)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "token_type": "Bearer"
    }
```

**Security Benefits:**
- User logs in on phone
- All other session tokens (computer, tablet) are immediately revoked
- Prevents unauthorized access from compromise of other devices

---

## Token Rotation

### Refresh Token Rotation

```python
async def refresh_access_token(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh endpoint with token rotation.

    When client uses refresh token:
    1. Verify refresh token
    2. Check if in whitelist (not revoked)
    3. DELETE old refresh token (rotation)
    4. Issue new token pair
    """
    refresh_token = request.get("refresh_token")

    # Verify refresh token signature and expiration
    try:
        payload = verify_token(refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")

    # Check if token is in whitelist (not revoked)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    )
    db_token = result.scalar()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked (rotation)"
        )

    # TOKEN ROTATION: Delete old token before issuing new one
    await db.delete(db_token)

    # Create new token pair
    new_access_token = create_access_token(UUID(user_id))
    new_refresh_token = create_refresh_token(UUID(user_id))

    # Store new refresh token in whitelist
    new_token_obj = RefreshToken(
        token=new_refresh_token,
        user_id=UUID(user_id),
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )
    db.add(new_token_obj)
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "token_type": "Bearer"
    }
```

**Security Benefits:**
- Old token immediately invalidated
- Stolen token only useful until next refresh
- Client-side errors detected (token missing from whitelist)

---

## JWKS Endpoint for Distributed Verification

### Public Key Distribution

```python
from cryptography.hazmat.primitives import serialization
import base64
from cryptography.hazmat.backends import default_backend

def get_rsa_public_numbers():
    """Extract RSA public numbers for JWKS"""
    _, public_key_pem = get_rsa_keys()

    public_key = serialization.load_pem_public_key(
        public_key_pem,
        backend=default_backend()
    )

    numbers = public_key.public_numbers()

    # Convert to base64url (for JWKS)
    n = base64.urlsafe_b64encode(
        numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, 'big')
    ).rstrip(b'=').decode()

    e = base64.urlsafe_b64encode(
        numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, 'big')
    ).rstrip(b'=').decode()

    return n, e

@router.get("/.well-known/jwks.json")
async def get_jwks():
    """
    JWKS (JSON Web Key Set) endpoint.

    Returns public key in standardized format for:
    - Other microservices to verify tokens
    - Frontend to validate tokens locally
    - OpenID Connect compliance
    """
    n, e = get_rsa_public_numbers()

    return {
        "keys": [
            {
                "kty": "RSA",                              # Key type
                "kid": settings.RSA_PUBLIC_KEY_ID,         # Key ID
                "use": "sig",                              # Usage (signature)
                "n": n,                                    # Modulus (base64url)
                "e": e,                                    # Exponent
                "alg": ALGORITHM,                          # Algorithm (RS256)
            }
        ]
    }
```

**Distributed Verification Example:**

```python
# Other microservice can verify tokens without private key
import requests

def verify_token_distributed(token: str):
    """Verify JWT using JWKS endpoint"""
    # Fetch JWKS
    response = requests.get("https://auth-service.example.com/.well-known/jwks.json")
    jwks = response.json()

    # Decode and verify (library handles JWKS lookup)
    decoded = jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],
        audience=None,
    )
    return decoded
```

---

## Security Checklist

| Item | Status | Note |
|------|--------|------|
| RS256 (asymmetric) | ✅ | Use, not HS256 |
| Bcrypt cost 12 | ✅ | ~250ms hash time |
| Short access token | ✅ | 15 minutes |
| Long refresh token | ✅ | 7 days |
| Token rotation | ✅ | Delete old on refresh |
| Single-session | ✅ | Revoke all on login |
| Refresh whitelist | ✅ | Database validation |
| JWKS endpoint | ✅ | For distributed verification |
| HTTPS only | ✅ | Production requirement |
| Secure storage | ✅ | HTTP-only cookies or secure storage |

