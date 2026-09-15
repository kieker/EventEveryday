"""Shared fixed-window limits, applied before request parsing or authentication."""

import hashlib
import ipaddress
import logging
import math
import time

from django.conf import settings
from django.core.cache import caches
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


def client_address(request):
    peer = request.META.get("REMOTE_ADDR", "")
    networks = [ipaddress.ip_network(value) for value in settings.RATE_LIMIT_TRUSTED_PROXIES]

    def trusted(value):
        return any(ipaddress.ip_address(value) in network for network in networks)

    try:
        address = ipaddress.ip_address(peer)
        if networks and trusted(peer):
            # Walk from the known peer toward the client, ignoring spoofed prefixes.
            for value in reversed(request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")):
                if not trusted(str(address)):
                    break
                address = ipaddress.ip_address(value.strip())
        return str(address)
    except ValueError:
        return peer


class RateLimitMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        name = request.resolver_match.view_name
        if request.method == "OPTIONS" or name in {"core:health", "payments:notify"}:
            return None
        scopes = ["api"] if request.path_info.startswith("/api/") else []
        if request.method == "POST":
            if name in {"core:auth-login", "admin:login"}:
                scopes.append("login")
            elif name == "core:auth-register":
                scopes.append("register")
            elif name == "payments:checkout":
                scopes.append("checkout")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and name in {
            "bookings:create", "bookings:detail"
        }:
            scopes.append("booking_write")
        if not scopes:
            return None
        identity = hashlib.sha256(client_address(request).encode()).hexdigest()
        now = time.time()
        cache = caches["rate_limits"]
        try:
            for scope in scopes:
                limit, seconds = settings.RATE_LIMITS[scope]
                window = int(now // seconds)
                remaining = max(1, math.ceil((window + 1) * seconds - now))
                key = f"rate:{scope}:{identity}:{window}"
                # Redis add (SET NX) and INCR are atomic across workers.
                if cache.add(key, 1, timeout=seconds + 1):
                    count = 1
                else:
                    count = cache.incr(key)
                if count > limit:
                    response = JsonResponse(
                        {"detail": "Too many requests. Please try again later."}, status=429
                    )
                    response["Retry-After"] = str(remaining)
                    response["Cache-Control"] = "no-store"
                    return response
        except Exception:
            logger.exception("Rate limit store unavailable")
            response = JsonResponse(
                {"detail": "Service temporarily unavailable. Please try again later."}, status=503
            )
            response["Retry-After"] = "30"
            response["Cache-Control"] = "no-store"
            return response
        return None
