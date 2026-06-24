# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 — 2026-06-24
# dose/polysniffer/views/proxy.py — legacy proxy (deprecated in PolySniffer 2.0)

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.admin.views.decorators import staff_member_required


@csrf_exempt
@xframe_options_exempt
@staff_member_required
def scp_catchall(request, path=''):
    return HttpResponse("Not found", status=404)


@csrf_exempt
@xframe_options_exempt
@staff_member_required
def proxy_capture(request, endpoint_id, path=''):
    """
    DEPRECATED — PolySniffer 2.0 uses /dose/sniff/<id>/ native and passthrough modes.
    Redirect legacy /admin/polysniffer/proxy/ URLs to the mode picker.
    """
    return redirect('polysniffer_v2:mode_picker', endpoint_id=endpoint_id)
