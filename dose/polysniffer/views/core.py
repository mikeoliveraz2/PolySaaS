# dose/polysniffer/views/core.py - 2026-01-17 22:35 PST

from django.http import Http404
from django.db import connection
from dose.utils import get_current_tenant
from dose.models import PassThroughEndpoint
import re
from urllib.parse import urlparse

STATIC_PATHS = ['/_next/', '/chat-static/', '/static/', '/assets/', '/css/', '/js/', '/fonts/', '/images/', '/image']
STATIC_EXTS = ['.css', '.js', '.woff', '.woff2', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.json', '.webp', '.ttf', '.otf', '.eot']

def is_static_asset(url):
    if not url:
        return False
    url_lower = url.lower()
    if '/chat-static/' in url or '/_next/' in url:
        return True
    return (
        any(p in url for p in STATIC_PATHS) or
        any(url_lower.endswith(ext) for ext in STATIC_EXTS) or
        'image?' in url_lower or
        'draft-preview' in url_lower or
        'manifest.json' in url_lower
    )

def is_external_asset(url):
    if not url:
        return False
    return url.startswith('https://cdn.') or url.startswith('https://assets.') or 'vercel' in url or 'cdn.' in url

def rewrite_static_url(match, base_url):
    attr = match.group(1)
    quote = match.group(2)
    url = match.group(3)
    if not url:
        return match.group(0)
    url = url.strip()
    if url.startswith('#') or url.startswith('javascript:') or url.startswith('data:') or url.startswith('mailto:'):
        return match.group(0)
    if is_external_asset(url):
        return match.group(0)
    if '/chat-static/' in url or '/_next/' in url:
        try:
            if url.startswith('http://') or url.startswith('https://'):
                parsed = urlparse(url)
                path = parsed.path
                query = '?' + parsed.query if parsed.query else ''
            elif url.startswith('/'):
                path = url.split('?')[0]
                query = '?' + url.split('?')[1] if '?' in url else ''
            else:
                path = '/' + url.split('?')[0]
                query = '?' + url.split('?')[1] if '?' in url else ''
            new_url = base_url + path + query
            return f'{attr}={quote}{new_url}{quote}'
        except:
            return match.group(0)
    if url.startswith('http://') or url.startswith('https://'):
        if 'localhost' not in url and '127.0.0.1' not in url and ':8000' not in url:
            return match.group(0)
        if '/chat-static/' in url or '/_next/' in url or is_static_asset(url):
            try:
                parsed = urlparse(url)
                new_url = base_url + parsed.path
                if parsed.query:
                    new_url += '?' + parsed.query
                if parsed.fragment:
                    new_url += '#' + parsed.fragment
                return f'{attr}={quote}{new_url}{quote}'
            except:
                pass
        return match.group(0)
    if url.startswith('/'):
        if '/chat-static/' in url or '/_next/' in url:
            return f'{attr}={quote}{base_url}{url}{quote}'
        if is_static_asset(url) or is_static_asset(url.split('?')[0]):
            return f'{attr}={quote}{base_url}{url}{quote}'
    return match.group(0)

def convert_relative_static_to_absolute(match, base_url):
    attr = match.group(1)
    quote = match.group(2)
    url = match.group(3)
    if not url:
        return match.group(0)
    url = url.strip()
    if url.startswith('#') or url.startswith('javascript:') or url.startswith('data:') or url.startswith('mailto:'):
        return match.group(0)
    if url.startswith('http://') or url.startswith('https://'):
        return match.group(0)
    if url.startswith('/') and ('/chat-static/' in url or '/_next/' in url or is_static_asset(url)):
        new_url = base_url + url
        return f'{attr}={quote}{new_url}{quote}'
    return match.group(0)

def get_endpoint_any_schema(endpoint_id, request=None):
    # FIX 2026-08-08 (owner-approved): PassThroughEndpoint.id is a per-schema
    # row id, not a global identifier -- id=1 in tenant A's schema and id=1 in
    # tenant B's schema are unrelated rows. This function used to trust
    # get_current_tenant(request) (the browser session's "active tenant")
    # blindly, so entering PolySniffer for one tenant's endpoint while the
    # session's active tenant was a *different* tenant silently resolved to
    # the wrong row (e.g. Odoo's admin-widget link opened Mattermost's
    # endpoint instead), which then broke browse-subpath/redirect logic
    # downstream in confusing, hard-to-diagnose ways.
    # Now the admin's PolySniffer entry link passes ?schema=<owning tenant
    # schema> explicitly (the schema is already known for certain at render
    # time -- it's whatever search_path was active when the admin listed that
    # row). If present and valid, that schema is authoritative for this
    # lookup and is also persisted to the session so subsequent in-workspace
    # navigation (which does not repeat the query param) stays consistent.
    # BINGO: PolySniffer Endpoint Schema Guard — 2026-08-08
    schema_param = (request.GET.get('schema') or '').strip() if request else ''
    if schema_param:
        if request is None or not getattr(request.user, 'is_staff', False):
            raise Http404("PolySniffer tenant context is invalid")

        from dose.models import Tenant
        owning_tenant = Tenant.objects.filter(schema_name=schema_param, is_active=True).first()
        if owning_tenant is None:
            raise Http404("PolySniffer endpoint not found in the requested tenant")

        try:
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{owning_tenant.schema_name}",public;')
            endpoint = PassThroughEndpoint.objects.filter(id=endpoint_id).first()
        except Exception as exc:
            raise Http404("PolySniffer endpoint lookup failed") from exc

        if endpoint is None:
            raise Http404("PolySniffer endpoint not found in the requested tenant")

        request.tenant = owning_tenant
        request.schema_name = owning_tenant.schema_name
        if request.session.get('tenant_slug') != owning_tenant.slug:
            from dose.doseusertenantmiddleware import set_tenant_in_session
            set_tenant_in_session(request, owning_tenant)
        return endpoint

    tenant = get_current_tenant(request) if request else None
    if not tenant or not tenant.schema_name:
        raise Http404("No active tenant context for endpoint lookup")

    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant.schema_name}",public;')
            endpoint = PassThroughEndpoint.objects.filter(id=endpoint_id).first()
            if endpoint:
                return endpoint
    except Exception:
        pass
    raise Http404(f"PassThroughEndpoint with id={endpoint_id} does not exist")


def get_endpoint_by_host(endpoint_host, request=None):
    """Resolve one tenant endpoint by its exact URL host, never by database ID."""
    schema_param = (request.GET.get('schema') or '').strip() if request else ''
    if schema_param:
        if request is None or not getattr(request.user, 'is_staff', False):
            raise Http404("PolySniffer tenant context is invalid")
        from dose.models import Tenant
        tenant = Tenant.objects.filter(schema_name=schema_param, is_active=True).first()
        if tenant is None:
            raise Http404("PolySniffer endpoint not found in the requested tenant")
    else:
        tenant = get_current_tenant(request) if request else None
        if not tenant or not tenant.schema_name:
            raise Http404("No active tenant context for endpoint lookup")

    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant.schema_name}",public;')
        matches = [
            endpoint for endpoint in PassThroughEndpoint.objects.all()
            if urlparse((endpoint.endpoint_url or '').strip()).netloc == endpoint_host
        ]
    except Exception as exc:
        raise Http404("PolySniffer endpoint lookup failed") from exc
    if len(matches) != 1:
        raise Http404("PolySniffer endpoint host is not unique in the requested tenant")

    if request is not None:
        request.tenant = tenant
        request.schema_name = tenant.schema_name
        if request.session.get('tenant_slug') != tenant.slug:
            from dose.doseusertenantmiddleware import set_tenant_in_session
            set_tenant_in_session(request, tenant)
    return matches[0]
