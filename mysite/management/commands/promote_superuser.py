"""
Grant is_staff + is_superuser to an existing user (Render / fresh DB).

Examples (Render Shell, same env as the web service):

  python manage.py promote_superuser --email you@example.com
  python manage.py promote_superuser --username admin
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Set is_staff and is_superuser for an existing user (lookup by email and/or username)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            dest="email",
            default="",
            help="Match User.email case-insensitively",
        )
        parser.add_argument(
            "--username",
            dest="username",
            default="",
            help="Match User.USERNAME_FIELD case-insensitively",
        )

    def handle(self, *args, **options):
        email = (options.get("email") or "").strip()
        username = (options.get("username") or "").strip()
        if not email and not username:
            raise CommandError("Provide --email and/or --username.")

        User = get_user_model()
        user = None
        if email:
            user = User.objects.filter(email__iexact=email).first()
        if user is None and username:
            user = User.objects.filter(**{f"{User.USERNAME_FIELD}__iexact": username}).first()

        if user is None:
            raise CommandError("No user found for the given email/username.")

        if user.is_staff and user.is_superuser:
            self.stdout.write(
                self.style.WARNING(
                    f"User pk={user.pk} ({getattr(user, User.USERNAME_FIELD)}) "
                    "already has is_staff and is_superuser."
                )
            )
            return

        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=["is_staff", "is_superuser"])
        ident = getattr(user, User.USERNAME_FIELD)
        self.stdout.write(
            self.style.SUCCESS(
                f"Promoted pk={user.pk} username={ident!r} email={user.email!r} "
                "→ is_staff=True, is_superuser=True"
            )
        )
