from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medical', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='reminder_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='medicalentry',
            name='care_stage',
            field=models.CharField(
                choices=[
                    ('initial_assessment', 'Evaluation initiale'),
                    ('treatment_plan', 'Plan de traitement'),
                    ('follow_up', 'Suivi'),
                    ('completed', 'Parcours termine'),
                ],
                default='initial_assessment',
                max_length=30,
            ),
        ),
    ]
