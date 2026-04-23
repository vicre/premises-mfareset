import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from environment variables if it does not already exist."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping superuser creation: DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD is missing."
                )
            )
            return

        User = get_user_model()

        user = User.objects.filter(username=username).first()
        if user:
            changed = False

            if not user.is_staff:
                user.is_staff = True
                changed = True

            if not user.is_superuser:
                user.is_superuser = True
                changed = True

            if email and getattr(user, "email", "") != email:
                user.email = email
                changed = True

            # Optional: keep password synced with env on startup
            if not user.check_password(password):
                user.set_password(password)
                changed = True

            if changed:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Updated existing superuser: {username}")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Superuser already exists: {username}")
                )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Created superuser: {username}")
        )