import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check(self):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "ok", "service": "eventeveryday-api"}
        )

    def test_admin_login_uses_eventeveryday_branding(self):
        response = self.client.get("/admin/login/")

        self.assertContains(response, "EventEveryday")
        self.assertContains(response, "admin/css/eventeveryday.css")

    def test_admin_navigation_sidebar_is_disabled(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username="navigation-admin@example.com",
            email="navigation-admin@example.com",
            password="test-password-not-used-elsewhere",
        )
        self.client.force_login(admin_user)

        response = self.client.get("/admin/")

        self.assertNotContains(response, 'id="nav-sidebar"')
        self.assertNotContains(response, "Toggle navigation")
        self.assertContains(response, "View site")
        self.assertContains(response, "Log out")


class SeedDevelopmentAdminTests(TestCase):
    @patch.dict(
        os.environ,
        {
            "DEV_ADMIN_USERNAME": "admin@example.com",
            "DEV_ADMIN_EMAIL": "admin@example.com",
            "DEV_ADMIN_PASSWORD": "test-password-not-used-elsewhere",
        },
        clear=False,
    )
    def test_seed_is_idempotent_and_creates_a_superuser(self):
        call_command("seed_dev_admin")
        call_command("seed_dev_admin")

        user_model = get_user_model()
        user = user_model.objects.get(username="admin@example.com")
        self.assertEqual(user_model.objects.count(), 1)
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("test-password-not-used-elsewhere"))
