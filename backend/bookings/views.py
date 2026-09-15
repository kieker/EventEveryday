from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer, BookingUpdateSerializer
from .services import expire_booking_if_needed


class BookingCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BookingCreateSerializer


class BookingDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_booking(self, request, reference):
        try:
            booking = Booking.objects.select_related("event", "user", "payment").prefetch_related(
                "attendees"
            ).get(reference=reference)
        except Booking.DoesNotExist:
            return None

        user_can_view = request.user.is_authenticated and (
            request.user.is_staff or booking.user_id == request.user.id
        )
        token = request.headers.get("X-Booking-Token", "")
        if not user_can_view and not booking.token_matches(token):
            return None

        return booking

    def get(self, request, reference):
        booking = self.get_booking(request, reference)
        if booking is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        expire_booking_if_needed(booking)
        return Response(BookingSerializer(booking, context={"request": request}).data)

    def patch(self, request, reference):
        booking = self.get_booking(request, reference)
        if booking is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        expire_booking_if_needed(booking)
        if booking.status != Booking.Status.PENDING_PAYMENT:
            return Response(
                {"detail": "Only bookings awaiting payment can be edited."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = BookingUpdateSerializer(booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingSerializer(booking, context={"request": request}).data)


class MyBookingListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):
        bookings = (
            Booking.objects.filter(user=self.request.user)
            .select_related("event", "payment")
            .prefetch_related("attendees")
        )
        for booking in bookings:
            expire_booking_if_needed(booking)
        return bookings
