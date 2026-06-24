"""URL routes for /pt/polysniff/{endpoint_id}/ passthrough browse (iframe-safe)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Passthrough Workspace Iframe — 2026-06-24
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt

from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough


@staff_member_required
@csrf_exempt
@xframe_options_exempt
def pt_polysniff_passthrough(request, endpoint_id: int, path: str = ""):
    return dispatch_polysniff_passthrough(request, endpoint_id, path)


app_name = "pt_polysniff"

urlpatterns = [
    path("<int:endpoint_id>/", pt_polysniff_passthrough, {"path": ""}, name="root"),
    re_path(r"^(?P<endpoint_id>\d+)/(?P<path>.*)$", pt_polysniff_passthrough, name="subpath"),
]
