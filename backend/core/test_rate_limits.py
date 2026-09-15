from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import caches
from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from .rate_limits import RateLimitMiddleware, client_address


class RateLimitTests(SimpleTestCase):
    def setUp(self):
        caches['rate_limits'].clear()
        self.addCleanup(caches['rate_limits'].clear)
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda request: JsonResponse({}))

    def request(self, name='core:auth-login', path='/api/auth/login/', method='post', ip='192.0.2.1'):
        request = getattr(self.factory, method)(path, REMOTE_ADDR=ip)
        request.resolver_match = SimpleNamespace(view_name=name)
        return self.middleware.process_view(request, None, (), {})

    @override_settings(RATE_LIMITS={'api': (100, 60), 'login': (2, 60)})
    def test_limit_retry_and_recovery(self):
        with patch('core.rate_limits.time.time', return_value=120):
            self.assertIsNone(self.request())
            self.assertIsNone(self.request())
            response = self.request()
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response['Retry-After'], '60')
            self.assertEqual(response['Cache-Control'], 'no-store')
            self.assertIsNone(self.request(ip='192.0.2.2'))
        with patch('core.rate_limits.time.time', return_value=180):
            self.assertIsNone(self.request())

    @override_settings(RATE_LIMITS={
        'api': (100, 60), 'login': (1, 60), 'register': (1, 60),
        'booking_write': (1, 60), 'checkout': (1, 60),
    })
    def test_sensitive_scopes_and_exemptions(self):
        for name, path in [('core:auth-register', '/api/auth/register/'),
                           ('bookings:create', '/api/bookings/'),
                           ('bookings:detail', '/api/bookings/abc/'),
                           ('payments:checkout', '/api/payments/payfast/checkout/abc/'),
                           ('admin:login', '/admin/login/')]:
            with self.subTest(name=name):
                caches['rate_limits'].clear()
                self.assertIsNone(self.request(name, path))
                self.assertEqual(self.request(name, path).status_code, 429)
        for name in ['core:health', 'payments:notify']:
            for _ in range(3):
                self.assertIsNone(self.request(name))
        self.assertIsNone(self.request(method='options'))

    @override_settings(RATE_LIMITS={'api': (1, 60)})
    def test_global_limit_across_endpoints(self):
        self.assertIsNone(self.request('events:list', '/api/events/', 'get'))
        self.assertEqual(self.request('core:auth-me', '/api/auth/me/', 'get').status_code, 429)

    def test_untrusted_forwarded_header(self):
        request = self.factory.get('/', REMOTE_ADDR='192.0.2.1', HTTP_X_FORWARDED_FOR='198.51.100.1')
        self.assertEqual(client_address(request), '192.0.2.1')

    @override_settings(RATE_LIMIT_TRUSTED_PROXIES=['10.0.0.0/8'])
    def test_trusted_proxy_ignores_spoofed_prefix(self):
        request = self.factory.get('/', REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR='198.51.100.99, 192.0.2.1, 10.0.0.2')
        self.assertEqual(client_address(request), '192.0.2.1')
        request.META['HTTP_X_FORWARDED_FOR'] = 'invalid'
        self.assertEqual(client_address(request), '10.0.0.1')

    def test_cache_failure_blocks_request(self):
        with patch.object(caches['rate_limits'], 'add', side_effect=ConnectionError), self.assertLogs('core.rate_limits', level='ERROR'):
            self.assertEqual(self.request().status_code, 503)
