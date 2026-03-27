from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class HealthSystemApiTests(APITestCase):
    def test_system_health_returns_200_when_db_and_redis_are_ok(self):
        with patch('health.views.redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value.ping.return_value = True
            response = self.client.get('/api/health/system/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertTrue(response.data['database']['ok'])
        self.assertTrue(response.data['redis']['ok'])

    def test_system_health_returns_503_when_redis_fails(self):
        with patch('health.views.redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value.ping.side_effect = RuntimeError('redis down')
            response = self.client.get('/api/health/system/')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['status'], 'degraded')
        self.assertTrue(response.data['database']['ok'])
        self.assertFalse(response.data['redis']['ok'])
        self.assertNotIn('error', response.data['redis'])

    def test_system_health_hides_error_details_for_public_users(self):
        with patch('health.views.redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value.ping.side_effect = RuntimeError('redis down')
            response = self.client.get('/api/health/system/')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertNotIn('error', response.data['database'])
        self.assertNotIn('error', response.data['redis'])

    def test_system_health_exposes_error_details_to_staff(self):
        staff = User.objects.create_user(username='staff-health', password='StrongPass123', is_staff=True)
        self.client.force_authenticate(user=staff)

        with patch('health.views.redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value.ping.side_effect = RuntimeError('redis down')
            response = self.client.get('/api/health/system/')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data['database'])
        self.assertIn('error', response.data['redis'])
        self.assertEqual(response.data['redis']['error'], 'redis down')


class HealthMetricApiTests(APITestCase):
    def test_vitals_endpoint_requires_authentication(self):
        response = self.client.get('/api/health/vitals/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
