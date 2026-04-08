"""
Async facade over ValorantAPI.
Provides clean async interface for handlers.
"""
import sys
import os
import asyncio
import random
import json

# Add parent directory to path to import clientapi
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from clientapi import ValorantAPI
import psutil
from valclient import Client
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ValorantService:
    def __init__(self):
        self.api = ValorantAPI()
    
    @property
    def pugsocket(self):
        """Expose pugsocket for pending events."""
        return self.api.pugsocket
    
    async def check_status(self):
        """Check if Valorant is running."""
        try:
            if self.api is None:
                return {
                    'status': 'not_running',
                    'message': 'Valorant API not initialized',
                    'details': None
                }
            
            # Check for VALORANT.exe process
            valorant_process_found = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'VALORANT' in proc.info['name'].upper():
                        valorant_process_found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check Riot Client connection
            temp_client = Client(region='na')
            try:
                temp_client.activate()
                
                if valorant_process_found:
                    is_authenticated = (self.api.client is not None and 
                                      hasattr(self.api.client, 'puuid') and 
                                      self.api.client.puuid is not None)
                    
                    return {
                        'status': 'running',
                        'message': 'Valorant game is running and ready',
                        'details': {
                            'region': temp_client.region,
                            'is_authenticated': is_authenticated
                        }
                    }
                else:
                    return {
                        'status': 'riot_only',
                        'message': 'Valorant not launched',
                        'details': {'region': temp_client.region}
                    }
            except Exception:
                return {
                    'status': 'not_running',
                    'message': 'Riot Client is not running',
                    'details': None
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking status: {str(e)}',
                'details': None
            }
    
    async def login(self, region: str):
        """Login to Valorant."""
        return await self.api.login(region)
    
    async def get_player_model(self):
        """Get player model from Django."""
        return await self.api.get_player_model()
    
    async def create_lobby(self):
        """Create a lobby."""
        return await self.api.createlobby()
    
    async def create_custom_game(self, match_id: str, map_name: str, server: str, team: str = None):
        """
        Constructor creates custom game in Valorant.
        Runs in background task to avoid blocking.
        """
        # Run in background task
        asyncio.create_task(self._create_custom_game_impl(match_id, map_name, server, team))
    
    async def _create_custom_game_impl(self, match_id: str, map_name: str, server: str, team: str = None):
        """
        Internal implementation of custom game creation.
        """
        try:
            if not self.api.client:
                logger.error("[CREATE_CUSTOM_GAME] Client not initialized")
                return
            
            logger.info(f"[CREATE_CUSTOM_GAME] Starting custom game creation for match {match_id}")
            logger.info(f"[CREATE_CUSTOM_GAME] Map: {map_name}, Server: {server}")
            
            # Mark this client as constructor
            self.api.is_constructor = True
            self.api.current_match_id = match_id
            
            # Change party to custom mode
            logger.info("[CREATE_CUSTOM_GAME] Changing to custom game mode...")
            custom_response = self.api.client.party_change_to_custom()
            pregame_id = custom_response.get('ID')
            
            if not pregame_id:
                raise ValueError("Failed to get pregame ID from custom game creation")
            
            logger.info(f"[CREATE_CUSTOM_GAME] Got pregame_id: {pregame_id}")
            
            # Track the pregame_id we're sending
            self.api.sent_pregame_id = pregame_id
            logger.info(f"[VALIDATION] Constructor tracking sent pregame_id: {pregame_id[:8]}")
            
            # Set custom game settings
            logger.info("[CREATE_CUSTOM_GAME] Configuring game settings...")
            
            # Get map UUID from args
            map_uuid = None
            if self.api.args and 'mapPreferences' in self.api.args:
                map_uuid = self.api.args['mapPreferences'].get(map_name.lower())
            
            if not map_uuid:
                raise ValueError(f"Map UUID not found for map: {map_name}")
            
            # Get server GamePod URL
            game_pod = self.api._get_server_url(server)
            if not game_pod:
                raise ValueError(f"Server GamePod not found for server: {server}")
            
            settings = {
                "Map": map_uuid,
                "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
                "GamePod": game_pod,
                "UseBots": False,
                "GameRules": {
                    "AllowGameModifiers": "true",
                    "PlayOutAllRounds": "true",
                    "SkipMatchHistory": "false",
                    "TournamentMode": "false",
                    "IsOvertimeWinByTwo": "true",
                },
            }
            
            logger.info(f"[CREATE_CUSTOM_GAME] Settings: {json.dumps(settings, indent=2)}")
            self.api.client.party_set_custom_game_settings(settings)
            logger.info("[CREATE_CUSTOM_GAME] Settings applied successfully")
            
            # Wait a moment for settings to apply
            await asyncio.sleep(2)
            
            # VALIDATION: Before notifying server, ensure we have a valid pregame_id
            if not self.api._validate_pregame_id(pregame_id, 'custom_game_creation', match_id):
                logger.error(
                    f"[VALIDATION] Failed validation before notifying server, "
                    "but proceeding with notification"
                )
            
            # Notify Django server via WebSocket
            logger.info(f"[CREATE_CUSTOM_GAME] Notifying server of custom game creation: {pregame_id}")
            if self.api.pugsocket:
                await self.api.pugsocket.send_message('custom_game_created', {
                    'match_id': match_id,
                    'pregame_id': pregame_id,
                    'constructor_puuid': self.api.client.puuid
                })
                logger.info("[CREATE_CUSTOM_GAME] Successfully notified server")
            else:
                logger.error("[CREATE_CUSTOM_GAME] PugSocket not connected, cannot notify server")
            
            # CRITICAL: Constructor must send player_joined_game so server counts it in joined_players
            # Without this, server will only see 9/10 joined (missing constructor)
            await asyncio.sleep(random.uniform(0.3, 0.8))  # Small delay before reporting join
            logger.info(f"[CREATE_CUSTOM_GAME] Constructor reporting self as joined (team: {team or 'unknown'})")
            if self.api.pugsocket:
                # If team not provided, try to determine from latest_match_state
                if not team and self.api.latest_match_state:
                    try:
                        team_a_players = self.api.latest_match_state.get('team_a_players', [])
                        team_b_players = self.api.latest_match_state.get('team_b_players', [])
                        if any(p.get('puuid') == self.api.client.puuid for p in team_a_players):
                            team = 'team_a'
                        elif any(p.get('puuid') == self.api.client.puuid for p in team_b_players):
                            team = 'team_b'
                    except Exception as e:
                        logger.warning(f"[CREATE_CUSTOM_GAME] Could not determine team from snapshot: {e}")
                
                # Default to team_a if still unknown
                if not team:
                    team = 'team_a'
                
                await self.api.pugsocket.send_message('player_joined_game', {
                    'match_id': match_id,
                    'player_puuid': self.api.client.puuid,
                    'team': team
                })
                logger.info("[CREATE_CUSTOM_GAME] Successfully reported constructor as joined")
            
            # Store the game creation data for when all players join
            self.api._pending_game_start = {
                'match_id': match_id,
                'pregame_id': pregame_id,
                'settings_applied': True
            }
            
            logger.info("[CREATE_CUSTOM_GAME] Waiting for all players to join before starting game...")
            
        except Exception as e:
            logger.exception(f"[CREATE_CUSTOM_GAME] Error creating custom game: {str(e)}")
            # Reset validation state on error
            self.api.reset_pregame_validation()
            # Notify server of failure
            if self.api.pugsocket:
                try:
                    await self.api.pugsocket.send_message('custom_game_created', {
                        'match_id': match_id,
                        'pregame_id': None,
                        'constructor_puuid': self.api.client.puuid if self.api.client else None,
                        'error': str(e)
                    })
                except Exception as notify_error:
                    logger.error(f"[CREATE_CUSTOM_GAME] Failed to notify server of error: {notify_error}")
    
    async def start_custom_game(self, match_id: str):
        """
        Constructor starts the custom game when all players have joined.
        """
        if not hasattr(self.api, '_pending_game_start') or not self.api._pending_game_start:
            logger.warning(f"[START_CUSTOM_GAME] No pending game start data found for match {match_id}")
            return
        
        game_data = self.api._pending_game_start
        pregame_id = game_data.get('pregame_id')
        
        logger.info(f"[START_CUSTOM_GAME] All players joined match {match_id}, constructor starting game...")
        
        # VALIDATION: Before starting game, verify pregame_id is still valid
        # Get actual pregame_id from Valorant
        try:
            current_pregame = self.api.client.pregame_fetch_player()
            actual_pregame_id = current_pregame.get('MatchID')
            
            if not self.api._validate_pregame_id(actual_pregame_id, 'match_start', match_id):
                logger.error(
                    f"[VALIDATION] Cannot start game - pregame_id mismatch. "
                    f"Expected: {self.api.sent_pregame_id[:8] if self.api.sent_pregame_id else 'None'}, "
                    f"Actual: {actual_pregame_id[:8] if actual_pregame_id else 'None'}. "
                    "Aborting game start."
                )
                return
                
        except Exception as e:
            logger.warning(f"[VALIDATION] Could not verify pregame_id before start: {e}")
            # Continue anyway, but log warning
        
        logger.info("All players ready - starting game now...")
        try:
            # Start the custom game
            self.api.client.party_start_custom_game()
            
            # Get coregame ID after match starts
            await asyncio.sleep(5)  # Wait for game to start
            coregame_data = self.api.client.coregame_fetch_player()
            coregame_id = coregame_data.get('MatchID')
            
            if coregame_id:
                # Notify Django that match is live
                await self.api.pugsocket.send_message('match_started', {
                    'match_id': match_id,
                    'coregame_id': coregame_id
                })
                
                # Start monitoring the match
                asyncio.create_task(self.api.monitor_match(match_id, coregame_id))
                
                logger.info(f"Match {match_id} started successfully with coregame {coregame_id}")
            else:
                logger.error(f"Failed to get coregame ID for match {match_id}")
            
            # Clear pending game start data
            self.api._pending_game_start = None
            
        except Exception as e:
            logger.exception(f"Error starting game: {str(e)}")

