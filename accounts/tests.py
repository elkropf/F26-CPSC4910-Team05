from django.db import models
from django.test import TestCase
from django.urls import reverse
from .models import User, Driver, Sponsor, Admin

# Create your tests here.
class ModelTests(TestCase):
    def test_user_marked_active_when_created(self):
        new_user = User()
        self.assertIs(new_user.is_active(), True)

    def test_user_type_init(self):
        new_user = User(user_type='driver')
        self.assertIs(new_user.user_type, 'Driver')

class ViewTests(TestCase):
    def test_find_register_page(self):
        response = self.client.get(reverse("accounts:register_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Register</h2>", html=True)

    def test_find_login_page(self):
        response = self.client.get(reverse("accounts:login_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Login</h2>", html=True)