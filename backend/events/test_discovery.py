from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from .tests import make_event


class DiscoveryTests(TestCase):
    def test_upcoming_only_search_and_detail_history(self):
        now = timezone.now()
        future = make_event()
        past = make_event(title="Past", start_at=now-timedelta(days=1), end_at=now-timedelta(hours=1))
        make_event(title="Started", start_at=now, end_at=now+timedelta(hours=1))
        make_event(title="Draft", status="draft")
        with patch("events.views.timezone.now", return_value=now):
            for query in ("", " design ", "WORKSHOP", "cape town"):
                response = self.client.get("/api/events/", {"q": query})
                self.assertEqual([row["slug"] for row in response.json()], [future.slug])
            self.assertEqual(self.client.get("/api/events/", {"q": "unknown"}).json(), [])
        self.assertEqual(self.client.get(f"/api/events/{past.slug}/").status_code, 200)
