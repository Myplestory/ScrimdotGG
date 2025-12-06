#!/bin/bash
# Entrypoint script for Docker containers
# Handles migrations and starts the appropriate service

set -e

# Debug: Check if DATABASE_URL is set (for troubleshooting)
echo "DEBUG: DATABASE_URL is ${DATABASE_URL:+set} ${DATABASE_URL:-not set}"
echo "DEBUG: REDIS_URL is ${REDIS_URL:+set} ${REDIS_URL:-not set}"
echo "DEBUG: CELERY_BROKER_URL is ${CELERY_BROKER_URL:+set} ${CELERY_BROKER_URL:-not set}"

# Wait for PostgreSQL only if using hostname-based connection (not DATABASE_URL)
# In production (ECS), DATABASE_URL is set from AWS Secrets Manager
if [ -z "$DATABASE_URL" ]; then
  echo "Waiting for PostgreSQL..."
  while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
    sleep 0.1
  done
  echo "PostgreSQL is up!"
else
  echo "Using DATABASE_URL for PostgreSQL connection (production mode)"
fi

# Wait for Redis only if using hostname-based connection (not REDIS_URL/CELERY_BROKER_URL)
# In production (ECS), REDIS_URL/CELERY_BROKER_URL is set from AWS Secrets Manager
if [ -z "$REDIS_URL" ] && [ -z "$CELERY_BROKER_URL" ]; then
  echo "Waiting for Redis..."
  while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    sleep 0.1
  done
  echo "Redis is up!"
else
  echo "Using REDIS_URL/CELERY_BROKER_URL for Redis connection (production mode)"
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
if [ "$COLLECT_STATIC" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Execute the command passed to the container
exec "$@"


