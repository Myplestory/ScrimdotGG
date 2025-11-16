import time
import logging
from typing import Dict, List, Optional

from django.utils import timezone
from asgiref.sync import sync_to_async

from match_system.models import Match, MatchPlayer, VetoAction
from ..constants import AVAILABLE_MAPS
from . import server_veto, map_veto, side_selection, construction, join, live

logger = logging.getLogger(__name__)


def _iso(dt):
    return dt.isoformat() if dt else None


def _build_public_player_stats(player_model: Optional['Player']) -> Dict:  # type: ignore
    default_stats = {
        'total_matches': 0,
        'wins': 0,
        'losses': 0,
        'win_rate': 0,
        'average_kd': 0.0,
        'recent_performance': {
            'frags': 0,
            'deaths': 0,
            'assists': 0,
        },
    }

    if not player_model:
        return default_stats

    wins = player_model.wins or 0
    losses = player_model.loss or 0
    total_matches = player_model.games_played or (wins + losses)

    win_rate = round((wins / total_matches) * 100) if total_matches else 0
    deaths = player_model.deaths or 0
    frags = player_model.frags or 0
    assists = player_model.assists or 0

    average_kd = frags / deaths if deaths else float(frags or 0)

    return {
        'total_matches': int(total_matches),
        'wins': int(wins),
        'losses': int(losses),
        'win_rate': int(win_rate),
        'average_kd': round(average_kd, 2),
        'recent_performance': {
            'frags': int(frags),
            'deaths': int(deaths),
            'assists': int(assists),
        },
    }


def _load_player_profiles(match_players: List[MatchPlayer]):
    from scrimgg.models import Player  # local import

    puuids = {player.player_puuid for player in match_players}
    if not puuids:
        return {}
    players = Player.objects.filter(puuid__in=puuids)
    return {player.puuid: player for player in players}


def _serialize_match_players(
    players: List[MatchPlayer],
    player_profiles: Optional[Dict[str, 'Player']] = None,  # type: ignore
) -> List[Dict]:
    serialized = []
    player_profiles = player_profiles or {}
    for player in players:
        stats = _build_public_player_stats(player_profiles.get(player.player_puuid))
        serialized.append({
            'puuid': player.player_puuid,
            'alias': player.player_alias,
            'elo': player.player_elo,
            'team': player.team,
            'is_captain': player.is_captain,
            'is_ready': player.is_ready,
            'joined_pregame': player.joined_pregame,
            'joined_at': _iso(player.joined_at),
            'last_seen': _iso(player.last_seen),
            'join_attempts': player.join_attempts,
            'stats': stats,
        })
    return serialized


def _serialize_veto_actions(veto_actions: List[VetoAction]) -> List[Dict]:
    serialized = []
    for action in veto_actions:
        serialized.append({
            'action_type': action.action_type,
            'map_name': action.map_name,
            'team': action.team,
            'player_puuid': action.player_puuid,
            'sequence_number': action.sequence_number,
            'was_timeout': action.was_timeout,
            'created_at': _iso(action.created_at),
        })
    return serialized


def _determine_current_phase(match: Match, remaining_servers: List[str], remaining_maps: List[str]) -> Dict:
    phase = {
        'type': match.state,
        'turn': None,
        'deadline': None,
        'remaining': [],
        'history': [],
        'final_choice': None,
        'selector': None,
    }

    if match.state == Match.STATE_SERVER_VETO:
        phase['turn'] = match.server_veto_turn
        phase['deadline'] = _iso(match.server_veto_deadline)
        phase['remaining'] = remaining_servers
        phase['history'] = match.server_veto_history or []
        phase['final_choice'] = match.final_server
    elif match.state == Match.STATE_MAP_VETO:
        phase['turn'] = match.veto_turn
        phase['deadline'] = _iso(match.veto_deadline)
        phase['remaining'] = remaining_maps
        phase['history'] = match.veto_history or []
        phase['final_choice'] = match.final_map
    elif match.state == Match.STATE_SIDE_SELECTION:
        phase['turn'] = match.side_selector
        phase['deadline'] = _iso(match.side_selection_deadline)
        if match.selected_side:
            remaining_sides = []
        else:
            remaining_sides = [side for side in ['attack', 'defense']]
        phase['remaining'] = remaining_sides
        phase['history'] = match.veto_history or []
        phase['final_choice'] = match.selected_side
        phase['selector'] = match.side_selector
    else:
        phase['turn'] = match.veto_turn or match.server_veto_turn
        phase['deadline'] = _iso(match.veto_deadline or match.server_veto_deadline)
        phase['remaining'] = remaining_maps if remaining_maps else remaining_servers
        phase['history'] = match.veto_history or match.server_veto_history or []
        phase['final_choice'] = match.final_map or match.final_server

    return phase


def _compose_veto_state(match: Match, remaining_servers: List[str], remaining_maps: List[str]) -> Dict:
    server_deadline = match.server_veto_deadline if match.state == Match.STATE_SERVER_VETO else None
    map_deadline = match.veto_deadline if match.state == Match.STATE_MAP_VETO else None
    return {
        'phase': match.state,
        'server_veto_complete': bool(match.final_server),
        'final_server': match.final_server,
        'final_map': match.final_map,
        'current_turn': match.veto_turn or match.server_veto_turn,
        'remaining_maps': remaining_maps,
        'remaining_servers': remaining_servers,
        'available_maps': match.map_pool,
        'available_servers': match.server_pool,
        'veto_deadline': _iso(map_deadline or server_deadline),
        'side_selector': match.side_selector,
        'selected_side': match.selected_side,
        'last_update': int(time.time() * 1000),
    }


async def build(
    match: Match,
    *,
    last_event: Optional[str] = None,
    event_context: Optional[Dict] = None,
) -> Dict:
    players = await sync_to_async(list, thread_sensitive=False)(
        MatchPlayer.objects.filter(match=match)
    )
    veto_actions = await sync_to_async(list, thread_sensitive=False)(
        match.veto_actions.order_by('sequence_number')
    )
    player_profiles = await sync_to_async(_load_player_profiles, thread_sensitive=False)(players)
    return _format_match_state(match, players, veto_actions, player_profiles, last_event, event_context)


def build_sync(
    match: Match,
    *,
    last_event: Optional[str] = None,
    event_context: Optional[Dict] = None,
) -> Dict:
    players = list(MatchPlayer.objects.filter(match=match))
    veto_actions = list(match.veto_actions.order_by('sequence_number'))
    player_profiles = _load_player_profiles(players)
    return _format_match_state(match, players, veto_actions, player_profiles, last_event, event_context)


def _format_match_state(
    match: Match,
    match_players: List[MatchPlayer],
    veto_actions: List[VetoAction],
    player_profiles: Dict[str, 'Player'],  # type: ignore
    last_event: Optional[str],
    event_context: Optional[Dict],
) -> Dict:
    serialized_players = _serialize_match_players(match_players, player_profiles)
    serialized_veto_history = _serialize_veto_actions(veto_actions)

    team_a_players = [p for p in serialized_players if p['team'] == 'team_a']
    team_b_players = [p for p in serialized_players if p['team'] == 'team_b']

    team_a_avg_elo = round(
        sum(p.get('elo', 0) for p in team_a_players) / len(team_a_players),
        1,
    ) if team_a_players else 0.0
    team_b_avg_elo = round(
        sum(p.get('elo', 0) for p in team_b_players) / len(team_b_players),
        1,
    ) if team_b_players else 0.0
    server_deadline = match.server_veto_deadline if match.state == Match.STATE_SERVER_VETO else None
    map_deadline = match.veto_deadline if match.state == Match.STATE_MAP_VETO else None

    remaining_servers = [s for s in match.server_pool if s not in (match.vetoed_servers or [])]
    remaining_maps = match.get_remaining_maps()

    phase = _determine_current_phase(match, remaining_servers, remaining_maps)

    draft_section = {
        'servers': {
            'pool': match.server_pool,
            'remaining': remaining_servers,
            'vetoed': match.vetoed_servers,
            'history': match.server_veto_history or [],
            'turn': match.server_veto_turn,
            'deadline': _iso(server_deadline),
            'final': match.final_server,
        },
        'maps': {
            'pool': match.map_pool,
            'remaining': remaining_maps,
            'vetoed': match.vetoed_maps,
            'history': match.veto_history or serialized_veto_history,
            'turn': match.veto_turn,
            'deadline': _iso(map_deadline),
            'final': match.final_map,
        },
        'side': {
            'selector': match.side_selector,
            'selected': match.selected_side,
            'deadline': _iso(match.side_selection_deadline),
        },
    }

    execution = {
        'state': match.state,
        'constructor': match.constructor_puuid,
        'pregame_id': match.pregame_id,
        'coregame_id': match.coregame_id,
        'server_region': match.server_region,
        'joined_players': [p['puuid'] for p in serialized_players if p['joined_pregame']],
        'ready_players': [p['puuid'] for p in serialized_players if p['is_ready']],
        'team_ready_counts': {
            'team_a': sum(1 for p in team_a_players if p['is_ready']),
            'team_b': sum(1 for p in team_b_players if p['is_ready']),
        },
        'team_joined_counts': {
            'team_a': sum(1 for p in team_a_players if p['joined_pregame']),
            'team_b': sum(1 for p in team_b_players if p['joined_pregame']),
        },
    }

    telemetry = _compose_veto_state(match, remaining_servers, remaining_maps)

    snapshot = {
        'version': int(time.time() * 1000),
        'match_id': str(match.id),
        'state': match.state,
        'phase': phase,
        'teams': {
            'team_a': {
                'captain': match.team_a_captain_puuid,
                'lobbies': match.team_a_lobbies,
                'players': team_a_players,
            },
            'team_b': {
                'captain': match.team_b_captain_puuid,
                'lobbies': match.team_b_lobbies,
                'players': team_b_players,
            },
        },
        'draft': draft_section,
        'execution': execution,
        'meta': {
            'created_at': _iso(match.created_at),
            'updated_at': _iso(match.updated_at),
            'match_quality': match.match_quality,
            'team_a_avg_elo': team_a_avg_elo,
            'team_b_avg_elo': team_b_avg_elo,
            'last_event': last_event,
            'last_event_context': event_context or {},
            'can_queue': False,
        },
        'team_a_players': team_a_players,
        'team_b_players': team_b_players,
        'team_a_captain': match.team_a_captain_puuid,
        'team_b_captain': match.team_b_captain_puuid,
        'team_a_lobbies': match.team_a_lobbies,
        'team_b_lobbies': match.team_b_lobbies,
        'team_a_avg_elo': team_a_avg_elo,
        'team_b_avg_elo': team_b_avg_elo,
        'server_pool': match.server_pool,
        'vetoed_servers': match.vetoed_servers,
        'server_veto_turn': match.server_veto_turn,
        'server_veto_deadline': _iso(server_deadline),
        'final_server': match.final_server,
        'map_pool': match.map_pool,
        'remaining_maps': remaining_maps,
        'vetoed_maps': match.vetoed_maps,
        'final_map': match.final_map,
        'veto_turn': match.veto_turn,
        'veto_deadline': _iso(map_deadline),
        'veto_history': serialized_veto_history,
        'side_selector': match.side_selector,
        'selected_side': match.selected_side,
        'side_selection_deadline': _iso(match.side_selection_deadline),
        'available_maps': remaining_maps or match.map_pool,
        'available_servers': remaining_servers or match.server_pool,
        'veto_state': telemetry,
    }

    # hook for future phases
    live.update_snapshot(match, snapshot)

    snapshot['meta']['can_queue'] = match.state in [Match.STATE_COMPLETED, Match.STATE_CANCELLED]

    return snapshot

