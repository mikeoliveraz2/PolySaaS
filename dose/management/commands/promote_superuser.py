"""
Grant is_staff + is_superuser (+ is_active) to an existing user (Render / fresh DB).

Lives under the ``dose`` app so Django discovers it (``mysite`` is not in INSTALLED_APPS).

Lookup order for ``--email``:
  1. ``User.email`` (case-insensitive)
  2. django-allauth ``EmailAddress.email`` (same address, Google signup often stores it here)

After promoting, verify the admin index sees models::

  python manage.py diagnose_admin_dashboard --email you@example.com

Examples (Render Shell):

  python manage.py promote_superuser --email you@example.com
  python manage.py promote_superuser --username admin
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


def _user_from_email(User, email: str):
    user = User.objects.filter(email__iexact=email).first()
    if user is not None:
        return user, "auth_user.email"

    try:
        from allauth.account.models import EmailAddress

        ea = (
            EmailAddress.objects.filter(email__iexact=email)
            .select_related("user")
            .order_by("-primary", "-verified", "id")
            .first()
        )
        if ea is not None and ea.user_id:
            return ea.user, "allauth.account.EmailAddress"
    except Exception:
        pass

    return None, ""


class Command(BaseCommand):
    help = (
        "Set is_staff, is_superuser, and is_active for an existing user "
        "(lookup by email and/or username; email also checks allauth EmailAddress)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            dest="email",
            default="",
            help="Match User.email or allauth EmailAddress (case-insensitive)",
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
        via = ""
        user = None
        if email:
            user, via = _user_from_email(User, email)
        if user is None and username:
            user = User.objects.filter(
                **{f"{User.USERNAME_FIELD}__iexact": username}
            ).first()
            via = f"auth_user.{User.USERNAME_FIELD}"

        if user is None:
            raise CommandError(
                "No user found for the given email/username. "
                "Try: python manage.py diagnose_admin_dashboard --username <name> "
                "or list users in Django shell."
            )

        ident = getattr(user, User.USERNAME_FIELD)
        self.stdout.write(
            f"Matched pk={user.pk} via {via or '?'} — "
            f"username={ident!r} email={user.email!r} "
            f"is_active={user.is_active} is_staff={user.is_staff} is_superuser={user.is_superuser}"
        )

        update_fields: list[str] = []
        if not user.is_staff:
            user.is_staff = True
            update_fields.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            update_fields.append("is_superuser")
        if not user.is_active:
            user.is_active = True
            update_fields.append("is_active")

        if not update_fields:
            self.stdout.write(
                self.style.WARNING(
                    "No DB changes needed (already staff, superuser, and active). "
                    "If /admin/ still has no model cards, run:\n"
                    "  python manage.py diagnose_admin_dashboard --email ...\n"
                    "and paste the app_list / card counts."
                )
            )
            return

        user.save(update_fields=update_fields)
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {ident!r}: {', '.join(update_fields)} → True"
            )
        )
        if email:
            self.stdout.write(
                "Next: python manage.py diagnose_admin_dashboard "
                f"--email {email!r}"
            )
        else:
            self.stdout.write(
                "Next: python manage.py diagnose_admin_dashboard "
                f"--username {ident!r}"
            )
