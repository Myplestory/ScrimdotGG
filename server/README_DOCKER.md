# Docker Setup for ScrimGG

This directory contains Docker configuration files for containerizing and deploying the ScrimGG Django application.

## Files Overview

- **Dockerfile**: Main Docker image for Django, Celery worker, and Celery beat
- **docker-compose.yml**: Local development setup with all services
- **docker-compose.prod.yml**: Production configuration (reference)
- **.dockerignore**: Files to exclude from Docker builds
- **entrypoint.sh**: Container startup script that handles migrations
- **settings_production.py**: Production settings using environment variables

## Quick Start (Local Development)

### Prerequisites
- Docker and Docker Compose installed
- Ports 8000, 5432, 6379 available

### Start All Services

```bash
cd server
docker-compose up --build
```

This will start:
- PostgreSQL database (port 5432)
- Valkey (Redis-compatible, port 6379)
- Django/Daphne server (port 8000)
- Celery worker
- Celery beat scheduler

### Access Services

- Django API: http://localhost:8000
- PostgreSQL: localhost:5432
- Valkey: localhost:6379

### Stop Services

```bash
docker-compose down
```

To remove volumes (database data):

```bash
docker-compose down -v
```

## Production Deployment

### Environment Variables

Set these environment variables in your production environment:

```bash
# Django
DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Valkey (Redis-compatible)
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/0
CHANNEL_LAYERS_REDIS=redis://host:6379/1

# Optional
STATIC_URL=/static/
MEDIA_URL=/media/
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Using Production Settings

In production, you can either:

1. **Use environment variables** - The `settings_production.py` reads from environment variables
2. **Override settings module** - Set `DJANGO_SETTINGS_MODULE=scrimgg.settings_production`

### Build and Run Production Image

```bash
# Build
docker build -t scrimgg-django:latest .

# Run Django server
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e DJANGO_SECRET_KEY=... \
  -e DEBUG=False \
  -e ALLOWED_HOSTS=yourdomain.com \
  --name scrimgg-django \
  scrimgg-django:latest

# Run Celery worker
docker run -d \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e DJANGO_SECRET_KEY=... \
  --name scrimgg-celery-worker \
  scrimgg-django:latest \
  pipenv run celery -A scrimgg worker --loglevel=info --pool=gevent -Q celery,matchmaking,cleanup

# Run Celery beat
docker run -d \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e DJANGO_SECRET_KEY=... \
  --name scrimgg-celery-beat \
  scrimgg-django:latest \
  pipenv run celery -A scrimgg beat --loglevel=info
```

## Cloud Platform Deployment

### AWS (ECS/Fargate)

1. Build and push to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t scrimgg-django .
docker tag scrimgg-django:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/scrimgg-django:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/scrimgg-django:latest
```

2. Create ECS task definitions for:
   - Django server
   - Celery worker
   - Celery beat

3. Use managed services:
   - RDS for PostgreSQL
   - ElastiCache for Redis

### Railway

1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Railway will auto-detect Docker and deploy

### Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `cd server && docker build -t app .`
4. Set start command: `docker run -p $PORT:8000 app`
5. Add PostgreSQL and Redis services
6. Set environment variables

### DigitalOcean App Platform

1. Create new app from GitHub
2. Select Docker
3. Add PostgreSQL and Redis components
4. Set environment variables
5. Configure build and run commands

## CircleCI Integration

The `.circleci/config.yml` file is configured to:

1. **Test**: Run Django tests with PostgreSQL and Redis
2. **Build**: Create Docker images
3. **Deploy**: Push to cloud platform (AWS ECR/ECS example included)

### CircleCI Environment Variables

Set these in CircleCI project settings:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `AWS_ECR_ACCOUNT_URL`
- `DATABASE_URL` (for tests)
- `DJANGO_SECRET_KEY` (for tests)

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running and accessible
- Check `DATABASE_URL` format: `postgresql://user:password@host:port/dbname`
- Verify network connectivity between containers

### Valkey/Redis Connection Issues

- Ensure Valkey/Redis is running
- Check `REDIS_URL` format: `redis://host:port/db` (works with both Redis and Valkey)
- Verify Valkey/Redis is accessible from Django container

### Static Files Not Loading

- Run `python manage.py collectstatic` before starting server
- Set `COLLECT_STATIC=true` environment variable
- Ensure `STATIC_ROOT` is writable

### WebSocket Issues

- Ensure load balancer supports WebSocket connections
- Check `CHANNEL_LAYERS_REDIS` configuration
- Verify Valkey/Redis is accessible for Channels

## Notes

- The entrypoint script automatically runs migrations on container start
- Static files are collected during build (can be overridden)
- Logs are written to `/app/logs` directory
- Media files are stored in `/app/media` directory
- Use managed PostgreSQL and Valkey/Redis in production for better reliability
- Note: Connection strings use `redis://` protocol which is compatible with both Redis and Valkey


