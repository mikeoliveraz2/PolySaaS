from dose.services.atomic_service_base import AtomicServiceBase
import requests
import logging
from django.http import HttpResponse
import json

logger = logging.getLogger(__name__)

class GmailProxyService(AtomicServiceBase):
    # Gmail API base URL (single source of truth)
    # Gmail API base URL (hard-coded, best practice for stable endpoint)
    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
    """
    Gmail Proxy Atomic Service

    Provides a custom Gmail proxy that uses OAuth tokens to access Gmail API
    instead of trying to proxy the Gmail web interface.
    """

    @staticmethod
    def execute_and_save(request, instruction_row):
        """
        Execute Gmail proxy service using OAuth token for API access.

        Thi                icon = {'INBOX': '&darr;', 'SENT': '&uarr;', 'DRAFT': '&clubs;', 'SPAM': '&times;', 'TRASH': '&empty;', 'STARRED': '&star;'}.get(label['name'], '&spades;') service intercepts Gmail passthrough requests and converts them
        to Gmail API calls, avoiding the web interface 302 redirect issues.
        """
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

        # 🔥 TRAFFIC ORCHESTRATION & DATA CAPTURE
        from dose.services.gmail_traffic_orchestrator import GmailTrafficOrchestrator

        # Determine Gmail action for orchestration
        gmail_action = GmailProxyService._determine_gmail_action(request)

        # Capture interaction for orchestration
        orchestration_data = GmailTrafficOrchestrator.capture_gmail_interaction(
            request,
            f"{gmail_action}_gmail",
            {'gmail_action': gmail_action, 'path': request.path}
        )

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
                return HttpResponse(
                    "<h1>Gmail Access Denied</h1>"
                    "<p>Please login with your Google account to access Gmail.</p>"
                    "<p><a href='/accounts/google/login/?next=/admin/passthrough/gmail/&process=connect'>Login with Google</a></p>",
                    status=401
                )

        # Determine what Gmail action to perform based on request path
        gmail_action = GmailProxyService._determine_gmail_action(request)

        if gmail_action == 'inbox':
            return GmailProxyService._handle_inbox(request, oauth_token, orchestration_data)
        elif gmail_action == 'compose':
            return GmailProxyService._handle_compose(request, oauth_token, orchestration_data)
        else:
            return GmailProxyService._handle_default_gmail(request, oauth_token, orchestration_data)

    @staticmethod
    def _determine_gmail_action(request):
        """Determine what Gmail action to perform based on request."""
        path = request.path_info.lower()

        if 'compose' in path or request.method == 'POST':
            return 'compose'
        else:
            return 'inbox'  # Default to inbox

    @staticmethod
    def _handle_inbox(request, oauth_token, orchestration_data=None):
        """Handle Gmail inbox display using Gmail API with Gmail-like UI."""
        try:

            # Call Gmail API to get inbox messages
            headers = {'Authorization': f'Bearer {oauth_token}'}
            from allauth.socialaccount.models import SocialToken
            try:
                token_obj = SocialToken.objects.get(
                    account__user=request.user,
                    account__provider__iexact='google'
                )
                logger.info(f"[GMAIL PROXY DEBUG] Using token: {token_obj.token[:12]}... (len={len(token_obj.token)})")
                logger.info(f"[GMAIL PROXY DEBUG] Token scopes: {token_obj.account.extra_data.get('scope', 'N/A')}")
                logger.info(f"[GMAIL PROXY DEBUG] Token expires at: {token_obj.expires_at}")
            except Exception as e:
                logger.warning(f"[GMAIL PROXY DEBUG] Could not retrieve SocialToken for debug: {e}")
            logger.info(f"[GMAIL PROXY DEBUG] Request headers: {headers}")

            # Use base URL for all Gmail API requests

            # Always use hard-coded Gmail API endpoint for inbox
            messages_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages?labelIds=INBOX&maxResults=50"
            messages_response = requests.get(
                messages_url,
                headers=headers,
                timeout=10
            )
            logger.info(f"[GMAIL PROXY DEBUG] Messages API status: {messages_response.status_code}")
            logger.info(f"[GMAIL PROXY DEBUG] Messages API response: {messages_response.text[:200]}")
            if messages_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Messages API failed: {messages_response.status_code}")
                return GmailProxyService._handle_api_error(messages_response)
            # Get user profile and labels for UI completeness
            profile_url = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
            profile_response = requests.get(
                profile_url,
                headers=headers,
                timeout=10
            )
            logger.info(f"[GMAIL PROXY DEBUG] Profile API status: {profile_response.status_code}")
            logger.info(f"[GMAIL PROXY DEBUG] Profile API response: {profile_response.text[:200]}")
            if profile_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Profile API failed: {profile_response.status_code}")
                return GmailProxyService._handle_api_error(profile_response)
            labels_url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
            labels_response = requests.get(
                labels_url,
                headers=headers,
                timeout=10
            )
            logger.info(f"[GMAIL PROXY DEBUG] Labels API status: {labels_response.status_code}")
            logger.info(f"[GMAIL PROXY DEBUG] Labels API response: {labels_response.text[:200]}")

            profile_data = profile_response.json()
            messages_data = messages_response.json().get('messages', [])
            labels_data = labels_response.json().get('labels', []) if labels_response.status_code == 200 else []

            # Fetch detailed message data for inbox
            detailed_messages = []
            for message in messages_data[:10]:  # Limit to first 10 messages for performance
                msg_metadata_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date&metadataHeaders=Return-Path"
                msg_response = requests.get(
                    msg_metadata_url,
                    headers=headers,
                    timeout=10
                )
                logger.info(f"[GMAIL PROXY DEBUG] Message {message['id']} metadata status: {msg_response.status_code}")
                logger.info(f"[GMAIL PROXY DEBUG] Message {message['id']} metadata response: {msg_response.text[:200]}")
                if msg_response.status_code == 200:
                    msg_data = msg_response.json()
                    # Extract message preview snippet
                    msg_full_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}?format=full"
                    snippet_response = requests.get(
                        msg_full_url,
                        headers=headers,
                        timeout=5
                    )
                    logger.info(f"[GMAIL PROXY DEBUG] Message {message['id']} full status: {snippet_response.status_code}")
                    logger.info(f"[GMAIL PROXY DEBUG] Message {message['id']} full response: {snippet_response.text[:200]}")
                    if snippet_response.status_code == 200:
                        snippet_data = snippet_response.json()
                        msg_data['snippet'] = snippet_data.get('snippet', '')
                    detailed_messages.append(msg_data)

            # Generate Gmail-like UI
            gmail_response = GmailProxyService._generate_gmail_interface(
                request, profile_data, detailed_messages, labels_data
            )

            # 🔥 APPLY ORCHESTRATION ENHANCEMENTS
            if orchestration_data:
                from dose.services.gmail_traffic_orchestrator import GmailTrafficOrchestrator
                gmail_response = GmailTrafficOrchestrator.enhance_gmail_response(
                    gmail_response, orchestration_data
                )

            return gmail_response

        except requests.exceptions.RequestException as e:
            logger.error(f"[GMAIL PROXY] Network error: {str(e)}")
            return GmailProxyService._network_error_response()
        except Exception as e:
            logger.error(f"[GMAIL PROXY] Unexpected error: {str(e)}")
            # Try to render a minimal inbox UI with whatever data is available
            try:
                profile_data = profile_response.json() if 'profile_response' in locals() else {}
                messages_data = []
                labels_data = []
                return GmailProxyService._generate_gmail_interface(request, profile_data, messages_data, labels_data)
            except Exception as inner_e:
                logger.error(f"[GMAIL PROXY] Fallback rendering failed: {inner_e}")
                return GmailProxyService._general_error_response(str(e))

    @staticmethod
    def _handle_compose(request, oauth_token):
        """Handle Gmail compose functionality."""
        # For now, redirect to Gmail compose
        compose_url = "https://mail.google.com/mail/?view=cm&fs=1&to=&su=&body="
        return HttpResponse(
            f'<script>window.open("{compose_url}", "_blank");</script>'
            '<p>Opening Gmail compose in new window...</p>'
            '<p><a href="javascript:history.back()">Go Back</a></p>',
            content_type='text/html'
        )

    @staticmethod
    def _handle_default_gmail(request, oauth_token):
        """Handle default Gmail access - redirect to inbox."""
        return GmailProxyService._handle_inbox(request, oauth_token)

    @staticmethod

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

        # Check for OAuth token expired/invalid error (401 Unauthorized)
        if error_code == 401:
            return HttpResponse(
                """
                <html>
                <head>
                    <title>Gmail API Error - Authentication Required</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .header { background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }
                        .content { padding: 30px; text-align: center; }
                        .error-icon { font-size: 48px; margin-bottom: 20px; }
                        .btn { background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; font-weight: 500; }
                        .btn:hover { background: #0056b3; text-decoration: none; color: white; }
                        .btn-secondary { background: #6c757d; }
                        .btn-secondary:hover { background: #545b62; }
                        .steps { text-align: left; margin: 20px 0; }
                        .step { margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
                        .back-link { margin-top: 20px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="error-icon">🔐</div>
                            <h1>Gmail API Error</h1>
                            <p>Error 401: Request had invalid authentication credentials</p>
                        </div>
                        <div class="content">
                            <h3>🔄 Your Google authentication has expired</h3>
                            <p>Your OAuth token has expired and needs to be refreshed. Please re-authenticate with your Google account to continue using Gmail.</p>

                            <div class="steps">
                                <div class="step">
                                    <strong>Step 1:</strong> Click "Re-authenticate" below to login with Google again
                                </div>
                                <div class="step">
                                    <strong>Step 2:</strong> Grant permission to access your Gmail account
                                </div>
                                <div class="step">
                                    <strong>Step 3:</strong> Return to Gmail integration
                                </div>
                            </div>

                            <div>
                                <a href="/accounts/google/login/?next=/admin/passthrough/gmail/" class="btn">🔄 Re-authenticate with Google</a>
                                <a href="/admin/" class="btn btn-secondary">← Back to Dashboard</a>
                            </div>

                            <div class="back-link">
                                <small>Having trouble? <a href="/admin/">Contact support</a></small>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """,
                status=401
            )

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
                <html>
                <head>
                    <title>Gmail API Setup Required</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .error-box {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 20px; border-radius: 5px; }}
                        .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block; margin: 10px 5px; }}
                        .btn:hover {{ background: #0056b3; }}
                        .steps {{ background: #e9ecef; padding: 15px; margin: 20px 0; border-radius: 3px; }}
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>📧 Gmail API Setup Required</h2>
                        <p><strong>Your Google OAuth is working perfectly!</strong> However, the Gmail API needs to be enabled in Google Cloud Console.</p>

                        <div class="steps">
                            <h3>📋 Quick Setup Steps:</h3>
                            <ol>
                                <li>Click the button below to open Google Cloud Console</li>
                                <li>Click the <strong>"ENABLE"</strong> button on the Gmail API page</li>
                                <li>Wait 2-3 minutes for changes to take effect</li>
                                <li>Return here and refresh the page</li>
                            </ol>
                        </div>

                        <a href="{enable_url}" target="_blank" class="btn">🔧 Enable Gmail API</a>
                        <a href="javascript:window.location.reload()" class="btn" style="background: #28a745;">🔄 Refresh Page</a>
                        <a href="/admin/" class="btn" style="background: #6c757d;">← Back to Dashboard</a>
                    </div>

                    <div style="margin-top: 30px; padding: 20px; background: #f0f8ff; border-radius: 5px;">
                        <h3>🎯 What You'll Get Once Enabled:</h3>
                        <ul>
                            <li>📬 Full Gmail inbox with all your emails</li>
                            <li>✉️ Compose and send emails directly</li>
                            <li>🔍 Search through your emails</li>
                            <li>🏷️ Organize with labels and folders</li>
                            <li>📱 Responsive Gmail-like interface</li>
                        </ul>
                    </div>
                </body>
                </html>
                """,
                status=403
            )

        # Generic API error
        return HttpResponse(f"""
            <html>
            <head><title>Gmail API Error</title></head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h2>Gmail API Error</h2>
                <p><strong>Error {error_code}:</strong> {error_message}</p>
                <p><a href="/admin/">← Back to Dashboard</a></p>
            </body>
            </html>
        """, status=response.status_code)

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
                'snippet': msg.get('snippet', 'No preview available'),
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

        # Render a simple HTML inbox table
        html = f"""
        <html>
        <head>
            <title>Gmail Inbox for {user_email}</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f8f9fa; }}
                h2 {{ color: #007bff; }}
                table {{ border-collapse: collapse; width: 100%; background: #fff; }}
                th, td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; }}
                th {{ background: #e9ecef; }}
                tr.unread td {{ font-weight: bold; background: #e3f2fd; }}
                tr:hover {{ background: #f1f3f4; }}
            </style>
        </head>
        <body>
            <h2>Gmail Inbox for {user_email}</h2>
            <p>Total messages: {total_messages}</p>
            <table>
                <tr>
                    <th>From</th>
                    <th>Subject</th>
                    <th>Date</th>
                    <th>Snippet</th>
                </tr>
        """
        for msg in processed_messages:
            row_class = "unread" if msg['unread'] else ""
            html += f"""
                <tr class='{row_class}'>
                    <td>{msg['from']}</td>
                    <td>{msg['subject']}</td>
                    <td>{msg['date']}</td>
                    <td>{msg['snippet']}</td>
                </tr>
            """
        html += """
            </table>
        </body>
        </html>
        """
        return HttpResponse(html)

    # Duplicate method removed - using enhanced version earlier in file

    @staticmethod
    def get_parameters(parameters, key):
        """Return parameters for this atomic service."""
        # Gmail proxy doesn't need external parameters
        return {}