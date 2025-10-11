import os
import sys
import django
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from matchmaking.match_confirmation import MatchConfirmationManager

async def test_match_acceptance():
    """Test the match acceptance flow"""
    print("Testing match acceptance flow...")
    
    # Create a test match confirmation
    test_match_data = {
        'lobby1': {
            'id': 'test-lobby-1',
            'players': [
                {'puuid': 'test-player-1'},
                {'puuid': 'test-player-2'},
                {'puuid': 'test-player-3'},
                {'puuid': 'test-player-4'},
                {'puuid': 'test-player-5'}
            ]
        },
        'lobby2': {
            'id': 'test-lobby-2', 
            'players': [
                {'puuid': 'test-player-6'},
                {'puuid': 'test-player-7'},
                {'puuid': 'test-player-8'},
                {'puuid': 'test-player-9'},
                {'puuid': 'test-player-10'}
            ]
        }
    }
    
    # Initiate match confirmation
    match_id = await MatchConfirmationManager.initiate_confirmation(test_match_data)
    print(f"Created test match confirmation: {match_id}")
    
    # Test accepting with first player
    result1 = await MatchConfirmationManager.mark_acceptance(match_id, 'test-player-1')
    print(f"Player 1 acceptance: {result1}")
    
    # Test accepting with second player
    result2 = await MatchConfirmationManager.mark_acceptance(match_id, 'test-player-2')
    print(f"Player 2 acceptance: {result2}")
    
    # Check if all accepted (should be False)
    all_accepted = await MatchConfirmationManager.check_all_accepted(match_id)
    print(f"All accepted: {all_accepted}")
    
    # Get acceptance counts
    accepting = await MatchConfirmationManager.get_accepting_players(match_id)
    non_accepting = await MatchConfirmationManager.get_non_accepting_players(match_id)
    print(f"Accepting players: {len(accepting)}")
    print(f"Non-accepting players: {len(non_accepting)}")
    
    # Clean up
    await MatchConfirmationManager.cleanup_match(match_id)
    print("Test match cleaned up")

if __name__ == '__main__':
    asyncio.run(test_match_acceptance())
