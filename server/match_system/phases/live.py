"""
Placeholder module for live match telemetry.
"""
from typing import Dict
from match_system.models import Match


async def handle_match_started(match: Match, coregame_id: str) -> Dict:
    return {'status': 'not_implemented'}


async def handle_round_summary(match: Match, round_data: Dict) -> Dict:
    return {'status': 'not_implemented'}


def update_snapshot(match: Match, snapshot: Dict) -> None:
    snapshot.setdefault('execution', {}).setdefault('live', {})

