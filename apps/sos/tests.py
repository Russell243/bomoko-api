from unittest.mock import patch
from datetime import timedelta
from django.test import override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from sos.models import SOSAlert, EmergencyContact, LocationUpdate
from sos.services import SMSService
from sos.tasks import retry_sos_sms_fallback, retry_pending_sos_sms, purge_expired_sos_audio_evidence

User = get_user_model()


class SosApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sos-user', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        EmergencyContact.objects.create(user=self.user, name='Contact Test 1', phone_number='+243810000111')
        EmergencyContact.objects.create(user=self.user, name='Contact Test 2', phone_number='+243810000112')
        EmergencyContact.objects.create(user=self.user, name='Contact Test 3', phone_number='+243810000113')

    def test_create_alert_defers_sms_until_location(self):
        with patch('sos.views.SMSService.send_sos_sms') as mocked_sms:
            response = self.client.post('/api/sos/alerts/', {'network_type': 'wifi'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_sms.assert_not_called()

    def test_location_endpoint_requests_sms_with_require_location(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')

        with patch('sos.views.SMSService.send_sos_sms', return_value=1) as mocked_sms:
            response = self.client.post(
                f'/api/sos/alerts/{alert.id}/location/',
                {'latitude': -4.325, 'longitude': 15.322},
                format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(mocked_sms.call_count, 1)
        self.assertEqual(mocked_sms.call_args.kwargs.get('require_location'), True)

    @override_settings(PUBLIC_TRACKING_BASE_URL='https://tracking.bomoko.app')
    def test_tracking_link_generates_token_for_owner(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')

        response = self.client.post(f'/api/sos/alerts/{alert.id}/tracking_link/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tracking_url', response.data)
        self.assertTrue(response.data['tracking_url'].startswith('https://tracking.bomoko.app/track/'))
        alert.refresh_from_db()
        self.assertIsNotNone(alert.public_tracking_token)

    def test_public_tracking_endpoint_returns_location_with_valid_token(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        LocationUpdate.objects.create(alert=alert, latitude=-4.325, longitude=15.322)
        token = alert.ensure_tracking_token()

        response = self.client.get(f'/api/sos/track/{alert.id}/{token}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')
        self.assertIsNotNone(response.data['latest_location'])

    def test_public_tracking_endpoint_rejects_expired_token(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        token = alert.ensure_tracking_token()
        alert.tracking_token_expires_at = timezone.now() - timedelta(minutes=1)
        alert.save(update_fields=['tracking_token_expires_at'])

        response = self.client.get(f'/api/sos/track/{alert.id}/{token}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_tracking_link_invalidates_old_token_and_allows_new_one(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        old_token = alert.ensure_tracking_token()

        revoke_response = self.client.post(f'/api/sos/alerts/{alert.id}/revoke_tracking_link/')
        self.assertEqual(revoke_response.status_code, status.HTTP_200_OK)

        old_public_response = self.client.get(f'/api/sos/track/{alert.id}/{old_token}/')
        self.assertEqual(old_public_response.status_code, status.HTTP_404_NOT_FOUND)

        new_link_response = self.client.post(f'/api/sos/alerts/{alert.id}/tracking_link/')
        self.assertEqual(new_link_response.status_code, status.HTTP_200_OK)
        new_token = new_link_response.data['tracking_token']
        self.assertNotEqual(str(old_token), new_token)

    def test_audio_upload_sets_audio_evidence(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        audio = SimpleUploadedFile('evidence.mp3', b'fake-audio-content', content_type='audio/mpeg')

        response = self.client.post(
            f'/api/sos/alerts/{alert.id}/audio/',
            {'audio': audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        alert.refresh_from_db()
        self.assertTrue(bool(alert.audio_evidence))
        self.assertEqual(alert.audio_original_name, 'evidence.mp3')
        self.assertEqual(alert.audio_mime_type, 'audio/mpeg')

    @override_settings(SOS_AUDIO_MAX_UPLOAD_BYTES=4)
    def test_audio_upload_rejects_oversized_files(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        audio = SimpleUploadedFile('huge.mp3', b'12345', content_type='audio/mpeg')

        response = self.client.post(
            f'/api/sos/alerts/{alert.id}/audio/',
            {'audio': audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_audio_history_stream_and_delete(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        audio = SimpleUploadedFile('clip.wav', b'fake-wave-content', content_type='audio/wav')
        upload_response = self.client.post(
            f'/api/sos/alerts/{alert.id}/audio/',
            {'audio': audio},
            format='multipart'
        )
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)

        history_response = self.client.get('/api/sos/alerts/audio-history/')
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history_response.data), 1)
        self.assertEqual(history_response.data[0]['alert_id'], str(alert.id))

        stream_response = self.client.get(f'/api/sos/alerts/{alert.id}/audio-stream/')
        self.assertEqual(stream_response.status_code, status.HTTP_200_OK)
        self.assertEqual(stream_response['Content-Type'], 'audio/wav')

        delete_response = self.client.delete(f'/api/sos/alerts/{alert.id}/audio/')
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)

    def test_audio_stream_forbidden_for_other_user(self):
        alert = SOSAlert.objects.create(user=self.user, status='active')
        audio = SimpleUploadedFile('proof.mp3', b'proof-audio', content_type='audio/mpeg')
        self.client.post(f'/api/sos/alerts/{alert.id}/audio/', {'audio': audio}, format='multipart')

        other_user = User.objects.create_user(username='other-stream-user', password='StrongPass123')
        self.client.force_authenticate(user=other_user)

        response = self.client.get(f'/api/sos/alerts/{alert.id}/audio-stream/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_alert_rejects_when_not_enough_contacts(self):
        user = User.objects.create_user(username='sos-user-insufficient', password='StrongPass123')
        self.client.force_authenticate(user=user)
        EmergencyContact.objects.create(user=user, name='Only One', phone_number='+243810000221')

        response = self.client.post('/api/sos/alerts/', {'network_type': 'wifi'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('required_contacts', response.data)


class SosServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sos-service-user', password='StrongPass123')
        self.alert = SOSAlert.objects.create(user=self.user, status='active')
        EmergencyContact.objects.create(
            user=self.user,
            name='Service Contact',
            phone_number='+243810000222'
        )

    def test_send_sos_sms_requires_location_when_flag_enabled(self):
        sent = SMSService.send_sos_sms(self.alert, require_location=True)
        self.assertEqual(sent, 0)

        self.alert.refresh_from_db()
        self.assertFalse(self.alert.sms_fallback_sent)

    def test_send_sos_sms_marks_alert_when_location_available(self):
        LocationUpdate.objects.create(alert=self.alert, latitude=-4.325, longitude=15.322)

        sent = SMSService.send_sos_sms(self.alert, require_location=True)
        self.assertGreater(sent, 0)

        self.alert.refresh_from_db()
        self.assertTrue(self.alert.sms_fallback_sent)
        self.assertIsNotNone(self.alert.public_tracking_token)


class SosTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sos-task-user', password='StrongPass123')
        self.alert = SOSAlert.objects.create(user=self.user, status='active', sms_fallback_sent=False)
        EmergencyContact.objects.create(
            user=self.user,
            name='Task Contact',
            phone_number='+243810000333'
        )
        LocationUpdate.objects.create(alert=self.alert, latitude=-4.325, longitude=15.322)

    def test_retry_sos_sms_fallback_sends_when_available(self):
        with patch('sos.tasks.SMSService.send_sos_sms', return_value=1) as mocked_send:
            result = retry_sos_sms_fallback.apply(args=[str(self.alert.id)]).get()

        self.assertEqual(result['status'], 'sent')
        mocked_send.assert_called_once()
        self.assertEqual(mocked_send.call_args.kwargs.get('allow_mock'), False)

    def test_retry_pending_sos_sms_queues_only_pending_active_alerts(self):
        resolved_alert = SOSAlert.objects.create(user=self.user, status='resolved', sms_fallback_sent=False)
        LocationUpdate.objects.create(alert=resolved_alert, latitude=-4.3, longitude=15.3)

        with patch('sos.tasks.retry_sos_sms_fallback.delay') as mocked_delay:
            result = retry_pending_sos_sms()

        self.assertEqual(result['retried'], 1)
        mocked_delay.assert_called_once_with(str(self.alert.id))

    @override_settings(SOS_AUDIO_RETENTION_ENABLED=True, SOS_AUDIO_RETENTION_DAYS=1)
    def test_purge_expired_sos_audio_evidence_deletes_old_audio(self):
        old_alert = SOSAlert.objects.create(
            user=self.user,
            status='resolved',
            created_at=timezone.now() - timedelta(days=2),
        )
        # Force created_at in DB because auto_now_add ignores explicit value on create.
        SOSAlert.objects.filter(id=old_alert.id).update(created_at=timezone.now() - timedelta(days=2))
        old_alert.refresh_from_db()

        audio = SimpleUploadedFile('old-proof.mp3', b'old-audio', content_type='audio/mpeg')
        self.client.force_authenticate(user=self.user)
        upload = self.client.post(f'/api/sos/alerts/{old_alert.id}/audio/', {'audio': audio}, format='multipart')
        self.assertEqual(upload.status_code, status.HTTP_201_CREATED)

        result = purge_expired_sos_audio_evidence()
        self.assertGreaterEqual(result['deleted'], 1)

        old_alert.refresh_from_db()
        self.assertFalse(bool(old_alert.audio_evidence))
