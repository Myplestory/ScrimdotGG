# Testing Scripts

This directory contains various testing and debugging scripts for the matchmaking system.

## How to Run Scripts

All scripts should be run from the `server/` directory using pipenv:

```powershell
cd server
pipenv run python testing/<script_name>.py
```

## Available Scripts

### Queue Testing
- **test_queue_with_bots.py** - Creates 9 bot players and waits for you to join via client
- **test_manual_matchmaking.py** - Manually trigger matchmaking and check queue status

### Lobby Management
- **check_my_lobby.py** - Check your current lobby state and eligibility
- **fix_my_lobby.py** - Fix lobby map preferences
- **delete_my_lobby.py** - Delete your existing lobby
- **check_new_lobby.py** - Check newly created lobby

### Match Confirmation
- **check_match_confirmations.py** - Check active match confirmations in Redis

### Cleanup
- **cleanup_bots_simple.py** - Remove all test/bot players from database and Redis
- **cleanup_bots.py** - Legacy cleanup script

### Debugging
- **debug_queue_join.py** - Debug queue joining process
- **test_match_acceptance.py** - Test match acceptance flow

### Legacy Tests
- **test_lobby_operations.py** - Test lobby CRUD operations
- **test_queue_operations.py** - Test queue operations
- **test_match_flow_simulation.py** - Simulate complete match flow
- **test_phase3_installation.py** - Verify Phase 3 installation

## Common Workflows

### Testing Complete Matchmaking Flow

1. Clean up old bots:
   ```powershell
   pipenv run python testing/cleanup_bots_simple.py
   ```

2. Create 9 bot players in queue:
   ```powershell
   pipenv run python testing/test_queue_with_bots.py
   ```

3. Start your Electron client and click "Find Match"

4. Check match confirmations (optional):
   ```powershell
   pipenv run python testing/check_match_confirmations.py
   ```

### Debugging Queue Issues

1. Check your lobby state:
   ```powershell
   pipenv run python testing/check_my_lobby.py
   ```

2. If map preferences are wrong:
   ```powershell
   pipenv run python testing/fix_my_lobby.py
   ```

3. If lobby is stuck:
   ```powershell
   pipenv run python testing/delete_my_lobby.py
   ```

4. Debug queue joining:
   ```powershell
   pipenv run python testing/debug_queue_join.py
   ```

## Notes

- All scripts use `sys.path.insert` to properly find Django modules
- Scripts should be run from the `server/` directory where Pipfile is located
- Match confirmations are stored in Redis, not in Django models
- Bots have all 9 maps selected by default

