# DO NOT MODIFY: Critical system file. Ask before making changes.
from django.http import HttpResponseForbidden
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant
from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS

class TenantSessionMiddleware(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    """
    Session-based tenant middleware for multi-tenant Django applications
    Attaches tenant information to request based on session data
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Initialize tenant as None
        request.tenant = None

        # Skip tenant checking for certain URLs
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/dose/login/',
            '/dose/setup-demo/',
            '/dose/debug/',
            '/dose/health-check/',
        ]

        # Allow admin and static files
        if any(request.path.startswith(path) for path in skip_paths):
            response = self.get_response(request)
            return response

        # If user is authenticated, try to get tenant from session
        if hasattr(request, 'user') and request.user.is_authenticated:
            tenant_slug = request.session.get('tenant_slug') or request.session.get('tenant_id')
            if tenant_slug:
                try:
                    tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
                    request.tenant = tenant
                except Tenant.DoesNotExist:
                    # Invalid tenant in session, clear it
                    self.clear_tenant_from_session(request)
                    request.tenant = None

        # Process the request
        response = self.get_response(request)
        return response

    def clear_tenant_from_session(self, request):
        """Clear tenant information from session only if user is not authenticated or tenant is invalid"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            tenant_keys = ['tenant_id', 'tenant_name', 'tenant_slug', 'tenant_description', 'tenant_logo_url']
            for key in tenant_keys:
                if key in request.session:
                    del request.session[key]

def get_current_tenant(request):
    """Utility function to get current tenant from session"""
    tenant_slug = request.session.get('tenant_slug') or request.session.get('tenant_id')
    if tenant_slug:
        try:
            return Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            clear_tenant_from_session(request)
    return None

def clear_tenant_from_session(request):
    """Clear tenant information from session only if user is not authenticated or tenant is invalid"""
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        tenant_keys = ['tenant_id', 'tenant_name', 'tenant_slug', 'tenant_description', 'tenant_logo_url']
        for key in tenant_keys:
            if key in request.session:
                del request.session[key]

def set_tenant_in_session(request, tenant):
    """Manually set tenant in session (for login views)"""
    request.session['tenant_slug'] = tenant.slug
    request.session['tenant_id'] = tenant.slug
    request.session['tenant_name'] = tenant.name
    request.session['tenant_description'] = tenant.description or ''
    if tenant.logo:
        request.session['tenant_logo_url'] = tenant.logo.url