"""URL routes for /pt/polysniff/{endpoint_host}/ passthrough browse (iframe-safe)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Passthrough Workspace Iframe — 2026-06-24
#
# FIX 2026-08-21 (owner-approved, frozen-file exception): routes were keyed by
# PassThroughEndpoint.id (/pt/polysniff/4/), which is redundant — the workspace
# already resolved the endpoint by host, then looked it up again by id (and
# needed ?_ps_tenant= because ids are per-schema). Align with /pt/admin/<host>/
# and /admin/polysniffer/sniff/<host>/: the host in the path IS the endpoint.
# BINGO: PolySniffer Host-Keyed Polysniff URLs — 2026-08-21
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt

from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough
from dose.polysniffer.views.sync_session import sync_hubspot_session


@staff_member_required
@csrf_exempt
@xframe_options_exempt
def pt_polysniff_passthrough(request, endpoint_host: str, path: str = ""):
    return dispatch_polysniff_passthrough(request, endpoint_host, path)


app_name = "pt_polysniff"

urlpatterns = [
    path("<str:endpoint_host>/api/sync-session/", sync_hubspot_session, name="sync_session"),
    path("<str:endpoint_host>/", pt_polysniff_passthrough, {"path": ""}, name="root"),
    re_path(r"^(?P<endpoint_host>[^/]+)/(?P<path>.*)$", pt_polysniff_passthrough, name="subpath"),
]
