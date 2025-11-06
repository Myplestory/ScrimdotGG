"""
Check if there are any active match confirmations in Redis
"""
import os
import sys
import django

# Add parent directory to Python path so Django can find the settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player
from matchmaking.match_confirmation import MatchConfirmationManager
import asyncio

async def check_confirmations():
    print("Checking match confirmations in Redis...")
    
    # Get all active match confirmations from Redis
    confirmations = await MatchConfirmationManager.get_all_active_confirmations()
    
    print(f"Found {len(confirmations)} active match confirmations")
    
    if not confirmations:
        print("\nNo active match confirmations found.")
        print("This is normal if:")
        print("  - No matches have been found yet")
        print("  - All matches have been accepted/declined")
        print("  - Match confirmations have timed out")
        return
    
    for conf in confirmations:
        match_id = conf.get('match_id', 'Unknown')
        initiated_at = conf.get('initiated_at', 'Unknown')
        
        # Get acceptance counts
        accepting = await MatchConfirmationManager.get_accepting_players(match_id)
        non_accepting = await MatchConfirmationManager.get_non_accepting_players(match_id)
        
        print(f"\nMatch Confirmation: {match_id}")
        print(f"  Initiated: {initiated_at}")
        print(f"  Players accepted: {len(accepting)}/10")
        print(f"  Players pending: {len(non_accepting)}")
        print(f"  Accepting: {accepting[:3]}..." if len(accepting) > 3 else f"  Accepting: {accepting}")
        print(f"  Pending: {non_accepting[:3]}..." if len(non_accepting) > 3 else f"  Pending: {non_accepting}")
    
    # Check if you're in any confirmations
    def get_player():
        return Player.objects.filter(username__icontains='evisc').first()
    
    from asgiref.sync import sync_to_async
    you = await sync_to_async(get_player)()
    
    if you:
        for conf in confirmations:
            match_id = conf.get('match_id')
            accepting = await MatchConfirmationManager.get_accepting_players(match_id)
            non_accepting = await MatchConfirmationManager.get_non_accepting_players(match_id)
            
            if you.puuid in accepting:
                print(f"\n[OK] You ACCEPTED match {match_id}")
            elif you.puuid in non_accepting:
                print(f"\n[PENDING] You have NOT accepted match {match_id} yet!")
                print(f"   Accept within 30 seconds or match will be cancelled.")

if __name__ == '__main__':
    asyncio.run(check_confirmations())
