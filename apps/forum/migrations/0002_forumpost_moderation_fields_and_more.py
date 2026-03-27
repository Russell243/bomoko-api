from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumpost',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='forumpost',
            name='moderation_reason',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='forumpost',
            name='moderation_status',
            field=models.CharField(
                choices=[('approved', 'Approved'), ('flagged', 'Flagged'), ('blocked', 'Blocked')],
                default='approved',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='forumreply',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='forumreply',
            name='moderation_reason',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='forumreply',
            name='moderation_status',
            field=models.CharField(
                choices=[('approved', 'Approved'), ('flagged', 'Flagged'), ('blocked', 'Blocked')],
                default='approved',
                max_length=20,
            ),
        ),
    ]
