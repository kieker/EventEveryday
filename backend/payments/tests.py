from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import urlencode

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from bookings.services import create_guest_booking
from events.models import Event

from .models import Payment, PaymentWebhookEvent
from .services import generate_signature, parameter_string


PAYFAST_TEST_SETTINGS = override_settings(
    PAYFAST_SANDBOX=True,
    PAYFAST_MERCHANT_ID="10000100",
    PAYFAST_MERCHANT_KEY="test-key",
    PAYFAST_PASSPHRASE="test-passphrase",
    PAYFAST_PROCESS_URL="https://sandbox.payfast.co.za/eng/process",
    PAYFAST_VALIDATE_URL="https://sandbox.payfast.co.za/eng/query/validate",
    PAYFAST_NOTIFY_URL="https://example.test/api/payments/payfast/notify/",
    PUBLIC_FRONTEND_URL="https://example.test",
    PAYFAST_TRUST_X_FORWARDED_FOR=True,
)


def make_booking():
    start_at = timezone.now() + timedelta(days=10)
    event = Event.objects.create(
        title="PayFast Test Event",
        summary="An event used to test PayFast checkout.",
        description="PayFast test event description.",
        venue_name="Test Venue",
        venue_address="1 Test Street",
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
        capacity=20,
        price=Decimal("325.00"),
        status=Event.Status.PUBLISHED,
    )
    return create_guest_booking(
        event=event,
        contact_name="Jamie Example",
        contact_email="jamie@example.com",
        contact_phone="0820000000",
        attendees=["Jamie Example", "Taylor Example"],
    )


@PAYFAST_TEST_SETTINGS
class PayFastCheckoutTests(TestCase):
    def test_checkout_returns_signed_form_and_initializes_payment(self):
        booking, token = make_booking()

        response = self.client.post(
            reverse("payments:checkout", args=[booking.reference]),
            HTTP_X_BOOKING_TOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["action_url"], "https://sandbox.payfast.co.za/eng/process")
        self.assertEqual(body["fields"]["amount"], "650.00")
        self.assertEqual(body["fields"]["m_payment_id"], booking.reference)
        signature = body["fields"].pop("signature")
        self.assertEqual(signature, generate_signature(body["fields"], "test-passphrase"))
        self.assertEqual(Payment.objects.get(booking=booking).status, Payment.Status.INITIALIZED)

    def test_checkout_requires_booking_access_token(self):
        booking, _ = make_booking()

        response = self.client.post(reverse("payments:checkout", args=[booking.reference]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Payment.objects.exists())


@PAYFAST_TEST_SETTINGS
class PayFastNotificationTests(TestCase):
    def notification_payload(self, booking, *, amount="650.00", status="COMPLETE"):
        data = OrderedDict(
            (
                ("m_payment_id", booking.reference),
                ("pf_payment_id", "123456789"),
                ("payment_status", status),
                ("item_name", booking.event.title),
                ("amount_gross", amount),
                ("merchant_id", "10000100"),
            )
        )
        data["signature"] = generate_signature(data, "test-passphrase")
        return data

    @patch("payments.services.confirm_with_payfast", return_value=True)
    @patch("payments.services.valid_source_ip", return_value=True)
    def test_complete_itn_confirms_booking_idempotently(self, source_check, server_check):
        booking, _ = make_booking()
        payload = self.notification_payload(booking)
        url = reverse("payments:notify")

        first = self.client.post(
            url,
            data=urlencode(payload),
            content_type="application/x-www-form-urlencoded",
            REMOTE_ADDR="196.33.227.1",
            HTTP_X_FORWARDED_FOR="197.97.145.156",
        )
        second = self.client.post(
            url,
            data=urlencode(payload),
            content_type="application/x-www-form-urlencoded",
            REMOTE_ADDR="196.33.227.1",
            HTTP_X_FORWARDED_FOR="197.97.145.156",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        booking.refresh_from_db()
        payment = Payment.objects.get(booking=booking)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(payment.status, Payment.Status.COMPLETE)
        self.assertEqual(payment.provider_transaction_reference, "123456789")
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        self.assertTrue(PaymentWebhookEvent.objects.get().accepted)
        source_check.assert_called_once_with("197.97.145.156")
        server_check.assert_called_once()

    @patch("payments.services.confirm_with_payfast", return_value=True)
    @patch("payments.services.valid_source_ip", return_value=True)
    def test_itn_with_wrong_amount_is_rejected(self, source_check, server_check):
        booking, _ = make_booking()
        payload = self.notification_payload(booking, amount="1.00")

        response = self.client.post(
            reverse("payments:notify"),
            data=urlencode(payload),
            content_type="application/x-www-form-urlencoded",
            REMOTE_ADDR="196.33.227.1",
        )

        self.assertEqual(response.status_code, 400)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING_PAYMENT)
        webhook = PaymentWebhookEvent.objects.get()
        self.assertFalse(webhook.amount_valid)
        self.assertFalse(webhook.accepted)
        server_check.assert_not_called()

    @patch("payments.services.confirm_with_payfast", return_value=True)
    @patch("payments.services.valid_source_ip", side_effect=(False, True))
    def test_rejected_itn_can_be_revalidated_on_retry(self, source_check, server_check):
        booking, _ = make_booking()
        payload = self.notification_payload(booking)
        request_kwargs = {
            "data": urlencode(payload),
            "content_type": "application/x-www-form-urlencoded",
            "REMOTE_ADDR": "172.20.0.4",
            "HTTP_X_FORWARDED_FOR": "197.97.145.156",
        }

        first = self.client.post(reverse("payments:notify"), **request_kwargs)
        second = self.client.post(reverse("payments:notify"), **request_kwargs)

        self.assertEqual(first.status_code, 400)
        self.assertEqual(second.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        self.assertTrue(PaymentWebhookEvent.objects.get().accepted)
        server_check.assert_called_once()


class PayFastSignatureTests(TestCase):
    def test_signature_preserves_field_order_and_php_style_encoding(self):
        data = OrderedDict(
            (("merchant_id", "10000100"), ("item_name", "Design & Ideas"), ("amount", "100.00"))
        )

        self.assertEqual(
            parameter_string(data, passphrase="salt phrase"),
            "merchant_id=10000100&item_name=Design+%26+Ideas&amount=100.00&passphrase=salt+phrase",
        )
        self.assertEqual(len(generate_signature(data, "salt phrase")), 32)

    def test_itn_signature_includes_blank_fields(self):
        data = OrderedDict(
            (
                ("m_payment_id", "EVT-123"),
                ("item_description", ""),
                ("amount_gross", "100.00"),
            )
        )

        self.assertEqual(
            parameter_string(data, passphrase="salt", include_empty=True),
            "m_payment_id=EVT-123&item_description=&amount_gross=100.00&passphrase=salt",
        )
        self.assertNotEqual(
            generate_signature(data, "salt"),
            generate_signature(data, "salt", include_empty=True),
        )
