# dose/polysniffer/views/core.py - 2026-01-17 22:35 PST

from django.http import Http404
from django.db import connection
from dose.utils import get_current_tenant
from dose.models import PassThroughEndpoint
import re

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
    tenant = get_current_tenant(request) if request else None
    if tenant and tenant.schema_name:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant.schema_name},public;")
                endpoint = PassThroughEndpoint.objects.filter(id=endpoint_id).first()
                if endpoint:
                    return endpoint
        except Exception:
            pass
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
            endpoint = PassThroughEndpoint.objects.filter(id=endpoint_id).first()
            if endpoint:
                return endpoint
    except Exception:
        pass
    try:
        from dose.models.tenant import Tenant
        with connection.cursor() as cursor:
            tenants = Tenant.objects.all()
            for tenant_obj in tenants:
                if tenant_obj.schema_name:
                    try:
                        cursor.execute(f"SET search_path TO {tenant_obj.schema_name},public;")
                        endpoint = PassThroughEndpoint.objects.filter(id=endpoint_id).first()
                        if endpoint:
                            return endpoint
                    except Exception:
                        continue
    except Exception:
        pass
    raise Http404(f"PassThroughEndpoint with id={endpoint_id} does not exist")