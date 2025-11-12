# Multi-stage Dockerfile for Selflytics FastAPI application
# Stage 1: Builder - Install dependencies
# IMPORTANT: Use linux/amd64 platform for Cloud Run compatibility
FROM --platform=linux/amd64 python:3.12-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy local packages (needed for workspace dependencies)
COPY packages/ ./packages/

# Install dependencies to a virtual environment
# Then install workspace packages as regular packages (not editable) to avoid symlink issues
RUN uv sync --frozen --no-dev --no-install-project && \
    uv pip install --no-deps ./packages/telemetry/

# Stage 2: Runtime - Minimal production image
FROM --platform=linux/amd64 python:3.12-slim AS runtime

# Install security updates and curl for health checks
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ /app/app/

# Copy local packages
COPY packages/ /app/packages/

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Environment variables (overridable at runtime)
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    DEBUG=false \
    HOST=0.0.0.0 \
    PORT=8080

# Expose port (Cloud Run expects 8080 by default)
EXPOSE 8080

# Health check (using curl for better performance)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application with uvicorn
# Note: Cloud Run manages scaling, so we use a single worker
# Multi-worker setup causes issues with 512MB memory limit
# Use shell form to allow environment variable expansion for PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
