from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseForbidden,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import re
import logging

logger = logging.getLogger(__name__)

print("[DEBUG] admin_views.py module loaded")


# =============================================
# THEME FUNCTIONS
# =============================================
@csrf_exempt
def set_theme(request):
    print("[DEBUG] --- set_theme ENTRY ---")
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "User not authenticated"}, status=400)
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)

    from dose.utils import get_current_tenant
    from dose.models import UserProfile, Tenant

    tenant = get_current_tenant(request)
    if not tenant:
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id).first()

    if not tenant:
        return JsonResponse({"status": "error", "message": "No tenant found"}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=tenant)

    light_theme = request.POST.get("light_theme")
    dark_theme = request.POST.get("dark_theme")
    display_mode = request.POST.get("display_mode")

    if not any([light_theme, dark_theme, display_mode]):
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            light_theme = data.get("light_theme")
            dark_theme = data.get("dark_theme")
            display_mode = data.get("display_mode")
        except:
            pass

    updated = []
    if light_theme:
        profile.light_theme = light_theme
        updated.append("light_theme")
    if dark_theme:
        profile.dark_theme = dark_theme
        updated.append("dark_theme")
    if display_mode in ("light", "dark"):
        profile.last_selected_theme = profile.light_theme if display_mode == "light" else profile.dark_theme
        updated.append("display_mode")

    profile.save()

    return JsonResponse({
        "status": "ok",
        "updated_fields": updated,
        "light_theme": profile.light_theme,
        "dark_theme": profile.dark_theme,
    })


LIGHT_THEMES = sorted(["flatly","cerulean","cosmo","journal","litera","lumen","lux","minty","pulse","sandstone","simplex","sketchy","spacelab","united","yeti"])
DARK_THEMES = sorted(["cyborg","darkly","slate","solar","superhero"])


@login_required
def select_theme_api(request):
    from dose.utils import get_current_tenant
    from dose.models import UserProfile

    tenant = get_current_tenant(request)
    profile = None
    if tenant:
        profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=tenant)

    return JsonResponse({
        'light_theme': profile.light_theme if profile else 'flatly',
        'dark_theme': profile.dark_theme if profile else 'darkly',
        'use_light_mode': request.session.get('display_mode', 'light') == 'light',
    })


@login_required
def select_theme(request):
    from dose.utils import get_current_tenant
    from dose.models import UserProfile
    from django.contrib import messages

    tenant = get_current_tenant(request)
    if not tenant:
        messages.error(request, "No tenant selected.")
        return redirect("/dose/")

    profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=tenant)

    if request.method == "POST":
        profile.light_theme = request.POST.get("light_theme", profile.light_theme)
        profile.dark_theme = request.POST.get("dark_theme", profile.dark_theme)
        profile.use_system_pref = request.POST.get("use_system_pref") == "on"
        profile.save()

        request.session['light_theme'] = profile.light_theme
        request.session['dark_theme'] = profile.dark_theme
        return JsonResponse({'status': 'success'})

    context = {
        "light_themes": LIGHT_THEMES,
        "dark_themes": DARK_THEMES,
        "light_theme": profile.light_theme,
        "dark_theme": profile.dark_theme,
        "use_system_pref": getattr(profile, 'use_system_pref', False),
        "display_mode": request.session.get('display_mode', 'light'),
    }
    return render(request, "admin/select_theme.html", context)


# =============================================
# PASSTHROUGH VIEWS
# =============================================
@csrf_exempt
@never_cache
@login_required
def mattermost_error_recover_view(request):
    """Recover Mattermost's /error?type=team_not_found navigation into passthrough."""
    err_type = (request.GET.get('type') or '').strip().lower()
    referer = (request.META.get('HTTP_REFERER') or '').strip()

    # Try to recover trigger from the referring passthrough URL.
    trigger = ''
    m = re.search(r'/pt/admin/([^/]+)/', referer)
    if m:
        trigger = m.group(1)

    if err_type in ('team_not_found', 'not_found', 'team-not-found') and trigger:
        target = f'/pt/admin/{trigger}/'
        print(f"[MM ERROR RECOVER] Redirecting /error?type={err_type} -> {target}")
        return redirect(target)

    # Safe fallback when referer trigger is unavailable.
    if trigger:
        return redirect(f'/pt/admin/{trigger}/')
    return redirect('/admin/')


@never_cache
@login_required
def pt_admin_generic_passthrough_view(request, endpoint, subpath=None):
    """Main clean passthrough view"""
    print(f"[PASSTHROUGH VIEW] endpoint={endpoint}, subpath={subpath}, path={request.path}")
    with open('/tmp/odoo_view_debug.log', 'a') as f:
        f.write(f"[VIEW] Called with endpoint={endpoint}, subpath={subpath}\n")

    from dose.utils import get_current_tenant
    from dose.models import UserTenantMembership, PassThroughEndpoint
    from dose.passthrough.registry import get_handler
    from dose.passthrough.forwarding import forward_request_standardized
    from urllib.parse import urlparse

    tenant = get_current_tenant(request)
    if not tenant:
        return HttpResponseForbidden("No tenant context.")

    u = request.user
    if not (u.is_superuser or UserTenantMembership.objects.filter(user=u, tenant=tenant).exists()):
        return HttpResponseForbidden("Access denied to this tenant.")

    # Use modern handler discovery system, not legacy get_handler()
    from dose.passthrough.registry import resolve_handler_for_pt_admin_trigger
    handler = resolve_handler_for_pt_admin_trigger(endpoint)

    if handler and hasattr(handler, 'handle_request'):
        print(f"[VIEW] Using handler: {handler.__class__.__name__}")
        response = handler.handle_request(request, subpath)
        if response is not None:
            return response

    # Construct the upstream endpoint URL from the endpoint parameter
    endpoint_url = f"https://{endpoint}" if not endpoint.startswith(('http://', 'https://')) else endpoint
    print(f"[VIEW] Using generic forwarder for {endpoint} -> {endpoint_url}")
    
    # Lookup the actual PassThroughEndpoint ORM object to pass to handler.
    # The handler needs self.endpoint to be set so proxy_prefix property works.
    endpoint_obj = None
    try:
        # Try to find by endpoint_url (full URL) or by hostname match
        host = urlparse(endpoint_url).netloc.lower()
        print(f"[VIEW] Looking up PassThroughEndpoint by host: {host}")
        endpoint_obj = PassThroughEndpoint.objects.filter(
            endpoint_url__icontains=host
        ).first()
        if endpoint_obj:
            print(f"[VIEW] Resolved endpoint_obj: {endpoint_obj.endpoint_url}")
            # SET the endpoint on the handler so proxy_prefix works
            if handler and hasattr(handler, 'endpoint'):
                handler.endpoint = endpoint_obj
                print(f"[VIEW] Set handler.endpoint to PassThroughEndpoint object")
                if hasattr(handler, 'proxy_prefix'):
                    print(f"[VIEW] Handler proxy_prefix is now: {handler.proxy_prefix}")
            else:
                print(f"[VIEW] Handler has no endpoint attr or handler is None")
        else:
            print(f"[VIEW] No PassThroughEndpoint found for host: {host}")
            # List what we have for debugging
            all_eps = PassThroughEndpoint.objects.all().values_list('endpoint_url', flat=True)
            print(f"[VIEW] Available endpoints: {list(all_eps)}")
    except Exception as e:
        print(f"[VIEW] Could not resolve PassThroughEndpoint: {e}")
        import traceback
        traceback.print_exc()
    
    return forward_request_standardized(request, endpoint_url, handler=handler, endpoint=endpoint_obj, trigger=endpoint)


@never_cache
@login_required
def passthrough_embed_view(request, endpoint):
    print(f"[EMBED VIEW] endpoint={endpoint}")
    return HttpResponse(f"Embed view for {endpoint} - not fully implemented yet")


@never_cache
@login_required
def odoo_stray_web_request_view(request, rest=''):
    """
    Catch orphaned /web/* requests (e.g., /web/manifest.webmanifest, /web/assets/...)
    that come from Odoo's HTML but aren't prefixed with /pt/admin/{trigger}/.
    
    rest: Everything after /web (e.g., 'assets/file.css' or empty string for just /web/)
    Look up the current tenant's Odoo endpoint and proxy the request to it.
    """
    from dose.utils import get_current_tenant
    from dose.models import UserTenantMembership, TenantApp, PassThroughEndpoint
    from dose.passthrough.registry import get_handler, resolve_handler_for_pt_admin_trigger
    from dose.passthrough.forwarding import forward_request_standardized
    from urllib.parse import urlparse
    
    print(f"[ODOO STRAY] Caught orphaned /web request: path={request.path}, rest={rest}")
    
    tenant = get_current_tenant(request)
    if not tenant:
        return HttpResponseForbidden("No tenant context.")
    
    u = request.user
    if not (u.is_superuser or UserTenantMembership.objects.filter(user=u, tenant=tenant).exists()):
        return HttpResponseForbidden("Access denied to this tenant.")
    
    # Find the Odoo TenantApp for this tenant
    try:
        odoo_app = TenantApp.objects.filter(
            tenant=tenant,
            app_name__icontains='odoo'
        ).first()
        if not odoo_app or not odoo_app.app_url:
            print(f"[ODOO STRAY] No Odoo endpoint found for tenant {tenant.slug}")
            return HttpResponseNotFound("Odoo not configured for this tenant.")
        
        endpoint_url = odoo_app.app_url
        trigger = odoo_app.app_url.replace('https://', '').replace('http://', '')
        print(f"[ODOO STRAY] Found Odoo endpoint: {endpoint_url}, trigger: {trigger}")
    except Exception as e:
        logger.error(f"[ODOO STRAY] Error looking up Odoo endpoint: {e}")
        return HttpResponseNotFound(f"Error resolving Odoo endpoint: {e}")
    
    # Get the Odoo handler
    handler = resolve_handler_for_pt_admin_trigger(trigger)
    
    # Lookup the actual PassThroughEndpoint ORM object
    endpoint_obj = None
    try:
        host = urlparse(endpoint_url).netloc.lower()
        endpoint_obj = PassThroughEndpoint.objects.filter(
            endpoint_url__icontains=host
        ).first()
        if endpoint_obj:
            print(f"[ODOO STRAY] Resolved endpoint_obj: {endpoint_obj.endpoint_url}")
            # SET the endpoint on the handler so proxy_prefix works
            if handler and hasattr(handler, 'endpoint'):
                handler.endpoint = endpoint_obj
                print(f"[ODOO STRAY] Set handler.endpoint to PassThroughEndpoint object")
    except Exception as e:
        print(f"[ODOO STRAY] Could not resolve PassThroughEndpoint: {e}")
    
    # Reconstruct the full path for forwarding
    # The request.path is /web/... so we just forward it as-is
    print(f"[ODOO STRAY] Forwarding {request.path} to {endpoint_url}")
    return forward_request_standardized(request, endpoint_url, handler=handler, endpoint=endpoint_obj, trigger=trigger)