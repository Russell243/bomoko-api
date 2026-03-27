from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from notifications.models import UserNotification
from notifications.services import create_user_notification
from notifications.tasks import send_push_for_notification
from sos.models import SOSAlert
from sos.models import EmergencyContact

User = get_user_model()


class NotificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notif-user', password='StrongPass123')
        self.client.force_authenticate(user=self.user)

    def test_list_returns_only_authenticated_user_notifications(self):
        other = User.objects.create_user(username='other-notif-user', password='StrongPass123')
        own = UserNotification.objects.create(user=self.user, title='A', body='B')
        UserNotification.objects.create(user=other, title='X', body='Y')

        response = self.client.get('/api/notifications/user-notifications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(own.id))

    def test_mark_read_sets_is_read_true(self):
        notification = UserNotification.objects.create(user=self.user, title='Need attention', body='Body')

        response = self.client.post(f'/api/notifications/user-notifications/{notification.id}/mark-read/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    @patch('notifications.tasks.send_push_for_notification.delay')
    def test_create_notification_endpoint_enqueues_push_task(self, mocked_delay):
        payload = {
            'title': 'Titre test',
            'body': 'Body test',
            'notification_type': UserNotification.TYPE_INFO,
        }

        response = self.client.post('/api/notifications/user-notifications/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserNotification.objects.filter(user=self.user).count(), 1)
        mocked_delay.assert_called_once()


class NotificationServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notif-service-user', password='StrongPass123')
        self.user.profile.firebase_token = 'ExponentPushToken[test-token]'
        self.user.profile.save(update_fields=['firebase_token'])

    @patch('notifications.tasks.send_push_for_notification.delay')
    def test_create_user_notification_creates_record_and_enqueues_push(self, mocked_delay):
        notification = create_user_notification(
            user=self.user,
            title='Service title',
            body='Service body',
            notification_type=UserNotification.TYPE_ALERT,
            metadata={'a': 1},
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, UserNotification.TYPE_ALERT)
        mocked_delay.assert_called_once_with(str(notification.id))

    @patch('notifications.tasks.send_expo_push', return_value=True)
    def test_send_push_for_notification_uses_profile_token(self, mocked_push):
        notification = UserNotification.objects.create(
            user=self.user,
            title='Push title',
            body='Push body',
            metadata={'screen': 'alerts'},
        )

        result = send_push_for_notification(str(notification.id))

        self.assertEqual(result['status'], 'sent')
        mocked_push.assert_called_once()


class SosNotificationIntegrationTests(APITestCase):
    def setUp(self):
        self.victim = User.objects.create_user(username='victim-user', password='StrongPass123')
        self.counselor = User.objects.create_user(username='counselor-user', password='StrongPass123')
        self.counselor.profile.role = 'counselor'
        self.counselor.profile.save(update_fields=['role'])
        EmergencyContact.objects.create(user=self.victim, name='Trust 1', phone_number='+243810001001')
        EmergencyContact.objects.create(user=self.victim, name='Trust 2', phone_number='+243810001002')
        EmergencyContact.objects.create(user=self.victim, name='Trust 3', phone_number='+243810001003')
        self.client.force_authenticate(user=self.victim)

    @patch('notifications.tasks.send_push_for_notification.delay')
    def test_create_sos_alert_creates_notifications(self, mocked_delay):
        response = self.client.post('/api/sos/alerts/', {'network_type': 'wifi'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        alert_id = response.data['id']
        self.assertTrue(
            UserNotification.objects.filter(user=self.victim, metadata__alert_id=alert_id).exists()
        )
        self.assertTrue(
            UserNotification.objects.filter(user=self.counselor, metadata__alert_id=alert_id).exists()
        )
        self.assertGreaterEqual(mocked_delay.call_count, 2)

    @patch('notifications.tasks.send_push_for_notification.delay')
    def test_resolve_sos_alert_creates_resolution_notification(self, mocked_delay):
        alert = SOSAlert.objects.create(user=self.victim, status='active')

        response = self.client.post(f'/api/sos/alerts/{alert.id}/resolve/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(
            UserNotification.objects.filter(
                user=self.victim,
                title='Alerte SOS resolue',
                metadata__alert_id=str(alert.id),
            ).exists()
        )
        self.assertTrue(mocked_delay.called)
