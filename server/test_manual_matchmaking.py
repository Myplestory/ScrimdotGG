"""
Manually trigger matchmaking to test if it works
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from matchmaking.queue_manager import QueueManager
from matchmaking.matchmaker import Matchmaker
import asyncio

async def test_matchmaking():
    print("Testing manual matchmaking...")
    
    # Check queue stats
    queue_stats = await QueueManager.get_queue_stats('pug')
    print(f"Queue stats: {queue_stats}")
    
    if queue_stats['total_lobbies'] < 2:
        print("Not enough lobbies for matchmaking")
        return
    
    # Try to find matches manually
    print("Running matchmaker...")
    try:
        result = await Matchmaker.find_matches()
        print(f"Matchmaking result: {result}")
    except Exception as e:
        print(f"Error in matchmaking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_matchmaking())
