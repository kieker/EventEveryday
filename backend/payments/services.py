import hashlib
import ipaddress
import socket
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking

from .models import Payment, PaymentWebhookEvent


PAYFAST_FIELD_ORDER = (
    "merchant_id",
    "merchant_key",
    "return_url",
    "cancel_url",
    "notify_url",
    "notify_method",
    "name_first",
    "name_last",
    "email_address",
    "cell_number",
    "m_payment_id",
    "amount",
    "item_name",
    "item_description",
    "custom_int1",
    "custom_int2",
    "custom_int3",
    "custom_int4",
    "custom_int5",
    "custom_str1",
    "custom_str2",
    "custom_str3",
    "custom_str4",
    "custom_str5",
    "email_confirmation",
    "confirmation_address",
    "currency",
    "payment_method",
    "subscription_type",
    "billing_date",
    "recurring_amount",
    "frequency",
    "cycles",
    "subscription_notify_email",
    "subscription_notify_webhook",
    "subscription_notify_buyer",
)


class PayFastConfigurationError(ImproperlyConfigured):
    pass


def require_configuration():
    missing = [
        name
        for name, value in (
            ("PAYFAST_MERCHANT_ID", settings.PAYFAST_MERCHANT_ID),
            ("PAYFAST_MERCHANT_KEY", settings.PAYFAST_MERCHANT_KEY),
            ("PAYFAST_PASSPHRASE", settings.PAYFAST_PASSPHRASE),
            ("PAYFAST_NOTIFY_URL", settings.PAYFAST_NOTIFY_URL),
        )
        if not value
    ]
    if missing:
        raise PayFastConfigurationError(f"Missing PayFast configuration: {', '.join(missing)}")


def encode_value(value):
    return quote_plus(str(value).strip(), safe="")


def parameter_string(data, *, passphrase=None, include_empty=False):
    pairs = [
        f"{key}={encode_value(value)}"
        for key, value in data.items()
        if key != "signature" and (include_empty or value not in (None, ""))
    ]
    if passphrase:
        pairs.append(f"passphrase={encode_value(passphrase)}")
    return "&".join(pairs)


def generate_signature(data, passphrase, *, include_empty=False):
    return hashlib.md5(
        parameter_string(
            data,
            passphrase=passphrase,
            include_empty=include_empty,
        ).encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()


def split_name(full_name):
    parts = full_name.strip().split(maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def build_checkout(booking):
    require_configuration()
    first_name, last_name = split_name(booking.contact_name)
    return_url = f"{settings.PUBLIC_FRONTEND_URL}/bookings/{booking.reference}?payment=returned"
    cancel_url = f"{settings.PUBLIC_FRONTEND_URL}/bookings/{booking.reference}?payment=cancelled"
    values = {
        "merchant_id": settings.PAYFAST_MERCHANT_ID,
        "merchant_key": settings.PAYFAST_MERCHANT_KEY,
        "return_url": return_url,
        "cancel_url": cancel_url,
        "notify_url": settings.PAYFAST_NOTIFY_URL,
        "name_first": first_name,
        "name_last": last_name,
        "email_address": booking.contact_email,
        "cell_number": booking.contact_phone,
        "m_payment_id": booking.reference,
        "amount": f"{booking.total:.2f}",
        "item_name": booking.event.title[:100],
        "item_description": f"{booking.quantity} ticket(s) — {booking.reference}"[:255],
        "currency": booking.currency,
    }
    ordered = OrderedDict(
        (field, values[field]) for field in PAYFAST_FIELD_ORDER if field in values and values[field]
    )
    ordered["signature"] = generate_signature(ordered, settings.PAYFAST_PASSPHRASE)
    Payment.objects.update_or_create(
        booking=booking,
        defaults={
            "amount": booking.total,
            "currency": booking.currency,
            "status": Payment.Status.INITIALIZED,
        },
    )
    return {"action_url": settings.PAYFAST_PROCESS_URL, "fields": ordered}


def notification_data(post_data):
    return OrderedDict((key, post_data.get(key, "")) for key in post_data.keys())


def payload_digest(data):
    serialized = "&".join(
        f"{key}={encode_value(value)}" for key, value in data.items() if value not in (None, "")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def valid_signature(data):
    received = data.get("signature", "")
    # PayFast signs every ITN field before ``signature``, including blank
    # values. Checkout form signatures, by contrast, omit blank fields.
    calculated = generate_signature(
        data,
        settings.PAYFAST_PASSPHRASE,
        include_empty=True,
    )
    return bool(received) and received == calculated


def valid_source_ip(remote_ip):
    try:
        address = ipaddress.ip_address(remote_ip)
    except ValueError:
        return False
    valid_addresses = set()
    for hostname in (
        "www.payfast.co.za",
        "w1w.payfast.co.za",
        "w2w.payfast.co.za",
        "sandbox.payfast.co.za",
    ):
        try:
            valid_addresses.update(item[4][0] for item in socket.getaddrinfo(hostname, 443))
        except socket.gaierror:
            continue
    return str(address) in valid_addresses


def valid_amount(booking, data):
    try:
        received = Decimal(data.get("amount_gross", ""))
    except InvalidOperation:
        return False
    return abs(booking.total - received) <= Decimal("0.01")


def confirm_with_payfast(data):
    body = parameter_string(data).encode("utf-8")
    request = Request(
        settings.PAYFAST_VALIDATE_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8").strip() == "VALID"
    except (URLError, TimeoutError):
        return False


@transaction.atomic
def process_notification(data, remote_ip):
    digest = payload_digest(data)
    existing = PaymentWebhookEvent.objects.select_for_update().filter(payload_digest=digest).first()
    if existing and existing.accepted:
        return existing

    reference = data.get("m_payment_id", "")
    provider_reference = data.get("pf_payment_id", "")
    payment_status = data.get("payment_status", "")
    event = existing or PaymentWebhookEvent(payload_digest=digest)
    event.provider_transaction_reference = provider_reference
    event.payment_status = payment_status
    event.merchant_payment_reference = reference
    event.signature_valid = False
    event.source_valid = False
    event.amount_valid = False
    event.server_confirmation_valid = False
    event.accepted = False
    event.rejection_reason = ""

    try:
        booking = Booking.objects.select_for_update().select_related("event").get(reference=reference)
    except Booking.DoesNotExist:
        event.rejection_reason = "Unknown booking reference."
        event.save()
        return event

    payment, _ = Payment.objects.select_for_update().get_or_create(
        booking=booking,
        defaults={"amount": booking.total, "currency": booking.currency},
    )
    event.payment = payment
    event.signature_valid = valid_signature(data)
    event.source_valid = valid_source_ip(remote_ip)
    event.amount_valid = valid_amount(booking, data)
    merchant_valid = data.get("merchant_id") == settings.PAYFAST_MERCHANT_ID
    if event.signature_valid and event.source_valid and event.amount_valid and merchant_valid:
        event.server_confirmation_valid = confirm_with_payfast(data)

    checks = (
        event.signature_valid,
        event.source_valid,
        event.amount_valid,
        event.server_confirmation_valid,
        merchant_valid,
    )
    if not all(checks):
        event.rejection_reason = "One or more PayFast security checks failed."
        event.save()
        return event

    payment.provider_transaction_reference = provider_reference
    if payment_status == "COMPLETE":
        payment.status = Payment.Status.COMPLETE
        payment.paid_at = timezone.now()
        booking.status = Booking.Status.CONFIRMED
    elif payment_status == "FAILED":
        payment.status = Payment.Status.FAILED
        if booking.status != Booking.Status.CONFIRMED:
            booking.status = Booking.Status.PAYMENT_FAILED
    elif payment_status == "CANCELLED":
        payment.status = Payment.Status.CANCELLED
        if booking.status != Booking.Status.CONFIRMED:
            booking.status = Booking.Status.CANCELLED
    else:
        payment.status = Payment.Status.PENDING

    payment.save()
    booking.save(update_fields=["status", "updated_at"])
    event.accepted = True
    event.save()
    return event
