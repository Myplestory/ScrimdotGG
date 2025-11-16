"""
Placeholder module for lobby construction phase.
Detailed implementation will be added when constructor flow is wired.
"""
from typing import Dict
from match_system.models import Match


async def start(match: Match) -> Dict:
    return {'status': 'not_implemented'}


async def handle_constructor_ack(match: Match, payload: Dict) -> Dict:
    return {'status': 'not_implemented'}


def handle_timeout(match_id: str, broadcast_callback) -> Dict:
    return {'status': 'not_implemented'}

