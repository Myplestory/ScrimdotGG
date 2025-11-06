"""
Application settings and configuration.
"""
import os

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5888"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# CORS settings
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")

# Django backend settings
DJANGO_WS_URL = os.getenv("DJANGO_WS_URL", "ws://localhost:8000/ws/matchmaking/")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://127.0.0.1:8000")

# Heartbeat settings
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "3"))

# Timeouts
PLAYER_MODEL_TIMEOUT = int(os.getenv("PLAYER_MODEL_TIMEOUT", "5"))
LOBBY_CREATION_TIMEOUT = int(os.getenv("LOBBY_CREATION_TIMEOUT", "5"))

