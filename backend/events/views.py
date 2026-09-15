from rest_framework import generics, permissions
from django.db.models import Q
from django.utils import timezone

from .models import Event
from .serializers import EventDetailSerializer, EventListSerializer


class PublishedEventListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EventListSerializer

    def get_queryset(self):
        events = Event.objects.published().filter(start_at__gt=timezone.now())
        query = self.request.query_params.get("q", "").strip()[:200]
        if query:
            events = events.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(venue_name__icontains=query) | Q(venue_address__icontains=query))
        return events


class PublishedEventDetailView(generics.RetrieveAPIView):
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
    serializer_class = EventDetailSerializer

    def get_queryset(self):
        return Event.objects.published()
