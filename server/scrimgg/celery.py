"""
Celery configuration for Scrim.GG
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')

app = Celery('scrimgg')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'periodic-matchmaking': {
        'task': 'matchmaking.tasks.periodic_matchmaking',
        'schedule': 10.0,  # Run every 30 seconds
    },
    'cleanup-expired-matches': {
        'task': 'matchmaking.tasks.cleanup_expired_matches',
        'schedule': 60.0,  # Run every 60 seconds
    },
    'cleanup-expired-queues': {
        'task': 'matchmaking.tasks.cleanup_expired_queues',
        'schedule': 300.0,  # Run every 5 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')