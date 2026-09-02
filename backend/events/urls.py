from django.urls import path

from .views import PublishedEventDetailView, PublishedEventListView


app_name = "events"

urlpatterns = [
    path("", PublishedEventListView.as_view(), name="list"),
    path("<slug:slug>/", PublishedEventDetailView.as_view(), name="detail"),
]

