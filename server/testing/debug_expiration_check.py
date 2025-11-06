"""
Debug Match Expiration Check
Tests the timezone and datetime parsing logic used in is_match_expired()
"""

import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from django.utils import timezone

print("="*70)
print("DEBUGGING EXPIRATION CHECK")
print("="*70)

# Simulate what happens in initiate_confirmation
print("\n1. CREATING initiated_at (simulating initiate_confirmation):")
initiated_at_value = timezone.now().isoformat()
print(f"   timezone.now().isoformat() = {initiated_at_value}")
print(f"   Type: {type(initiated_at_value)}")

# Wait a bit
import time
print("\n2. WAITING 5 SECONDS...")
time.sleep(5)

# Simulate what happens in is_match_expired
print("\n3. CHECKING EXPIRATION (simulating is_match_expired after 5 seconds):")
print(f"   initiated_at string: {initiated_at_value}")

# Parse it back
initiated_time = datetime.fromisoformat(initiated_at_value.replace('Z', '+00:00'))
print(f"   Parsed initiated_time: {initiated_time}")
print(f"   Type: {type(initiated_time)}")
print(f"   Timezone info: {initiated_time.tzinfo}")

# Get current time
now = timezone.now()
print(f"   Current time (now): {now}")
print(f"   Type: {type(now)}")
print(f"   Timezone info: {now.tzinfo}")

# Calculate difference
time_diff = (now - initiated_time).total_seconds()
print(f"\n4. TIME DIFFERENCE CALCULATION:")
print(f"   time_diff = (now - initiated_time).total_seconds()")
print(f"   time_diff = {time_diff} seconds")

# Check against timeout
ACCEPTANCE_TIMEOUT = 30
print(f"\n5. EXPIRATION CHECK:")
print(f"   ACCEPTANCE_TIMEOUT = {ACCEPTANCE_TIMEOUT}")
print(f"   time_diff > ACCEPTANCE_TIMEOUT = {time_diff} > {ACCEPTANCE_TIMEOUT}")
print(f"   Result: {time_diff > ACCEPTANCE_TIMEOUT}")
print(f"   Expected: False (only 5 seconds elapsed)")

# Now simulate 35 seconds
print("\n" + "="*70)
print("SIMULATING 35 SECOND TIMEOUT")
print("="*70)

# Create a timestamp 35 seconds ago
import time as time_module
past_timestamp = timezone.now()
# Manually create a timestamp 35 seconds in the past
from datetime import timedelta
past_timestamp = timezone.now() - timedelta(seconds=35)
past_initiated_at = past_timestamp.isoformat()

print(f"\n1. Created initiated_at 35 seconds ago:")
print(f"   initiated_at: {past_initiated_at}")

# Parse and check
initiated_time_past = datetime.fromisoformat(past_initiated_at.replace('Z', '+00:00'))
now_check = timezone.now()
time_diff_past = (now_check - initiated_time_past).total_seconds()

print(f"\n2. Checking expiration:")
print(f"   initiated_time: {initiated_time_past}")
print(f"   now: {now_check}")
print(f"   time_diff: {time_diff_past} seconds")
print(f"   time_diff > {ACCEPTANCE_TIMEOUT}: {time_diff_past > ACCEPTANCE_TIMEOUT}")
print(f"   Expected: True (35 seconds > 30 seconds)")

if time_diff_past > ACCEPTANCE_TIMEOUT:
    print(f"\n✅ EXPIRATION CHECK WORKS CORRECTLY!")
else:
    print(f"\n❌ EXPIRATION CHECK FAILED!")
    print(f"   This is the bug! time_diff should be ~35 but got {time_diff_past}")

print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)

