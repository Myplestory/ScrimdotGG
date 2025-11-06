#!/usr/bin/env python3
"""
Test Veto Flow
Simple test to verify the veto system works end-to-end.
"""
import os
import sys
import asyncio
import django

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from test_queue_with_bots_v4 import create_bot_with_websocket, run_bot_test

async def test_veto_flow():
    """Test the complete veto flow with bots"""
    print("🧪 Testing Veto Flow...")
    print("=" * 60)
    
    try:
        # Run the bot test which now includes veto functionality
        await run_bot_test()
        
        print("=" * 60)
        print("✅ Veto flow test completed!")
        print("")
        print("Expected behavior:")
        print("1. ✅ 9 bots join queue")
        print("2. ✅ You join queue (10th player)")
        print("3. ✅ Matchmaker finds match")
        print("4. ✅ All players accept match")
        print("5. ✅ Match transitions to VETO state")
        print("6. ✅ Veto component renders on MatchPage")
        print("7. ✅ Captain bots auto-veto maps")
        print("8. ✅ Veto buttons clickable for human captains")
        print("9. ✅ Veto phase completes → Side selection")
        print("")
        print("Check the logs above for veto activity!")
        
    except Exception as e:
        print(f"❌ Veto flow test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_veto_flow())
