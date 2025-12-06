"""
Configuration loader that reads from config.json file.
Falls back to environment variables, then defaults.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

def get_config_path() -> Path:
    """Get the path to config.json file."""
    # Get the backend directory (where this file is located)
    backend_dir = Path(__file__).parent.parent
    config_dir = backend_dir / "config"
    config_file = config_dir / "config.json"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # If config.json doesn't exist, create it from dev config
    if not config_file.exists():
        dev_config = config_dir / "config.dev.json"
        if dev_config.exists():
            import shutil
            shutil.copy(dev_config, config_file)
        else:
            # Create default dev config
            create_default_config(config_file)
    
    return config_file

def create_default_config(config_path: Path):
    """Create a default development config file."""
    default_config = {
        "environment": "development",
        "django": {
            "api_url": "http://127.0.0.1:8000",
            "ws_url": "ws://localhost:8000/ws/matchmaking/"
        },
        "client": {
            "host": "127.0.0.1",
            "port": 5888,
            "debug": True
        },
        "cors": {
            "origin": "http://localhost:3000"
        },
        "timeouts": {
            "player_model": 5,
            "lobby_creation": 5
        },
        "heartbeat": {
            "interval": 3
        }
    }
    
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file."""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load config file: {e}")
        print("Using default development configuration")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Return default development configuration."""
    return {
        "environment": "development",
        "django": {
            "api_url": "http://127.0.0.1:8000",
            "ws_url": "ws://localhost:8000/ws/matchmaking/"
        },
        "client": {
            "host": "127.0.0.1",
            "port": 5888,
            "debug": True
        },
        "cors": {
            "origin": "http://localhost:3000"
        },
        "timeouts": {
            "player_model": 5,
            "lobby_creation": 5
        },
        "heartbeat": {
            "interval": 3
        }
    }

# Cache the config to avoid reading file multiple times
_config_cache = None

def get_config() -> Dict[str, Any]:
    """Get cached config or load it."""
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache

def reload_config():
    """Reload config from file (clear cache)."""
    global _config_cache
    _config_cache = None
    return get_config()

