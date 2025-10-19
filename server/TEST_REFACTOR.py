#!/usr/bin/env python
"""
Test script to verify refactor works end-to-end.
Run this AFTER migrations to test the system.
"""

import asyncio
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()


async def test_imports():
    """Test that all imports work"""
    print("🧪 Testing imports...")
    
    try:
        from core.redis_manager import RedisManager
        from core.websocket_utils import WebSocketBroadcaster
        from match_system.models import Match
        from match_system.managers import MatchManager
        from realtime.consumers import RealtimeConsumer
        from lobby.manager import LobbyManager
        
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


async def test_redis_connection():
    """Test Redis connection"""
    print("\n🧪 Testing Redis connection...")
    
    try:
        from core.redis_manager import RedisManager
        
        if RedisManager.ping():
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False


async def test_websocket_routing():
    """Test WebSocket routing configuration"""
    print("\n🧪 Testing WebSocket routing...")
    
    try:
        from realtime.routing import websocket_urlpatterns
        from scrimgg.asgi import application
        
        print(f"✅ WebSocket routing configured with {len(websocket_urlpatterns)} pattern(s)")
        print("✅ ASGI application configured")
        return True
    except Exception as e:
        print(f"❌ WebSocket routing test failed: {e}")
        return False


async def test_model_operations():
    """Test basic model operations"""
    print("\n🧪 Testing model operations...")
    
    try:
        from match_system.models import Match
        from django.utils import timezone
        
        # Test model creation (don't save to DB)
        match = Match(
            state=Match.STATE_CONFIRMED,
            team_a_lobbies=[],
            team_b_lobbies=[],
            team_a_players=[],
            team_b_players=[],
            team_a_captain_puuid='test123',
            team_b_captain_puuid='test456',
            map_pool=['Bind', 'Haven'],
            server_region='na'
        )
        
        print("✅ Model instantiation successful")
        print(f"✅ Match state: {match.state}")
        return True
    except Exception as e:
        print(f"❌ Model operations test failed: {e}")
        return False


async def test_handler_initialization():
    """Test that handlers can be initialized"""
    print("\n🧪 Testing handler initialization...")
    
    try:
        from realtime.handlers import LobbyHandler, MatchHandler, VetoHandler, ExecutionHandler
        from realtime.handlers.base import BaseHandler
        
        # Mock consumer
        class MockConsumer:
            puuid = "test123"
            channel_layer = None
        
        consumer = MockConsumer()
        
        # Test handler initialization
        lobby_handler = LobbyHandler(consumer)
        match_handler = MatchHandler(consumer)
        veto_handler = VetoHandler(consumer)
        execution_handler = ExecutionHandler(consumer)
        
        print("✅ All handlers initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Handler initialization test failed: {e}")
        return False


async def test_celery_tasks():
    """Test that Celery tasks are importable"""
    print("\n🧪 Testing Celery tasks...")
    
    try:
        from matchmaking.tasks import periodic_matchmaking, cleanup_expired_queues
        from match_system.tasks import cleanup_expired_matches, check_veto_timeouts
        
        print("✅ All Celery tasks imported successfully")
        return True
    except Exception as e:
        print(f"❌ Celery tasks test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 70)
    print("  Django Refactor End-to-End Test")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Redis Connection", test_redis_connection),
        ("WebSocket Routing", test_websocket_routing),
        ("Model Operations", test_model_operations),
        ("Handler Initialization", test_handler_initialization),
        ("Celery Tasks", test_celery_tasks),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 70)
    print(f"  Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✨ All tests passed! Refactor is working correctly.")
        print("\nYou can now:")
        print("1. Start Django: python manage.py runserver")
        print("2. Start Celery worker: celery -A scrimgg worker --loglevel=info")
        print("3. Start Celery beat: celery -A scrimgg beat --loglevel=info")
        print("4. Test with your client")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

