from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseNotFound,
    Http404,
    HttpResponseForbidden,
)
from django.contrib.auth.decorators import login_required
import requests
import re

@csrf_exempt
def test_post(request):
    print('[DEBUG] /dose/test/ POST received:', request.method, request.body)
    return JsonResponse({'status': 'ok', 'method': request.method, 'body': request.body.decode('utf-8')})

print("[DEBUG] admin_views.py module loaded")

def _debug_pre_decorator():
    print("[DEBUG] set_theme PRE-DECORATOR ENTRY")
_debug_pre_decorator()

# AJAX endpoint to persist theme selection from Jazzmin GUI picker
@csrf_exempt
def set_theme(request):
    print("[DEBUG] --- set_theme ENTRY ---")
    print(f"[DEBUG] request.method: {request.method}")
    print(f"[DEBUG] request.path: {request.path}")
    print(f"[DEBUG] request.user: {getattr(request, 'user', None)} (is_authenticated: {getattr(request.user, 'is_authenticated', False)})")
    print(f"[DEBUG] request.tenant: {getattr(request, 'tenant', None)}")
    print(f"[DEBUG] request.GET: {request.GET.dict()}")
    print(f"[DEBUG] request.POST: {request.POST.dict()}")
    print(f"[DEBUG] request.body: {request.body}")
    print("[DEBUG] set_theme VIEW ENTRY: This should always print on POST to /dose/set-theme/")
    print(f"[DEBUG] Session keys: {getattr(request, 'session', None) and dict(request.session.items())}")
    print(f"[DEBUG] request.tenant: {getattr(request, 'tenant', None)}")
    # Try to fetch tenant from session if not present
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        tenant_id = request.session.get('tenant_id')
        print(f"[DEBUG] Fallback: tenant_id from session = {tenant_id}")
        from dose.models import Tenant
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id).first()
            print(f"[DEBUG] Fallback: tenant from DB = {tenant}")
    print(f"[DEBUG] set_theme called: method={request.method}, user={getattr(request, 'user', None)}")
    print(f"[DEBUG] request.POST: {request.POST.dict()}")
    print(f"[DEBUG] request.body: {request.body}")
    if not request.user.is_authenticated:
        print("[DEBUG] set_theme: user not authenticated")
        return JsonResponse({"status": "error", "message": "User not authenticated"}, status=400)
    if request.method != "POST":
        print(f"[DEBUG] set_theme: invalid method {request.method}")
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = getattr(request, 'user', None)
    if not tenant:
        print("[ERROR] set_theme: no tenant in session / request")
        return JsonResponse(
            {
                "status": "error",
                "message": "No tenant in session. Open a tenant workspace first (tenant isolation).",
            },
            status=400,
        )
    profile = None
    if user and user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=user, tenant=tenant)
        if created:
            print(f"[DEBUG] UserProfile created for user={user}, tenant={tenant}.")
        else:
            print(f"[DEBUG] UserProfile already exists for user={user}, tenant={tenant}.")
    print(f"[DEBUG] profile: {profile}")
    import logging
    # Main POST logic
    print(f"[ThemePicker] Raw POST body: {request.body}")
    print(f"[ThemePicker] request.POST dict: {request.POST.dict()}")
    # Try to get data from form-encoded POST first
    light_theme = request.POST.get("light_theme")
    dark_theme = request.POST.get("dark_theme")
    display_mode = request.POST.get("display_mode")
    print(f"[DEBUG] Parsed POST fields: light_theme={light_theme}, dark_theme={dark_theme}, display_mode={display_mode}")
    # Always try to parse JSON if POST is empty
    if not any([light_theme, dark_theme, display_mode]):
        try:
            import json
            body = request.body.decode().strip()
            print(f"[ThemePicker] Raw request.body: {body}")
            if body:
                data = json.loads(body)
                light_theme = data.get("light_theme", light_theme)
                dark_theme = data.get("dark_theme", dark_theme)
                display_mode = data.get("display_mode", display_mode)
                print(f"[ThemePicker] Parsed JSON: {data}")
        except Exception as e:
            print(f"[ThemePicker] JSON decode error: {e}")
    print(f"[DEBUG] Final fields: light_theme={light_theme}, dark_theme={dark_theme}, display_mode={display_mode}")
    updated_fields = []
    if light_theme is not None and str(light_theme).strip() != "":
        profile.light_theme = light_theme
        updated_fields.append("light_theme")
    if dark_theme is not None and str(dark_theme).strip() != "":
        profile.dark_theme = dark_theme
        updated_fields.append("dark_theme")
    if display_mode is not None and str(display_mode).strip() != "":
        if display_mode in ("light", "dark"):
            profile.last_selected_theme = profile.light_theme if display_mode == "light" else profile.dark_theme
            updated_fields.append("display_mode")
    print(f"[ThemePicker] Before save: light_theme={profile.light_theme}, dark_theme={profile.dark_theme}, last_selected_theme={profile.last_selected_theme}")
    try:
        profile.save()
        print(f"[ThemePicker] Save successful.")
    except Exception as e:
        print(f"[ThemePicker] Save failed: {e}")
    refreshed = UserProfile.objects.get(user=user, tenant=tenant)
    print(f"[ThemePicker] After save: last_selected_theme={refreshed.last_selected_theme}, light={refreshed.light_theme}, dark={refreshed.dark_theme}")
    return JsonResponse({"status": "ok", "updated_fields": updated_fields, "light_theme": profile.light_theme, "dark_theme": profile.dark_theme, "display_mode": display_mode, "last_selected_theme": profile.last_selected_theme})

from django.shortcuts import render, redirect
from dose.models import UserProfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Theme classification
THEMES = [
    "flatly","cerulean","cosmo","cyborg","darkly","journal","litera","lumen","lux","minty","pulse","sandstone","simplex","sketchy","slate","solar","spacelab","superhero","united","yeti"
]
LIGHT_THEMES = sorted([
    "flatly","cerulean","cosmo","journal","litera","lumen","lux","minty","pulse","sandstone","simplex","sketchy","spacelab","united","yeti"
])
DARK_THEMES = sorted([
    "cyborg","darkly","slate","solar","superhero"
])

@login_required
def select_theme_api(request):
    """JSON endpoint — returns current theme settings for the popup modal."""
    from dose.tenant_utils import get_current_tenant
    tenant = get_current_tenant(request)
    if not tenant:
        try:
            existing = getattr(request.user, 'userprofile', None)
            if existing and existing.tenant and existing.tenant.schema_name.lower() != 'public':
                tenant = existing.tenant
        except Exception:
            pass
    if not tenant:
        from django.http import JsonResponse as _J
        return _J({'light_theme': 'flatly', 'dark_theme': 'darkly', 'use_light_mode': True})
    from dose.models import UserProfile as _UP
    profile, _ = _UP.objects.get_or_create(user=request.user, tenant=tenant)
    from django.http import JsonResponse as _J
    return _J({
        'light_theme': profile.light_theme or 'flatly',
        'dark_theme':  profile.dark_theme  or 'darkly',
        'use_light_mode': not bool(getattr(profile, 'use_dark_mode', False)),
    })


@login_required
def select_theme(request):
    import logging
    from django.contrib import messages
    from dose.tenant_utils import get_current_tenant

    # Debug session contents
    print(f"[DEBUG] Session contents: {dict(request.session.items())}")
    print(f"[DEBUG] Session key 'tenant_id': {request.session.get('tenant_id')}")

    # Get the current tenant (required for UserProfile)
    tenant = get_current_tenant(request)
    print(f"[DEBUG] get_current_tenant returned: {tenant}")

    # If no tenant from session, try to get from user's existing profile
    if not tenant:
        try:
            existing_profile = getattr(request.user, 'userprofile', None)
            if existing_profile and existing_profile.tenant:
                t = existing_profile.tenant
                if t.schema_name and t.schema_name.lower() != "public":
                    tenant = t
                    print(f"[DEBUG] Fallback to tenant from user profile: {tenant}")
                    request.session['tenant_id'] = tenant.id
                    request.session['tenant_name'] = tenant.name
        except Exception as e:
            print(f"[DEBUG] Error getting tenant from user profile: {e}")

    if not tenant:
        messages.error(
            request,
            "No tenant selected. The shared public schema is not a tenant; choose your workspace first.",
        )
        return redirect("/dose/")

    print(f"[DEBUG] Using tenant: {tenant.name} (schema: {tenant.schema_name})")
    profile, created = UserProfile.objects.get_or_create(user=request.user, tenant=tenant)
    print(f"[DEBUG] Profile {'created' if created else 'found'}: light={profile.light_theme}, dark={profile.dark_theme}")
    if request.method == "POST":
        print(f"[DEBUG] POST request received")
        print(f"[DEBUG] POST data: {dict(request.POST.items())}")

        old_light = profile.light_theme
        old_dark = profile.dark_theme
        new_light = request.POST.get("light_theme", profile.light_theme)
        new_dark = request.POST.get("dark_theme", profile.dark_theme)
        new_system_pref = request.POST.get("use_system_pref") == "on"
        display_mode = request.POST.get("display_mode", "light")

        print(f"[DEBUG] Theme changes: {old_light}->{new_light}, old_dark->{new_dark}, system_pref: {new_system_pref}, display_mode: {display_mode}")

        profile.light_theme = new_light
        profile.dark_theme = new_dark
        profile.use_system_pref = new_system_pref
        profile.last_selected_theme = new_light if display_mode == "light" else new_dark
        profile.save()

        print(f"[DEBUG] Profile saved: light={profile.light_theme}, dark={profile.dark_theme}, last={profile.last_selected_theme}")
        logging.info(f"Theme selector POST: user={request.user.username}, old_light={old_light}, new_light={profile.light_theme}, old_dark={old_dark}, new_dark={profile.dark_theme}, use_system_pref={profile.use_system_pref}")

        return JsonResponse({
            'status': 'success',
            'message': 'Theme saved successfully',
            'light_theme': profile.light_theme,
            'dark_theme': profile.dark_theme,
            'last_selected_theme': profile.last_selected_theme
        })
    else:
        logging.info(f"Theme selector GET: user={request.user.username}, light_theme={profile.light_theme}, dark_theme={profile.dark_theme}")
        context = {
            "light_themes": LIGHT_THEMES,
            "dark_themes": DARK_THEMES,
            "light_theme": profile.light_theme,
            "dark_theme": profile.dark_theme,
            "use_system_pref": profile.use_system_pref,
        }
        print(f"[DEBUG] Template context: {context}")
        return render(request, "admin/select_theme.html", context)

@login_required
def font_controls(request):
    request.session['show_font_controls'] = True
    return redirect('/admin/')


def _split_html_document_for_jazzmin_embed(html: str):
    """
    Split a full HTML document into head/body inner HTML for admin/base_site.html.
    Drops upstream <title> so the admin page title block stays authoritative.

    Uses string boundaries only (no BeautifulSoup). BS4/html5lib can rewrite or
    break huge Mattermost shells (script order, attribute casing, stray tags).
    """
    import re

    raw = html or ""
    if not raw.strip():
        return "", ""

    lower = raw.lower()
    hi = lower.find("<head")
    if hi == -1:
        return "", raw

    open_gt = raw.find(">", hi)
    if open_gt == -1:
        return "", raw
    start_head_inner = open_gt + 1

    he = lower.find("</head>", start_head_inner)
    if he == -1:
        return "", raw

    head_inner = raw[start_head_inner:he]
    head_inner = re.sub(
        r"<title\b[^>]*>.*?</title>",
        "",
        head_inner,
        flags=re.IGNORECASE | re.DOTALL,
    )

    bi = lower.find("<body", he)
    if bi == -1:
        return head_inner, ""

    body_open_gt = raw.find(">", bi)
    if body_open_gt == -1:
        return head_inner, ""

    start_body_inner = body_open_gt + 1
    bcl = lower.rfind("</body>")
    if bcl == -1 or bcl < start_body_inner:
        body_inner = raw[start_body_inner:]
    else:
        body_inner = raw[start_body_inner:bcl]

    return head_inner, body_inner


def _process_upstream_html_for_embed(handler, raw_html: str, request, endpoint_url: str):
    """Same pipeline as passthrough forwarding HTML path; returns a single HTML string."""
    from django.http import HttpResponse

    processed = raw_html
    if handler and hasattr(handler, "process_html_response"):
        out = handler.process_html_response(raw_html, request, endpoint_url=endpoint_url)
        if isinstance(out, HttpResponse):
            return raw_html
        if isinstance(out, tuple):
            processed = out[0] if out[0] else raw_html
        else:
            processed = out if out is not None else raw_html
    return processed or raw_html


def _passthrough_debug_banner(trigger, info):
    """Render a collapsible debug banner above the passthrough content area."""
    rows = "".join(
        f"<tr><td style='padding:2px 8px;font-weight:600;white-space:nowrap'>{k}</td>"
        f"<td style='padding:2px 8px;font-family:monospace;word-break:break-all'>{v}</td></tr>"
        for k, v in info.items()
    )
    return (
        f'<details style="margin:0 0 6px 0;font-size:11px;background:#1e293b;color:#94a3b8;'
        f'border-radius:4px;padding:4px 8px;">'
        f'<summary style="cursor:pointer;color:#38bdf8;font-weight:600">'
        f'[DEBUG] passthrough:{trigger} — click to expand</summary>'
        f'<table style="border-collapse:collapse;margin-top:4px">{rows}</table>'
        f'</details>'
    )


@never_cache
@login_required
def passthrough_embed_view(request, trigger):
    """
    Renders admin/base_site.html with the passthrough app in {% block content %} only (no iframe).

    Upstream index HTML is fetched once, run through the same handler as /pt/... (rewrites + shims),
    then split so <head> fragments go to {% block extrahead %} and <body> inner HTML into the
    content column. Static assets may still load from the bundled app host; GET/POST API traffic
    uses the passthrough prefix via the injected client shim and middleware.
    """
    import logging

    from django.utils.html import escape
    from django.utils.safestring import mark_safe

    from dose.models import PassThroughEndpoint, TenantApp
    from dose.passthrough.forwarding import fetch_upstream_index_html
    from dose.passthrough.handlers.registry import get_handler_for_endpoint
    from dose.utils import get_current_tenant

    log = logging.getLogger(__name__)
    norm = trigger.strip('/').lower().split('/')[-1].replace('-', '_')
    tenant = get_current_tenant(request)

    try:
        subscribed = set(
            TenantApp.public_bundles.filter(
                tenant=tenant,
                status__in=['active', 'provisioning'],
            ).values_list('app_name', flat=True)
        ) if tenant else set()
    except Exception:
        subscribed = set()

    if not (getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)):
        if not (norm == 'gmail' or norm in subscribed):
            return HttpResponseNotFound('Not found')

    embed_src = f'/pt/admin/{norm}/'
    embed_title = norm.replace('_', ' ').title()
    _xrw = request.headers.get("X-Requested-With", "")
    print(
        f"[PSS_SHELL] passthrough_embed_view full_document=1 path={request.path!r} "
        f"trigger_norm={norm!r} user={getattr(request.user, 'username', None)!r} "
        f"tenant_schema={getattr(tenant, 'schema_name', None)!r} "
        f"x_requested_with={_xrw!r} "
        f"=> same admin/base_site.html request cycle as CRUD changelist"
    )
    log.info(
        "[PSS_SHELL] passthrough_embed_view path=%s trigger_norm=%s user_pk=%s tenant=%s xrw=%r",
        request.path,
        norm,
        getattr(request.user, "pk", None),
        getattr(tenant, "schema_name", None),
        _xrw,
    )

    embed_head = ""
    embed_body = ""
    debug_info = {}  # collect debug info for the banner

    # Query PassThroughEndpoint BEFORE setting tenant schema (it's in public)
    # Force public schema to avoid tenant schema issues
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public;")
    endpoint = PassThroughEndpoint.objects.filter(
        trigger_path__iexact=norm,
        is_enabled=True,
    ).order_by("-id").first()
    if endpoint is None and "_" in norm:
        endpoint = PassThroughEndpoint.objects.filter(
            trigger_path__iexact=norm.replace("_", ""),
            is_enabled=True,
        ).order_by("-id").first()

    # CRITICAL: Set search_path to tenant schema AFTER querying public models
    if tenant and tenant.schema_name:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant.schema_name}"')
            log.info(f"[PSS_SHELL] Set search_path to tenant schema: {tenant.schema_name}")

    if endpoint:
        handler = get_handler_for_endpoint(endpoint, request)

        # Collect debug info before fetch
        debug_info['endpoint_url'] = endpoint.endpoint_url
        debug_info['fetch_url'] = endpoint.endpoint_url.rstrip('/') + '/'
        upstream_cookies = {}
        if hasattr(handler, 'get_upstream_cookies'):
            try:
                upstream_cookies = handler.get_upstream_cookies(request) or {}
            except Exception as exc:
                debug_info['cookie_error'] = str(exc)
        debug_info['mmauthtoken'] = (upstream_cookies.get('MMAUTHTOKEN', '') or '')[:12] + '...' if upstream_cookies.get('MMAUTHTOKEN') else 'NONE'

        raw_html = fetch_upstream_index_html(request, endpoint.endpoint_url, "/", handler=handler)

        # PICOLLO PASSO: Raw mode for initial testing — set raw=1 query param to bypass all processing
        raw_mode = request.GET.get('raw', '0') == '1'

        if raw_html and raw_html.startswith("REDIRECT:"):
            parts = raw_html.split(":", 2)
            status_code = int(parts[1]) if len(parts) > 1 else 302
            location = parts[2] if len(parts) > 2 else "/"
            debug_info['result'] = f'REDIRECT {status_code} -> {location}'
            # Show debug banner instead of silently following the redirect
            embed_body = mark_safe(
                _passthrough_debug_banner(norm, debug_info) +
                f'<div class="alert alert-warning">Upstream returned {status_code} redirect to: <code>{escape(location)}</code></div>'
            )
        elif raw_mode and raw_html:
            # PICOLLO PASSO: Raw passthrough — handler fetches but no HTML processing
            debug_info['result'] = f'RAW MODE ({len(raw_html)} chars)'
            # NOTE: _process_upstream_html_for_embed and _split_html_document_for_jazzmin_embed
            # are bypassed in raw mode — no string replacements, no head/body split
            embed_body = mark_safe(
                f'<div class="alert alert-info">🧪 RAW MODE — No string replacements</div>'
                f'<div class="polysaas-raw-passthrough" style="width:100%;height:100%;">'
                f'{raw_html}</div>'
            )
            print(f"[PSS_SHELL] passthrough_embed RAW MODE trigger={norm!r} chars={len(raw_html)}")
        elif raw_html:
            debug_info['result'] = f'OK ({len(raw_html)} chars)'
            processed = _process_upstream_html_for_embed(
                handler, raw_html, request, endpoint.endpoint_url
            )
            _head, body_html = _split_html_document_for_jazzmin_embed(processed)
            debug_info['head_chars'] = len(_head or '')
            debug_info['body_chars'] = len(body_html or '')
            embed_body = mark_safe(
                _passthrough_debug_banner(norm, debug_info) +
                '<div class="polysaas-passthrough-scope" '
                f'data-polysaas-embed-trigger="{escape(norm)}">'
                f"{_head or ''}{body_html or ''}</div>"
            )
            print(
                f"[PSS_SHELL] passthrough_embed full_document trigger={norm!r} "
                f"head_chars={len(_head or '')} body_chars={len(body_html or '')}"
            )
        else:
            debug_info['result'] = 'EMPTY — upstream returned no HTML'
            embed_body = mark_safe(
                _passthrough_debug_banner(norm, debug_info) +
                '<div class="alert alert-warning">Could not load upstream HTML (check endpoint URL and network).</div>'
            )

    response = render(
        request,
        "admin/passthrough_embed.html",
        {
            "embed_src": embed_src,
            "embed_title": embed_title,
            "embed_head": embed_head,
            "embed_body": embed_body,
        },
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@never_cache
@login_required
def native_passthrough_alias_view(request, path):
    """
    Fallback view for handler-declared native aliases like /web/... .
    Middleware should normally rewrite and handle these before the view runs.
    """
    from dose.models import UserTenantMembership
    from dose.passthrough.incoming_path_rewrite import apply_incoming_path_rewrites
    from dose.passthrough.middleware import run_pt_admin_passthrough_core
    from dose.utils import get_current_tenant

    tenant = get_current_tenant(request)
    if not tenant:
        return HttpResponseForbidden("Tenant context is required for passthrough.")
    u = request.user
    if not u.is_superuser and not UserTenantMembership.objects.filter(
        user=u, tenant=tenant
    ).exists():
        return HttpResponseForbidden("You do not have access to this tenant.")

    apply_incoming_path_rewrites(request)
    if not request.path_info.startswith("/pt/"):
        raise Http404("No passthrough handler claimed this native alias path.")

    resp = run_pt_admin_passthrough_core(request)
    if resp is not None:
        return resp
    raise Http404("No enabled PassThroughEndpoint matches this native alias URL.")


@never_cache
@login_required
def pt_admin_generic_passthrough_view(request, trigger, subpath=None):
    """
    URLconf fallback for /pt/admin/<trigger>/ and nested paths. Middleware runs first;
    this view runs if the middleware delegated (e.g. ordering quirks) or for clearer
    login_required handling when the session is not yet authenticated.
    """
    from dose.models import UserTenantMembership
    from dose.passthrough.middleware import run_pt_admin_passthrough_core
    from dose.utils import get_current_tenant

    tenant = get_current_tenant(request)
    if not tenant:
        return HttpResponseForbidden("Tenant context is required for passthrough.")
    u = request.user
    if not u.is_superuser and not UserTenantMembership.objects.filter(
        user=u, tenant=tenant
    ).exists():
        return HttpResponseForbidden("You do not have access to this tenant.")

    resp = run_pt_admin_passthrough_core(request)
    if resp is not None:
        return resp
    raise Http404(
        "No enabled PassThroughEndpoint matches this URL, or the path is reserved "
        "(e.g. mattermost static, PolySniffer building pen)."
    )


@never_cache
@login_required
def passthrough_display_shell_view(request):
    """
    Phase 1: render admin/display.html — orchestration bar + head/body buckets only.
    No upstream HTML fetch and no URL rewriting; validates Jazzmin content shell.
    """
    response = render(
        request,
        "admin/display.html",
        {
            "display_title": "Passthrough display",
            "display_subtitle": "Shell (no proxified URLs yet)",
            "display_phase": "shell",
            "display_shell_footer": "Test shell (/admin/passthrough-display/) — open a sidebar passthrough link for a live app.",
            "display_enable_odoo_body_scope": False,
        },
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response