from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer
from .services import expire_booking_if_needed


class BookingCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookingCreateSerializer


class BookingDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, reference):
        try:
            booking = Booking.objects.select_related("event", "user").prefetch_related(
                "attendees"
            ).get(reference=reference)
        except Booking.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_can_view = request.user.is_authenticated and (
            request.user.is_staff or booking.user_id == request.user.id
        )
        token = request.headers.get("X-Booking-Token", "")
        if not user_can_view and not booking.token_matches(token):
            return Response(status=status.HTTP_404_NOT_FOUND)

        expire_booking_if_needed(booking)
        return Response(BookingSerializer(booking, context={"request": request}).data)

