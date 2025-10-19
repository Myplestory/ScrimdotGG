"""
WebSocket routing configuration.

MOVED FROM: matchmaking/routing.py
"""

from django.urls import re_path
from .consumers import RealtimeConsumer

websocket_urlpatterns = [
    # Single WebSocket endpoint per player (backward compatible)
    re_path(r'ws/matchmaking/(?P<puuid>[^/]+)/$', RealtimeConsumer.as_asgi()),
    # Alternative endpoint name (cleaner naming)
    re_path(r'ws/realtime/(?P<puuid>[^/]+)/$', RealtimeConsumer.as_asgi()),
    # Legacy/simple format (for old test scripts)
    re_path(r'ws/(?P<puuid>[^/]+)/?$', RealtimeConsumer.as_asgi()),
]

