from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scrimgg.settings")

# Initialize Django for shared tasks that need models
import django
django.setup()

# Create the Celery application instance.
app = Celery("scrimgg")

# Configure Celery using Django's settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from installed Django apps.
app.autodiscover_tasks()

