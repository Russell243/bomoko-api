from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from sos.models import EmergencyContact, LocationUpdate, SOSAlert
from sos.services import SMSService


class Command(BaseCommand):
    help = "Send a real SOS test SMS through Twilio to validate production delivery."

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='Recipient phone number in E.164 format (e.g. +243...)')
        parser.add_argument('--username', default='sos-twilio-test-user', help='Temporary username for the test alert')
        parser.add_argument(
            '--allow-mock',
            action='store_true',
            help='Allow mock mode when Twilio is not configured (disabled by default).',
        )

    def handle(self, *args, **options):
        sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        at_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
        
        if not options['allow_mock'] and not (sid and token) and not at_key:
            raise CommandError("SMS non configure. Renseignez TWILIO_ACCOUNT_SID/TOKEN ou AFRICASTALKING_API_KEY.")

        User = get_user_model()
        username = options['username']
        to = options['to']

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'phone_number': '+243000000000',
            },
        )
        EmergencyContact.objects.update_or_create(
            user=user,
            phone_number=to,
            defaults={'name': 'Twilio Test Contact', 'relationship': 'test'},
        )

        alert = SOSAlert.objects.create(user=user, status='active', network_type='test')
        LocationUpdate.objects.create(alert=alert, latitude=-4.325, longitude=15.322)
        token = alert.ensure_tracking_token()
        self.stdout.write(self.style.NOTICE(f"Tracking link: {settings.PUBLIC_TRACKING_BASE_URL.rstrip('/')}/track/{alert.id}/{token}/"))

        sent = SMSService.send_sos_sms(alert, require_location=True, allow_mock=options['allow_mock'])
        if sent <= 0:
            raise CommandError('Aucun SMS envoye. Verifiez Twilio, le numero destination et les logs.')

        self.stdout.write(self.style.SUCCESS(f'SMS SOS de test envoye a {sent} contact(s).'))
