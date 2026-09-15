import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from payments.models import Payment

from .models import Booking
from .services import create_guest_booking
from .tests import make_event


class BookingExportTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser(
            username="export-admin", email="admin@example.com", password="test-password"
        ))
        self.event = make_event()

    def make_booking(self, event=None):
        booking, _ = create_guest_booking(
            event=event or self.event, contact_name="Export Guest",
            contact_email="guest@example.com", contact_phone="",
            attendees=["Export Guest"],
        )
        return booking

    def export(self, bookings, query=""):
        response = self.client.post(reverse("admin:bookings_booking_changelist") + query, {
            "action": "export_csv", "_selected_action": [b.pk for b in bookings],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        return list(csv.DictReader(StringIO(response.content.decode())))

    def test_export_payment_details_and_missing_values(self):
        paid, pending, no_payment = [self.make_booking() for _ in range(3)]
        paid.status = Booking.Status.CONFIRMED
        paid.save(update_fields=["status"])
        paid_at = timezone.now()
        Payment.objects.create(booking=paid, amount=paid.total, status=Payment.Status.COMPLETE,
                               provider_transaction_reference="123456789", paid_at=paid_at)
        Payment.objects.create(booking=pending, amount=pending.total)
        rows = {row["Booking reference"]: row for row in self.export([paid, pending, no_payment])}
        self.assertEqual(rows[paid.reference]["Payment reference"], "123456789")
        self.assertEqual(rows[paid.reference]["Confirmation time"], paid_at.isoformat())
        for booking in (pending, no_payment):
            self.assertEqual(rows[booking.reference]["Payment reference"], "")
            self.assertEqual(rows[booking.reference]["Confirmation time"], "")

    def test_calendar_management_filters_apply_to_export(self):
        confirmed = self.make_booking()
        pending = self.make_booking()
        other_event = self.make_booking(make_event(title="Other Event"))
        Booking.objects.filter(pk__in=[confirmed.pk, other_event.pk]).update(status=Booking.Status.CONFIRMED)
        rows = self.export([confirmed, pending, other_event],
                           f"?event__id__exact={self.event.pk}&status__exact=confirmed")
        self.assertEqual([row["Booking reference"] for row in rows], [confirmed.reference])

    def test_late_payment_has_no_confirmation_time(self):
        booking = self.make_booking()
        booking.status = Booking.Status.EXPIRED
        booking.save(update_fields=["status"])
        Payment.objects.create(booking=booking, amount=booking.total,
                               status=Payment.Status.COMPLETE, paid_at=timezone.now(),
                               provider_transaction_reference="late-payment")
        row = self.export([booking])[0]
        self.assertEqual(row["Confirmation time"], "")
        self.assertEqual(row["Payment reference"], "late-payment")

    def test_attendee_list_and_export_deny_unauthorized_users(self):
        booking = self.make_booking()
        users = [None,
                 get_user_model().objects.create_user(username="customer"),
                 get_user_model().objects.create_user(username="staff-no-permissions", is_staff=True)]
        for user in users:
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                responses = [
                    self.client.get(reverse("admin:bookings_attendee_changelist")),
                    self.client.post(reverse("admin:bookings_booking_changelist"), {
                        "action": "export_csv", "_selected_action": [booking.pk],
                    }),
                ]
                for response in responses:
                    self.assertEqual(response.status_code, 403 if user and user.is_staff else 302)
                    self.assertNotIn(b"Export Guest", response.content)
                    self.assertNotEqual(response.get("Content-Type"), "text/csv")

    def test_admin_can_list_attendees(self):
        self.make_booking()
        self.assertContains(self.client.get(reverse("admin:bookings_attendee_changelist")), "Export Guest")
