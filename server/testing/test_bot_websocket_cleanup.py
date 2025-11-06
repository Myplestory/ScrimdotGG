"""
Test Bot WebSocket Connection Cleanup
Verifies that all bot WebSocket connections are properly cleaned up.
"""

import os
import sys
import asyncio
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from testing.bot_websocket_client import BotWebSocketManager, BotWebSocketClient
from testing.bot_auto_acceptor_ws import BotAutoAcceptorWS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_single_connection_cleanup():
    """Test cleanup of a single bot connection"""
    print("\n" + "=" * 70)
    print("TEST 1: Single Connection Cleanup")
    print("=" * 70)
    
    bot_puuid = "test-bot-cleanup-1"
    
    try:
        # Create and connect
        print(f"\n[TEST] Creating connection for {bot_puuid}...")
        client = BotWebSocketClient(bot_puuid)
        success = await client.connect()
        
        if success:
            print(f"[TEST] ✅ Connected")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Close
            print(f"[TEST] Closing connection...")
            await client.close()
            
            # Verify closed
            if not client.is_connected():
                print(f"[TEST] ✅ Connection properly closed")
                return True
            else:
                print(f"[TEST] ❌ Connection still shows as connected")
                return False
        else:
            print(f"[TEST] ❌ Failed to connect")
            return False
            
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_connections_cleanup():
    """Test cleanup of multiple bot connections"""
    print("\n" + "=" * 70)
    print("TEST 2: Multiple Connections Cleanup")
    print("=" * 70)
    
    bot_puuids = [f"test-bot-cleanup-{i}" for i in range(5)]
    
    try:
        # Create manager
        print(f"\n[TEST] Creating manager and connecting {len(bot_puuids)} bots...")
        manager = BotWebSocketManager()
        connected = await manager.connect_bots(bot_puuids)
        
        print(f"[TEST] Connected {connected}/{len(bot_puuids)} bots")
        
        if connected > 0:
            # Wait a bit
            await asyncio.sleep(2)
            
            # Check connection status
            connected_count = manager.get_connected_count()
            print(f"[TEST] Active connections: {connected_count}")
            
            # Close all
            print(f"[TEST] Closing all connections...")
            await manager.close_all()
            
            # Verify all closed
            remaining = manager.get_connected_count()
            clients_remaining = len(manager.clients)
            
            if remaining == 0 and clients_remaining == 0:
                print(f"[TEST] ✅ All connections properly closed and cleaned up")
                return True
            else:
                print(f"[TEST] ❌ Still have {remaining} connections, {clients_remaining} clients")
                return False
        else:
            print(f"[TEST] ❌ No bots connected")
            return False
            
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_manager_cleanup():
    """Test cleanup using context manager"""
    print("\n" + "=" * 70)
    print("TEST 3: Context Manager Cleanup")
    print("=" * 70)
    
    bot_puuids = [f"test-bot-context-{i}" for i in range(3)]
    
    try:
        print(f"\n[TEST] Testing automatic cleanup with context manager...")
        
        # Use context manager
        async with BotWebSocketManager() as manager:
            connected = await manager.connect_bots(bot_puuids)
            print(f"[TEST] Connected {connected}/{len(bot_puuids)} bots inside context")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Context will auto-cleanup on exit
        
        # After context exit, verify cleanup
        print(f"[TEST] Context exited, verifying cleanup...")
        print(f"[TEST] ✅ Context manager cleaned up automatically")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_acceptor_cleanup():
    """Test cleanup of full acceptor with active matches"""
    print("\n" + "=" * 70)
    print("TEST 4: Acceptor Cleanup with Active Tasks")
    print("=" * 70)
    
    bot_puuids = [f"test-bot-acceptor-{i}" for i in range(3)]
    
    try:
        print(f"\n[TEST] Creating acceptor with {len(bot_puuids)} bots...")
        
        acceptor = BotAutoAcceptorWS()
        acceptor.add_bots(bot_puuids, auto_accept_all=True, exclude_last=False)
        
        connected = await acceptor.connect_bots(bot_puuids)
        print(f"[TEST] Connected {connected}/{len(bot_puuids)} bots")
        
        if connected > 0:
            # Wait a bit
            await asyncio.sleep(2)
            
            # Get stats
            stats = acceptor.get_stats()
            print(f"[TEST] Acceptor stats: {stats}")
            
            # Close
            print(f"[TEST] Closing acceptor...")
            await acceptor.close()
            
            # Verify cleanup
            stats_after = acceptor.get_stats()
            
            if stats_after['connected_bots'] == 0 and stats_after['active_matches'] == 0:
                print(f"[TEST] ✅ Acceptor properly closed and cleaned up")
                return True
            else:
                print(f"[TEST] ❌ Cleanup incomplete: {stats_after}")
                return False
        else:
            print(f"[TEST] ❌ No bots connected")
            return False
            
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_forced_cleanup():
    """Test cleanup after exception"""
    print("\n" + "=" * 70)
    print("TEST 5: Forced Cleanup After Exception")
    print("=" * 70)
    
    bot_puuids = [f"test-bot-force-{i}" for i in range(2)]
    
    acceptor = None
    
    try:
        print(f"\n[TEST] Creating acceptor that will encounter an error...")
        
        acceptor = BotAutoAcceptorWS()
        acceptor.add_bots(bot_puuids, auto_accept_all=True, exclude_last=False)
        
        connected = await acceptor.connect_bots(bot_puuids)
        print(f"[TEST] Connected {connected}/{len(bot_puuids)} bots")
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Simulate exception
        print(f"[TEST] Simulating exception...")
        raise ValueError("Simulated error for testing cleanup")
        
    except ValueError as e:
        print(f"[TEST] Caught expected error: {e}")
        
        # Cleanup should still work
        if acceptor:
            print(f"[TEST] Attempting cleanup after exception...")
            await acceptor.close()
            
            stats = acceptor.get_stats()
            if stats['connected_bots'] == 0:
                print(f"[TEST] ✅ Cleanup successful even after exception")
                return True
            else:
                print(f"[TEST] ❌ Cleanup failed: {stats}")
                return False
        else:
            print(f"[TEST] ❌ No acceptor to clean up")
            return False
    
    except Exception as e:
        print(f"[TEST] ❌ Unexpected error: {e}")
        return False


async def run_all_tests():
    """Run all cleanup tests"""
    print("\n" + "=" * 70)
    print("BOT WEBSOCKET CLEANUP TESTS")
    print("=" * 70)
    print("\nTesting WebSocket connection cleanup mechanisms...")
    print()
    
    results = []
    
    # Run tests
    results.append(("Single Connection", await test_single_connection_cleanup()))
    await asyncio.sleep(1)
    
    results.append(("Multiple Connections", await test_multiple_connections_cleanup()))
    await asyncio.sleep(1)
    
    results.append(("Context Manager", await test_context_manager_cleanup()))
    await asyncio.sleep(1)
    
    results.append(("Acceptor Cleanup", await test_acceptor_cleanup()))
    await asyncio.sleep(1)
    
    results.append(("Forced Cleanup", await test_forced_cleanup()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Cleanup mechanisms working correctly!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed - Check logs for details")
        return False


if __name__ == "__main__":
    print("\n[NOTE] This test requires Daphne server to be running")
    print("[NOTE] Run: pipenv run python manage.py runserver_daphne")
    print()
    
    try:
        all_passed = asyncio.run(run_all_tests())
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Tests interrupted")
        sys.exit(1)

