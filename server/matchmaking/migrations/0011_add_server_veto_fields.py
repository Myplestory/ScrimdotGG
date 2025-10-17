# Generated manually for server veto implementation

from django.db import migrations, models


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
