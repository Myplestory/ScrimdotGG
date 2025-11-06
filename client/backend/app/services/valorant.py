"""
Async facade over ValorantAPI.
Provides clean async interface for handlers.
"""
import sys
import os

# Add parent directory to path to import clientapi
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from clientapi import ValorantAPI
import psutil
from valclient import Client

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

