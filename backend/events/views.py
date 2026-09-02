from rest_framework import generics, permissions

from .models import Event
from .serializers import EventDetailSerializer, EventListSerializer


class PublishedEventListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EventListSerializer

    def get_queryset(self):
        return Event.objects.published()


class PublishedEventDetailView(generics.RetrieveAPIView):
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
    serializer_class = EventDetailSerializer

    def get_queryset(self):
        return Event.objects.published()

