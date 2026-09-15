import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods

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


@csrf_protect
@require_http_methods(["GET", "PATCH"])
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
    user = request.user
    if request.method == "PATCH":
        data = request_data(request)
        if not isinstance(data, dict):
            return JsonResponse({"detail": "Provide profile fields."}, status=400)
        name = data.get("full_name", user.get_full_name())
        email = data.get("email", user.email)
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 150:
            return JsonResponse({"full_name": ["Enter a full name of at most 150 characters."]}, status=400)
        if not isinstance(email, str):
            return JsonResponse({"email": ["Enter a valid email address."]}, status=400)
        email = email.strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"email": ["Enter a valid email address."]}, status=400)
        if len(email) > 150:
            return JsonResponse({"email": ["Use an email address of at most 150 characters."]}, status=400)
        if email != user.email.lower():
            password = data.get("current_password", "")
            if not isinstance(password, str) or not user.check_password(password):
                return JsonResponse({"current_password": ["Enter your current password to change your email."]}, status=400)
            if get_user_model().objects.exclude(pk=user.pk).filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
                return JsonResponse({"email": ["An account with this email already exists."]}, status=400)
            user.email = email
            user.username = email
        parts = name.strip().split(maxsplit=1)
        user.first_name, user.last_name = parts[0], parts[1] if len(parts) > 1 else ""
        try:
            with transaction.atomic():
                user.save(update_fields=["first_name", "last_name", "email", "username"])
        except IntegrityError:
            return JsonResponse({"email": ["An account with this email already exists."]}, status=400)
    return JsonResponse(user_payload(user))
