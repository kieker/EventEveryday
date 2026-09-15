from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class BookingSnapshotMigrationTests(TransactionTestCase):
    def test_existing_bookings_are_backfilled(self):
        before = [("bookings", "0001_initial")]
        after = [("bookings", "0002_booking_event_snapshot")]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            start = timezone.now() + timedelta(days=1)
            event = apps.get_model("events", "Event").objects.create(
                title="Legacy event", slug="legacy", summary="Summary",
                description="Description", venue_name="Legacy venue",
                venue_address="Legacy address", timezone="Africa/Johannesburg",
                start_at=start, end_at=start + timedelta(hours=2),
                capacity=10, price=Decimal("50.00"),
            )
            booking = apps.get_model("bookings", "Booking").objects.create(
                reference="EVT-LEGACY", event=event, contact_name="Guest",
                contact_email="guest@example.com", quantity=1,
                unit_price=Decimal("25.00"), total=Decimal("25.00"),
                expires_at=start,
            )
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            migrated = apps.get_model("bookings", "Booking").objects.get(pk=booking.pk)
            for field in ("title", "venue_name", "venue_address", "timezone", "start_at", "end_at"):
                self.assertEqual(getattr(migrated, f"event_{field}"), getattr(event, field))
            self.assertEqual(migrated.unit_price, Decimal("25.00"))
        finally:
            MigrationExecutor(connection).migrate(after)
