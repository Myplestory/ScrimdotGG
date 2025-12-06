# Multi-stage Dockerfile for ScrimGG Django Application
# This Dockerfile can be used for Django server, Celery worker, and Celery beat

FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --upgrade pip && \
    pip install pipenv

# Set work directory
WORKDIR /app

# Copy Pipfile files
COPY Pipfile Pipfile.lock ./

# Install Python dependencies
# Using --system installs directly to system Python (better for Docker)
# Install from Pipfile (lock file may be out of date)
RUN pipenv install --system --skip-lock

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs media static

# Copy and set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["pipenv", "run", "daphne", "-b", "0.0.0.0", "-p", "8000", "scrimgg.asgi:application"]

