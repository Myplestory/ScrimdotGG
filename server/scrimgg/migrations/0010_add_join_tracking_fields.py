# Generated manually for join tracking implementation

from django.db import migrations, models
from django.db import connection


def add_join_tracking_fields_if_not_exist(apps, schema_editor):
    """Add join tracking fields only if they don't already exist."""
    with connection.cursor() as cursor:
        fields_to_add = [
            ('joined_players', 'JSONB', "DEFAULT '[]'::jsonb"),
            ('join_timeout_at', "TIMESTAMP WITH TIME ZONE", "DEFAULT NULL"),
        ]
        
        for field_name, sql_type, default in fields_to_add:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='scrimgg_match' AND column_name=%s
            """, [field_name])
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE scrimgg_match ADD COLUMN {field_name} {sql_type} {default}")


def reverse_add_join_tracking_fields(apps, schema_editor):
    """Remove join tracking fields if they exist."""
    with connection.cursor() as cursor:
        for field_name in ['joined_players', 'join_timeout_at']:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='scrimgg_match' AND column_name=%s
            """, [field_name])
            if cursor.fetchone():
                cursor.execute(f"ALTER TABLE scrimgg_match DROP COLUMN {field_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('scrimgg', '0009_match_completed_at_match_confirmation_completed_at_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_join_tracking_fields_if_not_exist,
                    reverse_add_join_tracking_fields,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='match',
                    name='joined_players',
                    field=models.JSONField(default=list),
                ),
                migrations.AddField(
                    model_name='match',
                    name='join_timeout_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
    ]


