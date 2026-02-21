"""
PolySniffer URLs - Admin Only Access
All URLs require staff access and should only be accessed from PassThrough Endpoint admin interface
"""
from django.urls import path
from .views.ui import redirect_to_admin, open_sniffer, navigate_with_toolbar, live_capture, capture_interface_view, split_window_view, polysniffer_in_content
from .views.proxy import proxy_capture, scp_catchall
from .views.dashboard import (
    debug_dashboard, view_log, export_har, capture_traffic, save_capture,
    log_capture_to_services, get_captures, apply_latest_capture,
    test_osticket_access, silent_capture, sync_v0_cookies
)
from .views.api import list_endpoints, csrf_token
from .views_ai import ai_analyze_endpoint, ai_generate_handler

app_name = 'polysniffer'

urlpatterns = [
    # Chrome Extension API endpoints
    path('api/endpoints/', list_endpoints, name='api_endpoints'),
    path('api/csrf-token/', csrf_token, name='api_csrf_token'),

    # AI analysis and handler generation
    path('ai-analyze/<int:endpoint_id>/', ai_analyze_endpoint, name='ai_analyze'),
    path('ai-generate-handler/<int:endpoint_id>/', ai_generate_handler, name='ai_generate_handler'),

    # Root URL - redirect to admin (PolySniffer should only be accessed via admin)
    path('', redirect_to_admin, name='index'),
    # Main entry point - accessed via admin "Sniff" button (old headless version)
    path('sniff/<int:endpoint_id>/', open_sniffer, name='open_sniffer'),
    # Live capture window - opens endpoint in new window with request interception
    path('capture/<int:endpoint_id>/', live_capture, name='live_capture'),
    # Navigate with persistent toolbar - redirects to endpoint with toolbar script
    path('navigate/<int:endpoint_id>/', navigate_with_toolbar, name='navigate_with_toolbar'),
    # Capture interface - green bar and capture log only (Tab 1)
    path('capture-interface/<int:endpoint_id>/', capture_interface_view, name='capture_interface'),
    # Split-window interface - top pane (controls/log) + bottom pane (iframe with proxied content)
    path('split-window/<int:endpoint_id>/', split_window_view, name='split_window'),
    # PolySniffer in content area - opens in main content area (for sidebar links)
    path('in-content/<int:endpoint_id>/', polysniffer_in_content, name='polysniffer_in_content'),
    # Proxy endpoint - forwards requests and captures traffic
    path('proxy/<int:endpoint_id>/', proxy_capture, name='proxy_capture'),
    path('proxy/<int:endpoint_id>/<path:path>', proxy_capture, name='proxy_capture_path'),
    # Dashboard - only accessible from within sniffer interface
    path('dashboard/', debug_dashboard, name='dashboard'),
    # Log detail view
    path('log/<int:log_id>/', view_log, name='log_detail'),
    # Export functions
    path('export/', export_har, name='export_har'),
    path('export/<int:log_id>/', export_har, name='export_single'),
    # Capture endpoint - for automatic logging (staff only)
    path('capture/', capture_traffic, name='capture'),
    # Save captured data to endpoint
    path('save-capture/<int:endpoint_id>/', save_capture, name='save_capture'),
    # Log captured POST data to CallbackData and MonitorLogger
    path('log-capture/<int:endpoint_id>/', log_capture_to_services, name='log_capture'),
    # Get captured requests (for polling)
    path('get-captures/<int:endpoint_id>/', get_captures, name='get_captures'),
    # Apply latest capture from standalone PolySniffer
    path('apply-capture/<int:endpoint_id>/', apply_latest_capture, name='apply_capture'),
    # Diagnostic endpoint - test OS Ticket access
    path('test-osticket/', test_osticket_access, name='test_osticket_access'),
    # Silent capture endpoint - receives data from stealth PolySniffer
    path('silent-capture/<int:endpoint_id>/', silent_capture, name='silent_capture'),
    # V0.dev cookie sync endpoint - syncs cookies from v0.dev after auth callback
    path('sync-v0-cookies/<int:endpoint_id>/', sync_v0_cookies, name='sync_v0_cookies'),
    # FINAL OS TICKET ROUTING FIX — Catch /scp/ requests (when included from mysite.urls)
    # This MUST be last to catch any unmatched paths
    path('<path:path>', scp_catchall, name='scp_catchall'),
]