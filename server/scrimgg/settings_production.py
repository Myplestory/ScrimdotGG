"""
Production settings for ScrimGG
Import this in your production environment or use environment variables
"""
import os
from .settings import *

# Security settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', SECRET_KEY)

# Allowed hosts - set via environment variable (comma-separated)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Database - use DATABASE_URL if provided, otherwise default
if 'DATABASE_URL' in os.environ:
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.config(
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    except ImportError:
        # Fallback if dj-database-url not installed
        from urllib.parse import urlparse
        db_url = urlparse(os.environ['DATABASE_URL'])
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_url.path[1:],
                'USER': db_url.username,
                'PASSWORD': db_url.password,
                'HOST': db_url.hostname,
                'PORT': db_url.port or '5432',
            }
        }
else:
    # Fallback to PostgreSQL if DATABASE_URL not set
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'scrimgg'),
            'USER': os.getenv('DB_USER', 'scrimgg'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Channel Layers (WebSocket)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.getenv('CHANNEL_LAYERS_REDIS', REDIS_URL.replace('/0', '/1'))],
        },
    },
}

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv('REDIS_CACHE_URL', REDIS_URL.replace('/0', '/1')),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Static files - in production, use a CDN or object storage
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.getenv('STATIC_ROOT', os.path.join(BASE_DIR, 'static'))

# Media files
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ORIGIN_ALLOW_ALL = os.getenv('CORS_ORIGIN_ALLOW_ALL', 'False').lower() == 'true'

