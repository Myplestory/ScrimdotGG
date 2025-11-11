import logging
from datetime import timedelta
from typing import Dict

from django.utils import timezone
from asgiref.sync import sync_to_async

from match_system.models import Match
from ..constants import VETO_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


async def process_selection(match: Match, side: str, team: str, player_puuid: str) -> Dict:
    if match.state != Match.STATE_SIDE_SELECTION:
        return {'status': 'error', 'message': 'Match is not in side selection phase'}

    if match.side_selector != team:
        return {'status': 'error', 'message': 'Not your turn to select a side'}

    if team == 'team_a' and player_puuid != match.team_a_captain_puuid:
        return {'status': 'error', 'message': 'Only team captain can pick side'}
    if team == 'team_b' and player_puuid != match.team_b_captain_puuid:
        return {'status': 'error', 'message': 'Only team captain can pick side'}

    if side not in ['attack', 'defense']:
        return {'status': 'error', 'message': 'Invalid side selection'}

    match.selected_side = side
    match.side_selection_deadline = None
    match.state = Match.STATE_READY

    await sync_to_async(match.save, thread_sensitive=False)(
        update_fields=['selected_side', 'side_selection_deadline', 'state']
    )

    logger.info(f"Match {match.id}: {team} selected {side}")

    return {
        'status': 'success',
        'side': side,
        'selected_by': team,
        'side_complete': True,
    }


def handle_timeout(match_id: str, broadcast_callback) -> Dict:
    from match_system.models import Match  # local import

    try:
        match = Match.objects.get(id=match_id)

        if match.state != Match.STATE_SIDE_SELECTION:
            return {'status': 'error', 'message': 'Not in side selection phase'}

        auto_side = 'attack'
        match.selected_side = auto_side
        match.state = Match.STATE_READY
        match.side_selection_deadline = None
        match.save(update_fields=['selected_side', 'state', 'side_selection_deadline'])

        logger.warning(
            f"Match {match.id}: Side selection timed out, auto selected {auto_side}"
        )

        broadcast_callback(
            match_id,
            match,
            last_event='side_selection_timeout',
            event_context={
                'auto_selected_side': auto_side,
                'side_selection_complete': True,
                'match_ready': True,
            },
        )

        return {
            'status': 'success',
            'auto_selected_side': auto_side,
            'side_selection_complete': True,
            'match_ready': True,
        }

    except Match.DoesNotExist:
        logger.error(f"Match {match_id} not found")
        return {'status': 'error', 'message': f'Match {match_id} not found'}
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error handling side selection timeout for match {match_id}: {exc}")
        return {'status': 'error', 'message': str(exc)}

