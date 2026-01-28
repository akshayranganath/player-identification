# ==============================================================================
# CFL Player Identification - Production Dockerfile
# ==============================================================================
# Build optimized Docker image for CFL player identification system
#
# Usage:
#   docker build -f infrastructure/docker/Dockerfile -t cfl-player-id:latest .
#   docker run -p 8501:8501 --env-file .env cfl-player-id:latest
# ==============================================================================

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync --frozen || uv sync

# Copy application code
COPY src/ ./src/
COPY app.py ./
COPY prompt.py ./

# Copy data files (player database)
COPY data/db/ ./data/db/

# Create directory for temporary images
RUN mkdir -p /app/temp_images

# Set Python path
ENV PYTHONPATH=/app

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
