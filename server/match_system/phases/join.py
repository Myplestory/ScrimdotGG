"""
Placeholder module for player join phase.
"""
from typing import Dict
from match_system.models import Match


async def mark_joined(match: Match, player_puuid: str) -> Dict:
    return {'status': 'not_implemented'}


def handle_timeout(match_id: str, broadcast_callback) -> Dict:
    return {'status': 'not_implemented'}

