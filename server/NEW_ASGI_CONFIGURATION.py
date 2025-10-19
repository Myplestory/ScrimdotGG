"""
Updated ASGI configuration for refactored WebSocket routing.

REPLACE: scrimgg/asgi.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import re_path

django.setup()

# UPDATED: Import from realtime app instead of matchmaking
from realtime.routing import websocket_urlpatterns 

application = ProtocolTypeRouter({
    "http": get_asgi_application(), 
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  
        )
    ),
})

