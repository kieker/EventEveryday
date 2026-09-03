from django.urls import path

from .views import PayFastCheckoutView, PayFastNotificationView


app_name = "payments"

urlpatterns = [
    path("payfast/checkout/<str:reference>/", PayFastCheckoutView.as_view(), name="checkout"),
    path("payfast/notify/", PayFastNotificationView.as_view(), name="notify"),
]

