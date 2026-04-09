from django.test import TestCase
from django.urls import reverse

from .models import AdminCode, CustomUser


class AdminRegistrationTests(TestCase):
    def setUp(self):
        self.url = reverse('register_admin')
        self.creator = CustomUser.objects.create_user(
            email='creator@example.com',
            password='CreatorPass123!',
            user_type='ADMIN',
            phone_number='+1234567890',
            is_staff=True,
        )
        self.admin_code = AdminCode.objects.create(
            code='VALID-ADMIN-CODE',
            created_by=self.creator,
            is_active=True,
        )

    def test_admin_registration_saves_phone_number(self):
        response = self.client.post(
            self.url,
            data={
                'email': 'newadmin@example.com',
                'phone_number': '+19876543210',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'admin_code': self.admin_code.code,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

        created_user = CustomUser.objects.get(email='newadmin@example.com')
        self.assertEqual(created_user.phone_number, '+19876543210')
        self.assertEqual(created_user.user_type, 'ADMIN')
        self.assertTrue(created_user.is_staff)

        self.admin_code.refresh_from_db()
        self.assertEqual(self.admin_code.used_count, 1)
        self.assertEqual(self.admin_code.last_used_by, created_user)

    def test_admin_registration_requires_phone_number(self):
        response = self.client.post(
            self.url,
            data={
                'email': 'missingphone@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'admin_code': self.admin_code.code,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'phone_number', 'Phone number is required.')
        self.assertFalse(CustomUser.objects.filter(email='missingphone@example.com').exists())

    def test_admin_registration_rejects_invalid_admin_code_even_with_phone(self):
        response = self.client.post(
            self.url,
            data={
                'email': 'invalidcode@example.com',
                'phone_number': '+15551234567',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'admin_code': 'BAD-CODE',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            'form',
            'admin_code',
            'Invalid admin authorization code. Access denied.',
        )
        self.assertFalse(CustomUser.objects.filter(email='invalidcode@example.com').exists())
