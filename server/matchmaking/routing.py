from django.urls import re_path
from .consumers import PugSocketConsumer

websocket_urlpatterns = [
    re_path(r'ws/matchmaking/(?P<puuid>[^/]+)/$', PugSocketConsumer.as_asgi()),
]
