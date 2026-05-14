"""Dose utility helper functions (moved from utils.py)."""


def get_current_tenant(request):
    """Utility function to get current tenant from session."""
    import logging
    logger = logging.getLogger(__name__)
    tenant_slug = getattr(request, "current_tenant_slug", None)
    if tenant_slug is None:
        tenant_slug = request.session.get("tenant_slug")
    if tenant_slug is None:
        tenant_slug = request.session.get("tenant_id")
    logger.info(f"get_current_tenant: tenant_slug from session = {tenant_slug}")
    logger.info(f"get_current_tenant: session keys = {dict(request.session.items())}")
    if tenant_slug:
        from django.db import connection
        from dose.models import Tenant
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
                tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            logger.info(
                f"get_current_tenant: found tenant {tenant.name} (slug={tenant.slug}, active={tenant.is_active})"
            )
            return tenant
        except Tenant.DoesNotExist:
            logger.warning(
                f"get_current_tenant: Tenant with slug={tenant_slug} and is_active=True not found (public schema)"
            )
        except Exception as e:
            logger.error(f"get_current_tenant: Exception during tenant lookup (public schema): {e}")
    else:
        logger.warning("get_current_tenant: No tenant_slug in session, checking user profile")
        # Fallback: use user's profile tenant if session has no tenant
        try:
            from django.db import connection
            from dose.models import UserProfile, Tenant
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public;")
                    profile = UserProfile.objects.filter(user=user).select_related('tenant').first()
                    if profile and profile.tenant:
                        logger.info(f"get_current_tenant: using profile tenant {profile.tenant.name}")
                        # Set session tenant for future requests
                        request.session['tenant_slug'] = profile.tenant.slug
                        return profile.tenant
        except Exception as e:
            logger.error(f"get_current_tenant: Error checking user profile: {e}")


def get_current_tenant_role(request):
    """Active tenant role from middleware or session (for UI / API)."""
    role = getattr(request, "current_tenant_role", None)
    if role is not None:
        return role
    return request.session.get("tenant_role")


# Get theme colors based on tenant's selected theme
def get_tenant_theme_colors(theme_name):
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
            'light': '#eafaf1',
            'gradient': 'linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)',
            'name': 'Forest Green'
        },
        # Add more themes as needed
    }
    return theme_palettes.get(theme_name, theme_palettes['tech_blue'])


def create_schema_and_copy_tables(schema_name):
    """
    Ensure the PostgreSQL schema exists for a new tenant. Tables are created by
    ``python manage.py migrate`` (not by copying DDL from public), so django_migrations
    stays consistent with the physical schema.
    """
    from dose.management.schema_utils import create_tenant_schema_if_missing

    create_tenant_schema_if_missing(schema_name)
    print(f"✓ Schema '{schema_name}' ensured (empty). Run: python manage.py migrate")


def check_user_limit(tenant):
    """
    Check if a tenant can add another user based on their subscription plan.
    Returns (allowed: bool, message: str).
    """
    from dose.models import Subscription
    try:
        sub = Subscription.objects.get(tenant=tenant)
    except Subscription.DoesNotExist:
        return False, 'No active subscription. Please subscribe first.'

    if not sub.active:
        return False, 'Subscription is inactive. Please renew your subscription.'

    if sub.can_add_user():
        return True, ''

    max_users = sub.get_max_users()
    tier_label = dict(Subscription.PLAN_TIER_CHOICES).get(sub.plan_tier, sub.plan_tier)
    return False, (
        f'User limit reached for your {tier_label} plan '
        f'({max_users} user{"s" if max_users != 1 else ""}). '
        f'Please upgrade your plan to add more users.'
    )
