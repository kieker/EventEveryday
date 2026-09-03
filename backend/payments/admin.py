from django.contrib import admin

from .models import Payment, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "status",
        "amount",
        "currency",
        "provider_transaction_reference",
        "paid_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = (
        "booking__reference",
        "booking__contact_email",
        "provider_transaction_reference",
    )
    readonly_fields = (
        "booking",
        "provider",
        "provider_transaction_reference",
        "amount",
        "currency",
        "status",
        "paid_at",
        "created_at",
        "updated_at",
    )


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "received_at",
        "merchant_payment_reference",
        "provider_transaction_reference",
        "payment_status",
        "accepted",
    )
    list_filter = ("accepted", "payment_status", "received_at")
    search_fields = (
        "merchant_payment_reference",
        "provider_transaction_reference",
        "payload_digest",
    )
    readonly_fields = tuple(field.name for field in PaymentWebhookEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

