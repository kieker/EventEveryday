import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .emails import send_welcome_email


def user_payload(user):
    return {
        "id": user.pk,
        "email": user.email,
        "full_name": user.get_full_name(),
        "is_staff": user.is_staff,
    }


def request_data(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


@ensure_csrf_cookie
@require_GET
def csrf(request):
    return JsonResponse({"csrf_token": get_token(request)})


@csrf_protect
@require_POST
def register(request):
    data = request_data(request)
    email = str(data.get("email", "")).strip().lower()
    full_name = str(data.get("full_name", "")).strip()
    password = str(data.get("password", ""))

    if not email or "@" not in email:
        return JsonResponse({"email": ["Enter a valid email address."]}, status=400)
    if not full_name:
        return JsonResponse({"full_name": ["Enter your full name."]}, status=400)

    user_model = get_user_model()
    if user_model.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
        return JsonResponse({"email": ["An account with this email already exists."]}, status=400)

    name_parts = full_name.split(maxsplit=1)
    user = user_model(
        username=email,
        email=email,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
    )
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return JsonResponse({"password": list(exc.messages)}, status=400)

    user.set_password(password)
    user.save()
    login(request, user)
    send_welcome_email(user)
    return JsonResponse(user_payload(user), status=201)


@csrf_protect
@require_POST
def sign_in(request):
    data = request_data(request)
    email = str(data.get("email", "")).strip().lower()
    user = authenticate(request, username=email, password=str(data.get("password", "")))
    if user is None or not user.is_active:
        return JsonResponse({"detail": "The email address or password is incorrect."}, status=400)
    login(request, user)
    return JsonResponse(user_payload(user))


@csrf_protect
@require_POST
def sign_out(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
    logout(request)
    return JsonResponse({}, status=204)


@require_GET
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
    return JsonResponse(user_payload(request.user))
