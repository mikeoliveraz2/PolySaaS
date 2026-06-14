from dose.services.atomic_service_base import AtomicServiceBase
import requests
import logging
from django.http import HttpResponse
import json

logger = logging.getLogger(__name__)

class GmailProxy(AtomicServiceBase):
    """
    Gmail Proxy Atomic Service

    Provides a custom Gmail proxy that uses OAuth tokens to access Gmail API
    instead of trying to proxy the Gmail web interface.
    """

    @staticmethod
    def execute_and_save(request, instruction_row):
        """
        Execute Gmail proxy service using OAuth token for API access.

        This service intercepts Gmail passthrough requests and converts them
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
        gmail_action = GmailProxy._determine_gmail_action(request)

        # Capture interaction for orchestration
        orchestration_data = GmailTrafficOrchestrator.capture_gmail_interaction(
            request,
            gmail_action,
            {}  # Additional context can be added here
        )

        # Get OAuth token
        token = GmailProxy._get_oauth_token(request.user)
        if not token:
            logger.warning(f"[GMAIL PROXY] No OAuth token found for user {request.user.username}")
            return HttpResponse("""
                <html>
                <head><title>Gmail Access - OAuth Required</title></head>
                <body>
                    <h2>Gmail OAuth Required</h2>
                    <p><strong>OAuth Access Required</strong></p>
                    <p>You need to authorize Gmail access first.</p>
                    <p><a href="/accounts/google/login/?next=/admin/passthrough/gmail/">Authorize Gmail Access</a></p>
                    <p><a href="/admin/">Return to Admin</a></p>
                </body>
                </html>
            """, content_type="text/html")

        # Make Gmail API calls
        try:
            # Get user profile
            profile_response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/profile',
                headers={'Authorization': f'Bearer {token}'}
            )
            if profile_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Profile API error: {profile_response.status_code}")
                raise Exception(f"Gmail API error: {profile_response.status_code}")

            profile_data = profile_response.json()
            user_email = profile_data.get('emailAddress', 'Unknown')
            total_messages = profile_data.get('messagesTotal', 0)

            # Get labels
            labels_response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/labels',
                headers={'Authorization': f'Bearer {token}'}
            )
            if labels_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Labels API error: {labels_response.status_code}")
                raise Exception(f"Gmail Labels API error: {labels_response.status_code}")

            labels_data = labels_response.json()
            labels = labels_data.get('labels', [])

            # Get recent messages
            messages_response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=10&labelIds=INBOX',
                headers={'Authorization': f'Bearer {token}'}
            )
            if messages_response.status_code != 200:
                logger.error(f"[GMAIL PROXY] Messages API error: {messages_response.status_code}")
                messages = []
            else:
                messages_data = messages_response.json()
                messages = messages_data.get('messages', [])

            # Get detailed message info
            processed_messages = []
            for msg in messages[:5]:  # Limit to 5 for performance
                try:
                    msg_response = requests.get(
                        f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg["id"]}?format=metadata',
                        headers={'Authorization': f'Bearer {token}'}
                    )
                    if msg_response.status_code == 200:
                        msg_data = msg_response.json()
                        # Extract headers
                        headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                        processed_messages.append({
                            'id': msg['id'],
                            'from': headers.get('From', 'Unknown'),
                            'subject': headers.get('Subject', 'No Subject'),
                            'date': headers.get('Date', 'Unknown'),
                            'snippet': msg_data.get('snippet', ''),
                            'unread': 'UNREAD' in msg_data.get('labelIds', []),
                            'starred': 'STARRED' in msg_data.get('labelIds', [])
                        })
                except Exception as e:
                    logger.warning(f"[GMAIL PROXY] Failed to get message {msg['id']}: {e}")
                    continue

        except Exception as e:
            logger.error(f"[GMAIL PROXY] Gmail API error: {e}")
            return HttpResponse(f"""
                <html>
                <head><title>Gmail API Error</title></head>
                <body>
                    <h2>Gmail API Error</h2>
                    <p><strong>Error occurred while accessing Gmail API</strong></p>
                    <p>Error: {str(e)}</p>
                    <p><a href="/accounts/google/login/?next=/admin/passthrough/gmail/">Re-authorize Gmail Access</a></p>
                    <p><a href="/admin/">Return to Admin</a></p>
                </body>
                </html>
            """, content_type="text/html")

        # 🎯 ORCHESTRATION RESULT CAPTURE
        # Store the orchestration results for future analysis
        try:
            orchestration_result = GmailTrafficOrchestrator.finalize_gmail_interaction(
                orchestration_data,
                {
                    'status': 'success',
                    'messages_count': len(processed_messages),
                    'user_email': user_email,
                    'total_messages': total_messages
                }
            )
            logger.info(f"[GMAIL PROXY] Orchestration finalized: {orchestration_result}")
        except Exception as e:
            logger.warning(f"[GMAIL PROXY] Orchestration finalize failed: {e}")

        # Process labels
        system_labels = []
        user_labels = []
        for label in labels:
            if label['type'] == 'system':
                system_labels.append(label)
            else:
                user_labels.append(label)

        # Instead of returning complete HTML, return structured data for template rendering
        gmail_data = {
            'user_email': user_email,
            'total_messages': total_messages,
            'system_labels': system_labels,
            'user_labels': user_labels,
            'processed_messages': processed_messages,
            'status': 'success'
        }

        # Store the data to be used by the template
        instruction_row.response_output = gmail_data
        instruction_row.status_message = f"Gmail data loaded: {total_messages} messages"
        instruction_row.save()

        return HttpResponse("Gmail data prepared for template rendering", content_type="text/plain")

    @staticmethod
    def _get_oauth_token(user):
        """Get OAuth token for the user from django-allauth."""
        try:
            from allauth.socialaccount.models import SocialToken
            token = SocialToken.objects.filter(
                account__user=user,
                account__provider='google',
                app__provider='google'
            ).first()

            if token and not token.is_expired():
                return token.token
            else:
                logger.warning(f"[GMAIL PROXY] Token expired or not found for user {user.username}")
                return None
        except Exception as e:
            logger.error(f"[GMAIL PROXY] Error getting OAuth token: {e}")
            return None

    @staticmethod
    def _determine_gmail_action(request):
        """Determine the Gmail action from the request."""
        # Simple action determination based on request path or parameters
        if 'compose' in request.GET:
            return 'compose'
        elif 'message' in request.GET:
            return 'view_message'
        else:
            return 'inbox_view'

    @staticmethod
    def get_parameters(parameters, key):
        """Return parameters for this atomic service."""
        # Gmail proxy doesn't need external parameters
        return {}