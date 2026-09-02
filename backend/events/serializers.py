from rest_framework import serializers

from .models import Event


class EventListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    available_capacity = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return obj.image_url

    def get_available_capacity(self, obj):
        from bookings.services import available_capacity

        return available_capacity(obj)

    class Meta:
        model = Event
        fields = (
            "slug",
            "title",
            "summary",
            "venue_name",
            "timezone",
            "start_at",
            "end_at",
            "capacity",
            "available_capacity",
            "price",
            "currency",
            "image_url",
        )


class EventDetailSerializer(EventListSerializer):
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ("description", "venue_address")
