import logging
from datetime import timedelta
from typing import Dict, List

from django.utils import timezone
from asgiref.sync import sync_to_async, async_to_sync

from match_system.models import Match, VetoAction
from ..constants import VETO_TIMEOUT_SECONDS, AVAILABLE_SERVERS, AVAILABLE_MAPS

logger = logging.getLogger(__name__)


async def start_phase(match: Match) -> Dict:
    starting_team = 'team_a' if match.team_a_avg_mmr >= match.team_b_avg_mmr else 'team_b'

    if not match.server_pool:
        match.server_pool = AVAILABLE_SERVERS.copy()

    match.state = Match.STATE_SERVER_VETO
    match.vetoed_servers = []
    match.server_veto_turn = starting_team
    match.server_veto_started_at = timezone.now()
    match.server_veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)

    await sync_to_async(match.save, thread_sensitive=False)(
        update_fields=[
            'state',
            'server_pool',
            'vetoed_servers',
            'server_veto_turn',
            'server_veto_started_at',
            'server_veto_deadline',
        ]
    )

    logger.info(f"Match {match.id}: Server veto started, {starting_team} bans first")

    return {
        'status': 'success',
        'match_id': str(match.id),
        'current_turn': starting_team,
        'available_servers': match.server_pool,
        'deadline': match.server_veto_deadline.isoformat(),
    }


async def process_veto(match: Match, server_name: str, vetoing_team: str, player_puuid: str) -> Dict:
    if match.state != Match.STATE_SERVER_VETO:
        return {'status': 'error', 'message': 'Match is not in server veto phase'}

    if match.server_veto_turn != vetoing_team:
        return {'status': 'error', 'message': 'Not your turn to veto'}

    if server_name not in match.server_pool or server_name in match.vetoed_servers:
        return {'status': 'error', 'message': 'Invalid server selection'}

    if vetoing_team == 'team_a' and player_puuid != match.team_a_captain_puuid:
        return {'status': 'error', 'message': 'Only team captain can veto'}
    if vetoing_team == 'team_b' and player_puuid != match.team_b_captain_puuid:
        return {'status': 'error', 'message': 'Only team captain can veto'}

    match.vetoed_servers.append(server_name)

    sequence_number = len(match.vetoed_servers)
    await sync_to_async(VetoAction.objects.create, thread_sensitive=False)(
        match=match,
        action_type=VetoAction.ACTION_SERVER_VETO,
        map_name=server_name,
        team=vetoing_team,
        player_puuid=player_puuid,
        sequence_number=sequence_number,
        was_timeout=False,
    )

    logger.info(f"Match {match.id}: {vetoing_team} vetoed server {server_name}")

    remaining_servers = [s for s in match.server_pool if s not in match.vetoed_servers]

    if len(remaining_servers) == 1:
        match.final_server = remaining_servers[0]
        match.state = Match.STATE_MAP_VETO
        if not match.map_pool:
            match.map_pool = AVAILABLE_MAPS.copy()
        match.vetoed_maps = []
        match.veto_turn = 'team_b' if vetoing_team == 'team_a' else 'team_a'
        match.server_veto_turn = None
        match.server_veto_deadline = None
        match.veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)

        await sync_to_async(match.save, thread_sensitive=False)(
            update_fields=[
                'vetoed_servers',
                'final_server',
                'state',
                'map_pool',
                'vetoed_maps',
                'veto_turn',
                'server_veto_turn',
                'server_veto_deadline',
                'veto_deadline',
            ]
        )

        return {
            'status': 'success',
            'server_veto_complete': True,
            'vetoed_server': server_name,
            'final_server': match.final_server,
            'map_veto_started': True,
            'current_turn': match.veto_turn,
            'available_maps': match.map_pool,
            'veto_deadline': match.veto_deadline.isoformat(),
        }

    next_turn = 'team_b' if vetoing_team == 'team_a' else 'team_a'
    match.server_veto_turn = next_turn
    match.server_veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)

    await sync_to_async(match.save, thread_sensitive=False)(
        update_fields=['vetoed_servers', 'server_veto_turn', 'server_veto_deadline']
    )

    return {
        'status': 'success',
        'server_veto_complete': False,
        'vetoed_server': server_name,
        'next_turn': next_turn,
        'remaining_servers': remaining_servers,
        'deadline': match.server_veto_deadline.isoformat(),
    }


def handle_timeout(match_id: str, broadcast_callback) -> Dict:
    """
    Handle server veto timeout synchronously.

    Args:
        match_id: Match UUID
        broadcast_callback: Callable[[str, Match, str, Dict], None] used to emit snapshots
    """
    from match_system.models import Match  # local import to avoid cycles

    try:
        match = Match.objects.get(id=match_id)

        if match.state != Match.STATE_SERVER_VETO:
            return {'status': 'error', 'message': 'Not in server veto phase'}

        remaining_servers = [s for s in match.server_pool if s not in match.vetoed_servers]

        if not remaining_servers:
            return {'status': 'error', 'message': 'No servers remaining'}

        auto_server = remaining_servers[0]
        current_team = match.server_veto_turn

        match.vetoed_servers.append(auto_server)

        sequence_number = len(match.vetoed_servers)
        VetoAction.objects.create(
            match=match,
            action_type=VetoAction.ACTION_TIMEOUT,
            map_name=auto_server,
            team=current_team,
            player_puuid=None,
            sequence_number=sequence_number,
            was_timeout=True,
        )

        logger.warning(
            f"Match {match.id}: {current_team} timed out, auto-vetoed server {auto_server}"
        )

        remaining_servers = [s for s in match.server_pool if s not in match.vetoed_servers]

        if len(remaining_servers) == 1:
            match.final_server = remaining_servers[0]
            match.state = Match.STATE_MAP_VETO
            if not match.map_pool:
                match.map_pool = AVAILABLE_MAPS.copy()
            match.vetoed_maps = []
            match.veto_turn = 'team_b' if current_team == 'team_a' else 'team_a'
            match.server_veto_turn = None
            match.server_veto_deadline = None
            match.veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)
            match.save(
                update_fields=[
                    'vetoed_servers',
                    'final_server',
                    'state',
                    'map_pool',
                    'vetoed_maps',
                    'veto_turn',
                    'server_veto_turn',
                    'server_veto_deadline',
                    'veto_deadline',
                ]
            )

            broadcast_callback(
                match_id,
                match,
                last_event='server_veto_timeout',
                event_context={
                    'auto_vetoed_server': auto_server,
                    'timed_out_team': current_team,
                    'server_veto_complete': True,
                },
            )

            return {
                'status': 'success',
                'was_timeout': True,
                'server_veto_complete': True,
                'auto_vetoed_server': auto_server,
                'final_server': match.final_server,
                'map_veto_started': True,
                'current_turn': match.veto_turn,
                'available_maps': match.map_pool,
                'veto_deadline': match.veto_deadline.isoformat(),
            }

        next_turn = 'team_b' if current_team == 'team_a' else 'team_a'
        match.server_veto_turn = next_turn
        match.server_veto_deadline = timezone.now() + timedelta(seconds=VETO_TIMEOUT_SECONDS)
        match.save(update_fields=['vetoed_servers', 'server_veto_turn', 'server_veto_deadline'])

        broadcast_callback(
            match_id,
            match,
            last_event='server_veto_timeout',
            event_context={
                'auto_vetoed_server': auto_server,
                'timed_out_team': current_team,
                'server_veto_complete': False,
            },
        )

        remaining_servers = [s for s in match.server_pool if s not in match.vetoed_servers]
        return {
            'status': 'success',
            'was_timeout': True,
            'server_veto_complete': False,
            'auto_vetoed_server': auto_server,
            'next_turn': next_turn,
            'remaining_servers': remaining_servers,
            'deadline': match.server_veto_deadline.isoformat(),
        }

    except Match.DoesNotExist:
        logger.error(f"Match {match_id} not found")
        return {'status': 'error', 'message': f'Match {match_id} not found'}
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error handling server veto timeout for match {match_id}: {exc}")
        return {'status': 'error', 'message': str(exc)}

