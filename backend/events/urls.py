from django.urls import path
from .calendar import CalendarView

from .views import PublishedEventDetailView, PublishedEventListView


app_name = "events"

urlpatterns = [
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("", PublishedEventListView.as_view(), name="list"),
    path("<slug:slug>/", PublishedEventDetailView.as_view(), name="detail"),
]
