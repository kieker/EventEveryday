import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
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
        self.assertContains(response, "Visit site")
        self.assertContains(response, 'class="admin-page-bar"')
        self.assertContains(response, 'class="change-password-link"')
        self.assertContains(response, "Log out")

        content = response.content.decode()
        self.assertLess(content.index("app-events module"), content.index("app-bookings module"))
        self.assertLess(content.index("app-bookings module"), content.index("app-payments module"))
        self.assertLess(content.index("app-payments module"), content.index("app-auth module"))
        self.assertLess(
            content.index("model-payment\""),
            content.index("model-paymentwebhookevent\""),
        )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CustomerAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def csrf_token(self):
        response = self.client.get(reverse("core:auth-csrf"))
        self.assertEqual(response.status_code, 200)
        return response.json()["csrf_token"]

    def test_customer_can_register_and_use_session(self):
        response = self.client.post(
            reverse("core:auth-register"),
            {
                "full_name": "Ava Customer",
                "email": "AVA@example.com",
                "password": "A-strong-customer-password-2026!",
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "ava@example.com")
        self.assertEqual(response.json()["full_name"], "Ava Customer")
        self.assertFalse(response.json()["is_staff"])
        self.assertEqual(self.client.get(reverse("core:auth-me")).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome to EventEveryday")
        self.assertIn("text/html", [alternative[1] for alternative in mail.outbox[0].alternatives])

    def test_staff_status_is_included_in_current_user(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="test-password-not-used-elsewhere",
            is_staff=True,
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("core:auth-me"))

        self.assertTrue(response.json()["is_staff"])

    def test_registration_requires_csrf_token(self):
        response = self.client.post(
            reverse("core:auth-register"),
            {"full_name": "Ava Customer", "email": "ava@example.com", "password": "password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)


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
