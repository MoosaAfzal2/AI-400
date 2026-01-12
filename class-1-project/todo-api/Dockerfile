# Multi-stage Dockerfile for Todo API
# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy pyproject.toml
COPY pyproject.toml .

# Build virtual environment
RUN uv venv /app/.venv && \
    /app/.venv/bin/pip install --upgrade pip && \
    uv sync --no-dev

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ /app/src/
COPY main.py /app/main.py
COPY .env.example /app/.env.example

# Set environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "main.py"]
