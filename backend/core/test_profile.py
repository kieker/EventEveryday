from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="old@example.com", email="old@example.com", password="test-password")
        self.client.force_login(self.user)

    def update(self, **data):
        return self.client.patch("/api/auth/me/", data, content_type="application/json")

    def test_name_and_privilege_fields(self):
        self.assertEqual(self.update(full_name="New Name", is_staff=True).status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), "New Name")
        self.assertFalse(self.user.is_staff)

    def test_email_requires_password_and_changes_login(self):
        self.assertEqual(self.update(email="new@example.com").status_code, 400)
        self.assertEqual(self.update(email="NEW@example.com", current_password="test-password", full_name="New Name").status_code, 200)
        self.assertTrue(self.client.login(username="new@example.com", password="test-password"))

    def test_duplicate_and_invalid_email(self):
        get_user_model().objects.create_user(username="taken@example.com", email="taken@example.com")
        for email in ("bad", "taken@example.com"):
            self.assertEqual(self.update(email=email, current_password="test-password").status_code, 400)

    def test_authentication_and_csrf_required(self):
        self.client.logout()
        self.assertEqual(self.update(full_name="New Name").status_code, 401)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.patch("/api/auth/me/", {"full_name": "New Name"}, content_type="application/json").status_code, 403)
