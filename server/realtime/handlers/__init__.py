"""
WebSocket event handlers organized by domain.
"""

from .base import BaseHandler
from .lobby_handler import LobbyHandler
from .match_handler import MatchHandler
from .veto_handler import VetoHandler
from .execution_handler import ExecutionHandler

__all__ = [
    'BaseHandler',
    'LobbyHandler',
    'MatchHandler',
    'VetoHandler',
    'ExecutionHandler'
]

