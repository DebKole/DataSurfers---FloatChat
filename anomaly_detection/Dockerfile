# Multi-stage Dockerfile for Argo Anomaly Detection System

# Stage 1: Builder
FROM python:3.9-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgeos-c1v5 \
    libproj22 \
    libspatialindex6 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p artifacts/{models,polygons,scalers,results} logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port for API
EXPOSE 8000

# Default command
CMD ["python", "scripts/run_full_pipeline.py"]
