# Deployment Guide

Production deployment guide for Todo API with authentication.

## Prerequisites

- Docker and docker-compose
- Neon Postgres account
- GitHub Actions (for CI/CD)
- Basic knowledge of FastAPI, async Python, and PostgreSQL

## Environment Configuration

### Production Environment Variables

Create a `.env.production` file with these settings:

```bash
# Database (Neon Postgres)
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/todo_db

# JWT Configuration
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=<generate-256-bit-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Bcrypt
BCRYPT_COST_FACTOR=10

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=production
DEBUG=false

# CORS (update for your domain)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Logging
LOG_LEVEL=INFO
```

### Generate JWT Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and set as `JWT_SECRET_KEY`.

## Docker Deployment

### Build Docker Image

```bash
cd todo-api
docker build -t todo-api:latest .
```

### Run with Docker Compose (Local)

```bash
docker-compose up -d
```

Access at `http://localhost:8000`

### Production Deployment with Docker

```bash
# Run database migrations
docker run -e DATABASE_URL=<neon-url> todo-api:latest \
  python -m alembic upgrade head

# Run application
docker run -d \
  -e DATABASE_URL=<neon-url> \
  -e JWT_SECRET_KEY=<your-secret> \
  -p 8000:8000 \
  todo-api:latest
```

## Kubernetes Deployment

### Prerequisites

- kubectl configured
- Docker registry access
- Kubernetes cluster (EKS, GKE, AKS, etc.)

### Deploy to Kubernetes

```bash
# 1. Push image to registry
docker tag todo-api:latest myregistry.azurecr.io/todo-api:latest
docker push myregistry.azurecr.io/todo-api:latest

# 2. Create namespace
kubectl create namespace todo-api

# 3. Create secrets
kubectl create secret generic todo-api-secrets \
  --from-literal=database-url=<neon-url> \
  --from-literal=jwt-secret=<jwt-secret> \
  -n todo-api

# 4. Apply deployment (see todo-api-deployment.yaml below)
kubectl apply -f todo-api-deployment.yaml
```

### Example Kubernetes Manifests

**todo-api-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-api
  namespace: todo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: todo-api
  template:
    metadata:
      labels:
        app: todo-api
    spec:
      containers:
      - name: todo-api
        image: myregistry.azurecr.io/todo-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: todo-api-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: todo-api-secrets
              key: jwt-secret
        - name: ENVIRONMENT
          value: "production"
        - name: DEBUG
          value: "false"
        - name: SERVER_HOST
          value: "0.0.0.0"
        - name: SERVER_PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: todo-api
  namespace: todo-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: todo-api
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: todo-api-hpa
  namespace: todo-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: todo-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Neon Postgres Setup

1. Create account at https://neon.tech
2. Create a project and database
3. Copy the connection string:
   ```
   postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/todo_db
   ```
4. Add connection string to environment variables
5. Run migrations:
   ```bash
   python -m alembic upgrade head
   ```

## Database Migrations

### Run Migrations

```bash
# Using Alembic directly
alembic upgrade head

# Using Docker
docker run -e DATABASE_URL=<neon-url> todo-api:latest \
  python -m alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

## Monitoring & Observability

### Health Checks

- **Liveness**: GET /health (basic health status)
- **Readiness**: GET /ready (database connectivity check)
- **Metrics**: GET /metrics (Prometheus format)

### Logging

Logs are structured JSON format for easy parsing:

```json
{
  "timestamp": "2026-01-12T20:30:00.000Z",
  "level": "INFO",
  "logger": "todo_api.routes.auth",
  "message": "User registered successfully",
  "user_id": 1,
  "email": "user@example.com"
}
```

### Performance Metrics

Endpoints should respond within:
- Register: < 500ms
- Login: < 500ms
- Create todo: < 200ms
- List todos: < 500ms
- Update todo: < 200ms
- Delete todo: < 200ms

### Database Connection Pool

Production settings:
```python
pool_size=20              # Base connections
max_overflow=10           # Max additional connections
pool_recycle=3600         # Recycle connections after 1 hour
pool_pre_ping=True        # Verify connections before use
```

## Security Hardening

### Checklist

- [ ] JWT secret key is 256+ bits
- [ ] CORS origins configured for production domain
- [ ] HTTPS enforced (redirect http → https)
- [ ] Database credentials in environment variables
- [ ] No sensitive data in logs
- [ ] Bcrypt cost factor set to 10 or higher
- [ ] Rate limiting configured
- [ ] Security headers configured
- [ ] OWASP vulnerabilities checked

### HTTPS Configuration

Use a reverse proxy (nginx) or load balancer to handle HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/key.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Backup & Disaster Recovery

### Database Backups

Neon Postgres provides automatic backups. Configure:

1. Backup frequency: Daily
2. Retention: 7 days minimum
3. Geographic replication: Enable

### Recovery Procedure

```bash
# Restore from backup via Neon console
# OR via CLI
neon project restore --branch main --backup-id <backup-id>
```

## Troubleshooting

### Connection Issues

```bash
# Test database connection
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; \
  engine = create_async_engine('<DATABASE_URL>'); \
  asyncio.run(engine.dispose())"
```

### JWT Secret Issues

```bash
# Verify JWT secret is valid
python -c "print(len('your-secret-key') >= 32)"  # Must return True
```

### Performance Issues

```bash
# Check slow queries
psql -U user -h host -d todo_db -c \
  "SELECT query, calls, mean_exec_time FROM pg_stat_statements \
   ORDER BY mean_exec_time DESC LIMIT 10;"
```

## Scaling Considerations

### Horizontal Scaling

- Stateless API (all state in database)
- Load balancer for traffic distribution
- Auto-scaling based on CPU/memory metrics

### Vertical Scaling

- Increase connection pool size for high traffic
- Upgrade database instance size for large datasets
- Cache frequently accessed data (future enhancement)

## Rollback Procedure

```bash
# 1. Stop current deployment
kubectl set image deployment/todo-api \
  todo-api=myregistry.azurecr.io/todo-api:previous-version

# 2. Verify health
kubectl get pods -n todo-api

# 3. If needed, rollback database
alembic downgrade <revision>
```

## CI/CD Pipeline

See `.github/workflows/deploy.yml` for automated deployment on push to main.

### Deployment Steps

1. Run tests
2. Build Docker image
3. Push to registry
4. Deploy to Kubernetes
5. Run smoke tests

---

**Last Updated**: 2026-01-12
**Supported Python**: 3.9+
**Database**: Neon Postgres (PostgreSQL 15+)
