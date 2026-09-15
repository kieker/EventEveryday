from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event


def make_event(**overrides):
    start_at = timezone.now() + timedelta(days=10)
    values = {
        "title": "Cape Town Design Evening",
        "summary": "An evening of practical design talks.",
        "description": "Meet local designers and learn from short, useful talks.",
        "venue_name": "The Workshop",
        "venue_address": "1 Long Street, Cape Town",
        "start_at": start_at,
        "end_at": start_at + timedelta(hours=3),
        "capacity": 120,
        "price": Decimal("250.00"),
        "status": Event.Status.PUBLISHED,
    }
    values.update(overrides)
    return Event.objects.create(**values)


class CalendarApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="calendar-user")
        self.event = make_event(start_at="2026-09-30T23:00:00+02:00", end_at="2026-10-01T02:00:00+02:00")
        self.draft = make_event(title="Draft", status=Event.Status.DRAFT, start_at=self.event.start_at, end_at=self.event.end_at)
        self.url = reverse("events:calendar")

    def test_public_calendar_includes_overlapping_events_but_hides_drafts(self):
        response = self.client.get(self.url, {"month": "2026-10"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()], [self.event.pk])
        self.assertEqual(self.client.get(self.url, {"month": "2026-11"}).json(), [])

    def test_private_scopes_require_access_and_month_is_validated(self):
        for scope in ("mine", "admin"):
            self.assertEqual(self.client.get(self.url, {"month": "2026-10", "scope": scope}).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url, {"month": "2026-10", "scope": "admin"}).status_code, 403)
        for month in ("bad", "2026-13", "9999-12"):
            self.assertEqual(self.client.get(self.url, {"month": month}).status_code, 400)

    def test_customer_calendar_only_contains_own_confirmed_events_once(self):
        from bookings.models import Booking
        other = get_user_model().objects.create_user(username="other-calendar-user")
        for user, event, status in ((self.user, self.event, "confirmed"), (self.user, self.event, "confirmed"), (self.user, self.draft, "pending_payment"), (other, self.draft, "confirmed")):
            Booking.objects.create(user=user, event=event, status=status, contact_name="Guest", contact_email="guest@example.com", quantity=1, unit_price=250, total=250, expires_at=timezone.now())
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"month": "2026-10", "scope": "mine"})
        self.assertEqual([row["id"] for row in response.json()], [self.event.pk])

    def test_authorized_admin_can_see_drafts(self):
        from django.contrib.auth.models import Permission
        self.user.is_staff = True
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename="view_event"))
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"month": "2026-10", "scope": "admin"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)


class EventModelTests(TestCase):
    def test_slug_is_generated_and_made_unique(self):
        first = make_event()
        second = make_event(title=first.title)

        self.assertEqual(first.slug, "cape-town-design-evening")
        self.assertEqual(second.slug, "cape-town-design-evening-2")

    def test_end_must_be_after_start(self):
        start_at = timezone.now() + timedelta(days=1)
        event = Event(
            title="Invalid event",
            summary="Invalid schedule",
            description="This event has an invalid schedule.",
            venue_name="Test venue",
            venue_address="Test address",
            start_at=start_at,
            end_at=start_at,
            capacity=1,
            price=Decimal("0.00"),
        )

        with self.assertRaises(ValidationError):
            event.full_clean()


class PublishedEventApiTests(TestCase):
    def test_list_includes_published_events_and_excludes_drafts(self):
        published = make_event()
        make_event(title="Hidden draft", status=Event.Status.DRAFT)

        response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["slug"], published.slug)

    def test_detail_returns_published_event(self):
        event = make_event()

        response = self.client.get(reverse("events:detail", args=[event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["currency"], "ZAR")
        self.assertEqual(response.json()["description"], event.description)

    def test_detail_hides_draft_event(self):
        event = make_event(status=Event.Status.DRAFT)

        response = self.client.get(reverse("events:detail", args=[event.slug]))

        self.assertEqual(response.status_code, 404)

    def test_uploaded_image_takes_precedence_over_external_url(self):
        image = SimpleUploadedFile(
            "event.gif",
            (
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00"
                b"\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )
        event = make_event(image=image, image_url="https://example.com/fallback.jpg")
        try:
            response = self.client.get(reverse("events:detail", args=[event.slug]))

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["image_url"].startswith("/media/events/"))
        finally:
            event.image.delete(save=False)


class EventAdminDashboardTests(TestCase):
    def test_dashboard_lists_events_with_management_links(self):
        event = make_event()
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username="dashboard-admin@example.com",
            email="dashboard-admin@example.com",
            password="test-password-not-used-elsewhere",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:index"))

        self.assertContains(response, event.title)
        self.assertContains(response, reverse("admin:events_event_change", args=[event.pk]))
        self.assertContains(response, reverse("admin:events_event_delete", args=[event.pk]))
        self.assertContains(response, "Site management")
        content = response.content.decode()
        self.assertLess(content.index("Site management"), content.index(event.title))
        self.assertLess(content.index(event.title), content.index("Recent actions"))
