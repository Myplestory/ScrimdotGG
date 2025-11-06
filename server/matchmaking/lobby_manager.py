"""
Lobby Manager Service
Handles all lobby lifecycle operations for PUG matchmaking system.
"""

from django.apps import apps
from django.db.models import Avg, Min, Max
from django.utils import timezone
from asgiref.sync import sync_to_async
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class LobbyManager:
    """
    Manages lobby lifecycle and operations.
    Every player (even solo) is part of a lobby for consistent matchmaking.
    """
    
    MAX_LOBBY_SIZE = 5
    MIN_MAP_SELECTIONS = 5
    
    @staticmethod
    async def create_lobby(player_puuid: str) -> Dict:
        """
        Create a new lobby with player as leader.
        
        Args:
            player_puuid: PUUID of the player creating the lobby
            
        Returns:
            Dict containing lobby data and status
        """
        try:
            Player = apps.get_model('scrimgg', 'Player')
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            # Get player
            player = await sync_to_async(Player.objects.get)(puuid=player_puuid)
            logger.info(f"Creating lobby for player: {player.alias} ({player_puuid})")
            
            # Check if player already has an active lobby
            def get_existing_lobby():
                return Lobby.objects.select_related('lobby_leader').filter(
                    players=player, 
                    is_active=True
                ).first()
            
            existing_lobby = await sync_to_async(get_existing_lobby)()
            
            if existing_lobby:
                logger.info(f"Player already in lobby {existing_lobby.id}")
                # Return existing lobby
                lobby_data = await LobbyManager._serialize_lobby(existing_lobby)
                return {
                    'status': 'success',
                    'message': 'Player already in lobby',
                    'lobby': lobby_data
                }
            
            # Create new lobby
            lobby = await sync_to_async(Lobby.objects.create)(
                lobby_leader=player,
                size=1,
                average_elo=player.elo,
                elo_range={'min': player.elo, 'max': player.elo}
            )
            
            # Add player to lobby
            await sync_to_async(lobby.players.add)(player)
            await sync_to_async(lobby.save)()
            
            logger.info(f"Lobby created: {lobby.id} with leader {player.alias}")
            
            lobby_data = await LobbyManager._serialize_lobby(lobby)
            return {
                'status': 'success',
                'message': 'Lobby created successfully',
                'lobby': lobby_data
            }
            
        except Exception as e:
            logger.error(f"Error creating lobby: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to create lobby: {str(e)}'
            }
    
    @staticmethod
    async def add_player_to_lobby(lobby_id: str, player_puuid: str, inviter_puuid: Optional[str] = None) -> Dict:
        """
        Add a player to an existing lobby (via invite).
        
        Args:
            lobby_id: UUID of the lobby
            player_puuid: PUUID of player to add
            inviter_puuid: PUUID of player sending invite (must be leader or member)
            
        Returns:
            Dict containing updated lobby data and status
        """
        try:
            Player = apps.get_model('scrimgg', 'Player')
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            # Get lobby with leader pre-loaded
            def get_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id, is_active=True)
            
            lobby = await sync_to_async(get_lobby)()
            
            # Check if lobby is full
            if lobby.size >= LobbyManager.MAX_LOBBY_SIZE:
                return {
                    'status': 'error',
                    'message': 'Lobby is full'
                }
            
            # Check if lobby is in queue (can't add players while in queue)
            if lobby.in_queue:
                return {
                    'status': 'error',
                    'message': 'Cannot add players while lobby is in queue'
                }
            
            # Get player to add
            player = await sync_to_async(Player.objects.get)(puuid=player_puuid)
            
            # Check if player is already in lobby
            player_in_lobby = await sync_to_async(
                lambda: lobby.players.filter(pk=player.pk).exists()
            )()
            
            if player_in_lobby:
                return {
                    'status': 'error',
                    'message': 'Player already in lobby'
                }
            
            # Check if player is in another active lobby
            existing_lobby = await sync_to_async(
                lambda: Lobby.objects.filter(
                    players=player,
                    is_active=True
                ).exclude(id=lobby_id).first()
            )()
            
            if existing_lobby:
                return {
                    'status': 'error',
                    'message': 'Player is already in another lobby'
                }
            
            # Add player to lobby
            await sync_to_async(lobby.players.add)(player)
            
            # Refetch lobby with relationships to get fresh data
            def refetch_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
            
            lobby = await sync_to_async(refetch_lobby)()
            
            # Update lobby stats
            await LobbyManager._update_lobby_stats(lobby)
            
            logger.info(f"Player {player.alias} added to lobby {lobby_id}")
            
            lobby_data = await LobbyManager._serialize_lobby(lobby)
            return {
                'status': 'success',
                'message': 'Player added to lobby',
                'lobby': lobby_data
            }
            
        except Exception as e:
            logger.error(f"Error adding player to lobby: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to add player: {str(e)}'
            }
    
    @staticmethod
    async def remove_player_from_lobby(lobby_id: str, player_puuid: str, kicked_by: Optional[str] = None) -> Dict:
        """
        Remove a player from lobby (kick or leave).
        If leader leaves, lobby is disbanded or leadership transferred.
        
        Args:
            lobby_id: UUID of the lobby
            player_puuid: PUUID of player to remove
            kicked_by: PUUID of player kicking (None if player is leaving voluntarily)
            
        Returns:
            Dict containing status and updated lobby data (if lobby still exists)
        """
        try:
            Player = apps.get_model('scrimgg', 'Player')
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            # Get lobby with leader pre-loaded
            def get_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id, is_active=True)
            
            lobby = await sync_to_async(get_lobby)()
            
            # Get player
            player = await sync_to_async(Player.objects.get)(puuid=player_puuid)
            
            # If kicked_by is provided, verify they have permission
            if kicked_by:
                if lobby.lobby_leader and lobby.lobby_leader.puuid != kicked_by:
                    return {
                        'status': 'error',
                        'message': 'Only the lobby leader can kick players'
                    }
                
                # Can't kick yourself
                if kicked_by == player_puuid:
                    return {
                        'status': 'error',
                        'message': 'Use leave_lobby to leave the lobby'
                    }
            
            # Remove player from lobby
            await sync_to_async(lobby.players.remove)(player)
            
            # Refetch lobby with relationships to get fresh data
            def refetch_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
            
            lobby = await sync_to_async(refetch_lobby)()
            
            is_leader = lobby.lobby_leader and lobby.lobby_leader.puuid == player_puuid
            
            # Get remaining player count
            def get_count():
                return lobby.players.count()
            
            remaining_players = await sync_to_async(get_count)()
            
            logger.info(f"Player {player.alias} removed from lobby {lobby_id}. Remaining: {remaining_players}")
            
            # If no players left, disband lobby
            if remaining_players == 0:
                await LobbyManager.disband_lobby(lobby_id)
                return {
                    'status': 'success',
                    'message': 'Player left lobby. Lobby disbanded (no players remaining)',
                    'lobby_disbanded': True
                }
            
            # If leader left, transfer leadership to next player
            if is_leader:
                new_leader = await sync_to_async(lambda: lobby.players.first())()
                lobby.lobby_leader = new_leader
                await sync_to_async(lobby.save)()
                logger.info(f"Leadership transferred to {new_leader.alias}")
            
            # Update lobby stats
            await LobbyManager._update_lobby_stats(lobby)
            
            lobby_data = await LobbyManager._serialize_lobby(lobby)
            return {
                'status': 'success',
                'message': 'Player removed from lobby',
                'lobby': lobby_data,
                'lobby_disbanded': False
            }
            
        except Exception as e:
            logger.error(f"Error removing player from lobby: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to remove player: {str(e)}'
            }
    
    @staticmethod
    async def disband_lobby(lobby_id: str) -> Dict:
        """
        Disband a lobby (mark as inactive).
        
        Args:
            lobby_id: UUID of the lobby to disband
            
        Returns:
            Dict containing status
        """
        try:
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            lobby = await sync_to_async(Lobby.objects.get)(id=lobby_id)
            lobby.is_active = False
            lobby.in_queue = False
            await sync_to_async(lobby.save)()
            
            logger.info(f"Lobby {lobby_id} disbanded")
            
            return {
                'status': 'success',
                'message': 'Lobby disbanded'
            }
            
        except Exception as e:
            logger.error(f"Error disbanding lobby: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to disband lobby: {str(e)}'
            }
    
    @staticmethod
    async def update_lobby_preferences(lobby_id: str, map_preferences: List[str] = None, 
                                      server_preferences: List[str] = None, 
                                      requester_puuid: str = None) -> Dict:
        """
        Update lobby matchmaking preferences (maps and servers).
        Only lobby leader can update preferences.
        
        Args:
            lobby_id: UUID of the lobby
            map_preferences: List of preferred map names
            server_preferences: List of preferred server names
            requester_puuid: PUUID of player making the request
            
        Returns:
            Dict containing status and updated lobby data
        """
        try:
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            # Get lobby with leader pre-loaded
            def get_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id, is_active=True)
            
            lobby = await sync_to_async(get_lobby)()
            
            # Verify requester is lobby leader
            if requester_puuid and lobby.lobby_leader and lobby.lobby_leader.puuid != requester_puuid:
                return {
                    'status': 'error',
                    'message': 'Only the lobby leader can update preferences'
                }
            
            # Update preferences
            if map_preferences is not None:
                lobby.map_preferences = map_preferences
            if server_preferences is not None:
                lobby.server_preferences = server_preferences
            
            await sync_to_async(lobby.save)()
            
            # Refetch lobby with relationships to get fresh data
            def refetch_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
            
            lobby = await sync_to_async(refetch_lobby)()
            
            logger.info(f"Lobby {lobby_id} preferences updated")
            
            lobby_data = await LobbyManager._serialize_lobby(lobby)
            return {
                'status': 'success',
                'message': 'Preferences updated',
                'lobby': lobby_data
            }
            
        except Exception as e:
            logger.error(f"Error updating lobby preferences: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to update preferences: {str(e)}'
            }
    
    @staticmethod
    async def validate_queue_eligibility(lobby_id: str) -> Dict:
        """
        Validate if lobby can join matchmaking queue.
        
        Requirements:
        - At least MIN_MAP_SELECTIONS maps selected
        - Lobby not already in queue
        - Lobby is active
        
        Args:
            lobby_id: UUID of the lobby
            
        Returns:
            Dict with eligibility status and reason if not eligible
        """
        try:
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            lobby = await sync_to_async(Lobby.objects.get)(id=lobby_id)
            
            if not lobby.is_active:
                return {
                    'eligible': False,
                    'reason': 'Lobby is not active'
                }
            
            if lobby.in_queue:
                return {
                    'eligible': False,
                    'reason': 'Lobby is already in queue'
                }
            
            if len(lobby.map_preferences) < LobbyManager.MIN_MAP_SELECTIONS:
                return {
                    'eligible': False,
                    'reason': f'Must select at least {LobbyManager.MIN_MAP_SELECTIONS} maps'
                }
            
            if lobby.size < 1:
                return {
                    'eligible': False,
                    'reason': 'Lobby has no players'
                }
            
            return {
                'eligible': True,
                'reason': None
            }
            
        except Exception as e:
            logger.error(f"Error validating queue eligibility: {str(e)}")
            return {
                'eligible': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    @staticmethod
    async def _update_lobby_stats(lobby) -> None:
        """
        Update lobby statistics (average ELO, ELO range, size).
        
        Args:
            lobby: Lobby model instance
        """
        # Get player stats asynchronously
        def get_stats():
            return lobby.players.aggregate(
                avg_elo=Avg('elo'),
                min_elo=Min('elo'),
                max_elo=Max('elo'),
            )
        
        stats = await sync_to_async(get_stats)()
        
        # Get player count
        def get_count():
            return lobby.players.count()
        
        lobby.size = await sync_to_async(get_count)()
        lobby.average_elo = stats['avg_elo'] or 0.0
        lobby.elo_range = {
            'min': stats['min_elo'] or 0,
            'max': stats['max_elo'] or 0
        }
        
        await sync_to_async(lobby.save)()
        
        logger.debug(f"Lobby {lobby.id} stats updated: size={lobby.size}, avg_elo={lobby.average_elo:.2f}")
    
    @staticmethod
    async def _serialize_lobby(lobby) -> Dict:
        """
        Serialize lobby to dictionary for API responses.
        
        Args:
            lobby: Lobby model instance
            
        Returns:
            Dict containing lobby data
        """
        # Fetch players asynchronously
        def get_players():
            return list(lobby.players.all())
        
        players = await sync_to_async(get_players)()
        
        # Fetch lobby leader data safely (in case it needs DB access)
        leader_data = None
        if lobby.lobby_leader:
            def get_leader_data():
                return {
                    'puuid': lobby.lobby_leader.puuid,
                    'alias': lobby.lobby_leader.alias,
                    'elo': lobby.lobby_leader.elo
                }
            leader_data = await sync_to_async(get_leader_data)()
        
        return {
            'id': str(lobby.id),
            'lobby_leader': leader_data,
            'players': [{
                'puuid': p.puuid,
                'alias': p.alias,
                'elo': p.elo,
                'mmr': p.mmr,  # Add MMR
                'rank': p.rank,
            } for p in players],
            'size': lobby.size,
            'max_size': lobby.max_size,
            'average_elo': lobby.average_elo,
            'average_mmr': sum(p.mmr for p in players) / len(players) if players else 0,  # Add average MMR
            'elo_range': lobby.elo_range,
            'is_active': lobby.is_active,
            'in_queue': lobby.in_queue,
            'queue_type': lobby.queue_type,
            'map_preferences': lobby.map_preferences,
            'server_preferences': lobby.server_preferences,
            'created_at': lobby.created_at.isoformat() if lobby.created_at else None,
            'queued_at': lobby.queued_at.isoformat() if lobby.queued_at else None,
        }
    
    @staticmethod
    async def get_lobby_by_player(player_puuid: str) -> Optional[Dict]:
        """
        Get active lobby for a player.
        
        Args:
            player_puuid: PUUID of the player
            
        Returns:
            Lobby data dict or None if player not in active lobby
        """
        try:
            Player = apps.get_model('scrimgg', 'Player')
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            player = await sync_to_async(Player.objects.get)(puuid=player_puuid)
            
            def get_lobby():
                return Lobby.objects.select_related('lobby_leader').filter(
                    players=player,
                    is_active=True
                ).first()
            
            lobby = await sync_to_async(get_lobby)()
            
            if not lobby:
                return None
            
            return await LobbyManager._serialize_lobby(lobby)
            
        except Exception as e:
            logger.error(f"Error getting lobby by player: {str(e)}")
            return None

