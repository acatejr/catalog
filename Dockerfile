# Build stage - includes build tools and compilers
FROM python:3.14-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Install only runtime dependencies in the venv (no dev/test packages)
# Using psycopg2-binary means we don't need libpq-dev at runtime
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage - minimal image
FROM python:3.14-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory and copy application code
WORKDIR /app
COPY src/ /app/src/
COPY data/ /app/data/

# Use the virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/src

# Don't write .pyc files and run in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

