"""
Check if there are any active match confirmations
"""
import os
import sys
import django

# Add parent directory to Python path so Django can find the settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from asgiref.sync import sync_to_async
import asyncio

async def check_confirmations():
    print("Checking match confirmations...")
    
    def get_confirmations():
        return list(MatchConfirmation.objects.filter(
            status='pending'
        ).select_related('match'))
    
    confirmations = await sync_to_async(get_confirmations)()
    
    print(f"Found {len(confirmations)} active match confirmations")
    
    for conf in confirmations:
        print(f"\nConfirmation {conf.id}:")
        print(f"  Match ID: {conf.match.id}")
        print(f"  Status: {conf.status}")
        print(f"  Created: {conf.created_at}")
        print(f"  Players: {conf.matched_players}")
        print(f"  Lobbies: {conf.matched_lobbies}")
    
    # Check if you're in any confirmations
    you = Player.objects.filter(username__icontains='evisc').first()
    if you:
        your_confirmations = [c for c in confirmations if str(you.puuid) in c.matched_players]
        if your_confirmations:
            print(f"\n✅ You are in {len(your_confirmations)} match confirmations!")
            for conf in your_confirmations:
                print(f"  - Confirmation {conf.id} (Match {conf.match.id})")
        else:
            print(f"\n❌ You are not in any match confirmations")

if __name__ == '__main__':
    asyncio.run(check_confirmations())
