def get_tenant_theme_colors(theme_name):
    """Get theme colors based on tenant's selected theme"""
    theme_palettes = {
        'tech_blue': {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'dark': '#1a252f',
            'light': '#ecf0f1',
            'gradient': 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)',
            'name': 'Tech Blue'
        },
        'forest_green': {
            'primary': '#27ae60',
            'secondary': '#2ecc71',
            'accent': '#e67e22',
            'success': '#27ae60',
            'warning': '#f39c12',
            'dark': '#1e8449',
            'light': '#d5f4e6',
            'gradient': 'linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)',
            'name': 'Forest Green'
        },
        'royal_purple': {
            'primary': '#8e44ad',
            'secondary': '#9b59b6',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'dark': '#6c3483',
            'light': '#ebdef0',
            'gradient': 'linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%)',
            'name': 'Royal Purple'
        },
        'sunset_orange': {
            'primary': '#e67e22',
            'secondary': '#f39c12',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'dark': '#d35400',
            'light': '#fdeaa7',
            'gradient': 'linear-gradient(135deg, #e67e22 0%, #f39c12 100%)',
            'name': 'Sunset Orange'
        },
        'steel_gray': {
            'primary': '#34495e',
            'secondary': '#5d6d7e',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'dark': '#2c3e50',
            'light': '#d5dbdb',
            'gradient': 'linear-gradient(135deg, #34495e 0%, #5d6d7e 100%)',
            'name': 'Steel Gray'
        }
    }
    return theme_palettes.get(theme_name, theme_palettes['tech_blue'])

def tenants_for_user_assignment():
    """
    Active tenants that are allowed to hold tenant-isolated app data.
    The PostgreSQL catalog schema 'public' is never a tenant (shared registry only).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    from dose.models import Tenant

    queryset = Tenant.objects.filter(is_active=True).exclude(schema_name__iexact="public")
    count = queryset.count()
    logger.info(f"tenants_for_user_assignment: found {count} active tenants (excluding public)")
    
    # Log all tenants for debugging
    all_tenants = Tenant.objects.all()
    logger.info(f"tenants_for_user_assignment: total tenants in DB: {all_tenants.count()}")
    for tenant in all_tenants:
        logger.info(f"  - {tenant.slug}: is_active={tenant.is_active}, schema_name={tenant.schema_name}")
    
    return queryset


def get_current_tenant(request):
    import logging
    logger = logging.getLogger(__name__)
    tenant_slug = request.session.get('tenant_slug')
    logger.info(f"get_current_tenant: tenant_slug from session = {tenant_slug}")
    logger.info(f"get_current_tenant: session keys = {dict(request.session.items())}")
    if tenant_slug:
        from django.db import connection
        from dose.models import Tenant
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
                tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            logger.info(f"get_current_tenant: found tenant {tenant.name} (slug={tenant.slug}, active={tenant.is_active})")
            return tenant
        except Tenant.DoesNotExist:
            logger.warning(f"get_current_tenant: Tenant with slug={tenant_slug} and is_active=True not found (public schema)")
        except Exception as e:
            logger.error(f"get_current_tenant: Exception during tenant lookup (public schema): {e}")
    else:
        logger.warning("get_current_tenant: No tenant_slug in session")
    return None

def require_tenant(view_func):
    from django.http import HttpResponseForbidden
    def wrapper(request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"require_tenant: session keys = {dict(request.session.items())}")
        tenant = get_current_tenant(request)
        logger.info(f"require_tenant: tenant from get_current_tenant = {tenant}")
        if not tenant:
            logger.error("require_tenant: No active tenant session. Returning 403.")
            return HttpResponseForbidden("No active tenant session")
        return view_func(request, *args, **kwargs)
    return wrapper
