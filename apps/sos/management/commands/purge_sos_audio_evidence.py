from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from sos.models import SOSAlert


class Command(BaseCommand):
    help = "Purge audio evidence older than SOS_AUDIO_RETENTION_DAYS."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=None, help='Override retention days for this run.')
        parser.add_argument('--dry-run', action='store_true', help='Show how many items would be deleted.')

    def handle(self, *args, **options):
        retention_days = options['days']
        if retention_days is None:
            retention_days = int(getattr(settings, 'SOS_AUDIO_RETENTION_DAYS', 90))
        cutoff = timezone.now() - timedelta(days=retention_days)

        queryset = (
            SOSAlert.objects.filter(created_at__lt=cutoff)
            .exclude(audio_evidence='')
            .exclude(audio_evidence__isnull=True)
        )
        count = queryset.count()

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'DRY-RUN: {count} audio file(s) would be deleted (retention={retention_days} days).'))
            return

        deleted = 0
        for alert in queryset.iterator():
            try:
                alert.audio_evidence.close()
            except Exception:
                pass
            alert.audio_evidence.delete(save=False)
            alert.audio_evidence = None
            alert.audio_mime_type = ''
            alert.audio_original_name = ''
            alert.audio_encrypted = False
            alert.save(update_fields=['audio_evidence', 'audio_mime_type', 'audio_original_name', 'audio_encrypted'])
            deleted += 1

        self.stdout.write(self.style.SUCCESS(f'Purge terminee: {deleted} audio file(s) supprime(s).'))
