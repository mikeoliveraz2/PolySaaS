# dose/polysniffer/views/ui.py - 2026-01-17 22:35 PST

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from .core import get_endpoint_any_schema

@staff_member_required
def redirect_to_admin(request):
    return redirect('admin:dose_passthroughendpoint_changelist')

@staff_member_required
def open_sniffer(request, endpoint_id):
    if not request.user.is_staff:
        return redirect('admin:index')
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error Loading Endpoint</h1>
            <p>Could not find endpoint with ID: {endpoint_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=404)
    if not endpoint.endpoint_url:
        error_html = """
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error: No Endpoint URL</h1>
            <p>This endpoint does not have a URL configured.</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=400)
    return redirect('polysniffer:live_capture', endpoint_id=endpoint_id)

@staff_member_required
def navigate_with_toolbar(request, endpoint_id):
    if not request.user.is_staff:
        return redirect('admin:index')
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error Loading Endpoint</h1>
            <p>Could not find endpoint with ID: {endpoint_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=404)
    if not endpoint.endpoint_url:
        error_html = """
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error: No Endpoint URL</h1>
            <p>This endpoint does not have a URL configured.</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=400)
    target_url = request.GET.get('url', endpoint.endpoint_url)
    proxy_url_capture = f"/admin/polysniffer/capture-interface/{endpoint_id}/"
    proxy_url_nav = f"/admin/polysniffer/proxy/{endpoint_id}/"
    endpoint_name = endpoint.menu_title or endpoint.trigger_path or "Endpoint"
    is_mattermost = (endpoint.trigger_path or "").lower() == "mattermost"
    if is_mattermost:
        step2_href = reverse(
            "building_pen_embed",
            kwargs={"service_name": "mattermost", "endpoint_id": endpoint_id},
        )
        step2_title = "Open Embedded Mattermost"
        step2_description = (
            "Opens Mattermost through the server-side embed view (green PolySniffer toolbar). "
            "Keep the capture window from Step 1 open if you want traffic logged."
        )
        step2_button_class = "step-button btn btn-success"
        step2_button_text = "🚀 Open Embedded Mattermost"
    else:
        step2_href = proxy_url_nav
        step2_title = "Browse Application"
        step2_description = (
            "Opens the external application in the proxy. Navigate through the app normally — "
            "all traffic will be captured in the capture window from Step 1."
        )
        step2_button_class = "step-button secondary"
        step2_button_text = f"🌐 Browse {endpoint_name}"
    notice_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PolySniffer - {endpoint_name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: rgba(0, 0, 0, 0.7); margin: 0; padding: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
            .overlay-container {{ background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px 50px; max-width: 650px; width: 90%; text-align: center; }}
            .overlay-icon {{ font-size: 72px; margin-bottom: 20px; }}
            .overlay-title {{ font-size: 28px; font-weight: bold; color: #333; margin-bottom: 12px; }}
            .overlay-subtitle {{ font-size: 16px; color: #666; margin-bottom: 30px; }}
            .steps-container {{ display: flex; flex-direction: column; gap: 20px; margin-bottom: 30px; }}
            .step-card {{ background: #f8f9fa; border: 2px solid #e9ecef; border-radius: 12px; padding: 24px; text-align: left; transition: border-color 0.2s, box-shadow 0.2s; }}
            .step-card:hover {{ border-color: #667eea; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2); }}
            .step-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
            .step-number {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px; }}
            .step-title {{ font-size: 18px; font-weight: 600; color: #333; }}
            .step-description {{ font-size: 14px; color: #666; line-height: 1.5; margin-bottom: 16px; }}
            .step-button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 28px; font-size: 15px; font-weight: 600; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); }}
            .step-button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }}
            .step-button:active {{ transform: translateY(0); }}
            .step-button.secondary {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3); }}
            .step-button.secondary:hover {{ box-shadow: 0 6px 20px rgba(40, 167, 69, 0.5); }}
            a.step-button.btn-success {{ background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); color: #fff; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.35); }}
            a.step-button.btn-success:hover {{ box-shadow: 0 6px 20px rgba(40, 167, 69, 0.55); }}
            .endpoint-info {{ margin-top: 20px; padding: 16px; background: #f1f3f4; border-radius: 8px; font-size: 13px; color: #666; }}
            .endpoint-info strong {{ color: #333; }}
            .endpoint-url {{ word-break: break-all; font-family: monospace; background: #e9ecef; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-top: 4px; }}
            .close-btn {{ position: absolute; top: 20px; right: 20px; background: none; border: none; font-size: 28px; cursor: pointer; color: #999; transition: color 0.2s; }}
            .close-btn:hover {{ color: #333; }}
            .overlay-wrapper {{ position: relative; }}
            .step-status {{ display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: auto; }}
            .step-status.pending {{ background: #fff3cd; color: #856404; }}
            .step-status.complete {{ background: #d4edda; color: #155724; }}
        </style>
    </head>
    <body>
        <div class="overlay-wrapper">
            <div class="overlay-container">
                <button class="close-btn" onclick="window.close()" title="Close">&times;</button>
                <div class="overlay-icon">🔍</div>
                <div class="overlay-title">PolySniffer Capture</div>
                <div class="overlay-subtitle">Capture traffic from <strong>{endpoint_name}</strong></div>
                
                <div class="steps-container">
                    <div class="step-card" id="step1-card">
                        <div class="step-header">
                            <div class="step-number">1</div>
                            <div class="step-title">Open Capture Window</div>
                            <span class="step-status pending" id="step1-status">Pending</span>
                        </div>
                        <div class="step-description">
                            Opens the PolySniffer capture interface in a new tab. This window will record all HTTP requests and responses as you browse the application.
                        </div>
                        <a href="{proxy_url_capture}" target="_blank" class="step-button" onclick="markStep1Complete()">
                            📡 Open Capture Window
                        </a>
                    </div>
                    
                    <div class="step-card" id="step2-card">
                        <div class="step-header">
                            <div class="step-number">2</div>
                            <div class="step-title">{step2_title}</div>
                            <span class="step-status pending" id="step2-status">Pending</span>
                        </div>
                        <div class="step-description">
                            {step2_description}
                        </div>
                        <a href="{step2_href}" target="_blank" class="{step2_button_class}" onclick="markStep2Complete()">
                            {step2_button_text}
                        </a>
                    </div>
                </div>
                
                <div class="endpoint-info">
                    <strong>Endpoint URL:</strong><br>
                    <span class="endpoint-url">{target_url}</span>
                </div>
            </div>
        </div>
        
        <script>
            function markStep1Complete() {{
                document.getElementById('step1-status').textContent = 'Complete';
                document.getElementById('step1-status').className = 'step-status complete';
                localStorage.setItem('polysniffer_step1_{endpoint_id}', 'complete');
            }}
            
            function markStep2Complete() {{
                document.getElementById('step2-status').textContent = 'Complete';
                document.getElementById('step2-status').className = 'step-status complete';
                localStorage.setItem('polysniffer_step2_{endpoint_id}', 'complete');
            }}
            
            // Check if steps were previously completed
            window.onload = function() {{
                if (localStorage.getItem('polysniffer_step1_{endpoint_id}') === 'complete') {{
                    document.getElementById('step1-status').textContent = 'Complete';
                    document.getElementById('step1-status').className = 'step-status complete';
                }}
                if (localStorage.getItem('polysniffer_step2_{endpoint_id}') === 'complete') {{
                    document.getElementById('step2-status').textContent = 'Complete';
                    document.getElementById('step2-status').className = 'step-status complete';
                }}
            }};
            
            // Clear status when window closes
            window.onbeforeunload = function() {{
                localStorage.removeItem('polysniffer_step1_{endpoint_id}');
                localStorage.removeItem('polysniffer_step2_{endpoint_id}');
            }};
        </script>
    </body>
    </html>
    """
    return HttpResponse(notice_html)


@staff_member_required
def live_capture(request, endpoint_id):
    """
    Live capture interface - shows captured traffic in real-time
    """
    if not request.user.is_staff:
        return redirect('admin:index')
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error Loading Endpoint</h1>
            <p>Could not find endpoint with ID: {endpoint_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=404)
    endpoint_name = endpoint.menu_title or endpoint.trigger_path or "Endpoint"
    capture_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PolySniffer Live Capture - {endpoint_name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }}
            .header {{ background: #2a2a2a; padding: 15px 20px; border-bottom: 2px solid #0f0; display: flex; justify-content: space-between; align-items: center; }}
            .header-left h1 {{ margin: 0; font-size: 22px; color: #0f0; }}
            .header-left p {{ margin: 4px 0 0 0; color: #ccc; font-size: 14px; }}
            .header-right {{ display: flex; gap: 10px; align-items: center; }}
            .status {{ padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: bold; }}
            .status.polling {{ background: #1b5e20; color: #4caf50; }}
            .status.paused {{ background: #4a1010; color: #f44336; }}
            .btn {{ padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 13px; }}
            .btn-open {{ background: #2196f3; color: white; }}
            .btn-open:hover {{ background: #1976d2; }}
            .btn-clear {{ background: #dc3545; color: white; }}
            .btn-clear:hover {{ background: #c82333; }}
            .btn-pause {{ background: #ff9800; color: white; }}
            .btn-pause:hover {{ background: #f57c00; }}
            .btn-done {{ background: #2e7d32; color: white; font-weight: bold; }}
            .btn-done:hover {{ background: #1b5e20; }}
            #done-toast {{
                display: none; position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
                background: #1b5e20; color: #fff; padding: 12px 22px; border-radius: 8px;
                font-size: 14px; font-weight: 600; z-index: 99999; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            }}
            #done-toast.show {{ display: block; animation: fadein 0.3s ease; }}
            @keyframes fadein {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            .stats {{ background: #2a2a2a; padding: 10px 20px; border-bottom: 1px solid #444; display: flex; gap: 30px; font-size: 13px; color: #aaa; }}
            .stats span {{ color: #0f0; font-weight: bold; }}
            .captures {{ padding: 10px 20px; overflow-y: auto; height: calc(100vh - 130px); }}
            .capture-item {{ background: #2a2a2a; border: 1px solid #444; border-radius: 6px; padding: 12px 15px; margin-bottom: 8px; cursor: pointer; transition: background 0.15s; }}
            .capture-item:hover {{ background: #333; border-color: #0f0; }}
            .capture-item.new {{ animation: flash 0.5s; }}
            @keyframes flash {{ 0% {{ background: #1b3a1b; }} 100% {{ background: #2a2a2a; }} }}
            .capture-row {{ display: flex; justify-content: space-between; align-items: center; }}
            .capture-method {{ font-weight: bold; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
            .capture-method.GET {{ background: #1565c0; color: #bbdefb; }}
            .capture-method.POST {{ background: #2e7d32; color: #c8e6c9; }}
            .capture-method.PUT {{ background: #e65100; color: #ffe0b2; }}
            .capture-method.DELETE {{ background: #b71c1c; color: #ffcdd2; }}
            .capture-method.UNKNOWN {{ background: #555; color: #ccc; }}
            .capture-path {{ color: #ccc; font-size: 13px; margin-left: 10px; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .capture-status {{ font-size: 12px; margin-left: 10px; }}
            .capture-status.s2xx {{ color: #4caf50; }}
            .capture-status.s3xx {{ color: #ff9800; }}
            .capture-status.s4xx {{ color: #f44336; }}
            .capture-status.s5xx {{ color: #e91e63; }}
            .capture-status.s0 {{ color: #888; }}
            .capture-time {{ color: #666; font-size: 11px; margin-left: 10px; white-space: nowrap; }}
            .capture-detail {{ margin-top: 10px; padding-top: 10px; border-top: 1px solid #444; display: none; }}
            .capture-detail.open {{ display: block; }}
            .capture-detail pre {{ background: #1a1a1a; padding: 10px; border-radius: 4px; font-size: 11px; overflow-x: auto; max-height: 200px; overflow-y: auto; margin: 5px 0; }}
            .capture-detail h4 {{ margin: 8px 0 4px 0; color: #0f0; font-size: 12px; }}
            .empty {{ text-align: center; color: #666; padding: 60px 20px; font-size: 16px; }}
            .empty p {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div id="polysniffer-config"
             data-django-url="{request.scheme}://{request.get_host()}"
             data-endpoint-id="{endpoint_id}"
             data-endpoint-url="{endpoint.endpoint_url}"
             data-endpoint-name="{endpoint_name}"
             style="display:none;"></div>
        <div class="header">
            <div class="header-left">
                <h1>PolySniffer Live Capture</h1>
                <p>{endpoint_name}</p>
            </div>
            <div class="header-right">
                <span id="status" class="status polling">POLLING</span>
                <span id="ext-status" class="status" style="display:none;"></span>
                <button class="btn btn-open" onclick="window.open('{endpoint.endpoint_url}', '_blank')">Open {endpoint_name}</button>
                <button id="pause-btn" class="btn btn-pause" onclick="togglePoll()">Pause</button>
                <button class="btn btn-clear" onclick="clearAll()">Clear</button>
                <button type="button" id="done-btn" class="btn btn-done" title="Stop extension capture and release the target tab">Done — stop sniffing</button>
            </div>
        </div>
        <div class="stats">
            Captured: <span id="count">0</span> &nbsp;|&nbsp;
            Last update: <span id="last-update">-</span> &nbsp;|&nbsp;
            Target: <span>{endpoint.endpoint_url}</span>
        </div>
        <div class="captures" id="captures"></div>
        <div id="done-toast" role="status">PolySniffer stopped. Extension is idle — passthrough tabs behave normally.</div>

        <script src="/static/polysniffer/live_capture.js"></script>
    </body>
    </html>
    """
    return HttpResponse(capture_html, content_type='text/html; charset=utf-8')

@staff_member_required
def capture_interface_view(request, endpoint_id):
    """
    Capture interface - shows the proxied page with capture overlay
    """
    if not request.user.is_staff:
        return redirect('admin:index')

    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error Loading Endpoint</h1>
            <p>Could not find endpoint with ID: {endpoint_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=404)

    endpoint_name = endpoint.menu_title or endpoint.trigger_path or "Endpoint"
    capture_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PolySniffer Capture - {endpoint_name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }}
            .header {{ background: #2a2a2a; padding: 20px; border-bottom: 1px solid #444; display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ margin: 0; font-size: 24px; color: #0f0; }}
            .header .controls {{ display: flex; gap: 10px; }}
            .btn {{ background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; }}
            .btn:hover {{ background: #0056b3; }}
            .btn.danger {{ background: #dc3545; }}
            .btn.danger:hover {{ background: #c82333; }}
            .iframe-container {{ width: 100%; height: calc(100vh - 80px); border: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 PolySniffer Capture</h1>
            <div class="controls">
                <button class="btn" onclick="saveCaptures()">💾 Save Captures</button>
                <button class="btn danger" onclick="clearCaptures()">🗑️ Clear</button>
                <button class="btn" onclick="window.close()">✖️ Close</button>
            </div>
        </div>
        <iframe id="proxy-iframe" class="iframe-container" src="/admin/polysniffer/proxy/{endpoint_id}/"></iframe>
        <script>
            let captures = [];

            // Listen for messages from the iframe
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'polysniffer-capture') {{
                    captures.push(event.data.payload);
                    console.log('Captured:', event.data.payload);
                }}
            }});

            function saveCaptures() {{
                if (captures.length === 0) {{
                    alert('No captures to save');
                    return;
                }}
                fetch('/admin/polysniffer/save-capture/{endpoint_id}/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }},
                    body: JSON.stringify({{ captures: captures }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert(`Saved ${{captures.length}} captures`);
                        captures = [];
                    }} else {{
                        alert('Error saving captures: ' + data.error);
                    }}
                }})
                .catch(error => {{
                    alert('Error saving captures: ' + error);
                }});
            }}

            function clearCaptures() {{
                captures = [];
                alert('Captures cleared');
            }}

            function getCookie(name) {{
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {{
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {{
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }}
                    }}
                }}
                return cookieValue;
            }}
        </script>
    </body>
    </html>
    """
    return HttpResponse(capture_html)

@staff_member_required
def split_window_view(request, endpoint_id):
    """
    Split window view - capture interface on left, proxied page on right
    """
    if not request.user.is_staff:
        return redirect('admin:index')

    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error Loading Endpoint</h1>
            <p>Could not find endpoint with ID: {endpoint_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=404)

    endpoint_name = endpoint.menu_title or endpoint.trigger_path or "Endpoint"
    split_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PolySniffer Split View - {endpoint_name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a1a; color: #f0f0f0; margin: 0; padding: 0; }}
            .header {{ background: #2a2a2a; padding: 20px; border-bottom: 1px solid #444; }}
            .header h1 {{ margin: 0; font-size: 24px; color: #0f0; }}
            .header p {{ margin: 5px 0 0 0; color: #ccc; }}
            .container {{ display: flex; height: calc(100vh - 80px); }}
            .capture-panel {{ width: 400px; background: #2a2a2a; border-right: 1px solid #444; padding: 20px; overflow-y: auto; }}
            .proxy-panel {{ flex: 1; }}
            .capture-item {{ background: #333; border: 1px solid #555; border-radius: 8px; padding: 15px; margin-bottom: 10px; }}
            .capture-item:hover {{ background: #3a3a3a; }}
            .capture-method {{ font-weight: bold; color: #0f0; }}
            .capture-url {{ color: #ccc; font-size: 14px; margin: 5px 0; word-break: break-all; }}
            .capture-status {{ color: #ffa500; }}
            .capture-time {{ color: #888; font-size: 12px; }}
            .capture-data {{ margin-top: 10px; }}
            .capture-data pre {{ background: #1a1a1a; padding: 10px; border-radius: 4px; font-size: 12px; overflow-x: auto; max-height: 200px; overflow-y: auto; }}
            .clear-btn {{ background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 10px; }}
            .clear-btn:hover {{ background: #c82333; }}
            .iframe-container {{ width: 100%; height: 100%; border: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 PolySniffer Split View</h1>
            <p>Endpoint: {endpoint_name} | URL: {endpoint.endpoint_url}</p>
        </div>
        <div class="container">
            <div class="capture-panel">
                <h3>Captured Requests</h3>
                <div id="captures-list"></div>
                <button class="clear-btn" onclick="clearCaptures()">Clear All</button>
            </div>
            <div class="proxy-panel">
                <iframe id="proxy-iframe" class="iframe-container" src="/admin/polysniffer/proxy/{endpoint_id}/"></iframe>
            </div>
        </div>
        <script>
            let captures = [];
            const capturesList = document.getElementById('captures-list');

            // Listen for messages from the iframe
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'polysniffer-capture') {{
                    addCapture(event.data.payload);
                }}
            }});

            function addCapture(data) {{
                captures.unshift(data);
                if (captures.length > 100) captures.pop(); // Keep only last 100
                updateCapturesList();
            }}

            function updateCapturesList() {{
                capturesList.innerHTML = captures.map((capture, index) => `
                    <div class="capture-item">
                        <div class="capture-method">${{capture.method || 'GET'}}</div>
                        <div class="capture-url">${{capture.url || 'N/A'}}</div>
                        <div class="capture-status">Status: ${{capture.status || 'N/A'}}</div>
                        <div class="capture-time">${{new Date(capture.timestamp || Date.now()).toLocaleTimeString()}}</div>
                        ${{(capture.data && Object.keys(capture.data).length > 0) ? `
                            <div class="capture-data">
                                <strong>Data:</strong>
                                <pre>${{JSON.stringify(capture.data, null, 2)}}</pre>
                            </div>
                        ` : ''}}
                    </div>
                `).join('');
            }}

            function clearCaptures() {{
                captures = [];
                updateCapturesList();
            }}

            // Auto-scroll to top when new captures arrive
            const observer = new MutationObserver(() => {{
                capturesList.scrollTop = 0;
            }});
            observer.observe(capturesList, {{ childList: true }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(split_html)

@staff_member_required
def polysniffer_in_content(request, endpoint_id):
    """
    PolySniffer embedded in content - for iframe integration
    """
    if not request.user.is_staff:
        return redirect('admin:index')
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=404)
    # Just proxy the endpoint directly for in-content view
    return redirect(f'/admin/polysniffer/proxy/{endpoint_id}/')