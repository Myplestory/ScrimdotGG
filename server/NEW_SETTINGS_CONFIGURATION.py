"""
Updated INSTALLED_APPS configuration for refactored architecture.

ADD TO: scrimgg/settings.py

IMPORTANT: Order matters for migrations!
- Core should come first (no dependencies)
- match_system before match_execution (execution depends on match_system models)
- realtime after all domain apps (imports from them)
"""

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'channels',
    
    # Core utilities (no dependencies)
    'core',
    
    # Main domain apps
    'scrimgg',
    'users',
    'riotlogin',
    
    # Matchmaking system
    'lobby',                # Enhanced with lobby_manager
    'matchmaking',          # Queue + Matchmaker only
    'match_system',         # NEW: Post-acceptance match flow
    'match_execution',      # NEW: Live game management
    
    # Realtime communication (depends on all above)
    'realtime',            # NEW: WebSocket layer
    
    # Legacy/utility apps
    'maps',
    'match',               # Legacy - consider deprecating
]

# Updated Celery task routing
CELERY_TASK_ROUTES = {
    # Matchmaking tasks
    'matchmaking.tasks.periodic_matchmaking': {'queue': 'matchmaking'},
    'matchmaking.tasks.cleanup_expired_queues': {'queue': 'cleanup'},
    
    # Match system tasks
    'match_system.tasks.cleanup_expired_matches': {'queue': 'cleanup'},
    'match_system.tasks.check_veto_timeouts': {'queue': 'match_system'},
    
    # Default queue for everything else
    '*': {'queue': 'celery'},
}

# Updated Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'periodic-matchmaking': {
        'task': 'matchmaking.tasks.periodic_matchmaking',
        'schedule': 10.0,  # Run every 10 seconds
    },
    'cleanup-expired-matches': {
        'task': 'match_system.tasks.cleanup_expired_matches',  # NEW location
        'schedule': 10.0,
    },
    'cleanup-expired-queues': {
        'task': 'matchmaking.tasks.cleanup_expired_queues',
        'schedule': 300.0,
    },
    'check-veto-timeouts': {
        'task': 'match_system.tasks.check_veto_timeouts',  # NEW location
        'schedule': 3.0,
    },
}

