"""
Application settings and configuration.
Now reads from config.json file with environment variable override support.
"""
import os
from app.config_loader import get_config

# Load config from file
_config = get_config()

# Django backend settings (from config, with env var override)
DJANGO_API_URL = os.getenv("DJANGO_API_URL", _config["django"]["api_url"])
DJANGO_WS_URL = os.getenv("DJANGO_WS_URL", _config["django"]["ws_url"])

# Server settings (from config, with env var override)
HOST = os.getenv("HOST", _config["client"]["host"])
PORT = int(os.getenv("PORT", str(_config["client"]["port"])))
DEBUG = os.getenv("DEBUG", str(_config["client"]["debug"])).lower() == "true"

# CORS settings
CORS_ORIGIN = os.getenv("CORS_ORIGIN", _config["cors"]["origin"])

# Heartbeat settings
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", str(_config["heartbeat"]["interval"])))

# Timeouts
PLAYER_MODEL_TIMEOUT = int(os.getenv("PLAYER_MODEL_TIMEOUT", str(_config["timeouts"]["player_model"])))
LOBBY_CREATION_TIMEOUT = int(os.getenv("LOBBY_CREATION_TIMEOUT", str(_config["timeouts"]["lobby_creation"])))

# Expose environment for debugging
ENVIRONMENT = _config.get("environment", "development")

