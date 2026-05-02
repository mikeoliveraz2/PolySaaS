from dose.utils import get_current_tenant, get_current_tenant_role
from dose.models import UserProfile, Tenant
from django.db.models import Count, Max, Q
import logging

logger = logging.getLogger(__name__)

def tenant_context(request):
    """
    Req 5: expose tenant + role for templates.

    Use: ``{{ current_tenant.name }} ({{ current_tenant_role_display }})`` or
    ``{{ current_tenant_header_label }}`` for a single header string.
    """
    tenant = get_current_tenant(request)
    role = get_current_tenant_role(request) if tenant else None
    role_display = ""
    if role:
        role_display = role.replace("_", " ").strip().title()
    header_label = ""
    if tenant and role_display:
        header_label = f"{tenant.name} ({role_display})"
    elif tenant:
        header_label = tenant.name or ""
    return {
        "current_tenant": tenant,
        "current_tenant_role": role,
        "current_tenant_role_display": role_display,
        "current_tenant_header_label": header_label,
    }

def jazzmin_theme(request):
    import logging
    import logging
    import logging
    themes = [
        "default","cerulean","cosmo","cyborg","darkly","flatly","journal","litera","lumen","lux","materia","minty","pulse","sandstone","simplex","sketchy","slate","solar","spacelab","superhero","united","yeti"
    ]
    dark_themes = ["darkly","cyborg","slate","solar","superhero"]
    jazzmin_light_theme = "default"
    jazzmin_dark_theme = ""
    theme = "flatly"
    if request.user.is_authenticated:
        from dose.models import UserProfile
        from dose.tenant_utils import get_current_tenant

        # Get the user's actual tenant, not hardcoded public
        tenant = get_current_tenant(request)

        # If no tenant from session, try to get from user's existing profile
        if not tenant:
            try:
                existing_profile = getattr(request.user, 'userprofile', None)
                if existing_profile and existing_profile.tenant:
                    t = existing_profile.tenant
                    if t.schema_name and t.schema_name.lower() != "public":
                        tenant = t
            except Exception:
                tenant = None

        if tenant:
            try:
                profile = UserProfile.objects.get(user=request.user, tenant=tenant)
                theme = profile.last_selected_theme or "flatly"
                jazzmin_light_theme = profile.light_theme or "default"
                jazzmin_dark_theme = profile.dark_theme or ""
                # print(f"[CTXPROC] Found profile for {request.user.username} in {tenant.name}: light={jazzmin_light_theme}, dark={jazzmin_dark_theme}")
            except UserProfile.DoesNotExist:
                # print(f"[CTXPROC] No profile found for {request.user.username} in {tenant.name}")
                pass
        if theme not in themes:
            theme = "flatly"
        logging.info(f"Jazzmin context processor: user={request.user.username}, tenant={tenant}, injected jazzmin_theme={theme}, light={jazzmin_light_theme}, dark={jazzmin_dark_theme}")
    # print(f"[CTXPROC] Injecting jazzmin_theme={theme}, jazzmin_light_theme={jazzmin_light_theme}, jazzmin_dark_theme={jazzmin_dark_theme} for user={getattr(request.user, 'username', None)}")
    return {
        "jazzmin_theme": theme,
        "jazzmin_light_theme": jazzmin_light_theme,
        "jazzmin_dark_theme": jazzmin_dark_theme,
        "theme_list": themes,
        "dark_theme_list": dark_themes,
    }

# --- Theme toggle: Jazzmin UI tweaks context processor ---
def jazzmin_ui_tweaks(request):
    import logging
    from django.conf import settings

    # DYNAMIC MENU INTEGRATION: Check if middleware set custom jazzmin_settings
    context = {}
    if hasattr(request, 'jazzmin_settings'):
        # print(f"[CONTEXT DEBUG] Using custom jazzmin_settings from middleware")
        context['jazzmin_settings'] = request.jazzmin_settings
        # Extract topmenu_links for debugging
        topmenu_links = request.jazzmin_settings.get('topmenu_links', [])
        # print(f"[CONTEXT DEBUG] Custom topmenu_links count: {len(topmenu_links)}")
        # for i, link in enumerate(topmenu_links, 1):
        #     print(f"[CONTEXT DEBUG] {i}. {link.get('name', 'Unknown')}")
    else:
        pass
        # print(f"[CONTEXT DEBUG] Using default JAZZMIN_SETTINGS")
        context['jazzmin_settings'] = settings.JAZZMIN_SETTINGS

    if not request.user.is_authenticated:
        return context

    from dose.models import UserProfile
    from dose.tenant_utils import get_current_tenant

    profile = None
    if request.user.is_authenticated:
        tenant = get_current_tenant(request)
        if not tenant:
            try:
                up = getattr(request.user, "userprofile", None)
                if up and up.tenant and (up.tenant.schema_name or "").lower() != "public":
                    tenant = up.tenant
            except Exception:
                tenant = None
        if tenant:
            try:
                profile = UserProfile.objects.get(user=request.user, tenant=tenant)
            except UserProfile.DoesNotExist:
                return context
    if not profile:
        return context

    theme = getattr(profile, "last_selected_theme", "flatly")
    light_theme = getattr(profile, "light_theme", "flatly")
    dark_theme = getattr(profile, "dark_theme", "darkly")
    use_system_pref = getattr(profile, "use_system_pref", False)
    logging.info(f"Jazzmin context processor: user={request.user.username}, theme={theme}, light_theme={light_theme}, dark_theme={dark_theme}, use_system_pref={use_system_pref}")

    # Add theme-related context
    context.update({
        "JAZZMIN_UI_TWEAKS": {
            "theme": light_theme,
            "dark_mode_theme": dark_theme,
        },
        "JAZZMIN_USE_SYSTEM_PREF": use_system_pref,
        "jazzmin_theme": theme,
        "jazzmin_light_theme": light_theme,
        "jazzmin_dark_theme": dark_theme,
    })

    return context


def admin_active_urls(request):
    """
    Context processor to provide Active URLs data for admin dashboard.
    Only provides data if user is staff and accessing admin interface.
    """
    from django.db.models import Count, Max
    from dose.models.user_request_tracker import UserRequestTracker
    from dose.utils import get_current_tenant

    # Only provide data for admin interface
    if not (request.user.is_authenticated and request.user.is_staff):
        return {}

    # Only provide data for admin paths (include ``/admin`` index, no trailing slash)
    _p = request.path or ''
    if not (_p == '/admin' or _p.startswith('/admin/')):
        return {}

    try:
        tenant = get_current_tenant(request)

        # Get recent paths with aggregated data
        recent_paths_data = (
            UserRequestTracker.objects
            .filter(user=request.user, tenant=tenant)
            .values('path', 'method')
            .annotate(
                count=Count('id'),
                last_accessed=Max('timestamp')
            )
            .order_by('-last_accessed')[:20]
        )

        return {
            'recent_paths': recent_paths_data,
            'tenant': tenant,
        }
    except Exception as e:
        # Fail silently in production, just return empty context
        print(f"[ADMIN_CONTEXT] Error getting active URLs: {e}")
        return {}


def admin_navigation(request):
    """
    Context processor to provide navigation data for custom admin sidebar.
    Provides same navigation structure as landing page.
    """
    print(f"[ADMIN_NAV] ====== admin_navigation called for path: {request.path} ======")
    from dose.models import PassThroughEndpoint, NavigationPanel, NavigationItem
    from dose.utils import get_current_tenant

    # Only provide navigation data if user is authenticated
    if not request.user.is_authenticated:
        print("[ADMIN_NAV] User not authenticated - returning empty context")
        return {
            'passthrough_services': [],
            'external_services': [],
            'navigation_panels': [],
            'top_navigation_items': [],
        }

    try:
        # Ensure session is available
        if not hasattr(request, 'session'):
            print("[ADMIN_NAV] WARNING: Request has no session attribute")
            return {
                'passthrough_services': [],
                'external_services': [],
                'navigation_panels': [],
                'top_navigation_items': [],
            }

        tenant = get_current_tenant(request)
        print(f"[ADMIN_NAV] get_current_tenant returned: {tenant}")

        print(f"[ADMIN_NAV] User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        print(f"[ADMIN_NAV] Tenant: {tenant.name if tenant else 'None'}")

        # All PassThroughEndpoint records are passthrough services
        passthrough_services = []  # Passthrough endpoints (Gmail, HubSpot, etc.)
        external_services = []     # Other external integrations (from NavigationPanel if added later)

        try:
            from .models import TenantApp
            _subscribed = set(
                TenantApp.public_bundles.filter(
                    tenant=tenant,
                    status__in=['active', 'provisioning'],
                ).values_list('app_name', flat=True)
            ) if tenant else set()
        except Exception:
            _subscribed = set()

        def _endpoint_visible(trigger_path):
            if getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
                return True
            # Normalise: last path segment, lowercase, hyphens→underscores
            # so /dose/monitor-logger/ → monitor_logger, monitor-logger → monitor_logger
            n = trigger_path.strip('/').lower().split('/')[-1].replace('-', '_')
            return n == 'gmail' or n in _subscribed

        # Use endpoints from middleware if available (already queried and filtered)
        endpoints = []
        if hasattr(request, 'passthrough_endpoints') and request.passthrough_endpoints:
            endpoints = list(request.passthrough_endpoints)
            print(f"[ADMIN_NAV] Using {len(endpoints)} endpoints from request.passthrough_endpoints (set by middleware)")
            # Debug: print all endpoint trigger_paths to see what we have
            for ep in endpoints:
                print(f"[ADMIN_NAV]   - {ep.trigger_path} (menu_title: {ep.menu_title}, show_in_menu: {ep.show_in_menu}, is_enabled: {ep.is_enabled})")

            # Also include endpoints that might not have menu_title (like v0)
            # The middleware excludes endpoints without menu_title, but we want to show them in sidebar
            from django.db import connection
            if tenant and tenant.schema_name:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{tenant.schema_name}",public;')
                        # Get endpoints with show_in_menu=True but without menu_title (or with empty menu_title)
                        additional_endpoints = PassThroughEndpoint.objects.filter(
                            show_in_menu=True
                        ).filter(
                            Q(menu_title__isnull=True) | Q(menu_title__exact='')
                        )
                        additional_endpoints = list(additional_endpoints)

                        # Add endpoints that aren't already in the list
                        existing_trigger_paths = {ep.trigger_path for ep in endpoints}
                        for ep in additional_endpoints:
                            if ep.trigger_path not in existing_trigger_paths:
                                endpoints.append(ep)
                                print(f"[ADMIN_NAV] Added endpoint without menu_title: {ep.trigger_path}")

                        print(f"[ADMIN_NAV] Total endpoints after adding ones without menu_title: {len(endpoints)}")
                except Exception as e:
                    print(f"[ADMIN_NAV] Error querying additional endpoints: {e}")
                    import traceback
                    print(traceback.format_exc())
        else:
            # Fallback: query endpoints ourselves if middleware didn't set them
            print(f"[ADMIN_NAV] request.passthrough_endpoints not available, querying ourselves")
            from django.db import connection
            if tenant and tenant.schema_name:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{tenant.schema_name}",public;')
                        # First, check total count without filters
                        total_count = PassThroughEndpoint.objects.count()
                        print(f"[ADMIN_NAV] Total PassThroughEndpoints in schema {tenant.schema_name}: {total_count}")

                        # Check count with is_enabled filter only
                        enabled_count = PassThroughEndpoint.objects.filter(is_enabled=True).count()
                        print(f"[ADMIN_NAV] Enabled PassThroughEndpoints: {enabled_count}")

                        # Check count with show_in_menu filter only
                        menu_count = PassThroughEndpoint.objects.filter(show_in_menu=True).count()
                        print(f"[ADMIN_NAV] Show in menu PassThroughEndpoints: {menu_count}")

                        # Now get the filtered list
                        endpoints = PassThroughEndpoint.objects.filter(is_enabled=True, show_in_menu=True)
                        endpoints = list(endpoints)  # Convert to list while still in correct schema
                        print(f"[ADMIN_NAV] Found {len(endpoints)} enabled PassThroughEndpoints with show_in_menu=True in current tenant schema: {tenant.schema_name}")

                        # If no endpoints found with show_in_menu=True, try with just is_enabled=True
                        if len(endpoints) == 0 and enabled_count > 0:
                            print(f"[ADMIN_NAV] No endpoints with show_in_menu=True, trying with just is_enabled=True")
                            endpoints = PassThroughEndpoint.objects.filter(is_enabled=True)
                            endpoints = list(endpoints)
                            print(f"[ADMIN_NAV] Found {len(endpoints)} enabled PassThroughEndpoints (ignoring show_in_menu)")
                except Exception as e:
                    print(f"[ADMIN_NAV] Error querying PassThroughEndpoint in schema {tenant.schema_name}: {e}")
                    import traceback
                    print(traceback.format_exc())
            else:
                print(f"[ADMIN_NAV] No tenant found - no PassThroughEndpoints will be shown")

        # Track seen normalized trigger names to prevent duplicates.
        # Normalise: strip slashes, lowercase, take last path segment
        # so /Admin/Passthrough/Odoo/ and odoo both map to 'odoo'.
        # Prefer the clean simple-name entry; path-based stale entries are skipped.
        seen_normalized = set()

        for endpoint in endpoints:
            print(f"[ADMIN_NAV] Endpoint: {endpoint.trigger_path} - {endpoint.menu_title}")

            # Filter: only show gmail + subscribed bundled apps
            if not _endpoint_visible(endpoint.trigger_path):
                print(f"[ADMIN_NAV] Skipping unsubscribed: {endpoint.trigger_path}")
                continue

            # Deduplicate by normalized trigger name (last path segment, hyphens→underscores)
            norm = endpoint.trigger_path.strip('/').lower().split('/')[-1].replace('-', '_')
            if norm in seen_normalized:
                print(f"[ADMIN_NAV] Skipping duplicate (normalized '{norm}'): {endpoint.trigger_path}")
                continue
            seen_normalized.add(norm)

            # Build the sidebar URL from the endpoint_url hostname.
            # The trigger in the URL must be the real hostname — never a short name.
            # If endpoint_url is missing/invalid, skip this endpoint to avoid broken links.
            from urllib.parse import urlparse
            parsed = urlparse(endpoint.endpoint_url or '')
            hostname = parsed.netloc
            if not hostname:
                print(f"[ADMIN_NAV] Skipping endpoint '{endpoint.trigger_path}' — endpoint_url missing or invalid: {endpoint.endpoint_url!r}")
                continue
            url = f'/pt/admin/{hostname}/'
            title = endpoint.menu_title or norm.replace('_', ' ').title()
            print(f"[ADMIN_NAV] Passthrough service: {title} -> {url} (from {endpoint.endpoint_url})")

            service_data = {
                'id': endpoint.id,
                'url': url,
                'title': title,
                'description': endpoint.description or '',
                'icon': endpoint.menu_icon or '🔗',
            }

            # All PassThroughEndpoint records go to passthrough_services
            passthrough_services.append(service_data)

        # User Navigation Panels — current tenant schema only (no cross-tenant or public-schema menus)
        navigation_panels = []
        from django.db import connection

        all_panels = []
        seen_panel_ids = set()

        # Helper to query panels from a schema (matching landing_page approach)
        def query_panels_from_schema(schema_name, check_tenant=None):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}",public;')
                    # Use same query as landing_page
                    if check_tenant:
                        panels = NavigationPanel.objects.filter(
                            tenant=check_tenant,
                            is_active=True
                        ).order_by('sort_order')
                    else:
                        panels = NavigationPanel.objects.filter(is_active=True).order_by('sort_order')
                    return list(panels)
            except Exception as e:
                print(f"[ADMIN_NAV] Error querying NavigationPanel in schema {schema_name}: {e}")
                import traceback
                print(traceback.format_exc())
                return []

        # Try current tenant schema first (matching landing_page)
        if tenant and tenant.schema_name:
            panels = query_panels_from_schema(tenant.schema_name, tenant)
            for panel in panels:
                if panel.id not in seen_panel_ids:
                    all_panels.append(panel)
                    seen_panel_ids.add(panel.id)
            print(f"[ADMIN_NAV] Found {len(panels)} panels in current tenant schema {tenant.schema_name}")

        print(f"[ADMIN_NAV] Total panels found: {len(all_panels)}")

        # Process panels - use same approach as landing_page
        # Store panel data before processing (in case schema switches invalidate objects)
        panels_data = []
        for panel in all_panels:
            # Store panel attributes before any schema operations
            panel_tenant = panel.tenant if hasattr(panel, 'tenant') and panel.tenant else None
            panel_schema = (
                panel_tenant.schema_name if panel_tenant and panel_tenant.schema_name else ""
            )

            panels_data.append({
                'panel': panel,
                'panel_id': panel.id,
                'panel_title': panel.title,
                'panel_description': panel.description,
                'panel_type': panel.panel_type,
                'panel_background_color': panel.panel_background_color,
                'panel_schema': panel_schema,
                'panel_tenant': panel_tenant,
            })

        # Now process each panel with its items
        for panel_info in panels_data:
            panel = panel_info['panel']
            panel_schema = panel_info['panel_schema']
            panel_id = panel_info['panel_id']

            # Query NavigationItem in the correct schema - use same approach as landing_page
            items = []
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{panel_schema}",public;')
                    # Use same query as landing_page - filter by panel
                    items = NavigationItem.objects.filter(
                        panel_id=panel_id,  # Use panel_id to avoid object reference issues
                        is_active=True
                    ).order_by('sort_order')
                    items = list(items)  # Convert to list while still in correct schema
                    print(f"[ADMIN_NAV] Found {len(items)} items for panel '{panel_info['panel_title']}' (ID: {panel_id}) in schema {panel_schema}")
            except Exception as e:
                print(f"[ADMIN_NAV] Error querying NavigationItem for panel {panel_id} in schema {panel_schema}: {e}")
                import traceback
                print(traceback.format_exc())
                items = []

            # Filter items by user permissions (like landing_page)
            filtered_items = []
            for item in items:
                if item.has_permission(request.user):
                    filtered_items.append({
                        'id': item.id,
                        'url': item.url,
                        'title': item.title,
                        'description': item.description,
                        'target': item.target,
                        'item_type': item.item_type,
                        'item_css_class': item.item_css_class,
                        'button_color': item.button_color,
                        'icon_style': item.icon_style,
                        'icon_value': item.icon_value,
                        'click_count': item.click_count,
                    })

            # Only include panels that have at least one visible item (like landing_page)
            if filtered_items:
                panel_data = {
                    'title': panel_info['panel_title'],
                    'description': panel_info['panel_description'],
                    'panel_type': panel_info['panel_type'],
                    'panel_background_color': panel_info['panel_background_color'],
                    'filtered_items': filtered_items
                }
                navigation_panels.append(panel_data)
                print(f"[ADMIN_NAV] Added panel '{panel_info['panel_title']}' with {len(filtered_items)} visible items")

        # Top navigation items (system links) - MUST MATCH landing_page.py view
        # Index URL is often ``/admin`` (no trailing slash); ``startswith('/admin/')`` misses it.
        _admin_path = request.path or ''
        is_admin_context = _admin_path == '/admin' or _admin_path.startswith('/admin/')

        if is_admin_context:
            # No /admin/ “dashboard” link and no DoseAI/AI URLs in the admin sidebar.
            top_navigation_items = [
                {'name': 'Dose workspace', 'url': '/dose/dashboard/', 'icon': '📋'},
                {'name': 'Switch Tenant', 'url': '/dose/switch-tenant/', 'icon': '🔄'},
                {'name': 'Logout', 'url': '/dose/logout/', 'icon': '🚪'},
            ]
        else:
            top_navigation_items = [
                {'name': 'Dose workspace', 'url': '/dose/dashboard/', 'icon': '📊'},
                {'name': 'Admin home (models)', 'url': '/admin/', 'icon': '📋'},
                {'name': 'DoseAI Prompt & History', 'url': '/dose/doseai/', 'icon': '🤖'},
                {'name': 'Switch Tenant', 'url': '/dose/switch-tenant/', 'icon': '🔄'},
                {'name': 'Logout', 'url': '/dose/logout/', 'icon': '🚪'},
            ]

        # Add external services from 'External Services' NavigationPanel
        # Search across ALL schemas (schema-aware like PassThroughEndpoint)
        from django.db import connection

        # Helper to query NavigationPanel across schemas
        # Search for "External Services" or "External Resources" (user might have either name)
        # Also filter by tenant if tenant is provided
        def query_navigation_panels(schema_name, filter_tenant=None):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}",public;')
                    # Build query - filter by tenant if provided
                    base_filter = {'is_active': True}
                    if filter_tenant:
                        base_filter['tenant'] = filter_tenant

                    # Try "External Services" first (exact match)
                    panel = NavigationPanel.objects.filter(
                        title__iexact="External Services",
                        **base_filter
                    ).prefetch_related('navigation_items').first()

                    # If not found, try "External Resources" (exact match)
                    if not panel:
                        panel = NavigationPanel.objects.filter(
                            title__iexact="External Resources",
                            **base_filter
                        ).prefetch_related('navigation_items').first()

                    # If not found, try case-insensitive contains match for "External Services"
                    if not panel:
                        panel = NavigationPanel.objects.filter(
                            title__icontains="External Services",
                            **base_filter
                        ).prefetch_related('navigation_items').first()

                    # If not found, try case-insensitive contains match for "External Resources"
                    if not panel:
                        panel = NavigationPanel.objects.filter(
                            title__icontains="External Resources",
                            **base_filter
                        ).prefetch_related('navigation_items').first()

                    return panel
            except Exception as e:
                print(f"[ADMIN_NAV] Error querying NavigationPanel in schema {schema_name}: {e}")
                import traceback
                print(traceback.format_exc())
                return None

        # Try current tenant schema first (with tenant filter)
        external_panel = None
        external_panel_schema = None
        if tenant and tenant.schema_name:
            external_panel = query_navigation_panels(tenant.schema_name, filter_tenant=tenant)
            if external_panel:
                external_panel_schema = tenant.schema_name
                print(f"[ADMIN_NAV] Found External Services panel in current tenant schema: {tenant.schema_name} (tenant: {tenant.name})")

        # Do not load navigation from public or from other tenants' schemas (strict workspace isolation).

        if external_panel and external_panel_schema:
            try:
                # Use the schema where we found the panel
                panel_schema = external_panel_schema
                panel_id = external_panel.id
                panel_title = external_panel.title

                print(f"[ADMIN_NAV] Processing External Services panel: '{panel_title}' (ID: {panel_id}) in schema {panel_schema}")

                # Query items in the same schema as the panel
                external_items = []
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{panel_schema}",public;')
                        # Query items for this panel in the correct schema
                        external_items = list(NavigationItem.objects.filter(
                            panel_id=panel_id,
                            is_active=True
                        ).order_by('sort_order'))
                        print(f"[ADMIN_NAV] Found {len(external_items)} active items in panel '{panel_title}' (queried in schema {panel_schema})")
                        for item in external_items:
                            print(f"[ADMIN_NAV]   - Item: '{item.title}' (ID: {item.id}, URL: {item.url})")
                except Exception as e:
                    print(f"[ADMIN_NAV] Error querying NavigationItem in schema {panel_schema}: {e}")
                    import traceback
                    print(traceback.format_exc())

                # Only include items user has permission for
                for item in external_items:
                    has_perm = item.has_permission(request.user)
                    print(f"[ADMIN_NAV] Item '{item.title}': has_permission={has_perm}, requires_auth={item.requires_authentication}, requires_perms='{item.requires_permissions}'")
                    if has_perm:
                        # Check if already added (avoid duplicates)
                        if not any(svc['id'] == item.id for svc in external_services):
                            # Add to external_services list for sidebar display
                            external_services.append({
                                'id': item.id,
                                'title': item.title,
                                'url': item.url,
                                'description': item.description or '',
                                'icon': item.icon_value or '🔗',
                                'target': item.target or '_blank',  # Default to new window
                            })
                            print(f"[ADMIN_NAV] Added '{item.title}' to external_services list")
                            # Also add to top navigation for backward compatibility
                            top_navigation_items.append({
                                'name': item.title,
                                'url': item.url,
                                'icon': item.icon_value or '🔗',
                            })
            except Exception as e:
                import traceback
                print(f"[ADMIN_NAV] Error adding external services: {e}")
                print(traceback.format_exc())

        # DEBUG LOGGING
        print("\n" + "="*80)
        print(f"[ADMIN_NAV] CONTEXT DATA SUMMARY FOR {request.path}")
        print(f"  User: {request.user.username}")
        print(f"  Tenant: {tenant.name if tenant else 'None'}")
        print(f"  Passthrough Services: {len(passthrough_services)}")
        for svc in passthrough_services:
            print(f"    - {svc['title']}")
        print(f"  External Services: {len(external_services)}")
        for svc in external_services:
            print(f"    - {svc['title']}")
        print(f"  Navigation Panels: {len(navigation_panels)}")
        for panel in navigation_panels:
            print(f"    - {panel['title']}: {len(panel['filtered_items'])} items")
        print(f"  Top Navigation Items: {len(top_navigation_items)}")
        for item in top_navigation_items:
            print(f"    - {item['name']}")
        print("="*80 + "\n")

        return {
            'passthrough_services': passthrough_services,
            'external_services': external_services,
            'navigation_panels': navigation_panels,
            'top_navigation_items': top_navigation_items,
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            print(f"[ADMIN_NAV] ERROR getting navigation data: {e}")
            print(tb)
        except UnicodeEncodeError:
            print(f"[ADMIN_NAV] ERROR getting navigation data (encoding issue, see log)")
        logger.error(f"[ADMIN_NAV] Error: {e}")
        logger.error(tb)
        # Always return the expected structure, even on error.
        return {
            'passthrough_services': [],
            'external_services': [],
            'navigation_panels': [],
            'top_navigation_items': [],
        }

