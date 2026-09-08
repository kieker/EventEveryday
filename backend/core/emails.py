import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


logger = logging.getLogger(__name__)


def send_templated_email(*, subject, template_name, recipient, context):
    html = render_to_string(f"emails/{template_name}.html", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=[settings.EMAIL_REPLY_TO] if settings.EMAIL_REPLY_TO else None,
    )
    message.attach_alternative(html, "text/html")
    try:
        return message.send()
    except Exception:
        logger.exception("Transactional email delivery failed for template %s", template_name)
        return 0


def send_welcome_email(user):
    return send_templated_email(
        subject="Welcome to EventEveryday",
        template_name="welcome",
        recipient=user.email,
        context={"user": user, "account_url": f"{settings.PUBLIC_FRONTEND_URL}/account"},
    )


def send_booking_reserved_email(booking):
    return send_templated_email(
        subject=f"Reservation {booking.reference} created",
        template_name="booking_reserved",
        recipient=booking.contact_email,
        context={"booking": booking, "booking_url": f"{settings.PUBLIC_FRONTEND_URL}/bookings/{booking.reference}"},
    )


def send_booking_confirmed_email(booking):
    return send_templated_email(
        subject=f"Booking {booking.reference} confirmed",
        template_name="booking_confirmed",
        recipient=booking.contact_email,
        context={"booking": booking, "booking_url": f"{settings.PUBLIC_FRONTEND_URL}/bookings/{booking.reference}"},
    )
