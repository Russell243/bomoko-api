from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sos', '0004_sosalert_audio_evidence'),
    ]

    operations = [
        migrations.AddField(
            model_name='sosalert',
            name='audio_encrypted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sosalert',
            name='audio_mime_type',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='sosalert',
            name='audio_original_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
