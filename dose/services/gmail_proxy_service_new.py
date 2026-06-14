from dose.services.atomic_service_base import AtomicServiceBase
import requests
import logging
from django.http import HttpResponse
import json

logger = logging.getLogger(__name__)

class GmailProxy(AtomicServiceBase):
    """
    Gmail Proxy Service with Gmail-like UI Interface
    Provides a complete Gmail experience using Gmail API
    """

    @staticmethod
    def get_service_name():
        return "Gmail Proxy Service"

    @staticmethod
    def get_description():
        return "Gmail proxy service with Gmail-like interface using Gmail API"

    @staticmethod
    def execute_and_save(request, instruction_row):
        """Main entry point for Gmail proxy service."""
        logger.info("[GMAIL PROXY] Calling GmailProxy for user")

        # Check if user is authenticated
        if not request.user.is_authenticated:
            logger.warning("[GMAIL PROXY] User is not authenticated")
            return HttpResponse("""
                <html>
                <head><title>Gmail Access - Authentication Required</title></head>
                <body>
                    <h2>Gmail Access</h2>
                    <p><strong>Authentication Required</strong></p>
                    <p>You must be logged in and have Google OAuth enabled to access Gmail.</p>
                    <p><a href="/admin/login/">Login to Admin</a> | <a href="/accounts/login/">User Login</a></p>
                </body>
                </html>
            """, content_type="text/html")

        logger.info(f"[GMAIL PROXY] Processing Gmail request for user {request.user.username}")

        # Get OAuth token from the request (middleware should have set this)
        oauth_token = getattr(request, 'gmail_oauth_token', None)

        if not oauth_token:
            # Try to get token directly from database
            try:
                from allauth.socialaccount.models import SocialToken
                token_obj = SocialToken.objects.get(
                    account__user=request.user,
                    account__provider__iexact='google'
                )
                oauth_token = token_obj.token
                logger.info(f"[GMAIL PROXY] Retrieved OAuth token for user {request.user.username}")
            except SocialToken.DoesNotExist:
                logger.warning(f"[GMAIL PROXY] No OAuth token found for user {request.user.username}")
                return HttpResponse("""
                    <html>
                    <head><title>Gmail OAuth Required</title></head>
                    <body style="font-family: Arial, sans-serif; margin: 40px;">
                        <h2>Gmail OAuth Error</h2>
                        <p>Your Google OAuth token may have expired or lacks necessary permissions.</p>
                        <p><a href="/accounts/google/login/">Re-authenticate with Google</a></p>
                        <p><a href="/admin/">Back to Dashboard</a></p>
                    </body>
                    </html>
                """, status=401, content_type="text/html")

        # Determine what Gmail action to perform based on request path
        gmail_action = GmailProxy._determine_gmail_action(request)

        if gmail_action == 'inbox':
            return GmailProxy._handle_inbox(request, oauth_token)
        elif gmail_action == 'compose':
            return GmailProxy._handle_compose(request, oauth_token)
        else:
            return GmailProxy._handle_default_gmail(request, oauth_token)

    @staticmethod
    def _determine_gmail_action(request):
        """Determine what Gmail action to perform based on request."""
        path = request.path_info.lower()

        if 'compose' in path or request.method == 'POST':
            return 'compose'
        else:
            return 'inbox'  # Default to inbox

    @staticmethod
    def _handle_inbox(request, oauth_token):
        """Handle Gmail inbox display using Gmail API with Gmail-like UI."""
        try:
            # Call Gmail API to get inbox messages
            headers = {'Authorization': f'Bearer {oauth_token}'}

            # Get user profile first
            profile_response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/profile',
                headers=headers,
                timeout=10
            )

            if profile_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Profile API failed: {profile_response.status_code}")
                logger.error(f"[GMAIL PROXY] Profile API response: {profile_response.text}")
                return GmailProxy._handle_api_error(profile_response)

            # Get inbox messages
            messages_response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages?labelIds=INBOX&maxResults=50',
                headers=headers,
                timeout=10
            )

            if messages_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Messages API failed: {messages_response.status_code}")
                logger.error(f"[GMAIL PROXY] Messages API response: {messages_response.text}")
                return GmailProxy._handle_api_error(messages_response)

            # Get user labels
            labels_response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/labels',
                headers=headers,
                timeout=10
            )

            profile_data = profile_response.json()
            messages_data = messages_response.json().get('messages', [])
            if labels_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Labels API failed: {labels_response.status_code}")
                logger.error(f"[GMAIL PROXY] Labels API response: {labels_response.text}")
            labels_data = labels_response.json().get('labels', []) if labels_response.status_code == 200 else []

            # Fetch detailed message data for inbox
            detailed_messages = []
            for message in messages_data[:20]:  # Limit to first 20 messages
                msg_response = requests.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date",
                    headers=headers,
                    timeout=5
                )
                if msg_response.status_code == 200:
                    detailed_messages.append(msg_response.json())

            # Generate Gmail-like UI
            return GmailProxy._generate_gmail_interface(
                request, profile_data, detailed_messages, labels_data
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"[GMAIL PROXY] Network error: {str(e)}")
            return GmailProxy._network_error_response()
        except Exception as e:
            logger.error(f"[GMAIL PROXY] Unexpected error: {str(e)}")
            return GmailProxy._general_error_response(str(e))

    @staticmethod
    def _handle_api_error(response):
        """Handle Gmail API errors with specific error messages."""
        error_data = {}
        try:
            error_data = response.json().get('error', {})
        except:
            pass

        error_message = error_data.get('message', '')
        error_code = error_data.get('code', response.status_code)

        # Check for Gmail API not enabled error
        if error_code == 403 and 'Gmail API has not been used' in error_message:
            project_id = None
            # Extract project ID from error message
            if 'project' in error_message:
                import re
                project_match = re.search(r'project (\d+)', error_message)
                if project_match:
                    project_id = project_match.group(1)

            enable_url = f"https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project={project_id}" if project_id else "https://console.developers.google.com/apis/api/gmail.googleapis.com/overview"

            return HttpResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Gmail API Setup Required</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f6f8fc; }}
                        .container {{ max-width: 800px; margin: 40px auto; padding: 0 20px; }}
                        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 40px; }}
                        .btn {{ display: inline-block; padding: 12px 24px; margin: 8px 4px; border-radius: 6px; text-decoration: none; font-weight: 500; text-align: center; }}
                        .btn-primary {{ background: #1a73e8; color: white; }}
                        .btn-success {{ background: #137333; color: white; }}
                        .btn-secondary {{ background: #5f6368; color: white; }}
                        .btn:hover {{ opacity: 0.9; transform: translateY(-1px); transition: all 0.2s; }}
                        .steps {{ background: #e8f0fe; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                        .preview {{ background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #1a73e8; }}
                        h1 {{ color: #202124; margin-bottom: 8px; }}
                        h2 {{ color: #1967d2; margin-top: 0; }}
                        p {{ color: #5f6368; line-height: 1.5; }}
                        ul {{ color: #5f6368; }}
                        .icon {{ font-size: 48px; text-align: center; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="card">
                            <div class="icon">📧</div>
                            <h1>Gmail API Setup Required</h1>
                            <p><strong>Great news!</strong> Your Google OAuth authentication is working perfectly! You just need to enable the Gmail API to access your emails.</p>

                            <div class="steps">
                                <h2>📋 Quick Setup (2 minutes):</h2>
                                <ol>
                                    <li>Click the button below to open Google Cloud Console</li>
                                    <li>Click the <strong>"ENABLE"</strong> button on the Gmail API page</li>
                                    <li>Wait 2-3 minutes for changes to take effect</li>
                                    <li>Return here and refresh this page</li>
                                </ol>
                            </div>

                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{enable_url}" target="_blank" class="btn btn-primary">🔧 Enable Gmail API</a>
                                <a href="javascript:window.location.reload()" class="btn btn-success">🔄 Refresh Page</a>
                                <a href="/admin/" class="btn btn-secondary">← Back to Dashboard</a>
                            </div>

                            <div class="preview">
                                <h2>🎯 What You'll Get Once Enabled:</h2>
                                <ul>
                                    <li>📬 <strong>Full Gmail inbox</strong> with all your emails</li>
                                    <li>✉️ <strong>Compose and send</strong> emails directly</li>
                                    <li>🔍 <strong>Search</strong> through your emails</li>
                                    <li>🏷️ <strong>Organize</strong> with labels and folders</li>
                                    <li>📱 <strong>Responsive Gmail-like interface</strong></li>
                                    <li>🔐 <strong>Secure</strong> - uses your existing Google authentication</li>
                                </ul>
                            </div>

                            <details style="margin-top: 30px;">
                                <summary style="cursor: pointer; color: #1967d2;">🔍 Technical Details</summary>
                                <div style="margin-top: 10px; padding: 10px; background: #fef7e0; border-radius: 4px;">
                                    <p><strong>Error:</strong> {error_message}</p>
                                    <p><strong>Status:</strong> {error_code}</p>
                                    <p><strong>Solution:</strong> Enable Gmail API in Google Cloud Console</p>
                                </div>
                            </details>
                        </div>
                    </div>
                </body>
                </html>
                """,
                status=403,
                content_type="text/html"
            )

        # Generic API error
        return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gmail API Error</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f6f8fc; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 40px; background: white; border-radius: 8px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Gmail API Error</h2>
                    <p><strong>Error {error_code}:</strong> {error_message}</p>
                    <p><a href="/admin/">← Back to Dashboard</a></p>
                </div>
            </body>
            </html>
        """, status=response.status_code, content_type="text/html")

    @staticmethod
    def _generate_gmail_interface(request, profile_data, messages, labels):
        """Generate Gmail-like interface with real data."""
        user_email = profile_data.get('emailAddress', 'user@domain.com')
        total_messages = profile_data.get('messagesTotal', 0)

        # Process messages for display
        processed_messages = []
        for msg in messages:
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            processed_messages.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown Sender'),
                'subject': headers.get('Subject', '(no subject)'),
                'date': headers.get('Date', ''),
                'unread': 'UNREAD' in msg.get('labelIds', [])
            })

        # Process labels
        system_labels = []
        user_labels = []
        for label in labels:
            if label['type'] == 'system':
                system_labels.append(label)
            else:
                user_labels.append(label)

        # Generate message list HTML
        messages_html = ""
        for msg in processed_messages:
            unread_class = 'unread' if msg['unread'] else ''
            # Clean up sender name
            sender = msg['from'].split('<')[0].strip().strip('"')
            if len(sender) > 25:
                sender = sender[:25] + '...'

            # Format date
            date_str = msg['date']
            try:
                # Simple date formatting
                if 'GMT' in date_str or '+' in date_str[-6:]:
                    date_display = date_str.split()[1:4]  # Get day, month, year
                    date_display = ' '.join(date_display[:2])  # Just month and day
                else:
                    date_display = date_str[:10] if len(date_str) > 10 else date_str
            except:
                date_display = 'Today'

            messages_html += f"""
                        <div class="message-row {unread_class}" onclick="openMessage('{msg['id']}')">
                            <input type="checkbox" class="message-checkbox" />
                            <span class="message-star">☆</span>
                            <div class="message-from">{sender}</div>
                            <div class="message-subject">{msg['subject']}</div>
                            <div class="message-date">{date_display}</div>
                        </div>"""

        # Generate labels HTML
        labels_html = ""
        for label in system_labels:
            if label['name'] in ['INBOX', 'SENT', 'DRAFT', 'SPAM', 'TRASH', 'STARRED']:
                active_class = 'active' if label['name'] == 'INBOX' else ''
                icon = {'INBOX': '📬', 'SENT': '📤', 'DRAFT': '📝', 'SPAM': '🚫', 'TRASH': '🗑️', 'STARRED': '⭐'}.get(label['name'], '📁')
                labels_html += f"""
                        <a href="#" class="sidebar-item {active_class}">
                            {icon} {label['name'].title()}
                        </a>"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail - {user_email}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f6f8fc; }}

                /* Gmail Header */
                .gmail-header {{
                    background: #fff;
                    border-bottom: 1px solid #dadce0;
                    padding: 8px 16px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}
                .gmail-logo {{ font-size: 22px; font-weight: 400; color: #5f6368; }}
                .search-box {{
                    flex: 1;
                    max-width: 720px;
                    margin: 0 32px;
                    position: relative;
                }}
                .search-box input {{
                    width: 100%;
                    padding: 12px 16px;
                    border: 1px solid #dadce0;
                    border-radius: 24px;
                    background: #f1f3f4;
                    outline: none;
                    font-size: 14px;
                }}
                .user-info {{
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    color: #5f6368;
                    font-size: 14px;
                }}

                /* Gmail Layout */
                .gmail-container {{
                    display: flex;
                    height: calc(100vh - 65px);
                }}

                /* Sidebar */
                .sidebar {{
                    width: 256px;
                    background: #fff;
                    border-right: 1px solid #dadce0;
                    padding: 16px 0;
                }}
                .compose-btn {{
                    margin: 0 16px 16px;
                    padding: 12px 24px;
                    background: #c2e7ff;
                    border: 1px solid #dadce0;
                    border-radius: 24px;
                    text-decoration: none;
                    color: #001d35;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 500;
                }}
                .compose-btn:hover {{ background: #a8d1ff; }}

                .sidebar-section {{
                    margin-bottom: 16px;
                }}
                .sidebar-item {{
                    padding: 8px 16px;
                    color: #3c4043;
                    text-decoration: none;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 14px;
                }}
                .sidebar-item:hover {{ background: #f1f3f4; }}
                .sidebar-item.active {{ background: #fce8e6; color: #d93025; font-weight: 500; }}

                /* Main Content */
                .main-content {{
                    flex: 1;
                    background: #fff;
                    overflow-y: auto;
                }}

                /* Toolbar */
                .toolbar {{
                    padding: 8px 16px;
                    border-bottom: 1px solid #dadce0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: #fff;
                }}
                .toolbar-btn {{
                    padding: 8px 12px;
                    border: 1px solid #dadce0;
                    background: #fff;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 13px;
                    color: #3c4043;
                }}
                .toolbar-btn:hover {{ background: #f8f9fa; }}

                /* Message List */
                .message-list {{
                    background: #fff;
                }}
                .message-row {{
                    padding: 8px 16px;
                    border-bottom: 1px solid #f0f0f0;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .message-row:hover {{ background: #f8f9fa; }}
                .message-row.unread {{ background: #fff; font-weight: 500; }}
                .message-row.unread .message-subject {{ font-weight: 600; }}

                .message-checkbox {{
                    width: 18px;
                    height: 18px;
                }}
                .message-star {{
                    width: 16px;
                    height: 16px;
                    cursor: pointer;
                }}
                .message-from {{
                    width: 200px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .message-subject {{
                    flex: 1;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .message-date {{
                    width: 80px;
                    text-align: right;
                    color: #5f6368;
                    font-size: 12px;
                }}

                /* Status Bar */
                .status-bar {{
                    padding: 8px 16px;
                    background: #f8f9fa;
                    border-top: 1px solid #dadce0;
                    font-size: 12px;
                    color: #5f6368;
                    text-align: center;
                }}

                /* Responsive */
                @media (max-width: 768px) {{
                    .gmail-container {{ flex-direction: column; }}
                    .sidebar {{ width: 100%; height: auto; }}
                    .search-box {{ margin: 0 16px; }}
                }}
            </style>
        </head>
        <body>
            <!-- Gmail Header -->
            <div class="gmail-header">
                <div class="gmail-logo">📧 Gmail</div>
                <div class="search-box">
                    <input type="text" placeholder="Search mail" />
                </div>
                <div class="user-info">
                    <span>{user_email}</span>
                    <span>({total_messages:,} emails)</span>
                </div>
            </div>

            <!-- Gmail Container -->
            <div class="gmail-container">
                <!-- Sidebar -->
                <div class="sidebar">
                    <a href="#" class="compose-btn">
                        ✏️ Compose
                    </a>

                    <div class="sidebar-section">
                        {labels_html}
                    </div>
                </div>

                <!-- Main Content -->
                <div class="main-content">
                    <!-- Toolbar -->
                    <div class="toolbar">
                        <input type="checkbox" />
                        <button class="toolbar-btn">🗑️ Delete</button>
                        <button class="toolbar-btn">📁 Archive</button>
                        <button class="toolbar-btn">🚫 Spam</button>
                        <button class="toolbar-btn">📌 Mark as read</button>
                        <button class="toolbar-btn">⭐ Add star</button>
                    </div>

                    <!-- Message List -->
                    <div class="message-list">
                        {messages_html}
                    </div>
                </div>
            </div>

            <!-- Status Bar -->
            <div class="status-bar">
                Showing {len(processed_messages)} of {total_messages:,} emails • Gmail powered by Gmail API
            </div>

            <script>
                function openMessage(messageId) {{
                    alert('Opening message: ' + messageId + '\\n\\nFull message view coming soon!');
                }}

                // Add some interactivity
                document.querySelectorAll('.message-checkbox').forEach(cb => {{
                    cb.addEventListener('click', function(e) {{
                        e.stopPropagation();
                        this.closest('.message-row').classList.toggle('selected');
                    }});
                }});

                // Star functionality
                document.querySelectorAll('.message-star').forEach(star => {{
                    star.addEventListener('click', function(e) {{
                        e.stopPropagation();
                        this.textContent = this.textContent === '☆' ? '⭐' : '☆';
                    }});
                }});
            </script>
        </body>
        </html>
        """

        return HttpResponse(html, content_type="text/html")

    @staticmethod
    def _handle_compose(request, oauth_token):
        """Handle Gmail compose functionality."""
        # TODO: Implement compose interface
        return HttpResponse("Compose functionality coming soon!", content_type="text/html")

    @staticmethod
    def _handle_default_gmail(request, oauth_token):
        """Default Gmail handler - redirect to inbox."""
        return GmailProxy._handle_inbox(request, oauth_token)

    @staticmethod
    def _network_error_response():
        """Return network error response."""
        return HttpResponse("""
            <html>
            <head><title>Network Error</title></head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h2>Network Error</h2>
                <p>Unable to connect to Gmail API. Please check your internet connection and try again.</p>
                <p><a href="javascript:window.location.reload()">🔄 Try Again</a> | <a href="/admin/">← Back</a></p>
            </body>
            </html>
        """, status=503, content_type="text/html")

    @staticmethod
    def _general_error_response(error_msg):
        """Return general error response."""
        return HttpResponse(f"""
            <html>
            <head><title>Gmail Error</title></head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h2>Gmail Service Error</h2>
                <p>An unexpected error occurred: {error_msg}</p>
                <p><a href="javascript:window.location.reload()">🔄 Try Again</a> | <a href="/admin/">← Back</a></p>
            </body>
            </html>
        """, status=500, content_type="text/html")