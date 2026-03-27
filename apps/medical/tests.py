from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from medical.models import Doctor, Appointment, MedicalEntry

User = get_user_model()


class MedicalWorkflowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='medical-user', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        self.doctor = Doctor.objects.create(
            name='Jean Kabasele',
            specialty='Trauma',
            phone_number='+243810003001',
            is_available=True,
        )

    def test_due_reminders_returns_upcoming_appointments(self):
        soon = timezone.now() + timedelta(hours=5)
        Appointment.objects.create(user=self.user, doctor=self.doctor, date=soon, status='confirmed')
        Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(hours=30),
            status='confirmed',
        )

        response = self.client.get('/api/medical/appointments/due-reminders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('medical.views.send_due_appointment_reminders.delay')
    def test_send_reminders_action_queues_task(self, mocked_delay):
        self.user.profile.role = 'doctor'
        self.user.profile.save(update_fields=['role'])
        mocked_delay.return_value.id = 'task-123'
        response = self.client.post('/api/medical/appointments/send-reminders/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['queued'])
        mocked_delay.assert_called_once()

    @patch('medical.views.send_due_appointment_reminders.delay')
    def test_send_reminders_action_rejects_unauthorized_user(self, mocked_delay):
        response = self.client.post('/api/medical/appointments/send-reminders/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mocked_delay.assert_not_called()

    def test_advance_care_stage_moves_forward(self):
        entry = MedicalEntry.objects.create(
            user=self.user,
            description='Blessure au bras',
            severity='medium',
            pain_level=6,
        )

        response = self.client.post(f'/api/medical/entries/{entry.id}/advance-care-stage/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry.refresh_from_db()
        self.assertEqual(entry.care_stage, MedicalEntry.CARE_STAGE_TREATMENT)
