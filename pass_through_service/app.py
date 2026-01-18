#!/usr/bin/env python3
"""
Pass-Through Service for External URL Passthrough Middleware
=============================================================

This is a Flask-based pass-through service that can be used to test the Django
External URL Passthrough Middleware functionality. It accepts all HTTP methods
and returns detailed information about the request with an "I heard you!" message.

This service acts as a pass-through endpoint for testing new functionality
before implementing it formally in Django.

Usage:
    python app.py

The service will run on http://localhost:5000 by default.
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
from pathlib import Path

app = Flask(__name__)

# Configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000
DEBUG = False

# Events storage file
EVENTS_FILE = Path(__file__).parent / 'events.json'
MAX_EVENTS = 100  # Keep last 100 events

def format_headers(headers):
    """Convert headers to a clean dictionary format"""
    return {key: value for key, value in headers.items()}

def get_request_info():
    """Extract comprehensive request information"""
    return {
        'timestamp': datetime.now().isoformat(),
        'method': request.method,
        'url': request.url,
        'path': request.path,
        'query_string': request.query_string.decode('utf-8'),
        'headers': format_headers(request.headers),
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'content_type': request.content_type,
        'content_length': request.content_length,
        'args': dict(request.args),
        'form': dict(request.form),
        'json': request.get_json(silent=True),
        'data': request.get_data(as_text=True) if request.get_data() else None,
    }

def load_events():
    """Load events from file"""
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading events: {e}")
            return []
    return []

def save_event(event_data):
    """Save a new event to file"""
    events = load_events()

    # Add the new event at the beginning
    events.insert(0, event_data)

    # Keep only the last MAX_EVENTS
    events = events[:MAX_EVENTS]

    try:
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving event: {e}")

@app.route('/', methods=['GET'])
def monitor_dashboard():
    """
    Monitor Logger Dashboard - Display intercepted events
    """
    events = load_events()

    # Build HTML dashboard
    events_html = ""
    if events:
        for i, event in enumerate(events):
            event_time = event.get('timestamp', 'Unknown')
            service_name = event.get('service_name', 'Unknown')
            user = event.get('user_context', {}).get('username', 'Unknown')
            tenant = event.get('tenant_context', {}).get('name', 'Unknown')
            ticket_data = event.get('ticket_data', {})

            # Extract ticket subject if available
            subject = ticket_data.get('subject', ticket_data.get('name', 'N/A'))
            if isinstance(subject, list):
                subject = subject[0] if subject else 'N/A'

            events_html += f"""
            <div class="event-card">
                <div class="event-header">
                    <span class="event-number">#{len(events) - i}</span>
                    <span class="event-time">{event_time}</span>
                </div>
                <div class="event-body">
                    <div class="event-row">
                        <span class="label">Service:</span>
                        <span class="value">{service_name}</span>
                    </div>
                    <div class="event-row">
                        <span class="label">User:</span>
                        <span class="value">{user}</span>
                    </div>
                    <div class="event-row">
                        <span class="label">Tenant:</span>
                        <span class="value">{tenant}</span>
                    </div>
                    <div class="event-row">
                        <span class="label">Subject:</span>
                        <span class="value">{subject}</span>
                    </div>
                </div>
                <details class="event-details">
                    <summary>View Full Event Data</summary>
                    <pre>{json.dumps(event, indent=2)}</pre>
                </details>
            </div>
            """
    else:
        events_html = """
        <div class="no-events">
            <p>No events logged yet.</p>
            <p>Create a ticket in OSTicket to see events appear here in real-time!</p>
        </div>
        """

    html_response = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitor Logger - Real-Time Event Monitoring</title>
        <meta http-equiv="refresh" content="5">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
            .header p {{ opacity: 0.9; font-size: 16px; }}
            .stats {{
                display: flex;
                justify-content: space-around;
                padding: 20px;
                background: #f8f9fa;
                border-bottom: 2px solid #e9ecef;
            }}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 36px; font-weight: bold; color: #667eea; }}
            .stat-label {{ color: #6c757d; font-size: 14px; margin-top: 5px; }}
            .events-container {{
                padding: 30px;
                max-height: 70vh;
                overflow-y: auto;
            }}
            .event-card {{
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }}
            .event-card:hover {{
                transform: translateX(5px);
                box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            }}
            .event-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #dee2e6;
            }}
            .event-number {{
                background: #667eea;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            .event-time {{
                color: #6c757d;
                font-size: 14px;
            }}
            .event-body {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
            }}
            .event-row {{
                display: flex;
                flex-direction: column;
            }}
            .label {{
                font-weight: 600;
                color: #495057;
                font-size: 12px;
                text-transform: uppercase;
                margin-bottom: 3px;
            }}
            .value {{
                color: #212529;
                font-size: 16px;
            }}
            .event-details {{
                margin-top: 15px;
            }}
            .event-details summary {{
                cursor: pointer;
                color: #667eea;
                font-weight: 600;
                padding: 10px;
                background: #e7f1ff;
                border-radius: 5px;
            }}
            .event-details pre {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                margin-top: 10px;
                font-size: 12px;
            }}
            .no-events {{
                text-align: center;
                padding: 60px 20px;
                color: #6c757d;
            }}
            .no-events p {{
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .refresh-notice {{
                text-align: center;
                padding: 15px;
                background: #e7f1ff;
                color: #667eea;
                font-size: 14px;
                border-top: 2px solid #e9ecef;
            }}
        </style>
    </head>

    <body style="margin:0; padding:0; background:#f8f9fa;">
        <div class="container">
            <div class="header">
                <h1>Monitor Logger</h1>
                <p>Real-Time Event Monitoring Dashboard</p>
            </div>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(events)}</div>
                    <div class="stat-label">Total Events</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len([e for e in events if e.get('service_name') == 'TicketInterceptorService'])}</div>
                    <div class="stat-label">Ticket Events</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(events) - len([e for e in events if e.get('service_name') == 'TicketInterceptorService'])}</div>
                    <div class="stat-label">Other Events</div>
                </div>
            </div>
            <div class="events-container">
                {events_html}
            </div>
            <div class="refresh-notice">
                Auto-refreshing every 5 seconds | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    return html_response

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def catch_all(path):
    """
    Catch-all route for other paths - returns JSON for API requests
    """
    request_info = get_request_info()
    response_data = {
        'message': 'Monitor Logger Service',
        'status': 'success',
        'request_info': request_info
    }
    return jsonify(response_data), 200

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Django External URL Passthrough Test Service',
        'timestamp': datetime.now().isoformat(),
        'message': 'Service is running and ready to hear you! 🎯'
    }), 200

@app.route('/echo', methods=['POST'])
def echo():
    """Special echo endpoint for testing POST requests"""
    request_info = get_request_info()

    return jsonify({
        'message': '🔊 I heard you loud and clear!',
        'echo': 'Your data has been received',
        'request_info': request_info
    }), 200

@app.route('/tickets', methods=['POST'])
def receive_ticket():
    """
    Monitor Logger - Receive ticket data from DoseRequestController/AtomicService
    Real-time monitoring endpoint that logs intercepted events and saves to file
    """
    try:
        # Get JSON data from request
        ticket_data = request.get_json() if request.is_json else {}

        # Create event record with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        event_record = {
            'timestamp': timestamp,
            'service_name': ticket_data.get('service_name', 'Unknown'),
            'execution_timestamp': ticket_data.get('execution_timestamp', 'Unknown'),
            'user_context': ticket_data.get('user_context', {}),
            'tenant_context': ticket_data.get('tenant_context', {}),
            'ticket_data': ticket_data.get('ticket_data', {}),
            'request_metadata': ticket_data.get('request_metadata', {}),
        }

        # Save to file
        save_event(event_record)

        # Log to console
        print("\n" + "="*60)
        print(f"[{timestamp}] EVENT INTERCEPTED - Monitor Logger Service")
        print("="*60)
        print(f"Service: {event_record['service_name']}")
        print(f"User: {event_record['user_context'].get('username', 'Unknown')}")
        print(f"Tenant: {event_record['tenant_context'].get('name', 'Unknown')}")
        ticket_info = event_record.get('ticket_data', {})
        if ticket_info:
            subject = ticket_info.get('subject', ticket_info.get('name', 'N/A'))
            print(f"Subject: {subject}")
        print(f"Event saved to {EVENTS_FILE}")
        print("="*60 + "\n")

        # Return success response
        return jsonify({
            'message': 'Event logged successfully',
            'status': 'success',
            'service': 'Monitor Logger Service',
            'timestamp': timestamp,
            'events_count': len(load_events())
        }), 200

    except Exception as e:
        print(f"Error processing event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'message': 'Error processing event',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler - shouldn't be reached due to catch-all route"""
    return jsonify({
        'message': '🎯 I heard you, but this path is special!',
        'error': 'Not Found',
        'note': 'This should not happen with the catch-all route'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({
        'message': '😱 I heard you, but something went wrong!',
        'error': 'Internal Server Error',
        'details': str(error)
    }), 500

if __name__ == '__main__':
    print("Starting Monitor Logger Service...")
    print(f"Server will run on http://{HOST}:{PORT}")
    print("Ready to receive events!")
    print("\n" + "="*60)
    print("MONITOR LOGGER ENDPOINTS:")
    print(f"  • Dashboard: http://localhost:{PORT}/")
    print(f"  • Health Check: http://localhost:{PORT}/health")
    print(f"  • Ticket Events: http://localhost:{PORT}/tickets (POST)")
    print("="*60 + "\n")
    print("Waiting for events...")
    print("="*60 + "\n")

    # Run the Flask app
    try:
        app.run(
            host=HOST,
            port=PORT,
            debug=DEBUG,
            threaded=True,  # Handle multiple requests concurrently
            use_reloader=False  # Disable reloader to prevent port conflicts
        )
    except Exception as e:
        print(f"ERROR starting Flask service: {e}")
        import traceback
        traceback.print_exc()
        raise
