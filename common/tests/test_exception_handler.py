from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ExceptionHandlerTests(APITestCase):
    """Every API error should come back in the same {'error': {...}} shape."""

    def test_unauthenticated_request_has_consistent_error_shape(self):
        response = self.client.get(reverse('accounts:me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('message', response.data['error'])
        self.assertIn('details', response.data['error'])

    def test_validation_error_has_consistent_error_shape(self):
        response = self.client.post(reverse('accounts:register'), {'username': 'onlyusername'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['message'], 'Validation failed.')

    def test_permission_denied_has_consistent_error_shape(self):
        candidate = User.objects.create_user(username='cand', password='pass12345', role='candidate')
        self.client.force_authenticate(user=candidate)
        response = self.client.post(reverse('company-list'), {'name': 'Should Fail Inc'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
