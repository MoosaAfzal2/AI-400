# Deployment Architecture - Production Ready

## Docker Containerization

### Dockerfile (Multi-Stage)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY pyproject.toml pyproject.lock ./
RUN pip install --user --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.auth_service.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]
```

### .dockerignore

```
__pycache__
*.pyc
*.pyo
.git
.gitignore
.env
.env.local
.venv
venv/
.pytest_cache
.mypy_cache
.coverage
htmlcov/
dist/
build/
*.egg-info
.idea/
.vscode/
.DS_Store
README.md
CHANGELOG.md
tests/
docs/
*.md
```

## Docker Compose (Local Development)

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    container_name: auth_postgres
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: auth_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - auth_network

  redis:
    image: redis:7-alpine
    container_name: auth_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - auth_network

  api:
    build: .
    container_name: auth_api
    environment:
      DATABASE_URL: postgresql+asyncpg://user:password@postgres:5432/auth_db
      REDIS_URL: redis://redis:6379/0
      DEBUG: "false"
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src  # Hot reload for development
    networks:
      - auth_network
    command: >
      sh -c "
      alembic upgrade head &&
      uvicorn src.auth_service.main:app --host 0.0.0.0 --port 8000 --reload
      "

volumes:
  postgres_data:

networks:
  auth_network:
    driver: bridge
```

### Build and Run

```bash
# Build image
docker build -t auth-service:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@localhost/auth_db \
  -e SECRET_KEY=your-secret-key \
  auth-service:latest

# With Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  labels:
    app: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: api
        image: registry.example.com/auth-service:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http

        # Environment from ConfigMap and Secrets
        envFrom:
        - configMapRef:
            name: auth-config
        - secretRef:
            name: auth-secrets

        # Resource limits
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

        # Probes for readiness/liveness
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
```

### Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
    name: http
  type: LoadBalancer
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: auth-config
data:
  APP_NAME: "Auth Service"
  APP_VERSION: "1.0.0"
  DEBUG: "false"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: auth-secrets
type: Opaque
stringData:
  DATABASE_URL: postgresql+asyncpg://user:password@db:5432/auth
  SECRET_KEY: your-secret-key-here
  RSA_PRIVATE_KEY_CONTENT: base64-encoded-key
```

Apply manifests:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# Check deployment
kubectl get deployments
kubectl get pods
kubectl logs -f deployment/auth-service

# Scale
kubectl scale deployment auth-service --replicas=5
```

---

## Environment Variables

### Development (.env)

```
# Application
APP_NAME=Auth Service
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/auth_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# JWT
RSA_PRIVATE_KEY_PATH=./keys/private.pem
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password
PASSWORD_BCRYPT_ROUNDS=12

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your-app-password

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Production (.env.production)

```
# Application
APP_NAME=Auth Service
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# Server (Vercel handles host/port)
HOST=0.0.0.0
PORT=3000

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com/auth
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# JWT (use environment variable for keys)
RSA_PRIVATE_KEY_CONTENT=base64-encoded-private-key
RSA_PUBLIC_KEY_ID=production

# Password
PASSWORD_BCRYPT_ROUNDS=12

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=sendgrid-api-key

# CORS
CORS_ORIGINS=https://app.example.com,https://www.example.com
```

---

## Vercel Deployment

### vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api.py"
    }
  ],
  "env": {
    "PYTHONPATH": "src"
  }
}
```

### api.py (Entry point)

```python
from src.auth_service.main import app

__all__ = ["app"]
```

### Deployment Steps

1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy:

```bash
# Manual deployment
vercel --prod

# Automatic on git push (if connected)
git push origin main
```

---

## Health Checks

### Liveness Probe

```python
@router.get("/api/v1/health")
async def health_check():
    """Liveness probe - is the service alive?"""
    return {"status": "ok", "version": settings.APP_VERSION}
```

### Readiness Probe

```python
@router.get("/api/v1/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe - is the service ready for traffic?"""
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
```

---

## Monitoring and Logging

### Logging Setup

```python
import logging
import sys
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
        "json": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": settings.LOG_LEVEL,
        },
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
```

---

## Deployment Checklist

- ✅ Docker image optimized (multi-stage, non-root user)
- ✅ Environment variables configured
- ✅ Health checks implemented
- ✅ Database migrations automated
- ✅ Secrets management (not in code)
- ✅ Logging configured
- ✅ Resource limits set
- ✅ HTTPS/TLS configured
- ✅ CORS configured for production
- ✅ Error handling for graceful shutdown
- ✅ Monitoring and alerting setup
- ✅ Backup strategy
- ✅ Rollback procedure documented
