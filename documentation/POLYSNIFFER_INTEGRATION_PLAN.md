# PolySniffer Integration Plan

## Overview
Integrate PolySniffer as a first-class debugging feature in the Dose admin interface. This allows admins to debug passthrough endpoint issues by comparing real browser traffic with proxy traffic.

## Feature Name
**"Debug Live Traffic"** or **"Sniff This Endpoint"**

## Implementation Steps

### 1. Database Schema
**File:** `dose/models/pass_through_endpoint.py`

Add field to `PassThroughEndpoint` model:
```python
debug_har = models.TextField(
    null=True,
    blank=True,
    help_text="Last captured HAR file for debugging this endpoint"
)
debug_har_captured_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="Timestamp when HAR was last captured"
)
```

**Migration:**
```bash
python manage.py makemigrations dose
python manage.py migrate
```

### 2. Admin Interface Button
**File:** `dose/admin.py`

Add to `PassThroughEndpointAdmin`:
```python
class PassThroughEndpointAdmin(admin.ModelAdmin):
    list_display = ('get_menu_title', 'provider', 'endpoint_url', 'show_in_menu', 'is_enabled', 'debug_button', 'created_at')

    def debug_button(self, obj):
        """Render Sniff button for debugging"""
        from django.utils.html import format_html
        from django.urls import reverse
        url = reverse('dose:sniff_endpoint', args=[obj.id])
        return format_html(
            '<a href="{}" class="button" target="_blank">🔍 Sniff</a>',
            url
        )
    debug_button.short_description = 'Debug'
    debug_button.allow_tags = True
```

### 3. Backend Routes
**File:** `dose/views/debug_views.py` (new file)

```python
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, staff_member_required
from django.views.decorators.http import require_http_methods
import json
import subprocess
import tempfile
import os
from dose.models import PassThroughEndpoint
from dose.utils import get_current_tenant

@staff_member_required
def sniff_endpoint(request, endpoint_id):
    """Main debug interface - opens PolySniffer with pre-configured endpoint"""
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)
    tenant = get_current_tenant(request)

    context = {
        'endpoint': endpoint,
        'tenant': tenant,
        'sniffer_url': f'/dose/sniff/start/{endpoint_id}/',
    }
    return render(request, 'admin/debug_traffic.html', context)

@staff_member_required
@require_http_methods(["POST"])
def start_sniff(request, endpoint_id):
    """Start PolySniffer instance with pre-configured settings"""
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)
    tenant = get_current_tenant(request)

    # Extract domain from endpoint URL
    from urllib.parse import urlparse
    parsed = urlparse(endpoint.endpoint_url)
    domain = parsed.netloc

    # Get tenant cookies for this domain
    cookies = {}
    for cookie_name, cookie_value in request.COOKIES.items():
        if cookie_name.startswith('external_') or cookie_name in ['OSTSESSID', 'csrf_token']:
            cookies[cookie_name] = cookie_value

    # Start PolySniffer instance (using Playwright or subprocess)
    # This would spin up a PolySniffer container/process
    # For now, return a URL to an external PolySniffer instance with params

    sniffer_config = {
        'start_url': endpoint.endpoint_url,
        'domain_filter': domain,
        'cookies': cookies,
        'tenant_id': tenant.id if tenant else None,
    }

    # In production, this would:
    # 1. Start a PolySniffer Docker container
    # 2. Pre-load cookies and config
    # 3. Return the container URL

    return JsonResponse({
        'sniffer_url': f'http://localhost:3000?config={json.dumps(sniffer_config)}',
        'config': sniffer_config
    })

@staff_member_required
@require_http_methods(["POST"])
def capture_har(request, endpoint_id):
    """Receive HAR file from PolySniffer and store it"""
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)

    har_data = request.POST.get('har') or request.body.decode('utf-8')

    # Store HAR in database
    endpoint.debug_har = har_data
    from django.utils import timezone
    endpoint.debug_har_captured_at = timezone.now()
    endpoint.save()

    # Run diff analysis
    diff_result = analyze_traffic_diff(endpoint, har_data)

    return JsonResponse({
        'status': 'success',
        'har_captured': True,
        'diff': diff_result
    })

def analyze_traffic_diff(endpoint, har_data):
    """Compare HAR traffic with proxy logs to find discrepancies"""
    # Parse HAR file
    har_json = json.loads(har_data)

    # Get proxy logs for this endpoint (from RequestLog model)
    from dose.models import RequestLog
    proxy_logs = RequestLog.objects.filter(
        path__contains=endpoint.trigger_path
    ).order_by('-created_at')[:100]

    # Compare:
    # - Headers (missing in proxy)
    # - Cookies (missing in proxy)
    # - Request methods
    # - Request bodies
    # - Response status codes
    # - WebSocket connections
    # - GraphQL queries

    differences = []

    # Example comparison logic
    for entry in har_json.get('log', {}).get('entries', []):
        request = entry.get('request', {})
        response = entry.get('response', {})

        # Check headers
        har_headers = {h['name'].lower(): h['value'] for h in request.get('headers', [])}

        # Find matching proxy request
        matching_proxy = None
        for log in proxy_logs:
            if log.path == request.get('url', ''):
                matching_proxy = log
                break

        if matching_proxy:
            # Compare headers
            proxy_headers = json.loads(matching_proxy.headers) if matching_proxy.headers else {}
            missing_headers = set(har_headers.keys()) - set(proxy_headers.keys())
            if missing_headers:
                differences.append({
                    'type': 'missing_header',
                    'url': request.get('url'),
                    'headers': list(missing_headers)
                })

    return {
        'differences': differences,
        'total_requests': len(har_json.get('log', {}).get('entries', [])),
        'matched_requests': len([d for d in differences if d.get('matched')])
    }

@staff_member_required
def view_diff(request, endpoint_id):
    """Display side-by-side comparison view"""
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)

    if not endpoint.debug_har:
        return HttpResponse("No HAR file captured yet. Please capture one first.")

    # Parse HAR and generate diff
    har_data = json.loads(endpoint.debug_har)
    diff_result = analyze_traffic_diff(endpoint, endpoint.debug_har)

    context = {
        'endpoint': endpoint,
        'har_data': har_data,
        'diff': diff_result,
    }
    return render(request, 'admin/traffic_diff.html', context)

@staff_member_required
@require_http_methods(["POST"])
def apply_fix(request, endpoint_id):
    """Apply suggested fixes to endpoint configuration"""
    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)

    fixes = json.loads(request.body)

    # Apply fixes:
    # - Add missing headers to endpoint config
    # - Update cookie handling
    # - Add ignore paths
    # - Update request/response handling

    applied = []
    for fix in fixes:
        if fix['type'] == 'missing_header':
            # Store in discovered_subpaths or new field
            if 'required_headers' not in endpoint.discovered_subpaths:
                endpoint.discovered_subpaths['required_headers'] = []
            endpoint.discovered_subpaths['required_headers'].extend(fix['headers'])
            applied.append(f"Added headers: {', '.join(fix['headers'])}")

    endpoint.save()

    return JsonResponse({
        'status': 'success',
        'applied': applied
    })
```

### 4. URL Routes
**File:** `dose/urls.py`

```python
urlpatterns += [
    path('sniff/<int:endpoint_id>/', debug_views.sniff_endpoint, name='sniff_endpoint'),
    path('sniff/start/<int:endpoint_id>/', debug_views.start_sniff, name='start_sniff'),
    path('sniff/capture/<int:endpoint_id>/', debug_views.capture_har, name='capture_har'),
    path('sniff/diff/<int:endpoint_id>/', debug_views.view_diff, name='view_diff'),
    path('sniff/apply/<int:endpoint_id>/', debug_views.apply_fix, name='apply_fix'),
]
```

### 5. Frontend Templates
**File:** `dose/templates/admin/debug_traffic.html` (new file)

```html
{% extends "admin/base_site.html" %}
{% load static %}

{% block content %}
<div class="debug-traffic-container">
    <h1>🔍 Debug Live Traffic: {{ endpoint.get_menu_title }}</h1>

    <div class="instructions">
        <ol>
            <li>Click around in the service below for 30-60 seconds</li>
            <li>Perform the action that "doesn't work"</li>
            <li>Click "Export HAR + Diff" button</li>
            <li>Review differences and click "Apply Fix"</li>
        </ol>
    </div>

    <div class="sniffer-iframe">
        <iframe src="{{ sniffer_url }}" width="100%" height="600px"></iframe>
    </div>

    <div class="actions">
        <button id="capture-har" class="button">Export HAR + Diff</button>
        <a href="{% url 'dose:view_diff' endpoint.id %}" class="button">View Last Diff</a>
    </div>
</div>

<script>
document.getElementById('capture-har').addEventListener('click', function() {
    // Trigger HAR export from PolySniffer iframe
    // Then POST to capture_har endpoint
    fetch('{% url "dose:capture_har" endpoint.id %}', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({har: '...'}) // Get from iframe
    }).then(response => response.json())
      .then(data => {
          if (data.diff) {
              window.location.href = '{% url "dose:view_diff" endpoint.id %}';
          }
      });
});
</script>
{% endblock %}
```

**File:** `dose/templates/admin/traffic_diff.html` (new file)

```html
{% extends "admin/base_site.html" %}

{% block content %}
<h1>Traffic Diff: {{ endpoint.get_menu_title }}</h1>

<div class="diff-view">
    <div class="side-by-side">
        <div class="har-side">
            <h2>Real Browser (HAR)</h2>
            <!-- Display HAR entries -->
        </div>
        <div class="proxy-side">
            <h2>Proxy Logs</h2>
            <!-- Display proxy log entries -->
        </div>
    </div>

    <div class="differences">
        <h2>Differences Found</h2>
        <ul>
            {% for diff in diff.differences %}
            <li>
                <strong>{{ diff.type }}</strong>: {{ diff.description }}
                <button class="apply-fix" data-fix='{{ diff|safe }}'>Apply Fix</button>
            </li>
            {% endfor %}
        </ul>
    </div>

    <div class="actions">
        <button id="apply-all" class="button">Apply All Fixes</button>
    </div>
</div>
{% endblock %}
```

## Integration with PolySniffer

### Option 1: External PolySniffer Instance
- Deploy PolySniffer separately (Railway, Docker)
- Pass configuration via URL parameters
- Embed in iframe

### Option 2: Embedded PolySniffer
- Install PolySniffer as Django app
- Run in subprocess/thread
- Direct integration with Django views

## Benefits

1. **Self-Debugging**: PolySaaS can debug its own integrations
2. **Time Savings**: 5 minutes vs days of guessing
3. **Competitive Moat**: No other SaaS has this
4. **Premium Feature**: Charge $500/mo for enterprise debugging
5. **Investor Appeal**: Clear differentiation

## Next Steps

1. ✅ Create implementation plan (this document)
2. ⏳ Fix OSTicket login issue (blocking demo video)
3. ⏳ Add `debug_har` field to model
4. ⏳ Create backend routes
5. ⏳ Add admin button
6. ⏳ Create frontend templates
7. ⏳ Integrate with PolySniffer instance
8. ⏳ Test with OSTicket endpoint

## Estimated Time
- Database migration: 15 min
- Backend routes: 2 hours
- Admin button: 30 min
- Frontend templates: 1 hour
- PolySniffer integration: 1 hour
- Testing: 1 hour
**Total: ~6 hours**

