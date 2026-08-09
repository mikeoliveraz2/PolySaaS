"""
PolySniffer URLs - Admin Only Access
All URLs require staff access and should only be accessed from PassThrough Endpoint admin interface
"""
from django.urls import include, path
from .views.ui import redirect_to_admin
from .views.proxy import scp_catchall
from .views.dashboard import (
    debug_dashboard, view_log, export_har, capture_traffic,
)
from .views.api import list_endpoints, csrf_token, capture_endpoint
from .views_ai import ai_analyze_endpoint, ai_generate_handler

app_name = 'polysniffer'

urlpatterns = [
    # Chrome Extension API endpoints
    path('api/endpoints/', list_endpoints, name='api_endpoints'),
    path('api/csrf-token/', csrf_token, name='api_csrf_token'),
    path('api/capture/', capture_endpoint, name='api_capture'),

    # AI analysis and handler generation
    path('ai-analyze/<str:endpoint_host>/', ai_analyze_endpoint, name='ai_analyze'),
    path('ai-generate-handler/<str:endpoint_host>/', ai_generate_handler, name='ai_generate_handler'),

    # Root URL - redirect to admin (PolySniffer should only be accessed via admin)
    path('', redirect_to_admin, name='index'),
    # Canonical Admin-only workspace, identified by endpoint host.
    path('sniff/', include('dose.polysniffer.sniff_urls')),
    # Dashboard - only accessible from within sniffer interface
    path('dashboard/', debug_dashboard, name='dashboard'),
    # Log detail view
    path('log/<int:log_id>/', view_log, name='log_detail'),
    # Export functions
    path('export/', export_har, name='export_har'),
    path('export/<int:log_id>/', export_har, name='export_single'),
    # Capture endpoint - for automatic logging (staff only)
    path('capture/', capture_traffic, name='capture'),
    path('<path:path>', scp_catchall, name='scp_catchall'),
]