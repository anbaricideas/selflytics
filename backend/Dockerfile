# Multi-stage Dockerfile for Selflytics FastAPI application
# Security: Digest-pinned images, non-root user, minimal attack surface
# Optimization: Layer caching, multi-stage build

# Build-time arguments for metadata and multi-architecture support
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown
ARG TARGETPLATFORM=linux/amd64

# Stage 1: Builder - Install dependencies
# IMPORTANT: Digest-pinned for reproducible builds and supply chain security
FROM --platform=${TARGETPLATFORM} python:3.12-slim@sha256:d86b4c74b936c438cd4cc3a9f7256b9a7c27ad68c7caf8c205e18d9845af0164 AS builder

# Install uv for fast dependency management (pinned version)
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:08f409e1d53e77dfb5b65c788491f8ca70fe1d2d459f41c89afa2fcbef998abe /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files (least frequently changed - better layer caching)
COPY pyproject.toml uv.lock ./

# Copy workspace packages (needed for uv workspace resolution)
COPY packages/ ./packages/

# Install dependencies to a virtual environment
# Note: uv needs packages/ for workspace dependencies, even with --no-install-project
# Then install workspace packages as regular packages (not editable) to avoid symlink issues
RUN uv sync --frozen --no-dev --no-install-project && \
    uv pip install --no-deps ./packages/telemetry/

# Stage 2: Runtime - Minimal production image
FROM --platform=${TARGETPLATFORM} python:3.12-slim@sha256:d86b4c74b936c438cd4cc3a9f7256b9a7c27ad68c7caf8c205e18d9845af0164 AS runtime

# Metadata labels (OCI standard)
LABEL org.opencontainers.image.title="Selflytics API" \
      org.opencontainers.image.description="AI-powered analysis for quantified self data" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.source="https://github.com/anbaricideas/selflytics" \
      org.opencontainers.image.vendor="Selflytics" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.created="${BUILD_DATE}"

# Install security updates (provides latest security patches)
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder (includes all dependencies)
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ /app/app/

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

# Health check for local development (Cloud Run uses its own health check system)
# Note: Cloud Run ignores Dockerfile HEALTHCHECK - configure in Terraform instead
# This is only used for local docker run testing
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"]

# Run application with uvicorn
# Note: Cloud Run manages scaling, so we use a single worker
# Multi-worker setup causes issues with 512MB memory limit
# Use exec form for proper signal handling (SIGTERM for graceful shutdown)
CMD ["/bin/sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
