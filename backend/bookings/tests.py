from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event

from .models import Booking
from .services import create_guest_booking


def make_event(**overrides):
    start_at = timezone.now() + timedelta(days=14)
    values = {
        "title": "Booking Test Event",
        "summary": "An event used to verify booking behavior.",
        "description": "A complete description for the booking test event.",
        "venue_name": "Test Venue",
        "venue_address": "1 Test Street, Johannesburg",
        "start_at": start_at,
        "end_at": start_at + timedelta(hours=3),
        "capacity": 4,
        "price": Decimal("275.00"),
        "status": Event.Status.PUBLISHED,
    }
    values.update(overrides)
    return Event.objects.create(**values)


def booking_payload(event, attendees=None):
    names = attendees or ["Guest Attendee"]
    return {
        "event_slug": event.slug,
        "contact_name": "Guest Booker",
        "contact_email": "guest@example.com",
        "contact_phone": "+27 82 000 0000",
        "attendees": [{"full_name": name} for name in names],
    }


class BookingCreationTests(TestCase):
    def test_guest_booking_snapshots_price_and_creates_named_attendees(self):
        event = make_event()

        booking, _ = create_guest_booking(
            event=event,
            contact_name="Guest Booker",
            contact_email="GUEST@example.com",
            contact_phone="",
            attendees=["First Attendee", "Second Attendee"],
        )
        event.price = Decimal("999.00")
        event.save(update_fields=["price"])

        booking.refresh_from_db()
        self.assertEqual(booking.quantity, 2)
        self.assertEqual(booking.unit_price, Decimal("275.00"))
        self.assertEqual(booking.total, Decimal("550.00"))
        self.assertEqual(booking.contact_email, "guest@example.com")
        self.assertEqual(
            list(booking.attendees.values_list("full_name", flat=True)),
            ["First Attendee", "Second Attendee"],
        )

    def test_expired_hold_is_released_before_new_booking(self):
        event = make_event(capacity=1)
        first, _ = create_guest_booking(
            event=event,
            contact_name="First Guest",
            contact_email="first@example.com",
            contact_phone="",
            attendees=["First Guest"],
        )
        first.expires_at = timezone.now() - timedelta(seconds=1)
        first.save(update_fields=["expires_at"])

        second, _ = create_guest_booking(
            event=event,
            contact_name="Second Guest",
            contact_email="second@example.com",
            contact_phone="",
            attendees=["Second Guest"],
        )

        first.refresh_from_db()
        self.assertEqual(first.status, Booking.Status.EXPIRED)
        self.assertEqual(second.status, Booking.Status.PENDING_PAYMENT)


class BookingApiTests(TestCase):
    def test_cors_preflight_allows_booking_token_header(self):
        response = self.client.options(
            reverse("bookings:detail", args=["EVT-TEST"]),
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-booking-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "x-booking-token",
            response.headers["Access-Control-Allow-Headers"],
        )

    def test_guest_can_create_booking_and_access_it_with_returned_token(self):
        event = make_event()

        create_response = self.client.post(
            reverse("bookings:create"),
            booking_payload(event, ["One Guest", "Two Guest"]),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        body = create_response.json()
        self.assertEqual(body["quantity"], 2)
        self.assertEqual(body["total"], "550.00")
        self.assertIn("access_token", body)

        detail_url = reverse("bookings:detail", args=[body["reference"]])
        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(
            self.client.get(detail_url, HTTP_X_BOOKING_TOKEN="incorrect").status_code,
            404,
        )
        detail_response = self.client.get(
            detail_url,
            HTTP_X_BOOKING_TOKEN=body["access_token"],
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["contact_email"], "guest@example.com")

    def test_booking_cannot_exceed_remaining_capacity(self):
        event = make_event(capacity=1)
        first = self.client.post(
            reverse("bookings:create"),
            booking_payload(event),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("bookings:create"),
            booking_payload(event, ["Another Guest"]),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(Booking.objects.count(), 1)

    def test_draft_event_cannot_be_booked(self):
        event = make_event(status=Event.Status.DRAFT)

        response = self.client.post(
            reverse("bookings:create"),
            booking_payload(event),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_detail_request_expires_stale_booking(self):
        event = make_event()
        booking, token = create_guest_booking(
            event=event,
            contact_name="Guest Booker",
            contact_email="guest@example.com",
            contact_phone="",
            attendees=["Guest Booker"],
        )
        booking.expires_at = timezone.now() - timedelta(seconds=1)
        booking.save(update_fields=["expires_at"])

        response = self.client.get(
            reverse("bookings:detail", args=[booking.reference]),
            HTTP_X_BOOKING_TOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Booking.Status.EXPIRED)

    def test_guest_can_edit_pending_booking_with_access_token(self):
        event = make_event()
        booking, token = create_guest_booking(
            event=event,
            contact_name="Guest Booker",
            contact_email="guest@example.com",
            contact_phone="wrong number",
            attendees=["First Name", "Second Name"],
        )

        response = self.client.patch(
            reverse("bookings:detail", args=[booking.reference]),
            {
                "contact_name": "Updated Booker",
                "contact_email": "UPDATED@example.com",
                "contact_phone": "+27 82 123 4567",
                "attendees": [
                    {"full_name": "Correct First"},
                    {"full_name": "Correct Second"},
                ],
            },
            content_type="application/json",
            HTTP_X_BOOKING_TOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.contact_phone, "+27 82 123 4567")
        self.assertEqual(booking.contact_email, "updated@example.com")
        self.assertEqual(
            list(booking.attendees.values_list("full_name", flat=True)),
            ["Correct First", "Correct Second"],
        )

    def test_booking_edit_requires_access_and_pending_status(self):
        event = make_event()
        booking, token = create_guest_booking(
            event=event,
            contact_name="Guest Booker",
            contact_email="guest@example.com",
            contact_phone="",
            attendees=["Guest Booker"],
        )
        payload = {
            "contact_name": "Changed",
            "contact_email": "changed@example.com",
            "contact_phone": "",
            "attendees": [{"full_name": "Changed"}],
        }

        self.assertEqual(
            self.client.patch(
                reverse("bookings:detail", args=[booking.reference]),
                payload,
                content_type="application/json",
            ).status_code,
            404,
        )
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status"])
        self.assertEqual(
            self.client.patch(
                reverse("bookings:detail", args=[booking.reference]),
                payload,
                content_type="application/json",
                HTTP_X_BOOKING_TOKEN=token,
            ).status_code,
            409,
        )

    def test_signed_in_booking_is_owned_and_listed_for_customer(self):
        user = get_user_model().objects.create_user(
            username="customer@example.com",
            email="customer@example.com",
            password="test-password-not-used-elsewhere",
        )
        other_user = get_user_model().objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="test-password-not-used-elsewhere",
        )
        event = make_event()
        self.client.force_login(user)

        response = self.client.post(
            reverse("bookings:create"),
            booking_payload(event),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        booking = Booking.objects.get(reference=response.json()["reference"])
        self.assertEqual(booking.user, user)
        history = self.client.get(reverse("my-bookings"))
        self.assertEqual(history.status_code, 200)
        self.assertEqual([item["reference"] for item in history.json()], [booking.reference])

        self.client.force_login(other_user)
        self.assertEqual(self.client.get(reverse("my-bookings")).json(), [])
