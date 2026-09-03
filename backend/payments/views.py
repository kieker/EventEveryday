from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking
from bookings.services import expire_booking_if_needed

from .services import (
    PayFastConfigurationError,
    build_checkout,
    notification_data,
    process_notification,
)


def can_access_booking(request, booking):
    user_can_view = request.user.is_authenticated and (
        request.user.is_staff or booking.user_id == request.user.id
    )
    token = request.headers.get("X-Booking-Token", "")
    return user_can_view or booking.token_matches(token)


class PayFastCheckoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, reference):
        try:
            booking = Booking.objects.select_related("event", "user").get(reference=reference)
        except Booking.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not can_access_booking(request, booking):
            return Response(status=status.HTTP_404_NOT_FOUND)

        expire_booking_if_needed(booking)
        if booking.status != Booking.Status.PENDING_PAYMENT:
            return Response(
                {"detail": "This booking is no longer awaiting payment."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            checkout = build_checkout(booking)
        except PayFastConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(checkout)


@method_decorator(csrf_exempt, name="dispatch")
class PayFastNotificationView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.PAYFAST_MERCHANT_ID or not settings.PAYFAST_PASSPHRASE:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        data = notification_data(request.POST)
        remote_ip = request.META.get("REMOTE_ADDR", "")
        if settings.PAYFAST_TRUST_X_FORWARDED_FOR:
            forwarded_for = request.headers.get("X-Forwarded-For", "")
            remote_ip = forwarded_for.split(",", maxsplit=1)[0].strip() or remote_ip
        event = process_notification(data, remote_ip)
        if not event.accepted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)
