from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "EventEveryday"
admin.site.site_title = "EventEveryday Admin"
admin.site.index_title = "Event operations"
admin.site.enable_nav_sidebar = False


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/events/", include("events.urls")),
    path("api/bookings/", include("bookings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
