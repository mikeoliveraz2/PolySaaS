from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS


def _endpoint_to_app_name(endpoint):
    """Map a PassThroughEndpoint to its corresponding TenantApp.app_name."""
    title = (endpoint.menu_title or '').lower()
    url = (endpoint.endpoint_url or '').lower()
    # Direct title mappings
    if 'mattermost' in title or 'mattermost' in url:
        return 'mattermost'
    if 'odoo' in title or 'odoo' in url:
        return 'odoo'
    if 'nextcloud' in title or 'nextcloud' in url:
        return 'nextcloud'
    if 'dolibarr' in title or 'dolibarr' in url:
        return 'dolibarr'
    if 'wordpress' in title or 'wordpress' in url:
        return 'wordpress'
    if 'liferay' in title or 'liferay' in url:
        return 'liferay'
    if 'monitor' in title or 'logger' in url:
        return 'monitor_logger'
    if 'polysysmon' in title or 'polysysmon' in url:
        return 'polysysmon'
    return None


class JazzminTenantThemeMiddleware(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    """
    Middleware to dynamically adjust Jazzmin settings per tenant.
    This example changes the site_brand and primary_color based on the tenant name.
    UPDATED: Now also dynamically injects PassThroughEndpoint records into topmenu_links.
    """

    def __call__(self, request):
        # DebugStackMiddleware.__call__ skips MiddlewareMixin.process_request — run it here.
        self.process_request(request)
        return super().__call__(request)

    def process_request(self, request):
        # Jazzmin admin templates (e.g. base_site.html extrahead) assume these exist.
        request.jazzmin_settings = dict(getattr(settings, "JAZZMIN_SETTINGS", None) or {})
        request.passthrough_endpoints = []

        print(f"[MIDDLEWARE ENTRY] JazzminTenantThemeMiddleware process_request called for {request.path}")

        # SCHEMA-PER-TENANT: resolve active tenant schema for sidebar passthrough links
        current_schema = request.session.get('schema_name') or getattr(request, 'schema_name', None)
        if not current_schema:
            tenant_slug = request.session.get('tenant_slug')
            if tenant_slug:
                try:
                    from dose.models import Tenant
                    with connection.cursor() as cursor:
                        cursor.execute('SET LOCAL search_path TO public;')
                    _t = Tenant.objects.filter(slug=tenant_slug, is_active=True).first()
                    if _t and _t.schema_name:
                        current_schema = _t.schema_name
                except Exception:
                    pass

        # DEBUG: Log schema status
        print(f"[JAZZMIN DEBUG] Request path: {request.path}")
        print(f"[JAZZMIN DEBUG] Current schema: {current_schema}")

        if current_schema and current_schema != 'public':
            print(f"[JAZZMIN DEBUG] Processing for schema: {current_schema}")

            jazzmin_settings = settings.JAZZMIN_SETTINGS.copy()
            jazzmin_settings['site_brand'] = f"DoseSaaS - {current_schema.title()}"

            # DYNAMIC MENU INTEGRATION: Add PassThroughEndpoint records to topmenu_links
            # Default must exist before try: if the try fails early, we still assign
            # request.passthrough_endpoints below (avoids UnboundLocalError → 500 on /admin/).
            passthrough_endpoints = []
            try:
                from dose.models.pass_through_endpoint import PassThroughEndpoint
                from dose.models import TenantApp
                from django.db import connection

                # Set search_path to current tenant schema
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{current_schema}",public;')

                # Get all PassThroughEndpoint records for this schema that should show in menu
                all_endpoints = list(
                    PassThroughEndpoint.objects.filter(show_in_menu=True)
                    .exclude(menu_title__isnull=True)
                    .exclude(menu_title__exact='')
                )

                # Filter to only those whose TenantApp is provisioned (status='active')
                passthrough_endpoints = []
                for ep in all_endpoints:
                    app_name = _endpoint_to_app_name(ep)
                    if app_name:
                        try:
                            ta = TenantApp.public_bundles.filter(
                                tenant__schema_name=current_schema,
                                app_name=app_name,
                            ).first()
                            if ta and ta.status == 'active':
                                passthrough_endpoints.append(ep)
                                print(f"[JAZZMIN DEBUG] + {ep.menu_title}: TenantApp is ACTIVE")
                            elif ta:
                                print(f"[JAZZMIN DEBUG] - {ep.menu_title}: TenantApp status={ta.status} (skipping)")
                            else:
                                print(f"[JAZZMIN DEBUG] - {ep.menu_title}: No TenantApp found (skipping)")
                        except Exception as e:
                            print(f"[JAZZMIN DEBUG] ? {ep.menu_title}: lookup error: {e}")
                    else:
                        # Unknown mapping — show anyway for backward compat
                        passthrough_endpoints.append(ep)

                print(f"[JAZZMIN DEBUG] Found {len(passthrough_endpoints)} endpoints to add to menu (schema: {current_schema})")
                for ep in passthrough_endpoints:
                    print(f"[JAZZMIN DEBUG] - {ep.menu_title}: {ep.endpoint_url} (id: {ep.id}, enabled: {ep.is_enabled})")

                # Copy existing topmenu_links and add dynamic items
                topmenu_links = jazzmin_settings.get('topmenu_links', []).copy()
                print(f"[JAZZMIN DEBUG] Original menu links: {len(topmenu_links)}")

                for endpoint in passthrough_endpoints:
                    # Don't add duplicates - check if this URL already exists in static config
                    existing_urls = [link.get('url', '') for link in topmenu_links if 'url' in link]
                    # Use slug-based passthrough URL (/pt/admin/<slug>/) — handler resolves upstream
                    full_url = endpoint.get_menu_url()
                    if full_url not in existing_urls:
                        menu_link = {
                            "name": endpoint.menu_title,
                            "url": full_url,
                            "permissions": ["auth.view_user"]
                        }
                        # Add icon if available
                        if endpoint.menu_icon and endpoint.menu_icon.strip():
                            menu_link["icon"] = endpoint.menu_icon
                        topmenu_links.append(menu_link)

                jazzmin_settings['topmenu_links'] = topmenu_links
                print(f"[JAZZMIN DEBUG] Final menu links: {len(topmenu_links)}")

            except Exception as e:
                # Graceful fallback - if there's any error, just use original settings
                # This prevents the middleware from breaking the entire site
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to add dynamic menu items: {e}")
                print(f"[JAZZMIN ERROR] Failed to add dynamic menu items: {e}")
                passthrough_endpoints = []
                jazzmin_settings = settings.JAZZMIN_SETTINGS.copy()
                jazzmin_settings["site_brand"] = f"DoseSaaS - {current_schema.title()}"

            request.jazzmin_settings = jazzmin_settings

            # Also add endpoints directly to request for template access
            request.passthrough_endpoints = passthrough_endpoints
            print(f"[TEMPLATE DEBUG] Set request.passthrough_endpoints with {len(passthrough_endpoints)} items")
        else:
            print(f"[JAZZMIN DEBUG] No tenant schema found - using default settings")
            request.jazzmin_settings = dict(getattr(settings, "JAZZMIN_SETTINGS", None) or {})
            request.passthrough_endpoints = []
            print(f"[TEMPLATE DEBUG] Set empty request.passthrough_endpoints (no tenant schema)")
