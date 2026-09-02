from django.urls import path

from .views import BookingCreateView, BookingDetailView


app_name = "bookings"

urlpatterns = [
    path("", BookingCreateView.as_view(), name="create"),
    path("<str:reference>/", BookingDetailView.as_view(), name="detail"),
]

