# DO NOT MODIFY: Critical system file. Ask before making changes.
"""
Custom context processors for D.O.S.E. multi-tenant functionality
"""
from dose.models import Tenant, UserProfile
from django.db import connection

def tenant_theme_context(request):
    """
    Add tenant theme information to template context for admin interface
    """
    context = {
        'tenant_theme': 'tech_blue',  # Default theme
        'tenant_name': 'D.O.S.E.',
        'current_tenant': None,
        'current_schema': 'public',  # Default schema
        'schema_display': 'Public Schema',
    }
    
    # Get current database schema
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_schema()')
            current_schema = cursor.fetchone()[0]
            context['current_schema'] = current_schema
            
            # Format schema name for display
            if current_schema == 'public':
                context['schema_display'] = 'Public Schema'
            else:
                context['schema_display'] = f"{current_schema.replace('_', ' ').title()} Schema"
                
    except Exception:
        # If schema detection fails, keep defaults
        pass
    
    # Only process for authenticated users
    if request.user and request.user.is_authenticated:
        try:
            # Get user's tenant from UserProfile
            user_profile = UserProfile.objects.select_related('tenant').get(user=request.user)
            
            if user_profile.tenant:
                context.update({
                    'tenant_theme': user_profile.tenant.admin_theme,
                    'tenant_name': user_profile.tenant.name,
                    'current_tenant': user_profile.tenant,
                })
                
                # If tenant has schema_name, use it for display
                if user_profile.tenant.schema_name:
                    context['schema_display'] = f"{user_profile.tenant.name} Schema ({user_profile.tenant.schema_name})"
                
        except UserProfile.DoesNotExist:
            # User has no tenant profile, use defaults
            pass
        except Exception:
            # Any other error, use defaults
            pass
    
    return context
