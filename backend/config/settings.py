import os
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "unsafe-development-key-change-before-deployment"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes"}
BEHIND_HTTPS_PROXY = os.environ.get("DJANGO_BEHIND_HTTPS_PROXY", "false").lower() in {
    "1", "true", "yes"
}
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if BEHIND_HTTPS_PROXY else None
SESSION_COOKIE_SECURE = BEHIND_HTTPS_PROXY
CSRF_COOKIE_SECURE = BEHIND_HTTPS_PROXY
SECURE_SSL_REDIRECT = BEHIND_HTTPS_PROXY
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "anymail",
    "core",
    "events",
    "bookings",
    "payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.rate_limits.RateLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=60,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-za"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_headers, "x-booking-token")
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# Use shared Redis counters for every worker in deployed environments.
RATE_LIMIT_REDIS_URL = os.environ.get("RATE_LIMIT_REDIS_URL", "")
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "rate_limits": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache"
        if RATE_LIMIT_REDIS_URL else "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": RATE_LIMIT_REDIS_URL or "eventeveryday-rate-limits",
        "KEY_PREFIX": "eventeveryday",
    },
}
# Only trust forwarded addresses when the immediate peer is a trusted proxy.
RATE_LIMIT_TRUSTED_PROXIES = [
    value.strip() for value in os.environ.get("RATE_LIMIT_TRUSTED_PROXIES", "").split(",")
    if value.strip()
]
RATE_LIMITS = {
    "api": (120, 60),
    "login": (10, 300),
    "register": (5, 3600),
    "booking_write": (20, 300),
    "checkout": (10, 60),
}

PAYFAST_SANDBOX = os.environ.get("PAYFAST_SANDBOX", "true").lower() in {
    "1",
    "true",
    "yes",
}
PAYFAST_MERCHANT_ID = os.environ.get("PAYFAST_MERCHANT_ID", "")
PAYFAST_MERCHANT_KEY = os.environ.get("PAYFAST_MERCHANT_KEY", "")
PAYFAST_PASSPHRASE = os.environ.get("PAYFAST_PASSPHRASE", "")
PAYFAST_PROCESS_URL = os.environ.get(
    "PAYFAST_PROCESS_URL",
    "https://sandbox.payfast.co.za/eng/process"
    if PAYFAST_SANDBOX
    else "https://www.payfast.co.za/eng/process",
)
PAYFAST_VALIDATE_URL = os.environ.get(
    "PAYFAST_VALIDATE_URL",
    "https://sandbox.payfast.co.za/eng/query/validate"
    if PAYFAST_SANDBOX
    else "https://www.payfast.co.za/eng/query/validate",
)
PUBLIC_FRONTEND_URL = os.environ.get("PUBLIC_FRONTEND_URL", "http://localhost:3000").rstrip("/")
PUBLIC_BACKEND_URL = os.environ.get("PUBLIC_BACKEND_URL", "http://localhost:8000").rstrip("/")
PAYFAST_NOTIFY_URL = os.environ.get(
    "PAYFAST_NOTIFY_URL", f"{PUBLIC_BACKEND_URL}/api/payments/payfast/notify/"
)
PAYFAST_TRUST_X_FORWARDED_FOR = os.environ.get(
    "PAYFAST_TRUST_X_FORWARDED_FOR", "false"
).lower() in {"1", "true", "yes"}

EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "smtp").lower()
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "EventEveryday <bookings@eventeveryday.local>"
)
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO", "")

if EMAIL_PROVIDER == "resend":
    EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
    ANYMAIL = {"RESEND_API_KEY": os.environ.get("RESEND_API_KEY", "")}
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "mailpit")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "1025"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "false").lower() in {
        "1", "true", "yes"
    }
