from django.urls import path

from .views import health
from .auth_views import csrf, me, register, sign_in, sign_out


app_name = "core"

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/csrf/", csrf, name="auth-csrf"),
    path("auth/register/", register, name="auth-register"),
    path("auth/login/", sign_in, name="auth-login"),
    path("auth/logout/", sign_out, name="auth-logout"),
    path("auth/me/", me, name="auth-me"),
]
