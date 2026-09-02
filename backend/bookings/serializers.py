from rest_framework import serializers

from events.models import Event
from events.serializers import EventListSerializer

from .models import Attendee, Booking
from .services import BookingUnavailable, create_guest_booking


class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = ("full_name",)


class BookingSerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)
    attendees = AttendeeSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = (
            "reference",
            "event",
            "contact_name",
            "contact_email",
            "contact_phone",
            "quantity",
            "unit_price",
            "total",
            "currency",
            "status",
            "expires_at",
            "created_at",
            "attendees",
        )


class BookingCreateSerializer(serializers.Serializer):
    event_slug = serializers.SlugField(write_only=True)
    contact_name = serializers.CharField(max_length=180)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    attendees = AttendeeSerializer(many=True, min_length=1, max_length=10)

    def validate_event_slug(self, value):
        try:
            return Event.objects.get(slug=value)
        except Event.DoesNotExist as exc:
            raise serializers.ValidationError("Event not found.") from exc

    def validate_attendees(self, value):
        names = [attendee["full_name"].strip() for attendee in value]
        if any(not name for name in names):
            raise serializers.ValidationError("Every ticket requires an attendee name.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user if request.user.is_authenticated else None
        try:
            booking, token = create_guest_booking(
                event=validated_data["event_slug"],
                contact_name=validated_data["contact_name"],
                contact_email=validated_data["contact_email"],
                contact_phone=validated_data.get("contact_phone", ""),
                attendees=[item["full_name"] for item in validated_data["attendees"]],
                user=user,
            )
        except BookingUnavailable as exc:
            raise serializers.ValidationError({"event_slug": str(exc)}) from exc
        booking._raw_access_token = token
        return booking

    def to_representation(self, instance):
        data = BookingSerializer(instance, context=self.context).data
        data["access_token"] = instance._raw_access_token
        return data

