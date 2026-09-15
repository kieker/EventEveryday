import secrets
from datetime import timedelta

from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.emails import send_booking_reserved_email
from events.models import Event

from .models import Attendee, Booking, hash_access_token


class BookingUnavailable(Exception):
    pass


def reserved_quantity(event):
    active_status = Q(status=Booking.Status.CONFIRMED) | Q(
        status=Booking.Status.PENDING_PAYMENT,
        expires_at__gt=timezone.now(),
    )
    return event.bookings.filter(active_status).aggregate(
        total=Coalesce(Sum("quantity"), 0)
    )["total"]


def available_capacity(event):
    return max(event.capacity - reserved_quantity(event), 0)


@transaction.atomic
def create_guest_booking(*, event, contact_name, contact_email, contact_phone, attendees, user=None):
    locked_event = Event.objects.select_for_update().get(pk=event.pk)
    now = timezone.now()

    locked_event.bookings.filter(
        status=Booking.Status.PENDING_PAYMENT,
        expires_at__lte=now,
    ).update(status=Booking.Status.EXPIRED, updated_at=now)

    quantity = len(attendees)
    if locked_event.status != Event.Status.PUBLISHED:
        raise BookingUnavailable("This event is not currently available for booking.")
    if locked_event.end_at <= now:
        raise BookingUnavailable("This event has already ended.")
    if quantity < 1:
        raise BookingUnavailable("At least one attendee is required.")
    if quantity > available_capacity(locked_event):
        raise BookingUnavailable("There are not enough tickets available.")

    access_token = secrets.token_urlsafe(32)
    booking = Booking.objects.create(
        event=locked_event,
        user=user,
        contact_name=contact_name.strip(),
        contact_email=contact_email.strip().lower(),
        contact_phone=contact_phone.strip(),
        quantity=quantity,
        unit_price=locked_event.price,
        total=locked_event.price * quantity,
        currency=locked_event.currency,
        status=Booking.Status.PENDING_PAYMENT,
        expires_at=now + timedelta(minutes=15),
        access_token_hash=hash_access_token(access_token),
    )
    Attendee.objects.bulk_create(
        [Attendee(booking=booking, full_name=name.strip()) for name in attendees]
    )
    transaction.on_commit(lambda: send_booking_reserved_email(booking))
    return booking, access_token


def expire_booking_if_needed(booking):
    if (
        booking.status == Booking.Status.PENDING_PAYMENT
        and booking.expires_at <= timezone.now()
    ):
        Booking.objects.filter(
            pk=booking.pk, status=Booking.Status.PENDING_PAYMENT,
            expires_at__lte=timezone.now(),
        ).update(status=Booking.Status.EXPIRED, updated_at=timezone.now())
        booking.refresh_from_db()
    return booking
