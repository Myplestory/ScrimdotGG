"""
Manually trigger matchmaking to test if it works
Tests both SYNC (Celery-style) and ASYNC (WebSocket-style) versions.
"""
import os
import sys
import django

# Add parent directory to Python path so Django can find the settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from matchmaking.queue_manager import QueueManager
from matchmaking.matchmaker_v2 import MatchmakerV2
import asyncio

def test_matchmaking_sync():
    """Test SYNC matchmaking (Celery-style)"""
    print("\n" + "="*60)
    print("TESTING SYNC MATCHMAKING (Celery-style)")
    print("="*60)
    
    # Check queue stats (SYNC)
    queue_stats = QueueManager.get_queue_stats_sync('pug')
    print(f"Queue stats: {queue_stats}")
    
    if queue_stats['total_lobbies'] < 2:
        print("⚠️  Not enough lobbies for matchmaking")
        return
    
    # Try to find matches manually (SYNC)
    print("\nRunning SYNC matchmaker (MatchmakerV2.find_matches_sync)...")
    try:
        result = MatchmakerV2.find_matches_sync('pug')
        print(f"\n✅ Matchmaking result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Matches found: {result.get('matches_found', 0)}")
        
        if result.get('matches_found', 0) > 0:
            for idx, match in enumerate(result.get('matches', []), 1):
                print(f"\n   Match {idx}:")
                print(f"      Quality: {match.get('match_quality', 0):.2f}")
                print(f"      Team A MMR: {match.get('team_a', {}).get('average_mmr', 0):.0f}")
                print(f"      Team B MMR: {match.get('team_b', {}).get('average_mmr', 0):.0f}")
                print(f"      Lobbies: {len(match.get('lobbies', []))}")
    except Exception as e:
        print(f"❌ Error in sync matchmaking: {e}")
        import traceback
        traceback.print_exc()

async def test_matchmaking_async():
    """Test ASYNC matchmaking (WebSocket-style)"""
    print("\n" + "="*60)
    print("TESTING ASYNC MATCHMAKING (WebSocket-style)")
    print("="*60)
    
    # Check queue stats (ASYNC)
    queue_stats = await QueueManager.get_queue_stats('pug')
    print(f"Queue stats: {queue_stats}")
    
    if queue_stats['total_lobbies'] < 2:
        print("⚠️  Not enough lobbies for matchmaking")
        return
    
    # Try to find matches manually (ASYNC)
    print("\nRunning ASYNC matchmaker (MatchmakerV2.find_matches)...")
    try:
        result = await MatchmakerV2.find_matches('pug')
        print(f"\n✅ Matchmaking result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Matches found: {result.get('matches_found', 0)}")
        
        if result.get('matches_found', 0) > 0:
            for idx, match in enumerate(result.get('matches', []), 1):
                print(f"\n   Match {idx}:")
                print(f"      Quality: {match.get('match_quality', 0):.2f}")
                print(f"      Team A MMR: {match.get('team_a', {}).get('average_mmr', 0):.0f}")
                print(f"      Team B MMR: {match.get('team_b', {}).get('average_mmr', 0):.0f}")
                print(f"      Lobbies: {len(match.get('lobbies', []))}")
    except Exception as e:
        print(f"❌ Error in async matchmaking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Test SYNC version (what Celery uses)
    test_matchmaking_sync()
    
    # Test ASYNC version (what WebSockets use)
    print("\n")
    asyncio.run(test_matchmaking_async())
