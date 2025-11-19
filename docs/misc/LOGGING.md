# Scrim.GG Logging System

## Overview

This document describes the centralized logging system implemented across Scrim.GG's server and client backends. The system provides clean, concise logs with proper log levels, rotation, and structured output.

## Architecture

### Server-Side Logging (Django)

**Location**: `server/scrimgg/settings.py` (LOGGING configuration)

**Log Files**:
- `server/logs/scrimgg.log` - All INFO+ level logs
- `server/logs/errors.log` - ERROR level logs only
- `server/logs/matchmaking.log` - Matchmaking-specific logs
- `server/logs/celery.log` - Celery task logs
- `server/logs/websocket.log` - WebSocket/Channels logs

**Features**:
- Automatic log rotation (10MB per file, 5 backups)
- Separate handlers for different components
- Console output with concise format
- File output with verbose format including timestamps, module names, function names
- Reduces noise from third-party libraries (Redis, urllib3, asyncio)

### Client-Side Logging (Python Backend)

**Location**: `client/backend/app/utils/logger.py`

**Log Files**:
- `client/backend/logs/client.log` - All DEBUG+ level logs
- `client/backend/logs/client_errors.log` - ERROR level logs only

**Features**:
- Centralized logger utility with `get_logger(__name__)`
- Automatic log rotation (10MB per file, 5 backups)
- Consistent formatting across all modules
- Root logger configuration via `setup_root_logger()`

## Log Formats

### Console Format (Concise)
```
[INFO    ] matchmaking.consumers          | Match found! ID: abc123...
[WARNING ] matchmaking.queue_manager      | Queue timeout for lobby 456
[ERROR   ] matchmaking.tasks              | Failed to process match
```

### File Format (Verbose)
```
[INFO] 2025-10-17 14:23:45 | matchmaking.consumers | connect:42 | WebSocket connected: PUUID = abc123...
[ERROR] 2025-10-17 14:24:10 | matchmaking.tasks | process_match:128 | Failed to process match: Connection timeout
```

### Celery Format (Special)
```
[CELERY] [INFO] 2025-10-17 14:25:00 | matchmaking.tasks | Task: periodic_matchmaking | Starting matchmaking cycle
```

## Usage

### Server-Side (Django)

```python
import logging

logger = logging.getLogger(__name__)

# Basic logging
logger.info("Match started successfully")
logger.warning("Player not found in database")
logger.error("Failed to connect to Redis")

# Exception logging (includes full traceback)
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
```

### Client-Side (Python Backend)

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Creating custom game...")
logger.warning("Pregame ID not found")
logger.error("Failed to join party")

# Exception logging
try:
    create_custom_game()
except Exception as e:
    logger.exception(f"Custom game creation failed: {e}")
```

## Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed information for debugging (disabled in production) |
| `INFO` | General informational messages about system operations |
| `WARNING` | Something unexpected happened, but system continues |
| `ERROR` | Serious problem that needs attention |
| `CRITICAL` | Very serious error, system may not be able to continue |

## Component-Specific Loggers

### Server Components

**Matchmaking** (`matchmaking.*`)
- Level: DEBUG (dev) / INFO (prod)
- Outputs: Console + matchmaking.log + errors.log
- Use for: Queue operations, match creation, player matching

**WebSocket Consumers** (`matchmaking.consumers`)
- Level: DEBUG (dev) / INFO (prod)  
- Outputs: Console + websocket.log + errors.log
- Use for: WebSocket connections, lobby events, real-time updates

**Celery Tasks** (`matchmaking.tasks`)
- Level: INFO
- Outputs: Console + celery.log + errors.log
- Use for: Background tasks, periodic jobs, async operations

**Channels/Redis** (`channels`, `channels_redis`, `aioredis`)
- Level: WARNING (reduced noise)
- Outputs: Console
- Use for: WebSocket layer operations (mostly automatic)

### Client Components

All client backend modules use the centralized logger utility with consistent formatting and rotation.

## Configuration

### Changing Log Levels

**Development** (verbose):
```python
# server/scrimgg/settings.py
DEBUG = True  # Automatically enables DEBUG level for app loggers
```

**Production** (concise):
```python
# server/scrimgg/settings.py
DEBUG = False  # Sets app loggers to INFO level
```

### Adding New Loggers

**Server** - Add to `server/scrimgg/settings.py`:
```python
LOGGING = {
    # ... existing configuration ...
    'loggers': {
        'your_new_app': {
            'handlers': ['console', 'file_all', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Client** - Use the utility:
```python
from app.utils.logger import get_logger
logger = get_logger(__name__)
```

## Best Practices

### ✅ DO

- Use appropriate log levels (INFO for normal operations, ERROR for failures)
- Include relevant context (match IDs, player IDs, etc.)
- Use `logger.exception()` in except blocks to include tracebacks
- Truncate long values (UUIDs, PUUIDs) for readability: `puuid[:12]...`
- Log state transitions (match created → starting → in_progress → completed)

### ❌ DON'T

- Use `print()` statements (except for one-off debugging)
- Log sensitive information (passwords, auth tokens, full UUIDs)
- Log at DEBUG level in hot paths (performance impact)
- Log the same event multiple times
- Include emojis or special characters in logs

## Examples

### Good Logging

```python
# Context-rich, appropriate level
logger.info(f"Match {match_id} starting with {player_count} players")

# Error with context
logger.error(f"Failed to create lobby for player {puuid[:12]}...: {error}")

# Exception with full traceback
try:
    process_match(match_id)
except MatchError as e:
    logger.exception(f"Match processing failed for {match_id}")
```

### Bad Logging

```python
# Too vague
logger.info("Something happened")

# Too verbose for INFO
logger.info(f"Processing player {puuid} with data {full_player_dict}")

# Wrong level
logger.info("CRITICAL ERROR: Database connection lost")  # Should be ERROR

# Using print instead of logger
print(f"[MATCH] Match started")  # Should use logger.info()
```

## Monitoring & Troubleshooting

### View Recent Logs

**All logs**:
```bash
tail -f server/logs/scrimgg.log
```

**Errors only**:
```bash
tail -f server/logs/errors.log
```

**Matchmaking**:
```bash
tail -f server/logs/matchmaking.log
```

**Celery tasks**:
```bash
tail -f server/logs/celery.log
```

### Search Logs

```bash
# Find all errors related to a specific match
grep "match_abc123" server/logs/errors.log

# Find all WebSocket disconnections
grep "disconnected" server/logs/websocket.log
```

### Log Rotation

Logs automatically rotate when they reach 10MB. Old logs are kept with extensions `.1`, `.2`, etc., up to 5 backups.

## Performance Considerations

1. **Log Levels**: DEBUG logging is only enabled in development. Production uses INFO+.
2. **File Handlers**: Asynchronous writing prevents blocking main thread.
3. **Rotation**: Automatic rotation prevents disk space issues.
4. **Third-Party Noise**: Libraries like Redis, urllib3 are set to WARNING level.
5. **Structured Output**: Consistent formatting makes parsing/aggregation easier.

## Future Enhancements

- [ ] Integration with log aggregation service (ELK, Splunk, etc.)
- [ ] Structured logging with JSON format for better parsing
- [ ] Log correlation with request IDs across services
- [ ] Performance metrics logging
- [ ] Automated log analysis and alerting

## Support

For questions or issues with the logging system, contact the development team or refer to:
- Django Logging Documentation: https://docs.djangoproject.com/en/5.0/topics/logging/
- Python Logging Documentation: https://docs.python.org/3/library/logging.html

