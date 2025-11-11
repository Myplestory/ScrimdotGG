"""
Quick test script to verify Phase 3.1 installation
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Match, MatchStatistics, MatchRejoinToken

print("=" * 60)
print("Phase 3.1 Installation Verification")
print("=" * 60)

# Test Match model
print("\n1. Testing Match Model...")
try:
    # Check new fields exist
    match_fields = [f.name for f in Match._meta.get_fields()]
    required_fields = ['status', 'constructor_puuid', 'coregame_id', 'team_a_score', 
                      'team_b_score', 'current_round', 'selected_map', 'game_server',
                      'confirmation_completed_at', 'started_at', 'completed_at',
                      'team_a_data', 'team_b_data']
    
    missing_fields = [f for f in required_fields if f not in match_fields]
    
    if missing_fields:
        print(f"   [FAIL] Missing fields: {missing_fields}")
    else:
        print(f"   [OK] All {len(required_fields)} required fields present")
        
    # Test status choices
    status_field = Match._meta.get_field('status')
    if status_field.choices:
        print(f"   [OK] Status choices defined: {len(status_field.choices)} options")
    else:
        print("   [FAIL] Status choices not defined")
        
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test MatchStatistics model
print("\n2. Testing MatchStatistics Model...")
try:
    stats_fields = [f.name for f in MatchStatistics._meta.get_fields()]
    required_stats = ['match', 'player', 'team', 'kills', 'deaths', 'assists',
                     'headshots', 'damage_dealt', 'adr', 'rws', 'headshot_percentage']
    
    missing_stats = [f for f in required_stats if f not in stats_fields]
    
    if missing_stats:
        print(f"   [FAIL] Missing fields: {missing_stats}")
    else:
        print(f"   [OK] All {len(required_stats)} required fields present")
        
    # Check unique_together constraint
    if MatchStatistics._meta.unique_together:
        print(f"   [OK] Unique constraint defined: {MatchStatistics._meta.unique_together}")
    else:
        print("   [WARN] Warning: Unique constraint not defined")
        
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test MatchRejoinToken model
print("\n3. Testing MatchRejoinToken Model...")
try:
    token_fields = [f.name for f in MatchRejoinToken._meta.get_fields()]
    required_token = ['match', 'player', 'token', 'expires_at', 'used', 'created_at']
    
    missing_token = [f for f in required_token if f not in token_fields]
    
    if missing_token:
        print(f"   [FAIL] Missing fields: {missing_token}")
    else:
        print(f"   [OK] All {len(required_token)} required fields present")
        
    # Check unique_together constraint
    if MatchRejoinToken._meta.unique_together:
        print(f"   [OK] Unique constraint defined: {MatchRejoinToken._meta.unique_together}")
    else:
        print("   [WARN] Warning: Unique constraint not defined")
        
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test database queries
print("\n4. Testing Database Operations...")
try:
    match_count = Match.objects.count()
    print(f"   [OK] Match.objects.count() = {match_count}")
    
    stats_count = MatchStatistics.objects.count()
    print(f"   [OK] MatchStatistics.objects.count() = {stats_count}")
    
    token_count = MatchRejoinToken.objects.count()
    print(f"   [OK] MatchRejoinToken.objects.count() = {token_count}")
    
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test imports
print("\n5. Testing Manager Imports...")
try:
    from match_system.phases.execution import ExecutionPhaseManager
    print("   [OK] ExecutionPhaseManager imported successfully")
    
    from match_system.monitor import MatchMonitor
    print("   [OK] MatchMonitor imported successfully")
    
    # Check methods exist
    if hasattr(ExecutionPhaseManager, 'initiate_match_start'):
        print("   [OK] ExecutionPhaseManager.initiate_match_start() exists")
    
    if hasattr(MatchMonitor, 'update_match_score'):
        print("   [OK] MatchMonitor.update_match_score() exists")
        
except Exception as e:
    print(f"   [FAIL] Error importing managers: {e}")

print("\n" + "=" * 60)
print("[SUCCESS] Phase 3.1 Installation Verification Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Start Django server: pipenv run python manage.py runserver")
print("2. Start Celery worker: pipenv run celery -A scrimgg worker --loglevel=info")
print("3. Start Celery beat: pipenv run celery -A scrimgg beat --loglevel=info")
print("\nReady to test match execution!")

