import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the local development administrator from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DEV_ADMIN_USERNAME", "").strip()
        email = os.environ.get("DEV_ADMIN_EMAIL", "").strip()
        password = os.environ.get("DEV_ADMIN_PASSWORD", "")

        if not username and not email and not password:
            self.stdout.write("Development administrator seed is disabled.")
            return

        if not all((username, email, password)):
            self.stderr.write(
                "Development administrator was not seeded: set DEV_ADMIN_USERNAME, "
                "DEV_ADMIN_EMAIL, and DEV_ADMIN_PASSWORD together."
            )
            return

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(update_fields=["email", "is_staff", "is_superuser", "password"])

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} development administrator {username}."))

