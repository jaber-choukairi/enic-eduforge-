# ── EduForge — Production Dockerfile ──────────────────────────────────────────
# Multi-stage build: builder + runtime
# Base: Python 3.10-slim (matches your local Python 3.10.10)
# Target: CPU-only (no CUDA)

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# System deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .

# Install into a prefix dir (copy to runtime stage)
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

LABEL maintainer="EduForge Team"
LABEL version="1.0.0"
LABEL description="AI-powered educational exam generation microservice"

WORKDIR /app

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r eduforge && useradd -r -g eduforge eduforge

# Copy source code
COPY --chown=eduforge:eduforge . /app

# Create data directories
RUN mkdir -p /app/data/raw /app/data/processed /app/data/models \
    && chown -R eduforge:eduforge /app/data

# Switch to non-root
USER eduforge

# Environment defaults (override at runtime)
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Default command (override in docker-compose for workers)
CMD ["uvicorn", "services.gateway.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--loop", "asyncio"]
