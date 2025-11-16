"""
Execution phase manager.

Handles constructor election, custom game creation, join tracking, and live-state
transitions while keeping the unified match snapshot in sync.
"""

import asyncio
import logging
from typing import Dict

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.utils import timezone

from match_system.models import Match, MatchPlayer
logger = logging.getLogger(__name__)


class ExecutionPhaseManager:
    """
    Coordinates everything that happens after side selection completes.
    """

    JOIN_TIMEOUT_SECONDS = 300  # 5 minutes

    # ------------------------------------------------------------------ #
    # Constructor election & kickoff                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def initiate_match_start(match_id: str) -> Dict:
        """Pick a constructor and inform every client that the match is starting."""
        from match_system.managers.match_manager import MatchManager

        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)

            logger.info(
                "ExecutionPhaseManager: initiating constructor flow | match=%s state=%s final_map=%s final_server=%s",
                match_id,
                match.state,
                match.final_map,
                match.final_server,
            )

            if not match.final_map:
                logger.warning(
                    "ExecutionPhaseManager: cannot start constructor flow, final map missing | match=%s",
                    match_id,
                )
                return {'status': 'error', 'message': 'No final map selected'}
            if not match.final_server:
                logger.warning(
                    "ExecutionPhaseManager: cannot start constructor flow, final server missing | match=%s",
                    match_id,
                )
                return {'status': 'error', 'message': 'No final server selected'}

            constructor = ExecutionPhaseManager._select_constructor_from_match(match)
            match.constructor_puuid = constructor['puuid']
            match.state = Match.STATE_CREATING
            match.pregame_id = None
            match.coregame_id = None
            await sync_to_async(match.save)(
                update_fields=['constructor_puuid', 'state', 'pregame_id', 'coregame_id']
            )

            # Refresh match from DB to ensure snapshot has latest data (especially constructor_puuid)
            match = await sync_to_async(lambda: Match.objects.get(id=match.id), thread_sensitive=False)()

            await MatchManager.broadcast_match_state(
                str(match.id),
                match=match,
                last_event='match_construction_started',
                event_context={'constructor_puuid': constructor['puuid']},
            )

            await ExecutionPhaseManager._broadcast_construction_started(
                match, constructor
            )

            logger.info(
                "Match %s: constructor %s assigned, notifying players",
                match_id,
                constructor['puuid'],
            )

            return {
                'status': 'success',
                'match_id': str(match.id),
                'constructor_puuid': constructor['puuid'],
            }
        except Match.DoesNotExist:
            logger.error("Match %s not found when starting execution", match_id)
            return {'status': 'error', 'message': 'Match not found'}
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error initiating match start for %s: %s", match_id, exc)
            return {'status': 'error', 'message': str(exc)}

    @staticmethod
    def _select_constructor_from_match(match: Match) -> Dict:
        """Prefer the Team A captain, otherwise pick the highest ELO on Team A."""
        team_a_players = match.team_a_players or []

        captain = next(
            (p for p in team_a_players if p.get('puuid') == match.team_a_captain_puuid),
            None,
        )
        if captain:
            logger.info(
                "ExecutionPhaseManager: constructor selected (captain) | match=%s puuid=%s alias=%s",
                match.id,
                captain.get('puuid'),
                captain.get('alias'),
            )
            return {
                'puuid': captain.get('puuid'),
                'alias': captain.get('alias', 'Unknown'),
                'team': 'team_a',
            }

        if team_a_players:
            constructor = max(team_a_players, key=lambda p: p.get('elo', 0) or 0)
            logger.info(
                "ExecutionPhaseManager: constructor selected (fallback highest elo) | match=%s puuid=%s alias=%s",
                match.id,
                constructor.get('puuid'),
                constructor.get('alias'),
            )
            return {
                'puuid': constructor.get('puuid'),
                'alias': constructor.get('alias', 'Unknown'),
                'team': 'team_a',
            }

        raise ValueError("Unable to determine constructor for match")

    @staticmethod
    async def _broadcast_construction_started(match: Match, constructor: Dict) -> None:
        """Send targeted match_construction_started events to every player."""
        channel_layer = get_channel_layer()
        team_a_players = match.team_a_players or []
        team_b_players = match.team_b_players or []
        team_a_puuids = [p['puuid'] for p in team_a_players]

        for player in team_a_players + team_b_players:
            puuid = player['puuid']
            team = 'team_a' if puuid in team_a_puuids else 'team_b'
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'match_construction_started',
                    'match_id': str(match.id),
                    'constructor_puuid': constructor['puuid'],
                    'is_constructor': puuid == constructor['puuid'],
                    'map': match.final_map,
                    'server': match.final_server,
                    'team': team,
                },
            )

    # ------------------------------------------------------------------ #
    # Custom game creation & join flow                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def handle_custom_game_created(
        match_id: str, pregame_id: str, constructor_puuid: str
    ) -> Dict:
        """Constructor reports a new custom game; notify everyone else to join."""
        from match_system.managers.match_manager import MatchManager

        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)

            logger.info(
                "ExecutionPhaseManager: received custom_game_created | match=%s constructor=%s pregame_id=%s",
                match_id,
                constructor_puuid,
                pregame_id,
            )

            match.pregame_id = pregame_id
            match.state = Match.STATE_READY
            await sync_to_async(match.save)(update_fields=['pregame_id', 'state'])

            await MatchManager.broadcast_match_state(
                str(match.id),
                match=match,
                last_event='custom_game_created',
                event_context={'pregame_id': pregame_id},
            )

            await ExecutionPhaseManager._broadcast_join_custom_game(
                match, pregame_id, constructor_puuid
            )

            asyncio.create_task(ExecutionPhaseManager._join_timeout_task(match_id))

            logger.info(
                "ExecutionPhaseManager: join phase started | match=%s constructor=%s pregame_id=%s",
                match_id,
                constructor_puuid,
                pregame_id,
            )

            return {'status': 'success', 'pregame_id': pregame_id}
        except Match.DoesNotExist:
            logger.error("Match %s not found for custom game creation", match_id)
            return {'status': 'error', 'message': 'Match not found'}
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception(
                "Error handling custom game creation for %s: %s", match_id, exc
            )
            return {'status': 'error', 'message': str(exc)}

    @staticmethod
    async def _broadcast_join_custom_game(
        match: Match, pregame_id: str, constructor_puuid: str
    ) -> None:
        """Send join_custom_game to every non-constructor player."""
        channel_layer = get_channel_layer()
        team_a_players = match.team_a_players or []
        team_b_players = match.team_b_players or []
        team_a_puuids = [p['puuid'] for p in team_a_players]

        for player in team_a_players + team_b_players:
            puuid = player['puuid']
            if puuid == constructor_puuid:
                continue

            team = 'team_a' if puuid in team_a_puuids else 'team_b'
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'join_custom_game',
                    'match_id': str(match.id),
                    'pregame_id': pregame_id,
                    'team': team,
                },
            )

    @staticmethod
    async def _join_timeout_task(match_id: str) -> None:
        """Cancel the match if not everyone joins within JOIN_TIMEOUT_SECONDS."""
        from match_system.managers.match_manager import MatchManager

        await asyncio.sleep(ExecutionPhaseManager.JOIN_TIMEOUT_SECONDS)
        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)
        except Match.DoesNotExist:
            return

        logger.warning(
            "ExecutionPhaseManager: join timeout check fired | match=%s state=%s",
            match_id,
            match.state,
        )

        if match.state not in (Match.STATE_READY, Match.STATE_CREATING):
            return

        joined_count = await sync_to_async(
            lambda: MatchPlayer.objects.filter(match=match, joined_pregame=True).count()
        )()
        total_players = len(match.get_all_player_puuids())

        if joined_count >= total_players:
            return

        match.state = Match.STATE_CANCELLED
        match.game_ended_at = timezone.now()
        await sync_to_async(match.save)(update_fields=['state', 'game_ended_at'])

        await MatchManager.broadcast_match_state(
            str(match.id),
            match=match,
            last_event='match_cancelled',
            event_context={'reason': 'join_timeout'},
        )

        await ExecutionPhaseManager._broadcast_match_cancelled(
            match, reason='join_timeout'
        )

        logger.warning(
            "ExecutionPhaseManager: match cancelled due to join timeout | match=%s joined=%s total=%s",
            match_id,
            joined_count,
            total_players,
        )

    @staticmethod
    async def _broadcast_match_cancelled(match: Match, reason: str) -> None:
        """Notify every player that the match has been cancelled."""
        channel_layer = get_channel_layer()
        for puuid in match.get_all_player_puuids():
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'match_cancelled',
                    'match_id': str(match.id),
                    'reason': reason,
                },
            )

    # ------------------------------------------------------------------ #
    # Join tracking                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def handle_player_joined(match_id: str, player_puuid: str) -> Dict:
        """Record that a player successfully joined and emit an updated snapshot."""
        from match_system.managers.match_manager import MatchManager

        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)

            logger.info(
                "ExecutionPhaseManager: received player_joined event | match=%s player=%s",
                match_id,
                player_puuid,
            )

            match_player = await ExecutionPhaseManager._get_or_create_match_player(
                match, player_puuid
            )

            if not match_player.joined_pregame:
                await sync_to_async(match_player.mark_joined)()

            joined_count = await sync_to_async(
                lambda: MatchPlayer.objects.filter(
                    match=match, joined_pregame=True
                ).count()
            )()
            total_players = len(match.get_all_player_puuids())
            all_joined = joined_count >= total_players

            await MatchManager.broadcast_match_state(
                str(match.id),
                match=match,
                last_event='player_joined',
                event_context={
                    'player_puuid': player_puuid,
                    'joined_count': joined_count,
                    'total_players': total_players,
                },
            )

            if all_joined:
                await ExecutionPhaseManager._notify_constructor_all_joined(match)

            logger.info(
                "Match %s: player %s joined (%s/%s)",
                match_id,
                player_puuid,
                joined_count,
                total_players,
            )

            return {
                'status': 'success',
                'match_id': str(match.id),
                'player_puuid': player_puuid,
                'joined_count': joined_count,
                'total_players': total_players,
                'all_joined': all_joined,
            }
        except Match.DoesNotExist:
            logger.error("Match %s not found for player join", match_id)
            return {'status': 'error', 'message': 'Match not found'}
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error handling player join for %s: %s", match_id, exc)
            return {'status': 'error', 'message': str(exc)}

    @staticmethod
    async def _get_or_create_match_player(match: Match, player_puuid: str) -> MatchPlayer:
        """Ensure we have a MatchPlayer row for the given player."""

        def get_player():
            try:
                return MatchPlayer.objects.get(match=match, player_puuid=player_puuid)
            except MatchPlayer.DoesNotExist:
                team = match.get_player_team(player_puuid) or 'team_a'
                return MatchPlayer.objects.create(
                    match=match,
                    player_puuid=player_puuid,
                    player_alias=player_puuid[:8],
                    player_elo=0,
                    player_mmr=0.0,
                    team=team,
                )

        return await sync_to_async(get_player)()

    @staticmethod
    async def _notify_constructor_all_joined(match: Match) -> None:
        """Tell the constructor everyone is in; clients use this to start the match."""
        constructor_puuid = match.constructor_puuid
        if not constructor_puuid:
            return

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"player_{constructor_puuid}",
            {
                'type': 'all_players_joined',
                'match_id': str(match.id),
                'is_constructor': True,
            },
        )

        logger.info(
            "ExecutionPhaseManager: all players joined | match=%s constructor=%s",
            match.id,
            constructor_puuid,
        )

    # ------------------------------------------------------------------ #
    # Live match lifecycle                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def handle_match_started(match_id: str, coregame_id: str) -> Dict:
        """Constructor reports that the match has gone live."""
        from match_system.managers.match_manager import MatchManager

        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)

            logger.info(
                "ExecutionPhaseManager: received match_started event | match=%s coregame_id=%s",
                match_id,
                coregame_id,
            )

            match.coregame_id = coregame_id
            match.state = Match.STATE_IN_PROGRESS
            match.game_started_at = timezone.now()
            await sync_to_async(match.save)(
                update_fields=['coregame_id', 'state', 'game_started_at']
            )

            await MatchManager.broadcast_match_state(
                str(match.id),
                match=match,
                last_event='match_started',
                event_context={'coregame_id': coregame_id},
            )

            await ExecutionPhaseManager._broadcast_match_in_progress(match)

            logger.info("Match %s: now in progress (%s)", match_id, coregame_id)
            return {'status': 'success'}
        except Match.DoesNotExist:
            logger.error("Match %s not found when marking in progress", match_id)
            return {'status': 'error', 'message': 'Match not found'}
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error handling match start for %s: %s", match_id, exc)
            return {'status': 'error', 'message': str(exc)}

    @staticmethod
    async def _broadcast_match_in_progress(match: Match) -> None:
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"match_{match.id}",
            {
                'type': 'match_in_progress',
                'match_id': str(match.id),
                'coregame_id': match.coregame_id,
                'map': match.final_map,
                'server': match.final_server,
            },
        )

    @staticmethod
    async def handle_match_completion(match_id: str, final_data: Dict) -> Dict:
        """Match finished – store the outcome and notify everyone."""
        from match_system.managers.match_manager import MatchManager

        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)

            logger.info(
                "ExecutionPhaseManager: received match_completed event | match=%s payload=%s",
                match_id,
                final_data,
            )

            match.state = Match.STATE_COMPLETED
            match.game_ended_at = timezone.now()
            match.team_a_score = final_data.get('team_a_score', match.team_a_score)
            match.team_b_score = final_data.get('team_b_score', match.team_b_score)
            await sync_to_async(match.save)(
                update_fields=['state', 'game_ended_at', 'team_a_score', 'team_b_score']
            )

            await MatchManager.broadcast_match_state(
                str(match.id),
                match=match,
                last_event='match_completed',
                event_context={
                    'team_a_score': match.team_a_score,
                    'team_b_score': match.team_b_score,
                },
            )

            await ExecutionPhaseManager._broadcast_match_completed(match, final_data)
            logger.info(
                "ExecutionPhaseManager: final scores broadcast | match=%s team_a=%s team_b=%s",
                match_id,
                match.team_a_score,
                match.team_b_score,
            )
            return {'status': 'success'}
        except Match.DoesNotExist:
            logger.error("Match %s not found on completion", match_id)
            return {'status': 'error', 'message': 'Match not found'}
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error completing match %s: %s", match_id, exc)
            return {'status': 'error', 'message': str(exc)}

    @staticmethod
    async def _broadcast_match_completed(match: Match, final_data: Dict) -> None:
        channel_layer = get_channel_layer()
        winner = None
        if match.team_a_score > match.team_b_score:
            winner = 'team_a'
        elif match.team_b_score > match.team_a_score:
            winner = 'team_b'

        await channel_layer.group_send(
            f"match_{match.id}",
            {
                'type': 'match_completed',
                'match_id': str(match.id),
                'team_a_score': match.team_a_score,
                'team_b_score': match.team_b_score,
                'winner': winner,
                'final_data': final_data,
            },
        )

    # ------------------------------------------------------------------ #
    # Rejoin tokens (planned)                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def generate_rejoin_token(match_id: str, player_puuid: str) -> str:
        raise NotImplementedError("Rejoin tokens not yet implemented for match_system")

    @staticmethod
    async def validate_rejoin_token(token: str) -> Dict:
        raise NotImplementedError("Rejoin tokens not yet implemented for match_system")


