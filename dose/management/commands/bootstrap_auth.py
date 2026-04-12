import os

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from dose.models import Tenant, UserProfile, UserTenantMembership


class Command(BaseCommand):
    help = "Bootstrap Site, admin user, and Google SocialApp from environment variables"

    def handle(self, *args, **options):
        site_domain = os.environ.get("BOOTSTRAP_SITE_DOMAIN", "").strip()
        site_name = os.environ.get("BOOTSTRAP_SITE_NAME", "PolySaaS Production").strip()

        admin_username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin").strip()
        admin_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@polysaas.online").strip()
        admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "").strip()

        google_client_id = os.environ.get("BOOTSTRAP_GOOGLE_CLIENT_ID", "").strip()
        google_client_secret = os.environ.get("BOOTSTRAP_GOOGLE_CLIENT_SECRET", "").strip()

        tenant_admin_username = os.environ.get("BOOTSTRAP_TENANT_ADMIN_USERNAME", "olientAdmin").strip()
        tenant_admin_email = os.environ.get("BOOTSTRAP_TENANT_ADMIN_EMAIL", "").strip()
        tenant_admin_password = os.environ.get("BOOTSTRAP_TENANT_ADMIN_PASSWORD", "olientPasswor123!").strip()
        tenant_admin_tenant_slug = os.environ.get("BOOTSTRAP_TENANT_ADMIN_TENANT_SLUG", "olient").strip()
        tenant_admin_tenant_name = os.environ.get("BOOTSTRAP_TENANT_ADMIN_TENANT_NAME", "").strip()
        tenant_admin_force_password = os.environ.get("BOOTSTRAP_TENANT_ADMIN_FORCE_PASSWORD", "0").strip() == "1"

        user_model = get_user_model()
        existing_admin = user_model.objects.filter(username=admin_username).first()
        existing_tenant_admin = user_model.objects.filter(username=tenant_admin_username).first()

        if (
            not site_domain
            and not admin_password
            and not google_client_id
            and existing_admin is None
            and existing_tenant_admin is None
        ):
            self.stdout.write("bootstrap_auth: nothing to do, skipping")
            return

        with transaction.atomic():
            site = None
            if site_domain:
                site, _ = Site.objects.update_or_create(
                    id=1,
                    defaults={"domain": site_domain, "name": site_name},
                )
                self.stdout.write(f"bootstrap_auth: site ready -> {site.id} {site.domain}")

            # Always ensure existing admin user has staff/superuser access.
            if admin_password or existing_admin is not None:
                admin_user, created = user_model.objects.get_or_create(
                    username=admin_username,
                    defaults={"email": admin_email},
                )
                if admin_email:
                    admin_user.email = admin_email
                admin_user.is_staff = True
                admin_user.is_superuser = True
                if admin_password:
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
                if site is None:
                    site, _ = Site.objects.get_or_create(
                        id=1,
                        defaults={"domain": "production.polysaas.online", "name": "PolySaaS Production"},
                    )
                google_app.sites.set([site])

                state = "created" if created else "updated"
                self.stdout.write(
                    f"bootstrap_auth: google social app {state} -> id={google_app.id}, site={site.domain}"
                )

            if tenant_admin_username:
                tenant_slug = tenant_admin_tenant_slug or "olient"
                tenant_name = tenant_admin_tenant_name or tenant_slug.replace("-", " ").title()
                if tenant_admin_email:
                    resolved_email = tenant_admin_email
                else:
                    safe_slug = slugify(tenant_slug).replace("-", "") or "tenant"
                    resolved_email = f"{tenant_admin_username}@{safe_slug}.local"

                tenant_obj = Tenant.objects.filter(slug=tenant_slug).first()
                if tenant_obj is None:
                    tenant_obj = Tenant(name=tenant_name, slug=tenant_slug, is_active=True)
                    tenant_obj.save()
                    self.stdout.write(
                        f"bootstrap_auth: tenant created -> slug={tenant_obj.slug}, schema={tenant_obj.schema_name}"
                    )

                tenant_admin_user, tenant_admin_created = user_model.objects.get_or_create(
                    username=tenant_admin_username,
                    defaults={"email": resolved_email},
                )
                if resolved_email:
                    tenant_admin_user.email = resolved_email
                tenant_admin_user.is_active = True
                tenant_admin_user.is_staff = True
                tenant_admin_user.is_superuser = True
                if tenant_admin_password and (tenant_admin_created or tenant_admin_force_password):
                    tenant_admin_user.set_password(tenant_admin_password)
                tenant_admin_user.save()

                membership, membership_created = UserTenantMembership.objects.get_or_create(
                    user=tenant_admin_user,
                    tenant=tenant_obj,
                    defaults={"role": UserTenantMembership.Role.ADMIN},
                )
                if membership.role != UserTenantMembership.Role.ADMIN:
                    membership.role = UserTenantMembership.Role.ADMIN
                    membership.save(update_fields=["role", "updated_at"])

                profile, profile_created = UserProfile.objects.get_or_create(
                    user=tenant_admin_user,
                    defaults={"tenant": tenant_obj},
                )
                if profile.tenant_id != tenant_obj.id:
                    profile.tenant = tenant_obj
                    profile.save(update_fields=["tenant"])

                user_state = "created" if tenant_admin_created else "updated"
                member_state = "created" if membership_created else "updated"
                profile_state = "created" if profile_created else "updated"
                self.stdout.write(
                    "bootstrap_auth: tenant admin "
                    f"{user_state} -> {tenant_admin_username}, tenant={tenant_obj.slug}, "
                    f"membership={member_state}, profile={profile_state}"
                )
