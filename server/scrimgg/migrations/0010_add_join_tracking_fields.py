# Generated manually for join tracking implementation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrimgg', '0009_match_completed_at_match_confirmation_completed_at_and_more'),
    ]

    operations = [
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
    ]


