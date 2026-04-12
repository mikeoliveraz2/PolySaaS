import os

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Bootstrap Site, admin user, and Google SocialApp from environment variables"

    def handle(self, *args, **options):
        site_domain = os.environ.get("BOOTSTRAP_SITE_DOMAIN", "production.polysaas.online").strip()
        site_name = os.environ.get("BOOTSTRAP_SITE_NAME", "PolySaaS Production").strip()

        admin_username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin").strip()
        admin_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@polysaas.online").strip()
        admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "").strip()

        google_client_id = os.environ.get("BOOTSTRAP_GOOGLE_CLIENT_ID", "").strip()
        google_client_secret = os.environ.get("BOOTSTRAP_GOOGLE_CLIENT_SECRET", "").strip()

        if not admin_password and not google_client_id:
            self.stdout.write("bootstrap_auth: no bootstrap env vars set, skipping")
            return

        with transaction.atomic():
            site, _ = Site.objects.update_or_create(
                id=1,
                defaults={"domain": site_domain, "name": site_name},
            )
            self.stdout.write(f"bootstrap_auth: site ready -> {site.id} {site.domain}")

            if admin_password:
                user_model = get_user_model()
                admin_user, created = user_model.objects.get_or_create(
                    username=admin_username,
                    defaults={"email": admin_email},
                )
                if admin_email:
                    admin_user.email = admin_email
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.set_password(admin_password)
                admin_user.save()
                state = "created" if created else "updated"
                self.stdout.write(f"bootstrap_auth: admin {state} -> {admin_username}")

            if google_client_id:
                from allauth.socialaccount.models import SocialApp

                google_app = SocialApp.objects.filter(provider="google").order_by("id").first()
                if google_app is None:
                    google_app = SocialApp(provider="google", name="Google")
                    created = True
                else:
                    created = False

                google_app.name = "Google"
                google_app.client_id = google_client_id
                google_app.secret = google_client_secret
                google_app.key = ""
                google_app.save()
                google_app.sites.set([site])

                state = "created" if created else "updated"
                self.stdout.write(
                    f"bootstrap_auth: google social app {state} -> id={google_app.id}, site={site.domain}"
                )
