from django import template
from django.db.models import Count, Q
from django.utils import timezone

from events.models import Event


register = template.Library()


@register.simple_tag
def ordered_site_management_apps(app_list):
    """Return dashboard apps/models in the product's task-oriented order."""
    app_order = {
        "events": 0,
        "bookings": 1,
        "payments": 2,
        "auth": 4,
    }
    payment_model_order = {
        "payment": 0,
        "paymentwebhookevent": 1,
    }

    ordered_apps = []
    for app in app_list:
        ordered_app = {**app}
        models = list(app.get("models", []))
        if app.get("app_label") == "payments":
            models.sort(
                key=lambda model: (
                    payment_model_order.get(model.get("object_name", "").lower(), 2),
                    model.get("name", ""),
                )
            )
        ordered_app["models"] = models
        ordered_apps.append(ordered_app)

    return sorted(
        ordered_apps,
        key=lambda app: (
            app_order.get(app.get("app_label"), 3),
            app.get("name", ""),
        ),
    )


@register.simple_tag
def admin_dashboard_events(limit=8):
    return Event.objects.order_by("start_at")[:limit]


@register.simple_tag
def admin_event_stats():
    return Event.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Event.Status.PUBLISHED)),
        upcoming=Count("id", filter=Q(end_at__gte=timezone.now())),
        drafts=Count("id", filter=Q(status=Event.Status.DRAFT)),
    )
