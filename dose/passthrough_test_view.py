"""
Comprehensive passthrough test and debugging page
Access at: http://localhost:8000/dose/test-passthrough/
"""
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from dose.models import PassThroughEndpoint
import requests

@login_required
def passthrough_test_view(request):
    """Test page showing passthrough configuration and testing"""

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Passthrough Testing & Debugging</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .section {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 0;
            }
            .endpoint {
                background: #ecf0f1;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #3498db;
                border-radius: 4px;
            }
            .test-btn {
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                margin: 5px;
            }
            .test-btn:hover {
                background: #2980b9;
            }
            #test-results {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            }
            .status-ok { color: #2ecc71; font-weight: bold; }
            .status-error { color: #e74c3c; font-weight: bold; }
            .status-redirect { color: #f39c12; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🔍 Passthrough Testing & Debugging Dashboard</h1>

        <div class="section">
            <h2>📋 Configured Endpoints</h2>
    """

    # Get all endpoints
    endpoints = PassThroughEndpoint.objects.all()
    for endpoint in endpoints:
        status = "✅ Enabled" if endpoint.is_enabled else "❌ Disabled"
        html += f"""
            <div class="endpoint">
                <strong>{endpoint.trigger_path}</strong> {status}<br>
                Target: {endpoint.endpoint_url}<br>
                <button class="test-btn" onclick="testEndpoint('{endpoint.trigger_path}', '{endpoint.endpoint_url}')">
                    Test This Endpoint
                </button>
                <button class="test-btn" onclick="openInNewTab('{endpoint.trigger_path}')">
                    Open in New Tab
                </button>
            </div>
        """

    html += """
        </div>

        <div class="section">
            <h2>🧪 Quick Tests</h2>
            <button class="test-btn" onclick="testAllEndpoints()">Test All Endpoints</button>
            <button class="test-btn" onclick="clearResults()">Clear Results</button>
            <button class="test-btn" onclick="testLandingPageAjax()">Test Landing Page AJAX</button>
        </div>

        <div class="section">
            <h2>📊 Test Results</h2>
            <div id="test-results">Click a test button to see results...</div>
        </div>

        <script>
            function log(message) {
                const results = document.getElementById('test-results');
                results.textContent += message + '\\n';
                results.scrollTop = results.scrollHeight;
            }

            function clearResults() {
                document.getElementById('test-results').textContent = '';
            }

            async function testEndpoint(triggerPath, targetUrl) {
                log('\\n' + '='.repeat(60));
                log(`Testing: ${triggerPath}`);
                log(`Target: ${targetUrl}`);
                log('='.repeat(60));

                try {
                    const response = await fetch(triggerPath, {
                        method: 'GET',
                        credentials: 'include',
                        redirect: 'manual'
                    });

                    const statusClass = response.status === 200 ? 'status-ok' :
                                      (response.status >= 300 && response.status < 400) ? 'status-redirect' :
                                      'status-error';

                    log(`Status: ${response.status} ${response.statusText}`);
                    log(`Type: ${response.type}`);

                    if (response.status >= 300 && response.status < 400) {
                        const location = response.headers.get('Location');
                        log(`Redirect to: ${location || 'N/A'}`);
                    }

                    const contentType = response.headers.get('content-type');
                    log(`Content-Type: ${contentType}`);

                    if (response.status === 200) {
                        const text = await response.text();
                        log(`Content Length: ${text.length} bytes`);
                        log(`First 200 chars: ${text.substring(0, 200)}...`);
                    }

                    log('✅ Test completed');

                } catch (error) {
                    log(`❌ Error: ${error.message}`);
                }
            }

            async function testAllEndpoints() {
                clearResults();
                log('Starting comprehensive endpoint tests...\\n');
    """

    for endpoint in endpoints:
        if endpoint.is_enabled:
            html += f"""
                await testEndpoint('{endpoint.trigger_path}', '{endpoint.endpoint_url}');
                await new Promise(resolve => setTimeout(resolve, 1000));
            """

    html += """
                log('\\n\\n✅ All tests completed!');
            }

            function openInNewTab(path) {
                window.open(path, '_blank');
            }

            async function testLandingPageAjax() {
                log('\\n' + '='.repeat(60));
                log('Testing Landing Page AJAX Implementation');
                log('='.repeat(60));

                // Simulate what the landing page does
                const testPath = '/admin/osticket/';
                log(`Fetching: ${testPath}`);

                try {
                    const response = await fetch(testPath, {
                        credentials: 'include'
                    });

                    log(`Status: ${response.status}`);
                    const html = await response.text();
                    log(`Received ${html.length} bytes`);

                    // Parse HTML like landing page does
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    log(`Parsed document title: ${doc.title}`);
                    log(`Found ${doc.forms.length} forms`);
                    log(`Found ${doc.querySelectorAll('a').length} links`);

                    // Check for OsTicket login form
                    const loginForm = doc.querySelector('form[method="post"]');
                    if (loginForm) {
                        log('✅ Found login form');
                        log(`Form action: ${loginForm.action}`);
                    }

                    log('✅ Landing page AJAX test completed');

                } catch (error) {
                    log(`❌ Error: ${error.message}`);
                }
            }
        </script>
    </body>
    </html>
    """

    return HttpResponse(html)
