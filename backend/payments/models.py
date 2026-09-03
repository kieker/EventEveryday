from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIALIZED = "initialized", "Initialized"
        PENDING = "pending", "Pending"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="payment",
    )
    provider = models.CharField(max_length=24, default="payfast", editable=False)
    provider_transaction_reference = models.CharField(max_length=64, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZAR", editable=False)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.INITIALIZED,
        db_index=True,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PayFast payment for {self.booking.reference}"


class PaymentWebhookEvent(models.Model):
    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="webhook_events",
    )
    payload_digest = models.CharField(max_length=64, unique=True)
    provider_transaction_reference = models.CharField(max_length=64, blank=True)
    payment_status = models.CharField(max_length=32, blank=True)
    merchant_payment_reference = models.CharField(max_length=64, blank=True)
    signature_valid = models.BooleanField(default=False)
    source_valid = models.BooleanField(default=False)
    amount_valid = models.BooleanField(default=False)
    server_confirmation_valid = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    rejection_reason = models.CharField(max_length=240, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"PayFast ITN {self.provider_transaction_reference or self.payload_digest[:12]}"

