from django.contrib import admin
from django.utils.html import format_html

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "start_at",
        "venue_name",
        "capacity",
        "formatted_price",
    )
    list_filter = ("status", "start_at", "timezone")
    search_fields = ("title", "summary", "venue_name", "venue_address")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("image_preview", "published_at", "created_at", "updated_at")
    date_hierarchy = "start_at"
    fieldsets = (
        (
            "Event",
            {
                "fields": (
                    "title",
                    "slug",
                    "summary",
                    "description",
                    "image",
                    "image_preview",
                    "image_url",
                )
            },
        ),
        ("Schedule", {"fields": ("start_at", "end_at", "timezone")}),
        ("Venue", {"fields": ("venue_name", "venue_address")}),
        ("Tickets", {"fields": ("capacity", "price")}),
        ("Publishing", {"fields": ("status", "published_at")}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Price", ordering="price")
    def formatted_price(self, obj):
        return f"R {obj.price:,.2f}"

    @admin.display(description="Current image")
    def image_preview(self, obj):
        source = obj.image.url if obj.image else obj.image_url
        if not source:
            return "No image selected"
        return format_html(
            '<img src="{}" alt="" style="max-height: 180px; max-width: 100%;" />',
            source,
        )
