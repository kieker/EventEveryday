import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Attendee, Booking


class AttendeeInline(admin.TabularInline):
    model = Attendee
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "event",
        "contact_name",
        "quantity",
        "status",
        "total_display",
        "created_at",
    )
    list_filter = ("status", "event", "created_at")
    search_fields = (
        "reference",
        "contact_name",
        "contact_email",
        "attendees__full_name",
        "event__title",
    )
    readonly_fields = (
        "reference",
        "access_token_hash",
        "unit_price",
        "total",
        "currency",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("event", "user")
    inlines = (AttendeeInline,)
    actions = ("export_csv",)
    date_hierarchy = "created_at"

    @admin.display(description="Total", ordering="total")
    def total_display(self, obj):
        return f"R {obj.total:,.2f}"

    @admin.action(description="Export selected bookings as CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Booking reference",
                "Event",
                "Contact name",
                "Contact email",
                "Contact phone",
                "Attendees",
                "Quantity",
                "Status",
                "Total",
                "Currency",
                "Created",
            ]
        )
        for booking in queryset.select_related("event").prefetch_related("attendees"):
            writer.writerow(
                [
                    booking.reference,
                    booking.event.title,
                    booking.contact_name,
                    booking.contact_email,
                    booking.contact_phone,
                    "; ".join(booking.attendees.values_list("full_name", flat=True)),
                    booking.quantity,
                    booking.get_status_display(),
                    booking.total,
                    booking.currency,
                    booking.created_at.isoformat(),
                ]
            )
        return response


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "booking", "event_title", "booking_status")
    list_filter = ("booking__status", "booking__event")
    search_fields = ("full_name", "booking__reference", "booking__contact_email")
    autocomplete_fields = ("booking",)

    @admin.display(description="Event", ordering="booking__event__title")
    def event_title(self, obj):
        return obj.booking.event.title

    @admin.display(description="Status", ordering="booking__status")
    def booking_status(self, obj):
        return obj.booking.get_status_display()

