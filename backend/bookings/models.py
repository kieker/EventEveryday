import hashlib
import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


def generate_booking_reference():
    while True:
        reference = f"EVT-{secrets.token_hex(5).upper()}"
        if not Booking.objects.filter(reference=reference).exists():
            return reference


def hash_access_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        CONFIRMED = "confirmed", "Confirmed"
        PAYMENT_FAILED = "payment_failed", "Payment failed"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.CharField(
        max_length=24,
        unique=True,
        default=generate_booking_reference,
        editable=False,
    )
    access_token_hash = models.CharField(max_length=64, editable=False)
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    event_title = models.CharField(max_length=180, editable=False)
    event_venue_name = models.CharField(max_length=180, editable=False)
    event_venue_address = models.TextField(editable=False)
    event_timezone = models.CharField(max_length=64, editable=False)
    event_start_at = models.DateTimeField(editable=False)
    event_end_at = models.DateTimeField(editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bookings",
    )
    contact_name = models.CharField(max_length=180)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=40, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZAR", editable=False)
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="booking_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="booking_unit_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="booking_total_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(currency="ZAR"),
                name="booking_currency_zar",
            ),
        ]

    def __str__(self):
        return f"{self.reference} — {self.event_title}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            for field in ("title", "venue_name", "venue_address", "timezone", "start_at", "end_at"):
                setattr(self, f"event_{field}", getattr(self.event, field))
        super().save(*args, **kwargs)

    def token_matches(self, token):
        if not token:
            return False
        return secrets.compare_digest(self.access_token_hash, hash_access_token(token))


class Attendee(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="attendees",
    )
    full_name = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.full_name

