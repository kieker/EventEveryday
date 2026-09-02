from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event


class Command(BaseCommand):
    help = "Create idempotent published events for local development."

    def handle(self, *args, **options):
        now = timezone.now()
        event_data = [
            {
                "slug": "jozi-creative-summit",
                "title": "Jozi Creative Summit",
                "summary": "A full day of ideas, craft, and conversation for South Africa's creative community.",
                "description": "Join designers, makers, writers, and founders for practical talks and generous conversations about building meaningful creative work.",
                "venue_name": "The Forum",
                "venue_address": "Katherine Street, Sandton, Johannesburg",
                "start_at": now + timedelta(days=28),
                "end_at": now + timedelta(days=28, hours=8),
                "capacity": 240,
                "price": Decimal("450.00"),
                "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1600&q=80",
            },
            {
                "slug": "cape-town-food-stories",
                "title": "Cape Town Food Stories",
                "summary": "An intimate evening celebrating the people and stories behind the city's food.",
                "description": "Taste a thoughtful menu while local cooks and producers share the histories, ingredients, and communities that shape Cape Town's table.",
                "venue_name": "The Old Biscuit Mill",
                "venue_address": "375 Albert Road, Woodstock, Cape Town",
                "start_at": now + timedelta(days=42),
                "end_at": now + timedelta(days=42, hours=4),
                "capacity": 90,
                "price": Decimal("680.00"),
                "image_url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1600&q=80",
            },
            {
                "slug": "durban-sunrise-run",
                "title": "Durban Sunrise Run",
                "summary": "A relaxed beachfront 10 km run followed by coffee and breakfast.",
                "description": "Start the morning beside the Indian Ocean with a welcoming, untimed community run suitable for a range of paces.",
                "venue_name": "Moses Mabhida People's Park",
                "venue_address": "44 Isaiah Ntshangase Road, Durban",
                "start_at": now + timedelta(days=56),
                "end_at": now + timedelta(days=56, hours=3),
                "capacity": 400,
                "price": Decimal("180.00"),
                "image_url": "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=1600&q=80",
            },
        ]

        created_count = 0
        for values in event_data:
            _, created = Event.objects.get_or_create(
                slug=values["slug"],
                defaults={**values, "status": Event.Status.PUBLISHED},
            )
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Development events ready ({created_count} created, "
                f"{len(event_data) - created_count} already present)."
            )
        )
