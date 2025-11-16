import logging
from datetime import timedelta
from typing import Dict, List

from django.utils import timezone
from asgiref.sync import sync_to_async

from match_system.models import Match, VetoAction
from ..constants import VETO_TIMEOUT_SECONDS, AVAILABLE_MAPS

logger = logging.getLogger(__name__)


async def process_veto(match: Match, map_name: str, vetoing_team: str, player_puuid: str) -> Dict:
    if match.state != Match.STATE_MAP_VETO:
        return {'status': 'error', 'message': 'Match is not in map veto phase'}

    if match.veto_turn != vetoing_team:
        return {'status': 'error', 'message': 'Not your turn to veto'}

    if map_name not in match.map_pool or map_name in match.vetoed_maps:
        return {'status': 'error', 'message': 'Invalid map'}

    if vetoing_team == 'team_a' and player_puuid != match.team_a_captain_puuid:
        return {'status': 'error', 'message': 'Only team captain can veto'}
    if vetoing_team == 'team_b' and player_puuid != match.team_b_captain_puuid:
        return {'status': 'error', 'message': 'Only team captain can veto'}

    match.vetoed_maps.append(map_name)

    sequence_number = len(match.vetoed_maps)
    await sync_to_async(VetoAction.objects.create, thread_sensitive=False)(
        match=match,
        action_type=VetoAction.ACTION_BAN,
        map_name=map_name,
        team=vetoing_team,
        player_puuid=player_puuid,
        sequence_number=sequence_number,
        was_timeout=False,
    )

    logger.info(f"Match {match.id}: {vetoing_team} vetoed {map_name}")

    remaining_maps = match.get_remaining_maps()

    if len(remaining_maps) == 1:
        match.final_map = remaining_maps[0]
        match.state = Match.STATE_SIDE_SELECTION
        match.side_selector = 'team_b' if vetoing_team == 'team_a' else 'team_a'
        match.veto_turn = None
        match.veto_deadline = None
        match.side_selection_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)

        await sync_to_async(match.save, thread_sensitive=False)(
            update_fields=[
                'vetoed_maps',
                'final_map',
                'state',
                'side_selector',
                'side_selection_deadline',
                'veto_turn',
                'veto_deadline',
            ]
        )

        return {
            'status': 'success',
            'veto_complete': True,
            'final_map': match.final_map,
            'side_selector': match.side_selector,
            'side_selection_deadline': match.side_selection_deadline.isoformat()
            if match.side_selection_deadline
            else None,
            'map_name': map_name,
            'vetoed_by': vetoing_team,
        }

    next_turn = 'team_b' if vetoing_team == 'team_a' else 'team_a'
    match.veto_turn = next_turn
    match.veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)

    await sync_to_async(match.save, thread_sensitive=False)(
        update_fields=['vetoed_maps', 'veto_turn', 'veto_deadline']
    )

    return {
        'status': 'success',
        'veto_complete': False,
        'map_name': map_name,
        'vetoed_by': vetoing_team,
        'next_turn': next_turn,
        'remaining_maps': remaining_maps,
        'deadline': match.veto_deadline.isoformat(),
    }


def handle_timeout(match_id: str, broadcast_callback) -> Dict:
    from match_system.models import Match  # local import

    try:
        match = Match.objects.get(id=match_id)

        if match.state != Match.STATE_MAP_VETO:
            return {'status': 'error', 'message': 'Not in veto phase'}

        remaining_maps = match.get_remaining_maps()
        if not remaining_maps:
            return {'status': 'error', 'message': 'No maps available'}

        auto_map = remaining_maps[0]
        current_team = match.veto_turn

        match.vetoed_maps.append(auto_map)

        sequence_number = len(match.vetoed_maps)
        VetoAction.objects.create(
            match=match,
            action_type=VetoAction.ACTION_TIMEOUT,
            map_name=auto_map,
            team=current_team,
            player_puuid=None,
            sequence_number=sequence_number,
            was_timeout=True,
        )

        logger.warning(f"Match {match.id}: {current_team} timed out, auto-vetoed {auto_map}")

        remaining_maps = match.get_remaining_maps()

        if len(remaining_maps) == 1:
            match.final_map = remaining_maps[0]
            match.state = Match.STATE_SIDE_SELECTION
            match.side_selector = 'team_b' if current_team == 'team_a' else 'team_a'
            match.veto_turn = None
            match.veto_deadline = None
            match.side_selection_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)
            match.save(
                update_fields=[
                    'vetoed_maps',
                    'final_map',
                    'state',
                    'side_selector',
                    'side_selection_deadline',
                    'veto_turn',
                    'veto_deadline',
                ]
            )

            broadcast_callback(
                match_id,
                match,
                last_event='map_veto_timeout',
                event_context={
                    'auto_vetoed_map': auto_map,
                    'timed_out_team': current_team,
                    'veto_complete': True,
                },
            )

            return {
                'status': 'success',
                'auto_vetoed_map': auto_map,
                'veto_complete': True,
                'final_map': match.final_map,
                'side_selector': match.side_selector,
                'side_selection_deadline': match.side_selection_deadline.isoformat()
                if match.side_selection_deadline
                else None,
            }

        next_turn = 'team_b' if current_team == 'team_a' else 'team_a'
        match.veto_turn = next_turn
        match.veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)
        match.save(update_fields=['vetoed_maps', 'veto_turn', 'veto_deadline'])

        broadcast_callback(
            match_id,
            match,
            last_event='map_veto_timeout',
            event_context={
                'auto_vetoed_map': auto_map,
                'timed_out_team': current_team,
                'veto_complete': False,
            },
        )

        remaining_maps = match.get_remaining_maps()
        return {
            'status': 'success',
            'auto_vetoed_map': auto_map,
            'veto_complete': False,
            'next_turn': next_turn,
            'remaining_maps': remaining_maps,
            'deadline': match.veto_deadline.isoformat(),
        }

    except Match.DoesNotExist:
        logger.error(f"Match {match_id} not found")
        return {'status': 'error', 'message': f'Match {match_id} not found'}
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error handling map veto timeout for match {match_id}: {exc}")
        return {'status': 'error', 'message': str(exc)}

