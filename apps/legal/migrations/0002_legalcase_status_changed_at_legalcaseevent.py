import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='legalcase',
            name='status_changed_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.CreateModel(
            name='LegalCaseEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('status_change', 'Status change'), ('note', 'Note')], default='status_change', max_length=30)),
                ('from_status', models.CharField(blank=True, default='', max_length=20)),
                ('to_status', models.CharField(blank=True, default='', max_length=20)),
                ('note', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legal_case_events', to=settings.AUTH_USER_MODEL)),
                ('legal_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='legal.legalcase')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
