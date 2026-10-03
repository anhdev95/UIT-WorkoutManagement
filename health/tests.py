from rest_framework import status
from rest_framework.test import APITestCase

from accounts.tests import create_user

from .models import HealthRecord


class HealthRecordTests(APITestCase):
    url = '/api/health-records/'

    def setUp(self):
        self.user = create_user('duc')
        self.user.profile.height_cm = 168
        self.user.profile.save()
        self.client.force_authenticate(self.user)

    def test_create_valid_and_bmi_calculated(self):
        res = self.client.post(self.url, {'weight_kg': 72, 'recorded_date': '2026-09-01'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # 72 / (1.68 ^ 2) = 25.51
        self.assertEqual(res.data['bmi'], 25.51)

    def test_bmi_cannot_be_sent_by_client(self):
        res = self.client.post(self.url, {'weight_kg': 72, 'bmi': 10})
        self.assertEqual(res.data['bmi'], 25.51)

    def test_bmi_recalculated_on_update(self):
        record = self.client.post(self.url, {'weight_kg': 72}).data
        res = self.client.patch(f'{self.url}{record["id"]}/', {'weight_kg': 70.5})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['bmi'], 24.98)

    def test_negative_weight(self):
        res = self.client.post(self.url, {'weight_kg': -5})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_future_date(self):
        res = self.client.post(self.url, {'weight_kg': 70, 'recorded_date': '2999-01-01'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_height_in_profile(self):
        self.user.profile.height_cm = None
        self.user.profile.save()
        res = self.client.post(self.url, {'weight_kg': 70})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('height_cm', res.data)

    def test_filter_by_date_range(self):
        for day in ['2026-08-01', '2026-09-10', '2026-09-20']:
            self.client.post(self.url, {'weight_kg': 70, 'recorded_date': day})
        res = self.client.get(f'{self.url}?from=2026-09-01&to=2026-09-30')
        self.assertEqual(len(res.data), 2)

    def test_invalid_date_filter(self):
        res = self.client.get(f'{self.url}?from=abc')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_access_other_users_record(self):
        other = create_user('lan')
        record = HealthRecord.objects.create(user=other, weight_kg=50, bmi=20)
        self.assertEqual(self.client.get(f'{self.url}{record.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(f'{self.url}{record.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(self.client.get(self.url).data), 0)

    def test_delete_own_record(self):
        record = self.client.post(self.url, {'weight_kg': 72}).data
        res = self.client.delete(f'{self.url}{record["id"]}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_no_token(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
