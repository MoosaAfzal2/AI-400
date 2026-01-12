# Production Deployment Checklist

Before deploying a FastAPI application to production, verify all items in this checklist.

## Pre-Deployment Verification

### 🔒 Security Configuration

- [ ] **Environment Variables**: All secrets moved to `.env` or secrets management system
  - [ ] `SECRET_KEY` is strong (min 32 characters, random)
  - [ ] `DATABASE_URL` points to production database
  - [ ] No hardcoded passwords or API keys in code
  - [ ] `.env` file is in `.gitignore`

- [ ] **HTTPS/TLS**: SSL certificate installed
  - [ ] Certificate is valid and not self-signed
  - [ ] HTTPS redirects HTTP traffic
  - [ ] Certificate renewal automated (e.g., Let's Encrypt with certbot)

- [ ] **CORS Configuration**: Restricted to known origins
  - [ ] `allow_origins` lists specific domains (not `["*"]` unless intentional)
  - [ ] No overly permissive CORS headers

- [ ] **Authentication**: Properly configured
  - [ ] Passwords hashed with bcrypt or Argon2
  - [ ] JWT tokens have short expiry (15-30 minutes)
  - [ ] Refresh token rotation implemented
  - [ ] API keys rotated regularly

### 📊 Database Configuration

- [ ] **Connection Pooling**: Enabled and tuned
  - [ ] `pool_size` set appropriately (20-50 for typical apps)
  - [ ] `max_overflow` set (e.g., 10)
  - [ ] `pool_pre_ping=True` enabled (checks connection health)
  - [ ] Connection timeout configured

- [ ] **Backups**: Automated daily backups
  - [ ] Backup storage is off-site or replicated
  - [ ] Restore process tested and documented
  - [ ] Retention policy defined (e.g., keep 30 days)

- [ ] **Migrations**: Applied and tested
  - [ ] All Alembic migrations run successfully
  - [ ] Rollback plan documented
  - [ ] Database schema is optimized

- [ ] **Indexing**: Critical columns indexed
  - [ ] Foreign keys indexed
  - [ ] Frequently filtered columns indexed
  - [ ] Unique constraints defined

### 🚀 Application Configuration

- [ ] **Logging**: Properly configured
  - [ ] Log level set to INFO or WARNING (not DEBUG)
  - [ ] Logs written to files or external service (not just stdout)
  - [ ] Log rotation configured (e.g., max 100MB per file)
  - [ ] Sensitive data NOT logged (passwords, tokens, PII)

- [ ] **Monitoring**: Metrics and alerts active
  - [ ] Application metrics collected (requests, errors, latency)
  - [ ] Error tracking enabled (Sentry, DataDog, etc.)
  - [ ] Alerting configured for critical errors
  - [ ] Health check endpoint responding

- [ ] **Performance**: Optimized settings
  - [ ] Uvicorn workers configured (typically `workers = CPU_count * 2`)
  - [ ] Timeouts set appropriately (connection, read, write)
  - [ ] Gzip compression enabled
  - [ ] Static file caching configured

- [ ] **Error Handling**: Graceful error responses
  - [ ] 500 errors don't expose internal details
  - [ ] Standard error format implemented
  - [ ] Request IDs included in error responses
  - [ ] Exception handlers cover all error types

### 🐳 Container & Deployment

- [ ] **Docker Image**: Optimized and secure
  - [ ] Using slim base image (not full Python)
  - [ ] Multi-stage build implemented
  - [ ] Non-root user configured
  - [ ] `.dockerignore` excludes unnecessary files

- [ ] **Kubernetes (if applicable)**:
  - [ ] Resource requests/limits set
  - [ ] Liveness probe configured (checks `/health`)
  - [ ] Readiness probe configured (checks database + dependencies)
  - [ ] Rolling updates configured
  - [ ] Secrets stored in K8s secrets (not ConfigMap)

- [ ] **Reverse Proxy** (Nginx/HAProxy):
  - [ ] TLS termination configured
  - [ ] Request headers forwarded (X-Real-IP, X-Forwarded-For)
  - [ ] Rate limiting configured
  - [ ] Gzip compression enabled

### 📝 Documentation & Operations

- [ ] **Runbook**: Incident response procedures documented
  - [ ] Common error scenarios and solutions
  - [ ] Database troubleshooting steps
  - [ ] How to scale up/down
  - [ ] Rollback procedure

- [ ] **Health Checks**: Endpoints working
  - [ ] `/health` returns 200 when healthy
  - [ ] `/ready` validates database connectivity
  - [ ] Health check timeout < 30s

- [ ] **Graceful Shutdown**: Implemented
  - [ ] SIGTERM handler closes connections
  - [ ] In-flight requests complete before shutdown
  - [ ] Database session cleanup occurs

### ✅ Final Pre-Deployment Tests

- [ ] **Load Testing**: App can handle expected traffic
  - [ ] Tested with 2-3x expected peak load
  - [ ] No memory leaks over extended runs
  - [ ] Response times acceptable under load

- [ ] **Security Scanning**: Vulnerabilities checked
  - [ ] OWASP top 10 review completed
  - [ ] Dependency vulnerabilities scanned (`pip-audit`)
  - [ ] SQL injection protection verified
  - [ ] XSS protection confirmed (if frontend involved)

- [ ] **Smoke Tests**: Basic functionality verified
  - [ ] Health endpoints responding
  - [ ] Main API endpoints working
  - [ ] Database connectivity confirmed
  - [ ] Authentication flow tested

---

## Post-Deployment Verification

- [ ] Health checks passing consistently
- [ ] No error spikes in monitoring system
- [ ] Logs flowing normally
- [ ] Response times within expected range
- [ ] Database connections stable

---

## Rollback Plan

If issues discovered in production:

1. Monitor for critical errors (>1% error rate)
2. Execute rollback (revert to previous image/version)
3. Run smoke tests again
4. Verify logs and monitoring normal
5. Post-incident review

---

## Common Production Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Connection pool exhausted | "QueuePool limit exceeded" | Increase `pool_size`, check for leaked connections |
| Memory leak | Process memory growing over time | Profile with `memory_profiler`, check for circular references |
| Slow queries | High latency, database CPU high | Add indexes, analyze slow query log, increase connection timeout |
| Token expiry errors | 401 errors after 15-30 min | Check token expiry setting, ensure refresh token working |
| CORS errors | Client can't access API | Verify `allow_origins` includes client domain, enable credential sharing if needed |

---

## Monthly Maintenance

- [ ] Review and rotate secrets/API keys
- [ ] Update dependencies (pip list --outdated)
- [ ] Check database size and cleanup old records
- [ ] Review and archive old logs
- [ ] Test disaster recovery (restore from backup)
- [ ] Review performance metrics and identify optimization opportunities
