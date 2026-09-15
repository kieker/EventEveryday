from rest_framework import serializers
from rest_framework.exceptions import APIException
from django.db import transaction
from django.utils import timezone

from events.models import Event
from events.serializers import EventListSerializer

from .models import Attendee, Booking
from .services import BookingUnavailable, create_guest_booking


class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = ("full_name",)


class BookingSerializer(serializers.ModelSerializer):
    event = serializers.SerializerMethodField()
    payment_received = serializers.SerializerMethodField()
    reconciliation_required = serializers.SerializerMethodField()

    def get_payment_received(self, obj):
        payment = getattr(obj, "payment", None)
        return bool(payment and payment.status == "complete")

    def get_reconciliation_required(self, obj):
        return self.get_payment_received(obj) and obj.status != Booking.Status.CONFIRMED

    def get_event(self, obj):
        data = EventListSerializer(obj.event, context=self.context).data
        for field in ("title", "venue_name", "venue_address", "timezone"):
            data[field] = getattr(obj, f"event_{field}")
        for field in ("start_at", "end_at"):
            data[field] = serializers.DateTimeField().to_representation(
                getattr(obj, f"event_{field}")
            )
        data["price"] = serializers.DecimalField(
            max_digits=10, decimal_places=2
        ).to_representation(obj.unit_price)
        data["currency"] = obj.currency
        return data

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
            "payment_received",
            "reconciliation_required",
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


class BookingEditConflict(APIException):
    status_code = 409
    default_detail = "Only bookings awaiting payment can be edited."


class BookingUpdateSerializer(serializers.ModelSerializer):
    attendees = AttendeeSerializer(many=True)

    class Meta:
        model = Booking
        fields = ("contact_name", "contact_email", "contact_phone", "attendees")

    def validate_attendees(self, value):
        names = [attendee["full_name"].strip() for attendee in value]
        if any(not name for name in names):
            raise serializers.ValidationError("Every ticket requires an attendee name.")
        if len(names) != self.instance.quantity:
            raise serializers.ValidationError(
                f"This booking requires exactly {self.instance.quantity} attendee names."
            )
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Booking.objects.select_for_update().get(pk=instance.pk)
        if (instance.status != Booking.Status.PENDING_PAYMENT
                or instance.expires_at <= timezone.now()):
            raise BookingEditConflict()
        attendees = validated_data.pop("attendees")
        instance.contact_name = validated_data["contact_name"].strip()
        instance.contact_email = validated_data["contact_email"].strip().lower()
        instance.contact_phone = validated_data.get("contact_phone", "").strip()
        instance.save(
            update_fields=("contact_name", "contact_email", "contact_phone", "updated_at")
        )
        instance.attendees.all().delete()
        Attendee.objects.bulk_create(
            Attendee(booking=instance, full_name=item["full_name"].strip())
            for item in attendees
        )
        return instance
