from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from legal.models import LegalCase

User = get_user_model()


class LegalWorkflowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='legal-user', password='StrongPass123')
        self.client.force_authenticate(user=self.user)

    def _create_case(self):
        response = self.client.post(
            '/api/legal/cases/',
            {
                'case_type': 'complaint',
                'title': 'Plainte campus',
                'description': 'Details du dossier',
                'is_anonymous': True,
                'is_urgent': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['id']

    def test_transition_valid_path(self):
        case_id = self._create_case()

        response = self.client.post(
            f'/api/legal/cases/{case_id}/transition/',
            {'to_status': 'in_review', 'note': 'Analyse initiale'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_review')

    def test_transition_invalid_path_rejected(self):
        case_id = self._create_case()
        response = self.client.post(
            f'/api/legal/cases/{case_id}/transition/',
            {'to_status': 'resolved'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_history_contains_creation_event(self):
        case_id = self._create_case()
        response = self.client.get(f'/api/legal/cases/{case_id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['event_type'], 'status_change')

    def test_add_note_creates_event(self):
        case_id = self._create_case()
        response = self.client.post(
            f'/api/legal/cases/{case_id}/add-note/',
            {'note': 'Client contacte pour pieces supplementaires'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['event_type'], 'note')

    def test_user_cannot_see_other_case(self):
        case_id = self._create_case()
        other = User.objects.create_user(username='legal-other', password='StrongPass123')
        self.client.force_authenticate(user=other)
        response = self.client.get(f'/api/legal/cases/{case_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
