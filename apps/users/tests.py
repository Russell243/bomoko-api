from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UsersApiTests(APITestCase):
    def test_register_creates_profile_and_tokens(self):
        payload = {
            "username": "test-user",
            "phone_number": "+243810000000",
            "password": "StrongPass123",
            "role": "counselor",
            "first_name": "Jean",
            "last_name": "Mukendi",
        }
        response = self.client.post('/api/users/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        user = User.objects.get(username='test-user')
        self.assertEqual(user.profile.role, 'victim')
        self.assertEqual(user.first_name, 'Jean')
        self.assertEqual(user.last_name, 'Mukendi')

    def test_verify_otp_rejects_without_bypass_code(self):
        user = User.objects.create_user(username='otp-user', password='StrongPass123')
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/users/verify-otp/', {'code': '123456'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DEBUG=True, OTP_BYPASS_CODE='654321')
    def test_verify_otp_accepts_debug_bypass_code(self):
        user = User.objects.create_user(username='otp-user-2', password='StrongPass123')
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/users/verify-otp/', {'code': '654321'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_change_password_requires_correct_current_password(self):
        user = User.objects.create_user(username='pwd-user', password='StrongPass123')
        self.client.force_authenticate(user=user)

        response = self.client.post(
            '/api/users/change-password/',
            {'current_password': 'WrongPass', 'new_password': 'NewStrongPass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success(self):
        user = User.objects.create_user(username='pwd-user-2', password='StrongPass123')
        self.client.force_authenticate(user=user)

        response = self.client.post(
            '/api/users/change-password/',
            {'current_password': 'StrongPass123', 'new_password': 'NewStrongPass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.check_password('NewStrongPass123'))

    def test_deactivate_account(self):
        user = User.objects.create_user(username='deactivate-user', password='StrongPass123')
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/users/deactivate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_delete_account_anonymizes_and_disables_user(self):
        user = User.objects.create_user(
            username='delete-user',
            phone_number='+243810000777',
            password='StrongPass123',
            first_name='Delete',
            last_name='User',
            email='delete@example.com',
        )
        user.profile.firebase_token = 'ExpoPushToken[test-token]'
        user.profile.biometric_enabled = True
        user.profile.app_pin_hash = 'hash'
        user.profile.save(update_fields=['firebase_token', 'biometric_enabled', 'app_pin_hash'])
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/users/delete/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)
        self.assertIsNone(user.phone_number)
        self.assertEqual(user.email, '')
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertTrue(user.username.startswith('deleted-'))
        self.assertFalse(user.has_usable_password())

        user.profile.refresh_from_db()
        self.assertIsNone(user.profile.firebase_token)
        self.assertFalse(user.profile.biometric_enabled)
        self.assertIsNone(user.profile.app_pin_hash)

    def test_victim_onboarding_end_to_end_to_sos(self):
        register_payload = {
            "username": "victim-e2e",
            "phone_number": "+243810000900",
            "password": "StrongPass123",
            "role": "victim",
        }
        register_response = self.client.post('/api/users/register/', register_payload, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        login_response = self.client.post(
            '/api/users/login/',
            {"username": "victim-e2e", "password": "StrongPass123"},
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        profile_response = self.client.get('/api/users/profile/')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        for idx in range(3):
            contact_response = self.client.post(
                '/api/sos/contacts/',
                {
                    "name": f"Contact {idx+1}",
                    "phone_number": f"+24381000091{idx}",
                    "relationship": "trusted",
                },
                format='json',
            )
            self.assertEqual(contact_response.status_code, status.HTTP_201_CREATED)

        alert_response = self.client.post('/api/sos/alerts/', {"network_type": "4g"}, format='json')
        self.assertEqual(alert_response.status_code, status.HTTP_201_CREATED)
        alert_id = alert_response.data['id']

        location_response = self.client.post(
            f'/api/sos/alerts/{alert_id}/location/',
            {"latitude": -4.325, "longitude": 15.322},
            format='json',
        )
        self.assertEqual(location_response.status_code, status.HTTP_201_CREATED)

        resolve_response = self.client.post(f'/api/sos/alerts/{alert_id}/resolve/', {}, format='json')
        self.assertEqual(resolve_response.status_code, status.HTTP_200_OK)
