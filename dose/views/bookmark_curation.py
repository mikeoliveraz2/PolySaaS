import json
from urllib.parse import urlsplit

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST

from dose.polysniffer.handler_hooks import path_looks_like_non_page
from dose.polysniffer.sniff_tenant import bind_request_tenant
from dose.tenant_app_lookup import tenant_schema_search_path


def _endpoint_for_tenant(request, endpoint_host):
    tenant = bind_request_tenant(request)
    if not tenant:
        return None, None
    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return tenant, None
        from dose.polysniffer.views.core import get_endpoint_by_host

        endpoint = get_endpoint_by_host(endpoint_host, request)
    return tenant, endpoint


@staff_member_required
@require_GET
def bookmark_candidates(request, endpoint_host: str):
    tenant, endpoint = _endpoint_for_tenant(request, endpoint_host)
    if not tenant or endpoint is None:
        return JsonResponse(
            {"success": False, "error": "endpoint not found"},
            status=404,
        )
    from dose.passthrough.registry import resolve_handler_for_endpoint
    from dose.polysniffer.models import TrafficLog

    handler = resolve_handler_for_endpoint(endpoint)
    host = (urlsplit(endpoint.endpoint_url or "").hostname or "").lower()
    with tenant_schema_search_path(tenant):
        rows = (
            TrafficLog.objects.filter(method="GET", status_code__gte=200, status_code__lt=400)
            .filter(
                Q(url__icontains=host)
                | Q(endpoint_name__icontains=host)
                | Q(service__iexact=(endpoint.slug or ""))
            )
            .order_by("-captured_at")
            .values_list("path", flat=True)[:250]
        )
        candidates = []
        seen = set()
        for raw in rows:
            path = "/" + (raw or "").split("?", 1)[0].lstrip("/")
            if path in seen or path_looks_like_non_page(path, handler, request):
                continue
            seen.add(path)
            candidates.append(
                {
                    "path": path,
                    "title": path.strip("/").split("/")[-1].replace("-", " ").title()
                    or endpoint.get_menu_title(),
                }
            )
            if len(candidates) >= 30:
                break
    return JsonResponse({"success": True, "candidates": candidates})


@staff_member_required
@require_POST
def publish_bookmark(request, endpoint_host: str):
    tenant, endpoint = _endpoint_for_tenant(request, endpoint_host)
    if not tenant or endpoint is None:
        return JsonResponse(
            {"success": False, "error": "endpoint not found"},
            status=404,
        )
    try:
        data = json.loads(request.body or b"{}")
    except (TypeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        return JsonResponse(
            {"success": False, "error": "JSON object required"},
            status=400,
        )
    path = "/" + str(data.get("path") or "").split("?", 1)[0].lstrip("/")
    title = str(data.get("title") or path).strip()[:120]
    key = slugify(str(data.get("key") or title))[:100]
    destination_type = str(data.get("destination_type") or "passthrough_path")
    if destination_type not in ("passthrough_path", "external_path"):
        return JsonResponse(
            {"success": False, "error": "captured paths publish only as path bookmarks"},
            status=400,
        )
    if not key or not title:
        return JsonResponse(
            {"success": False, "error": "bookmark title and key are required"},
            status=400,
        )
    from dose.models import EndpointBookmark

    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return JsonResponse(
                {"success": False, "error": "invalid tenant schema"},
                status=400,
            )
        bookmark, created = EndpointBookmark.objects.update_or_create(
            endpoint=endpoint,
            key=key,
            defaults={
                "title": title,
                "destination_type": destination_type,
                "target": path,
                "is_active": True,
            },
        )
    return JsonResponse(
        {
            "success": True,
            "created": created,
            "bookmark": {
                "id": bookmark.id,
                "key": bookmark.key,
                "title": bookmark.title,
                "target": bookmark.target,
            },
        },
        status=201 if created else 200,
    )
