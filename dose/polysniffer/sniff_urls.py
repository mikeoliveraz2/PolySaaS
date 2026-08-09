# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION

# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24

"""PolySniffer 2.0 URL routes — mounted at /dose/sniff/."""

from django.urls import path

from dose.polysniffer.sniff_session import session_start, session_stop
from dose.polysniffer.views.sniff_v2 import export_session_har, sniff_diff

from dose.polysniffer.views.sniff_v2_workspace import (

    sniff_shell,

    workspace_poll,

)



app_name = 'polysniffer_v2'



urlpatterns = [

    path('<str:endpoint_host>/', sniff_shell, name='workspace'),
    path('<str:endpoint_host>/session/start/', session_start, name='session_start'),
    path('<str:endpoint_host>/session/stop/', session_stop, name='session_stop'),
    path('<str:endpoint_host>/diff/', sniff_diff, name='diff'),
    path('<str:endpoint_host>/export-har/', export_session_har, name='export_har'),
    path('<str:endpoint_host>/workspace/poll/', workspace_poll, name='workspace_poll'),
    path('<str:endpoint_host>/workspace/native/', sniff_shell, {'mode': 'native'}, name='workspace_native'),
    path('<str:endpoint_host>/workspace/passthrough/', sniff_shell, {'mode': 'passthrough'}, name='workspace_passthrough'),

]

