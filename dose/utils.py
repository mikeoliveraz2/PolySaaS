# Utility function to get current tenant from session
def get_current_tenant(request):
    import logging
    logger = logging.getLogger(__name__)
    tenant_id = request.session.get('tenant_id')
    logger.info(f"get_current_tenant: tenant_id from session = {tenant_id}")
    logger.info(f"get_current_tenant: session keys = {dict(request.session.items())}")
    if tenant_id:
        from django.db import connection
        from dose.models import Tenant
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            logger.info(f"get_current_tenant: found tenant {tenant.name} (id={tenant.id}, active={tenant.is_active})")
            return tenant
        except Tenant.DoesNotExist:
            logger.warning(f"get_current_tenant: Tenant with id={tenant_id} and is_active=True not found (public schema)")
        except Exception as e:
            logger.error(f"get_current_tenant: Exception during tenant lookup (public schema): {e}")
    else:
        logger.warning("get_current_tenant: No tenant_id in session")

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
from django.db import connection

def create_schema_and_copy_tables(schema_name):
    with connection.cursor() as cursor:
        # Create schema if it doesn't exist
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        print(f"✓ Schema '{schema_name}' ensured.")
        # Get all table names in public schema
        cursor.execute("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public';
        """)
        tables = [row[0] for row in cursor.fetchall()]
        # Copy each table structure to new schema
        for table in tables:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table} (LIKE public.{table} INCLUDING ALL);")
            print(f"✓ Table '{table}' copied to schema '{schema_name}'.")
    print(f"=== All tables copied to schema '{schema_name}' ===")

# Example usage:
# create_schema_and_copy_tables('alpha')


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
