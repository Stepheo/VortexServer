# Minimal Dockerfile for FastAPI + Uvicorn
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Avoids installing caches, reduces image size
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Copy entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENV RUN_MIGRATIONS=1 \
    WAIT_REDIS=1

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
