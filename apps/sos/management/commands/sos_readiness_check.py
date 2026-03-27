from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check critical SOS production readiness settings."

    def handle(self, *args, **options):
        checks = {
            'TWILIO_ACCOUNT_SID configured': bool(getattr(settings, 'TWILIO_ACCOUNT_SID', '')),
            'TWILIO_AUTH_TOKEN configured': bool(getattr(settings, 'TWILIO_AUTH_TOKEN', '')),
            'TWILIO_PHONE_NUMBER configured': bool(getattr(settings, 'TWILIO_PHONE_NUMBER', '')),
            'PUBLIC_TRACKING_BASE_URL configured': bool(getattr(settings, 'PUBLIC_TRACKING_BASE_URL', '')),
            'SOS_AUDIO_ENCRYPTION_ENABLED': bool(getattr(settings, 'SOS_AUDIO_ENCRYPTION_ENABLED', True)),
            'SOS_AUDIO_RETENTION_ENABLED': bool(getattr(settings, 'SOS_AUDIO_RETENTION_ENABLED', True)),
            'SOS_AUDIO_RETENTION_DAYS > 0': int(getattr(settings, 'SOS_AUDIO_RETENTION_DAYS', 0)) > 0,
            'SOS_MIN_CONTACTS_REQUIRED >= 3': int(getattr(settings, 'SOS_MIN_CONTACTS_REQUIRED', 0)) >= 3,
        }

        has_failure = False
        for label, ok in checks.items():
            prefix = self.style.SUCCESS('[OK]') if ok else self.style.ERROR('[KO]')
            self.stdout.write(f'{prefix} {label}')
            if not ok:
                has_failure = True

        if has_failure:
            self.stderr.write(self.style.ERROR('SOS readiness check failed. Corrigez les points [KO].'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('SOS readiness check passed.'))
