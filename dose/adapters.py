"""
Custom adapters for django-allauth to handle multi-tenant schema issues
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.sites.models import Site
from django.db import connection, connections
import logging

logger = logging.getLogger(__name__)


# ─────── PATCH SITE MODEL TO ALWAYS USE PUBLIC SCHEMA ───────
# This ensures django-allauth can find the Site object even when
# running in a tenant schema context
# CRITICAL: We need to use raw SQL with explicit schema reference
# because SET search_path doesn't work reliably with Django ORM

_original_site_get = Site.objects.get
_original_site_filter = Site.objects.filter
_original_site_get_current = getattr(Site.objects, 'get_current', None)

def _site_get_with_public_schema(*args, **kwargs):
    """Wrapper that ensures Site.get() always queries from public schema"""
    # Use raw SQL to query from public schema explicitly
    # Import Site here to avoid shadowing issues
    from django.contrib.sites.models import Site as SiteModel

    db_conn = connections['default']
    with db_conn.cursor() as cursor:
        # Query Site from public schema using raw SQL
        if 'pk' in kwargs:
            site_id = kwargs['pk']
        elif 'id' in kwargs:
            site_id = kwargs['id']
        elif args:
            site_id = args[0]
        else:
            # Fallback to original method
            return _original_site_get(*args, **kwargs)

        # Get the actual table name from Site model
        table_name = SiteModel._meta.db_table
        cursor.execute(f"SELECT id, domain, name FROM public.{table_name} WHERE id = %s;", [site_id])
        row = cursor.fetchone()
        if row:
            site = SiteModel()
            site.id = row[0]
            site.domain = row[1]
            site.name = row[2]
            logger.debug(f"[CUSTOM ADAPTER] Retrieved Site {site_id} from public schema via raw SQL: {site.domain}")
            return site
        else:
            raise SiteModel.DoesNotExist(f"Site matching query does not exist (id={site_id})")

def _site_filter_with_public_schema(*args, **kwargs):
    """Wrapper that ensures Site.filter() always queries from public schema"""
    # Use raw SQL to query from public schema explicitly
    # Import Site here to avoid shadowing issues
    from django.contrib.sites.models import Site as SiteModel

    db_conn = connections['default']
    with db_conn.cursor() as cursor:
        # Build WHERE clause from kwargs
        where_clause = "1=1"
        params = []
        if 'pk' in kwargs:
            where_clause = "id = %s"
            params = [kwargs['pk']]
        elif 'id__in' in kwargs:
            # Handle id__in explicitly
            id_list = list(kwargs['id__in'])
            if id_list:
                placeholders = ','.join(['%s'] * len(id_list))
                where_clause = f"id IN ({placeholders})"
                params = id_list
            else:
                # Empty list - return no results
                where_clause = "1=0"
        elif 'id' in kwargs:
            where_clause = "id = %s"
            params = [kwargs['id']]

        # Get the actual table name from Site model
        table_name = SiteModel._meta.db_table
        cursor.execute(f"SELECT id, domain, name FROM public.{table_name} WHERE {where_clause} ORDER BY id;", params)
        rows = cursor.fetchall()
        sites = []
        for row in rows:
            site = SiteModel()
            site.id = row[0]
            site.domain = row[1]
            site.name = row[2]
            sites.append(site)
        logger.debug(f"[CUSTOM ADAPTER] Retrieved {len(sites)} Site(s) from public schema via raw SQL")
        # Instead of a custom class, use a real Django QuerySet
        # We'll create Site instances and use the real manager to create a queryset
        # First, ensure all Site instances are saved (they should already exist in DB)
        # Then use Site.objects.filter(id__in=[s.id for s in sites])

        # Get site IDs
        site_ids = [site.id for site in sites]

        # Use the original Site manager to get a real QuerySet
        # Temporarily set search_path to public to ensure we query from public schema
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL search_path TO public;")
            # Use the original filter method (not our patched one) to get a real QuerySet
            # We need to bypass our patch temporarily
            from django.db import models
            real_queryset = SiteModel._base_manager.filter(id__in=site_ids).order_by('id')
            # Reset search_path
            cursor.execute("RESET search_path;")

        logger.debug(f"[CUSTOM ADAPTER] Returning real QuerySet with {len(site_ids)} Site(s)")
        return real_queryset

def _site_get_current_with_public_schema(request=None):
    """Wrapper for Site.objects.get_current() to use public schema"""
    from django.conf import settings
    site_id = getattr(settings, 'SITE_ID', 1)
    return _site_get_with_public_schema(pk=site_id)

# Patch the Site manager methods
Site.objects.get = _site_get_with_public_schema
Site.objects.filter = _site_filter_with_public_schema
if _original_site_get_current:
    Site.objects.get_current = _site_get_current_with_public_schema

logger.debug("[CUSTOM ADAPTER] Patched Site model to always query from public schema using raw SQL")


def _emails_from_extra_data(extra_data):
    """Best-effort emails from provider JSON (Google and others vary shape)."""
    if not extra_data or not isinstance(extra_data, dict):
        return []
    found = []
    v = extra_data.get("email")
    if isinstance(v, str) and "@" in v:
        found.append(v)
    user_blob = extra_data.get("user")
    if isinstance(user_blob, dict):
        v2 = user_blob.get("email")
        if isinstance(v2, str) and "@" in v2:
            found.append(v2)
    return found


def _collect_candidate_emails(user, sociallogin=None):
    """
    Every place we might learn the Google/workspace email: User row, SocialLogin bundle,
    and persisted SocialAccount (for user_logged_in when sociallogin is not passed).
    """
    out = []
    if user is not None:
        e = getattr(user, "email", None)
        if e:
            out.append(e)
    if sociallogin is not None:
        for ea in getattr(sociallogin, "email_addresses", None) or []:
            em = getattr(ea, "email", None)
            if em:
                out.append(em)
        acc = getattr(sociallogin, "account", None)
        if acc is not None:
            out.extend(_emails_from_extra_data(getattr(acc, "extra_data", None) or {}))
    if sociallogin is None and user is not None and getattr(user, "pk", None):
        try:
            from allauth.socialaccount.models import SocialAccount

            for sa in SocialAccount.objects.filter(user=user).only("extra_data"):
                out.extend(_emails_from_extra_data(sa.extra_data or {}))
        except Exception:
            logger.debug(
                "[CUSTOM ADAPTER] Could not load SocialAccount emails for user pk=%s",
                user.pk,
                exc_info=True,
            )
    return {str(x).strip().lower() for x in out if x and str(x).strip()}


def _maybe_promote_superuser_from_settings(user, sociallogin=None):
    """If any known email is listed in POLYSAAS_SUPERUSER_EMAILS, grant staff + superuser (dev / bootstrap)."""
    from django.conf import settings

    allowed = getattr(settings, "POLYSAAS_SUPERUSER_EMAILS", None) or []
    if not allowed or not user:
        return
    allow_norm = {str(x).strip().lower() for x in allowed if x and str(x).strip()}
    candidates = _collect_candidate_emails(user, sociallogin)
    if not (candidates & allow_norm):
        return
    if not getattr(user, "pk", None):
        return
    if user.is_staff and user.is_superuser:
        return
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    matched = next(iter(candidates & allow_norm))
    logger.info(
        "[CUSTOM ADAPTER] Granted staff/superuser (matched %s, POLYSAAS_SUPERUSER_EMAILS)",
        matched,
    )


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that ensures Site queries use the public schema
    in multi-tenant setups.
    """

    def get_login_redirect_url(self, request):
        from dose.account_adapter import CustomAccountAdapter

        return CustomAccountAdapter().get_login_redirect_url(request)

    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        u = sociallogin.user
        if u is not None and getattr(u, "pk", None):
            _maybe_promote_superuser_from_settings(u, sociallogin)

    def get_site(self, request):
        """
        Override to ensure Site is queried from public schema
        """
        from django.conf import settings
        site_id = getattr(settings, 'SITE_ID', 1)

        # Always query Site from public schema (now handled by patched manager)
        try:
            site = Site.objects.get(pk=site_id)
            logger.debug(f"[CUSTOM ADAPTER] Retrieved Site {site_id} from public schema: {site.domain}")
            return site
        except Site.DoesNotExist:
            logger.error(f"[CUSTOM ADAPTER] Site {site_id} not found in public schema")
            # Fallback: try to create it
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL search_path TO public;")
                    site = Site.objects.create(
                        id=site_id,
                        domain='localhost:8000',
                        name='PolySaaS Development'
                    )
                    logger.info(f"[CUSTOM ADAPTER] Created Site {site_id} in public schema")
                    return site
            except Exception as e:
                logger.error(f"[CUSTOM ADAPTER] Failed to create Site: {e}")
                # Last resort: return a default Site object
                site = Site()
                site.id = site_id
                site.domain = 'localhost:8000'
                site.name = 'PolySaaS Development'
                return site

    def get_app(self, request, provider, client_id=None, **kwargs):
        """
        Override to ensure SocialApp is found even when sites are empty or in multi-tenant setup.
        The default implementation filters by site, but we need to handle cases where:
        1. SocialApp has no sites (empty sites list)
        2. Site queries need to use public schema

        Args:
            request: The HTTP request
            provider: The OAuth provider name (e.g., 'google')
            client_id: Optional client_id to filter by (not used in our implementation)
            **kwargs: Additional keyword arguments (ignored)
        """
        from allauth.socialaccount.models import SocialApp

        logger.info(f"[CUSTOM ADAPTER] get_app called for provider '{provider}'")

        # Get current site (using patched method that queries from public schema)
        try:
            site = self.get_site(request)
            logger.debug(f"[CUSTOM ADAPTER] Current site: {site.id} ({site.domain})")
        except Exception as e:
            logger.error(f"[CUSTOM ADAPTER] Error getting site: {e}")
            site = None

        # Try to find SocialApp for this site
        # CRITICAL: Ensure we query from public schema
        if site:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL search_path TO public;")
                    # First try: find app with this site
                    app = SocialApp.objects.filter(provider=provider, sites=site).first()
                    if app:
                        logger.info(f"[CUSTOM ADAPTER] ✅ Found SocialApp '{provider}' for site {site.id}")
                        return app
                    else:
                        logger.debug(f"[CUSTOM ADAPTER] No SocialApp found for provider '{provider}' with site {site.id}")
            except Exception as e:
                logger.warning(f"[CUSTOM ADAPTER] Error finding SocialApp by site: {e}")

        # Fallback: find app with no sites (empty sites list) or any site
        # CRITICAL: Check both public schema AND tenant schema (SocialApp might be saved in tenant schema)
        try:
            # Get current tenant schema if available
            tenant_schema = None
            try:
                from dose.utils import get_current_tenant
                tenant = get_current_tenant(request)
                if tenant and tenant.schema_name:
                    tenant_schema = tenant.schema_name
                    logger.debug(f"[CUSTOM ADAPTER] Current tenant schema: {tenant_schema}")
            except Exception as e:
                logger.debug(f"[CUSTOM ADAPTER] Could not get tenant schema: {e}")

            # List of schemas to check (public first, then tenant)
            schemas_to_check = ['public']
            if tenant_schema:
                schemas_to_check.append(tenant_schema)

            table_name = SocialApp._meta.db_table
            all_rows = []

            with connection.cursor() as cursor:
                # Check each schema
                for schema in schemas_to_check:
                    try:
                        cursor.execute(
                            f"SELECT id, provider, name, client_id, secret, key, settings FROM {schema}.{table_name} WHERE provider = %s;",
                            [provider]
                        )
                        rows = cursor.fetchall()
                        if rows:
                            logger.debug(f"[CUSTOM ADAPTER] Found {len(rows)} SocialApp(s) in schema '{schema}' for provider '{provider}'")
                            all_rows.extend([(schema, row) for row in rows])
                    except Exception as e:
                        logger.debug(f"[CUSTOM ADAPTER] Schema '{schema}' doesn't have {table_name} or error: {e}")

                logger.debug(f"[CUSTOM ADAPTER] Total found: {len(all_rows)} SocialApp(s) across all schemas")

                # Process all found apps
                for schema_name, row in all_rows:
                    app_id = row[0]
                    # Temporarily set search_path to the schema where we found the app
                    try:
                        with connection.cursor() as schema_cursor:
                            schema_cursor.execute(f"SET LOCAL search_path TO {schema_name},public;")
                            # Get the app using ORM from the correct schema
                            app = SocialApp.objects.get(pk=app_id)
                            app_sites = list(app.sites.all())
                            logger.debug(f"[CUSTOM ADAPTER] App ID {app.id} from schema '{schema_name}' has {len(app_sites)} site(s): {[s.id for s in app_sites]}")
                            # If app has no sites OR current site is in the app's sites
                            if len(app_sites) == 0:
                                logger.info(f"[CUSTOM ADAPTER] ✅ Found SocialApp '{provider}' with no sites (ID: {app.id}, schema: {schema_name})")
                                return app
                            elif site and site in app_sites:
                                logger.info(f"[CUSTOM ADAPTER] ✅ Found SocialApp '{provider}' with site {site.id} (ID: {app.id}, schema: {schema_name})")
                                return app
                    except Exception as e:
                        logger.warning(f"[CUSTOM ADAPTER] Error getting app {app_id} from schema '{schema_name}' or checking sites: {e}")
                        # If we can't get the app via ORM, try again with explicit schema
                        if app_id:
                            try:
                                with connection.cursor() as schema_cursor:
                                    schema_cursor.execute(f"SET LOCAL search_path TO {schema_name},public;")
                                    app = SocialApp.objects.get(pk=app_id)
                                    logger.info(f"[CUSTOM ADAPTER] ✅ Using SocialApp '{provider}' (ID: {app.id}, schema: {schema_name}) despite site check error")
                                    return app
                            except Exception as e2:
                                logger.warning(f"[CUSTOM ADAPTER] Failed to get app {app_id} from schema '{schema_name}': {e2}")
        except Exception as e:
            logger.error(f"[CUSTOM ADAPTER] Error in fallback SocialApp lookup: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Last resort: get any app for this provider (ignore sites)
        # CRITICAL: Check both public and tenant schemas
        try:
            # Get current tenant schema if available
            tenant_schema = None
            try:
                from dose.utils import get_current_tenant
                tenant = get_current_tenant(request)
                if tenant and tenant.schema_name:
                    tenant_schema = tenant.schema_name
            except:
                pass

            schemas_to_check = ['public']
            if tenant_schema:
                schemas_to_check.append(tenant_schema)

            table_name = SocialApp._meta.db_table

            with connection.cursor() as cursor:
                # Check each schema
                for schema in schemas_to_check:
                    try:
                        cursor.execute(
                            f"SELECT id FROM {schema}.{table_name} WHERE provider = %s LIMIT 1;",
                            [provider]
                        )
                        row = cursor.fetchone()
                        if row:
                            app_id = row[0]
                            # Set search_path to the schema where we found it
                            with connection.cursor() as schema_cursor:
                                schema_cursor.execute(f"SET LOCAL search_path TO {schema},public;")
                                app = SocialApp.objects.get(pk=app_id)
                                logger.warning(f"[CUSTOM ADAPTER] ⚠️ Using SocialApp '{provider}' without site filtering (ID: {app.id}, schema: {schema})")
                                return app
                    except Exception as e:
                        logger.debug(f"[CUSTOM ADAPTER] Schema '{schema}' check failed: {e}")
        except Exception as e:
            logger.error(f"[CUSTOM ADAPTER] Error finding any SocialApp: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # If we get here, no app was found
        logger.error(f"[CUSTOM ADAPTER] ❌ No SocialApp found for provider '{provider}'")
        from allauth.socialaccount.models import SocialApp
        raise SocialApp.DoesNotExist(f"No SocialApp found for provider '{provider}'")

    def save_user(self, request, sociallogin, form=None):
        """
        Override to ensure tokens are saved correctly in multi-tenant setup.
        Also adds logging to debug token saving issues.
        """
        logger.info(f"[CUSTOM ADAPTER] save_user called for user: {sociallogin.user.username}, provider: {sociallogin.account.provider}")

        # Call parent to save user and account
        user = super().save_user(request, sociallogin, form)
        _maybe_promote_superuser_from_settings(user, sociallogin)

        # Log token information
        if hasattr(sociallogin, 'token') and sociallogin.token:
            logger.info(f"[CUSTOM ADAPTER] ✅ Token exists in sociallogin: {sociallogin.token.token[:20] if sociallogin.token.token else 'None'}...")
            logger.info(f"[CUSTOM ADAPTER] Token expires_at: {sociallogin.token.expires_at}")
            logger.info(f"[CUSTOM ADAPTER] Token refresh_token (has): {bool(sociallogin.token.token_secret)}")
        else:
            logger.warning(f"[CUSTOM ADAPTER] ⚠️ No token in sociallogin for user {user.username}")

        # Verify token was saved
        try:
            from allauth.socialaccount.models import SocialToken
            saved_token = SocialToken.objects.filter(
                account__user=user,
                account__provider=sociallogin.account.provider
            ).first()
            if saved_token:
                logger.info(f"[CUSTOM ADAPTER] ✅ Token saved successfully: {saved_token.token[:20]}...")
            else:
                logger.error(f"[CUSTOM ADAPTER] ❌ Token NOT saved to database for user {user.username}")
        except Exception as e:
            logger.error(f"[CUSTOM ADAPTER] Error checking saved token: {e}")

        return user
