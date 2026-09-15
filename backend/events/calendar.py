from datetime import datetime
from zoneinfo import ZoneInfo

from rest_framework import permissions, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView

from .models import Event


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "slug", "title", "venue_name", "start_at", "end_at", "timezone", "status")


class CalendarView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CalendarSerializer

    def get_queryset(self):
        scope = self.request.query_params.get("scope", "public")
        user = self.request.user
        if scope == "public":
            events = Event.objects.published()
        elif scope == "mine":
            if not user.is_authenticated:
                raise PermissionDenied("Sign in to view your calendar.")
            events = Event.objects.filter(bookings__user=user, bookings__status="confirmed").distinct()
        elif scope == "admin":
            if not user.is_staff or not user.has_perm("events.view_event"):
                raise PermissionDenied("Event administration permission is required.")
            events = Event.objects.all()
        else:
            raise ValidationError({"scope": "Choose public, mine, or admin."})

        try:
            month = self.request.query_params["month"]
            start = datetime.strptime(month, "%Y-%m").replace(tzinfo=ZoneInfo("Africa/Johannesburg"))
            end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
        except (KeyError, ValueError, OverflowError):
            raise ValidationError({"month": "Provide a month in YYYY-MM format."})
        return events.filter(start_at__lt=end, end_at__gt=start).order_by("start_at", "pk")
