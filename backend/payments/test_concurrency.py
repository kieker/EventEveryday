from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.db import connection, connections, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from bookings.models import Booking
from bookings.services import BookingUnavailable, create_guest_booking, expire_booking_if_needed, reserved_quantity
from bookings.tests import make_event
from bookings.serializers import BookingEditConflict, BookingUpdateSerializer
from payments.models import Payment, PaymentWebhookEvent
from payments.services import build_checkout, process_notification
from payments.tests import PAYFAST_TEST_SETTINGS, PayFastNotificationTests


@PAYFAST_TEST_SETTINGS
@skipUnlessDBFeature("has_select_for_update")
class PaymentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.event = make_event(capacity=1)
        for target in ("valid_source_ip", "confirm_with_payfast"):
            patcher = patch(f"payments.services.{target}", return_value=True)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch("payments.services.send_booking_confirmed_email")
        self.confirm_email = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("bookings.services.send_booking_reserved_email")
        patcher.start()
        self.addCleanup(patcher.stop)

    def reserve(self):
        try:
            booking, _ = create_guest_booking(
                event=self.event, contact_name="Guest", contact_email="guest@example.com",
                contact_phone="", attendees=["Guest"],
            )
            return booking.pk
        except BookingUnavailable:
            return None

    def payload(self, booking, status="COMPLETE"):
        return PayFastNotificationTests.notification_payload(
            self, booking, amount=str(booking.total), status=status,
        )

    def concurrently(self, *actions):
        barrier = Barrier(len(actions))

        def run(action):
            connections.close_all()
            try:
                if connection.vendor == "postgresql":
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '5s'")
                        cursor.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=5)
                return action()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            futures = [pool.submit(run, action) for action in actions]
            return [future.result(timeout=20) for future in futures]

    def test_simultaneous_reservations_only_sell_last_ticket_once(self):
        results = self.concurrently(self.reserve, self.reserve, self.reserve)
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(reserved_quantity(self.event), 1)

    def test_identical_webhooks_create_one_record_and_send_one_email(self):
        booking = Booking.objects.get(pk=self.reserve())
        data = self.payload(booking)
        results = self.concurrently(*[
            lambda: process_notification(data, "127.0.0.1").accepted for _ in range(3)
        ])
        self.assertEqual(results, [True, True, True])
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.confirm_email.assert_called_once()

    def test_different_webhooks_cannot_downgrade_complete_payment(self):
        booking = Booking.objects.get(pk=self.reserve())
        complete, failed = self.payload(booking), self.payload(booking, "FAILED")
        self.concurrently(
            lambda: process_notification(complete, "127.0.0.1"),
            lambda: process_notification(failed, "127.0.0.1"),
        )
        self.assertEqual(Payment.objects.get().status, Payment.Status.COMPLETE)
        self.assertEqual(PaymentWebhookEvent.objects.filter(accepted=True).count(), 2)
        self.assertLessEqual(self.confirm_email.call_count, 1)

    def test_late_payment_racing_resale_does_not_oversell(self):
        booking = Booking.objects.get(pk=self.reserve())
        Booking.objects.filter(pk=booking.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        data = self.payload(booking)
        results = self.concurrently(
            self.reserve, lambda: process_notification(data, "127.0.0.1").accepted,
        )
        self.assertIsNotNone(results[0])
        self.assertTrue(results[1])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertEqual(reserved_quantity(self.event), 1)
        self.assertEqual(Payment.objects.get().status, Payment.Status.COMPLETE)
        self.assertIn("manual refund", PaymentWebhookEvent.objects.get().rejection_reason)
        self.confirm_email.assert_not_called()

    def test_payment_after_resale_cannot_confirm_expired_booking(self):
        booking = Booking.objects.get(pk=self.reserve())
        Booking.objects.filter(pk=booking.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertIsNotNone(self.reserve())
        process_notification(self.payload(booking), "127.0.0.1")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertEqual(reserved_quantity(self.event), 1)
        self.confirm_email.assert_not_called()

    def test_live_confirmation_racing_reservation_preserves_capacity(self):
        booking = Booking.objects.get(pk=self.reserve())
        data = self.payload(booking)
        results = self.concurrently(
            self.reserve, lambda: process_notification(data, "127.0.0.1").accepted,
        )
        self.assertIsNone(results[0])
        self.assertTrue(results[1])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(reserved_quantity(self.event), 1)

    def test_stale_expiry_and_checkout_cannot_overwrite_completed_payment(self):
        booking = Booking.objects.get(pk=self.reserve())
        process_notification(self.payload(booking), "127.0.0.1")
        build_checkout(booking)
        self.assertEqual(Payment.objects.get().status, Payment.Status.COMPLETE)
        # Simulate a reader that fetched the pending booking before confirmation.
        booking.expires_at = timezone.now() - timedelta(seconds=1)
        Booking.objects.filter(pk=booking.pk).update(expires_at=booking.expires_at)
        expire_booking_if_needed(booking)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_edit_waits_for_confirmation_lock_and_rejects_stale_details(self):
        from threading import Event as Signal

        booking = Booking.objects.get(pk=self.reserve())
        locked, edit_started = Signal(), Signal()

        def confirm():
            with transaction.atomic():
                Booking.objects.select_for_update().get(pk=booking.pk)
                locked.set()
                self.assertTrue(edit_started.wait(timeout=5))
                process_notification(self.payload(booking), "127.0.0.1")

        def edit():
            serializer = BookingUpdateSerializer(booking, data={
                "contact_name": "Changed", "contact_email": "changed@example.com",
                "attendees": [{"full_name": "Changed"}],
            })
            serializer.is_valid(raise_exception=True)
            self.assertTrue(locked.wait(timeout=5))
            edit_started.set()
            try:
                serializer.save()
            except BookingEditConflict:
                return "conflict"
            return "saved"

        results = self.concurrently(confirm, edit)
        self.assertEqual(results[1], "conflict")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.contact_name, "Guest")
        self.assertEqual(booking.attendees.get().full_name, "Guest")
