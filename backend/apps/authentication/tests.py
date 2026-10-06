"""
apps/authentication/tests.py

Unit tests for the authentication module.
Run with: python manage.py test apps.authentication
"""
from django.urls import reverse
# pyrefly: ignore [missing-import]
from rest_framework import status
# pyrefly: ignore [missing-import]
from rest_framework.test import APITestCase
# pyrefly: ignore [missing-import]
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserRegistrationTests(APITestCase):
    """Tests for POST /api/auth/register/"""

    url = '/api/auth/register/'

    def test_successful_registration(self):
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(User.objects.count(), 1)

    def test_password_mismatch(self):
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'StrongPass123!',
            'password_confirm': 'WrongPass',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email(self):
        User.objects.create_user(email='test@example.com', password='pass', full_name='Existing')
        data = {
            'email': 'test@example.com',
            'full_name': 'Another User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(APITestCase):
    """Tests for POST /api/auth/login/"""

    url = '/api/auth/login/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='login@example.com',
            password='TestPass456!',
            full_name='Login User',
        )

    def test_successful_login(self):
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'TestPass456!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    def test_wrong_password(self):
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'WrongPassword!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_user(self):
        response = self.client.post(self.url, {
            'email': 'nobody@example.com',
            'password': 'anypass',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTests(APITestCase):
    """Tests for GET/PATCH /api/auth/profile/"""

    url = '/api/auth/profile/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='TestPass789!',
            full_name='Profile User',
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'profile@example.com')

    def test_update_profile(self):
        response = self.client.patch(self.url, {'full_name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['full_name'], 'Updated Name')

    def test_profile_requires_auth(self):
        self.client.credentials()  # Clear auth
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    """Tests for POST /api/auth/logout/"""

    url = '/api/auth/logout/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@example.com',
            password='TestPass000!',
            full_name='Logout User',
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')

    def test_successful_logout(self):
        response = self.client.post(self.url, {'refresh': str(self.refresh)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_token(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
