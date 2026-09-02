from django import template
from django.db.models import Count, Q
from django.utils import timezone

from events.models import Event


register = template.Library()


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

