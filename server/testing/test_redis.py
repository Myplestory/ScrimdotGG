"""
Test Redis connection and operations for Scrim.GG
Run this to verify Redis is working before Phase 2 implementation
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from django.core.cache import cache
from django_redis import get_redis_connection


def test_django_cache():
    """Test Django cache with Redis"""
    print("\n" + "="*60)
    print("TEST 1: Django Cache")
    print("="*60)
    
    try:
        cache.set('test_key', 'Hello Redis!', 30)
        value = cache.get('test_key')
        
        if value == 'Hello Redis!':
            print("✅ PASSED: Django cache working")
            print(f"   Value: {value}")
            return True
        else:
            print("❌ FAILED: Unexpected value")
            return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_direct_connection():
    """Test direct Redis connection"""
    print("\n" + "="*60)
    print("TEST 2: Direct Redis Connection")
    print("="*60)
    
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.set('direct_test', 'Direct connection works!')
        value = redis_conn.get('direct_test')
        
        if value and value.decode() == 'Direct connection works!':
            print("✅ PASSED: Direct Redis connection working")
            print(f"   Value: {value.decode()}")
            redis_conn.delete('direct_test')
            return True
        else:
            print("❌ FAILED: Unexpected value")
            return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_sorted_set():
    """Test sorted set operations (used for matchmaking queue)"""
    print("\n" + "="*60)
    print("TEST 3: Sorted Set Operations (Matchmaking Queue)")
    print("="*60)
    
    try:
        redis_conn = get_redis_connection("default")
        
        # Clean up any existing test data
        redis_conn.delete('test_queue')
        
        # Add lobbies to queue with ELO as score
        redis_conn.zadd('test_queue', {
            'lobby1': 1500,
            'lobby2': 1600,
            'lobby3': 1450
        })
        
        # Get queue size
        queue_size = redis_conn.zcard('test_queue')
        print(f"✓ Queue size: {queue_size}")
        
        # Get all lobbies with scores
        lobbies = redis_conn.zrange('test_queue', 0, -1, withscores=True)
        print(f"✓ Lobbies in queue:")
        for lobby_id, elo in lobbies:
            print(f"   - {lobby_id.decode()}: ELO {int(elo)}")
        
        # Get lobbies in ELO range
        lobbies_in_range = redis_conn.zrangebyscore('test_queue', 1400, 1550, withscores=True)
        print(f"✓ Lobbies with ELO 1400-1550: {len(lobbies_in_range)}")
        
        # Remove from queue
        redis_conn.zrem('test_queue', 'lobby1')
        remaining = redis_conn.zcard('test_queue')
        print(f"✓ After removing lobby1: {remaining} lobbies remaining")
        
        # Cleanup
        redis_conn.delete('test_queue')
        
        if queue_size == 3 and len(lobbies_in_range) == 2:
            print("✅ PASSED: Sorted set operations working")
            return True
        else:
            print("❌ FAILED: Unexpected results")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_expiration():
    """Test key expiration (used for match confirmation timeout)"""
    print("\n" + "="*60)
    print("TEST 4: Key Expiration (Match Timeouts)")
    print("="*60)
    
    try:
        redis_conn = get_redis_connection("default")
        
        # Set key with 2 second expiration
        redis_conn.setex('test_expiry', 2, 'will expire soon')
        
        # Check it exists
        value = redis_conn.get('test_expiry')
        print(f"✓ Key exists: {value.decode()}")
        
        # Check TTL
        ttl = redis_conn.ttl('test_expiry')
        print(f"✓ Time to live: {ttl} seconds")
        
        # Cleanup
        redis_conn.delete('test_expiry')
        
        if ttl > 0 and ttl <= 2:
            print("✅ PASSED: Key expiration working")
            return True
        else:
            print("❌ FAILED: Unexpected TTL")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_sets():
    """Test set operations (used for tracking accepted players)"""
    print("\n" + "="*60)
    print("TEST 5: Set Operations (Player Acceptance Tracking)")
    print("="*60)
    
    try:
        redis_conn = get_redis_connection("default")
        
        # Clean up
        redis_conn.delete('test_accepted_players')
        
        # Add players to set
        redis_conn.sadd('test_accepted_players', 'player1', 'player2', 'player3')
        
        # Get count
        count = redis_conn.scard('test_accepted_players')
        print(f"✓ Players accepted: {count}")
        
        # Check if player is in set
        is_member = redis_conn.sismember('test_accepted_players', 'player1')
        print(f"✓ Player1 accepted: {bool(is_member)}")
        
        # Get all members
        members = redis_conn.smembers('test_accepted_players')
        print(f"✓ All accepted players: {[m.decode() for m in members]}")
        
        # Cleanup
        redis_conn.delete('test_accepted_players')
        
        if count == 3 and is_member:
            print("✅ PASSED: Set operations working")
            return True
        else:
            print("❌ FAILED: Unexpected results")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("REDIS CONNECTION TEST SUITE")
    print("Testing Redis for Scrim.GG Phase 2 Matchmaking")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(('Django Cache', test_django_cache()))
    results.append(('Direct Connection', test_direct_connection()))
    results.append(('Sorted Sets', test_sorted_set()))
    results.append(('Key Expiration', test_expiration()))
    results.append(('Set Operations', test_sets()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("="*60)
        print("\n🚀 Redis is ready for Phase 2 implementation!")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("="*60)
        print("\n⚠️  Please check Redis installation and try again")
        print("   See: docs/REDIS_SETUP_WINDOWS.md")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        print("\n📖 Redis might not be installed or running.")
        print("   See: docs/REDIS_SETUP_WINDOWS.md")
        import traceback
        traceback.print_exc()
        exit(1)

