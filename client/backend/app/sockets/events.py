"""
Event registry for WebSocket handlers.
Provides decorator-based event registration.
"""
from typing import Callable, Awaitable, Dict

# Type alias for handler functions
Handler = Callable[[dict, int, "Websocket", "ConnectionManager"], Awaitable[None]]

# Global registry
registry: Dict[str, Handler] = {}

def on(event: str):
    """
    Decorator to register a handler for a specific event.
    
    Usage:
        @on("get_status")
        async def handle_get_status(payload, client_id, ws, mgr):
            # handler logic
    """
    def wrapper(fn: Handler):
        registry[event] = fn
        print(f"[REGISTRY] Registered handler for '{event}'")
        return fn
    return wrapper

def get_handler(event: str) -> Handler | None:
    """Get a handler for a specific event."""
    return registry.get(event)

