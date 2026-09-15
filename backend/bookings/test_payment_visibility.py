from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from payments.models import Payment
from .models import Booking
from .serializers import BookingUpdateSerializer
from .services import create_guest_booking
from .tests import make_event


class PaymentVisibilityAndEditTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="booking-owner")
        self.booking, self.token = create_guest_booking(
            event=make_event(), user=self.user, contact_name="Original",
            contact_email="owner@example.com", contact_phone="", attendees=["Original"],
        )
        self.url = reverse("bookings:detail", args=[self.booking.reference])

    def test_late_payment_visible_to_guest_and_owner(self):
        Booking.objects.filter(pk=self.booking.pk).update(status=Booking.Status.EXPIRED)
        Payment.objects.create(booking=self.booking, amount=self.booking.total,
                               status=Payment.Status.COMPLETE, paid_at=timezone.now())
        self.assertEqual(self.client.get(self.url).status_code, 404)
        data = self.client.get(self.url, HTTP_X_BOOKING_TOKEN=self.token).json()
        self.assertTrue(data["payment_received"])
        self.assertTrue(data["reconciliation_required"])
        self.client.force_login(self.user)
        data = self.client.get("/api/me/bookings/").json()[0]
        self.assertTrue(data["reconciliation_required"])
        Booking.objects.filter(pk=self.booking.pk).update(status=Booking.Status.CONFIRMED)
        self.assertFalse(self.client.get(self.url).json()["reconciliation_required"])

    def test_unpaid_booking_does_not_claim_payment_received(self):
        data = self.client.get(self.url, HTTP_X_BOOKING_TOKEN=self.token).json()
        self.assertFalse(data["payment_received"])
        self.assertFalse(data["reconciliation_required"])

    def test_edit_rechecks_after_validation(self):
        original_update = BookingUpdateSerializer.update
        for changes in ({"status": Booking.Status.CONFIRMED},
                        {"status": Booking.Status.PENDING_PAYMENT,
                         "expires_at": timezone.now() - timedelta(seconds=1)}):
            with self.subTest(changes=changes):
                Booking.objects.filter(pk=self.booking.pk).update(
                    status=Booking.Status.PENDING_PAYMENT,
                    expires_at=timezone.now() + timedelta(minutes=5))

                def raced_update(serializer, instance, data):
                    Booking.objects.filter(pk=instance.pk).update(**changes)
                    return original_update(serializer, instance, data)

                with patch.object(BookingUpdateSerializer, "update", raced_update):
                    response = self.client.patch(self.url, {
                        "contact_name": "Changed", "contact_email": "changed@example.com",
                        "attendees": [{"full_name": "Changed"}],
                    }, content_type="application/json", HTTP_X_BOOKING_TOKEN=self.token)
                self.assertEqual(response.status_code, 409)
                self.booking.refresh_from_db()
                self.assertEqual(self.booking.contact_name, "Original")
                self.assertEqual(self.booking.attendees.get().full_name, "Original")
