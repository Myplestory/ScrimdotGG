# Generated manually for server veto implementation

from django.db import migrations, models
from django.db import connection


def add_server_veto_fields_if_not_exist(apps, schema_editor):
    """Add server veto fields only if they don't already exist."""
    with connection.cursor() as cursor:
        fields_to_add = [
            ('server_pool', 'JSONB', "DEFAULT '[]'::jsonb"),
            ('vetoed_servers', 'JSONB', "DEFAULT '[]'::jsonb"),
            ('server_veto_history', 'JSONB', "DEFAULT '[]'::jsonb"),
            ('final_server', "VARCHAR(20)", "DEFAULT NULL"),
            ('server_veto_turn', "VARCHAR(10)", "DEFAULT NULL"),
            ('server_veto_deadline', "TIMESTAMP WITH TIME ZONE", "DEFAULT NULL"),
            ('server_veto_started_at', "TIMESTAMP WITH TIME ZONE", "DEFAULT NULL"),
        ]
        
        for field_name, sql_type, default in fields_to_add:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='matchmaking_match' AND column_name=%s
            """, [field_name])
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE matchmaking_match ADD COLUMN {field_name} {sql_type} {default}")


def reverse_add_server_veto_fields(apps, schema_editor):
    """Remove server veto fields if they exist."""
    with connection.cursor() as cursor:
        fields_to_remove = [
            'server_pool', 'vetoed_servers', 'server_veto_history',
            'final_server', 'server_veto_turn', 'server_veto_deadline',
            'server_veto_started_at'
        ]
        for field_name in fields_to_remove:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='matchmaking_match' AND column_name=%s
            """, [field_name])
            if cursor.fetchone():
                cursor.execute(f"ALTER TABLE matchmaking_match DROP COLUMN {field_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('matchmaking', '0001_initial'),
        ('scrimgg', '0011_merge_20251017_0836'),
    ]

    operations = [
        # Add server veto state to STATE_CHOICES
        migrations.AlterField(
            model_name='match',
            name='state',
            field=models.CharField(
                choices=[
                    ('CONFIRMED', 'All players accepted'),
                    ('SERVER_VETO', 'Server veto in progress'),
                    ('VETO', 'Map veto in progress'),
                    ('SIDE_SELECTION', 'Side selection in progress'),
                    ('CREATING', 'Custom game being created'),
                    ('READY', 'Ready to start'),
                    ('IN_PROGRESS', 'Match started'),
                    ('COMPLETED', 'Match finished'),
                    ('CANCELLED', 'Match cancelled'),
                ],
                db_index=True,
                default='CONFIRMED',
                max_length=20
            ),
        ),
        
        # Add server veto fields
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_server_veto_fields_if_not_exist,
                    reverse_add_server_veto_fields,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='match',
                    name='server_pool',
                    field=models.JSONField(default=list, help_text='Available servers for veto'),
                ),
                migrations.AddField(
                    model_name='match',
                    name='vetoed_servers',
                    field=models.JSONField(default=list, help_text='List of vetoed server names'),
                ),
                migrations.AddField(
                    model_name='match',
                    name='server_veto_history',
                    field=models.JSONField(default=list, help_text='History of server veto actions'),
                ),
                migrations.AddField(
                    model_name='match',
                    name='final_server',
                    field=models.CharField(blank=True, help_text='Selected server for the match', max_length=20, null=True),
                ),
                migrations.AddField(
                    model_name='match',
                    name='server_veto_turn',
                    field=models.CharField(blank=True, help_text="'team_a' or 'team_b'", max_length=10, null=True),
                ),
                migrations.AddField(
                    model_name='match',
                    name='server_veto_deadline',
                    field=models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                migrations.AddField(
                    model_name='match',
                    name='server_veto_started_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
        
        # Add server veto action type to VetoAction and increase max_length
        migrations.AlterField(
            model_name='vetoaction',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('BAN', 'Map banned'),
                    ('PICK', 'Map picked'),
                    ('TIMEOUT', 'Timeout auto-action'),
                    ('SERVER_VETO', 'Server vetoed'),
                ],
                max_length=15
            ),
        ),
    ]
