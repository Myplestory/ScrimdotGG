# Phase 1 Setup Instructions

## Step 1: Run Migrations

```bash
cd server
python manage.py makemigrations scrimgg
```

### Handling Migration Prompts

When asked about the `created_at` field:
```
It is impossible to add the field 'created_at' with 'auto_now_add=True' to lobby without providing a default.
1) Provide a one-off default now
2) Quit and manually define a default value
```

**Choose option 1** and enter: `timezone.now`

When asked about the `queued_at` field (if prompted):
**Choose option 1** and enter: `None`

## Step 2: Apply Migrations

```bash
python manage.py migrate
```

## Step 3: Verify Migration

```bash
python manage.py shell
```

Then in the Python shell:
```python
from scrimgg.models import Lobby
# Check if new fields exist
lobby_fields = [f.name for f in Lobby._meta.get_fields()]
print("New fields added:", [f for f in lobby_fields if f in ['queue_type', 'map_preferences', 'server_preferences', 'elo_range', 'max_size', 'created_at', 'queued_at']])
exit()
```

## Step 4: Start Server

```bash
python manage.py runserver
```

## Troubleshooting

### If migration fails:
1. Check if Redis is running: `redis-cli ping` (should return PONG)
2. Make sure you're in the server directory
3. Verify pipenv environment is activated: `pipenv shell`

### If you need to reset migrations:
```bash
# WARNING: This will delete your database!
# Only use in development

# Delete the database
rm db.sqlite3

# Delete migration files (except __init__.py)
# Then re-run makemigrations and migrate
python manage.py makemigrations
python manage.py migrate
```

## Next: Test the Implementation

Once setup is complete, refer to `docs/PHASE_1_LOBBY_SYSTEM_IMPLEMENTATION.md` for testing instructions.

