from django.test import TestCase
from django.contrib.auth.models import User
import json


class LoginUserTests(TestCase):
    def test_login_accepts_json_post(self):
        User.objects.create_user(username='testuser', password='secret123')

        response = self.client.post(
            '/djangoapp/login',
            data=json.dumps({'userName': 'testuser', 'password': 'secret123'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'Authenticated')

    def test_logout_clears_session(self):
        user = User.objects.create_user(username='logoutuser', password='secret123')
        self.client.force_login(user)

        response = self.client.get('/djangoapp/logout')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['userName'], '')

    def test_registration_creates_user(self):
        response = self.client.post(
            '/djangoapp/register',
            data=json.dumps({
                'userName': 'newuser',
                'password': 'secret123',
                'firstName': 'New',
                'lastName': 'User',
                'email': 'new@example.com',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'Authenticated')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_get_dealers_returns_json(self):
        response = self.client.get('/djangoapp/get_dealers')

        self.assertEqual(response.status_code, 200)
        self.assertIn('dealers', response.json())
