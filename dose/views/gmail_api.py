"""
Gmail API Integration Views

Provides dynamic Gmail API access for authenticated users with Google OAuth2.
"""

import logging
import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.core.cache import cache
from allauth.socialaccount.models import SocialToken

logger = logging.getLogger(__name__)


def get_google_token(user):
    """
    Retrieve the Google OAuth2 access token for the given user.
    Automatically refreshes expired tokens.

    Args:
        user: Django User object

    Returns:
        SocialToken object or None if not found
    """
    from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
    from datetime import datetime, timezone
    import requests as req

    # First, check all social accounts for this user
    accounts = SocialAccount.objects.filter(user=user)
    logger.info(f"[GMAIL TOKEN] Checking tokens for user {user.username}, found {accounts.count()} social accounts")
    for acc in accounts:
        logger.info(f"[GMAIL TOKEN] Account: provider={acc.provider}, uid={acc.uid}")

    # Try to find Google token - check both 'google' and 'dose' providers
    tokens = SocialToken.objects.filter(account__user=user)
    logger.info(f"[GMAIL TOKEN] Available tokens for user {user.username}: {[(t.account.provider, t.account.uid) for t in tokens]}")

    token_obj = None
    # First try exact 'google' match
    for token in tokens:
        if token.account.provider.lower() == 'google':
            token_obj = token
            logger.info(f"[GMAIL TOKEN] Found token with provider 'google'")
            break

    # If not found, try 'dose' provider (some setups use 'dose' for Google)
    if not token_obj:
        for token in tokens:
            if token.account.provider.lower() == 'dose':
                token_obj = token
                logger.info(f"[GMAIL TOKEN] Found token with provider 'dose' (treating as Google)")
                break

    # If still not found, try any provider containing 'google'
    if not token_obj:
        for token in tokens:
            if 'google' in token.account.provider.lower():
                token_obj = token
                logger.info(f"[GMAIL TOKEN] Found Google token via provider '{token.account.provider}'")
                break

    if not token_obj:
        logger.warning(f"[GMAIL TOKEN] No Google token found for user {user.username}")
        return None

    logger.info(f"[GMAIL TOKEN] Using token with provider '{token_obj.account.provider}', expires_at={token_obj.expires_at}")

    # Check if token is expired and refresh if needed
    now = datetime.now(timezone.utc)
    if token_obj.expires_at and token_obj.expires_at < now:
        logger.info(f"[GMAIL TOKEN] Token expired for {user.username}, attempting refresh...")

        # Get the social app for client credentials - try both 'google' and 'dose'
        social_app = SocialApp.objects.filter(provider='google').first()
        if not social_app:
            social_app = SocialApp.objects.filter(provider='dose').first()
        if not social_app or not token_obj.token_secret:  # token_secret stores refresh token
            logger.error(f"[GMAIL TOKEN] Cannot refresh token: missing social app or refresh token (app={social_app}, has_secret={bool(token_obj.token_secret)})")
            return None

        # Refresh the token
        try:
            refresh_response = req.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': social_app.client_id,
                    'client_secret': social_app.secret,
                    'refresh_token': token_obj.token_secret,
                    'grant_type': 'refresh_token'
                }
            )

            if refresh_response.status_code == 200:
                token_data = refresh_response.json()
                token_obj.token = token_data['access_token']
                if 'expires_in' in token_data:
                    from datetime import timedelta
                    token_obj.expires_at = now + timedelta(seconds=token_data['expires_in'])
                token_obj.save()
                logger.info(f"[GMAIL TOKEN] Token refreshed successfully for {user.username}")
            else:
                error_data = refresh_response.json() if refresh_response.content else {}
                error_msg = error_data.get('error_description', refresh_response.text)
                logger.error(f"[GMAIL TOKEN] Token refresh failed: {refresh_response.status_code} - {error_msg}")

                # If refresh token is invalid, delete the token so user can reconnect
                if 'invalid_grant' in error_msg.lower() or 'expired' in error_msg.lower() or 'revoked' in error_msg.lower():
                    logger.warning(f"[GMAIL TOKEN] Refresh token invalid, deleting token for {user.username}")
                    token_obj.delete()  # Delete invalid token so user can reconnect
                return None
        except Exception as e:
            logger.error(f"[GMAIL TOKEN] Token refresh error: {e}")
            return None

    return token_obj


@login_required
def dynamic_gmail_api(request, endpoint=''):
    """
    Dynamic Gmail API proxy that forwards requests to Gmail API.

    Supports any Gmail API endpoint dynamically. The endpoint parameter can be
    passed as part of the URL path or as a query/POST parameter.

    Args:
        request: Django HttpRequest
        endpoint: Gmail API endpoint path (optional, can also come from params)

    Returns:
        JsonResponse with Gmail API response data
    """
    # Get the user's Google access token
    token = get_google_token(request.user)
    if not token:
        logger.error(f"[GMAIL API] No token found for user {request.user.username}")
        return JsonResponse({
            'error': 'No Google token found. Your Google account connection may have expired. Please reconnect your Google account.',
            'auth_url': '/accounts/google/login/?process=connect&next=' + request.path
        }, status=400)

    logger.info(f"[GMAIL API] Token found for user {request.user.username}, endpoint: '{endpoint}'")

    # Get endpoint from URL path parameter or request params
    if not endpoint:
        endpoint = request.GET.get('endpoint') or request.POST.get('endpoint', '')

    # Bulletproof rewrite: any variant of 'messages' should map to '/users/me/messages'
    import re
    endpoint_clean = endpoint.strip().lower().rstrip('/')
    # Rewrite /messages to /users/me/messages
    if endpoint_clean == 'messages' or endpoint_clean == '/messages':
        endpoint = '/users/me/messages'
    # Rewrite /messages/<id> to /users/me/messages/<id>
    match = re.match(r'^/?messages/([a-zA-Z0-9_-]+)$', endpoint_clean)
    if match:
        endpoint = f'/users/me/messages/{match.group(1)}'

    # Get additional parameters
    params = {}
    force_refresh = False
    if request.method == 'GET':
        params = {k: v for k, v in request.GET.items() if k not in ['endpoint', '_refresh']}
        # Check for cache-busting parameter
        force_refresh = '_refresh' in request.GET
    elif request.method == 'POST' and request.content_type == 'application/json':
        import json
        try:
            params = json.loads(request.body)
            params.pop('endpoint', None)
        except:
            params = {}

    # Build the Gmail API URL
    base_url = 'https://gmail.googleapis.com/gmail/v1'
    # Ensure endpoint starts with /
    if endpoint and not endpoint.startswith('/'):
        endpoint = '/' + endpoint

    full_url = f'{base_url}{endpoint}' if endpoint else f'{base_url}/users/me/messages'

    # Prepare headers with OAuth2 token
    headers = {
        'Authorization': f'Bearer {token.token}',
        'Content-Type': 'application/json',
    }

    # Make the API request
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:
            response = requests.request(
                method=request.method,
                url=full_url,
                headers=headers,
                json=params if params else None,
                timeout=30
            )
        else:
            response = requests.get(
                url=full_url,
                headers=headers,
                params=params,
                timeout=30
            )

        logger.info(f"[GMAIL API] Request: {request.method} {full_url} -> {response.status_code}")
        logger.info(f"[GMAIL API] Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            logger.error(f"[GMAIL API] Error response: {response.text[:500]}")
            return JsonResponse({
                'error': f'Gmail API error: {response.status_code}',
                'details': response.text[:500]
            }, status=response.status_code)

        # Special handling for messages list - enrich with metadata using parallel requests + caching
        # Match both exact endpoint and endpoint with trailing slash
        is_messages_list = (endpoint in ['/users/me/messages', '/users/me/messages/'] and request.method == 'GET')
        logger.info(f"📧 Endpoint check: '{endpoint}' | is_messages_list={is_messages_list} | method={request.method}")

        if is_messages_list:
            try:
                import concurrent.futures

                # Create cache key based on user and page token
                page_token = params.get('pageToken', '')
                cache_key = f'gmail_messages_{request.user.id}_{page_token}'

                # Try to get from cache first (5 minute cache) unless force refresh
                if not force_refresh:
                    cached_data = cache.get(cache_key)
                    if cached_data:
                        logger.info(f"📧 Returning cached Gmail messages for user {request.user.id}")
                        return JsonResponse(cached_data, safe=False)

                response_data = response.json()
                messages = response_data.get('messages', [])
                logger.info(f"📧 Gmail API returned {len(messages)} messages")
                logger.info(f"📧 Response keys: {list(response_data.keys())}")
                logger.info(f"📧 resultSizeEstimate: {response_data.get('resultSizeEstimate', 'N/A')}")
                if not messages:
                    logger.warning(f"📧 No messages in response! Full response: {response_data}")
                logger.info(f"📧 Starting metadata enrichment for {len(messages)} messages")

                def fetch_message_metadata(msg):
                    """Fetch metadata for a single message with per-message caching"""
                    msg_cache_key = f'gmail_msg_{msg["id"]}'
                    cached_msg = cache.get(msg_cache_key)
                    if cached_msg:
                        return cached_msg

                    try:
                        meta_url = f"{base_url}/users/me/messages/{msg['id']}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date"
                        meta_resp = requests.get(meta_url, headers=headers, timeout=3)

                        if meta_resp.status_code == 200:
                            meta_data = meta_resp.json()
                            headers_list = meta_data.get('payload', {}).get('headers', [])

                            from_header = next((h['value'] for h in headers_list if h['name'].lower() == 'from'), 'Unknown')
                            subject_header = next((h['value'] for h in headers_list if h['name'].lower() == 'subject'), '(No subject)')
                            date_header = next((h['value'] for h in headers_list if h['name'].lower() == 'date'), '')

                            msg_data = {
                                'id': msg['id'],
                                'threadId': msg.get('threadId'),
                                'from': from_header,
                                'subject': subject_header,
                                'date': date_header,
                                'snippet': meta_data.get('snippet', '')
                            }

                            # Cache individual message for 30 minutes
                            cache.set(msg_cache_key, msg_data, 1800)
                            return msg_data
                    except Exception as e:
                        logger.warning(f"Failed to fetch metadata for message {msg['id']}: {e}")

                    return {
                        'id': msg['id'],
                        'threadId': msg.get('threadId'),
                        'from': 'Unknown',
                        'subject': '(No subject)',
                        'date': '',
                        'snippet': ''
                    }

                # Fetch metadata in parallel using ThreadPoolExecutor (max 10 concurrent)
                enriched_messages = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    enriched_messages = list(executor.map(fetch_message_metadata, messages[:20]))

                # Prepare response
                result = {
                    'messages': enriched_messages,
                    'nextPageToken': response_data.get('nextPageToken'),
                    'resultSizeEstimate': response_data.get('resultSizeEstimate')
                }

                # Cache the full response for 5 minutes
                cache.set(cache_key, result, 300)
                logger.info(f"📧 Cached Gmail messages for user {request.user.id}")

                return JsonResponse(result, safe=False)

            except Exception as e:
                logger.error(f"Failed to enrich messages: {e}")
                # Fallback to original response
                return JsonResponse(
                    response.json() if response.content else {},
                    status=response.status_code,
                    safe=False
                )

        # Return the Gmail API response for other endpoints
        return JsonResponse(
            response.json() if response.content else {},
            status=response.status_code,
            safe=False
        )

    except requests.RequestException as e:
        logger.error(f"Gmail API request failed: {e}")
        return JsonResponse(
            {'error': f'Gmail API request failed: {str(e)}'},
            status=500
        )


@login_required
def gmail_inbox(request):
    """
    Display Gmail inbox for the authenticated user.

    This view renders a template that displays the user's Gmail inbox
    using the Gmail API.
    """
    from allauth.socialaccount.models import SocialAccount, SocialToken
    user = request.user
    logger.info(f"[GMAIL DEBUG] gmail_inbox called for user: {user} (id={user.id})")
    # Print all SocialAccounts for this user
    accounts = SocialAccount.objects.filter(user=user)
    logger.info(f"[GMAIL DEBUG] SocialAccounts for user: {[f'{a.provider}:{a.uid}' for a in accounts]}")
    # Print all SocialTokens for this user
    tokens = SocialToken.objects.filter(account__user=user)
    logger.info(f"[GMAIL DEBUG] SocialTokens for user: {[f'{t.account.provider}:{t.token[:8]}...' for t in tokens]}")
    # Try to get Google token
    token = get_google_token(user)
    logger.info(f"[GMAIL DEBUG] get_google_token returned: {token.token[:12]+'...' if token else 'None'}")
    if not token:
        return render(request, 'dose/gmail_error.html', {
            'error': 'No Google authentication found. Your Google account connection may have expired. Please reconnect your Google account.',
            'auth_url': '/accounts/google/login/?process=connect&next=' + request.path
        })

    from dose.utils import get_current_tenant, get_tenant_theme_colors

    current_tenant = get_current_tenant(request)
    theme_colors = get_tenant_theme_colors('tech_blue')

    return render(request, 'dose/gmail_inbox.html', {
        'user': user,
        'current_tenant': current_tenant,
        'theme_colors': theme_colors,
    })


@login_required
def gmail_send(request):
    """
    Display Gmail send email form and handle email sending.

    GET: Display the send email form
    POST: Send the email via Gmail API
    """
    token = get_google_token(request.user)
    if not token:
        return render(request, 'dose/gmail_error.html', {
            'error': 'No Google authentication found. Please connect your Google account.'
        })

    if request.method == 'POST':
        # Handle email sending
        to = request.POST.get('to', '')
        subject = request.POST.get('subject', '')
        body = request.POST.get('body', '')

        if not to or not subject:
            return JsonResponse({
                'error': 'To and Subject fields are required'
            }, status=400)

        # Create the email message in RFC 2822 format
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send via Gmail API
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                headers=headers,
                json={'raw': raw_message},
                timeout=30
            )

            if response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'message': 'Email sent successfully',
                    'data': response.json()
                })
            else:
                return JsonResponse({
                    'error': f'Failed to send email: {response.text}'
                }, status=response.status_code)

        except requests.RequestException as e:
            logger.error(f"Gmail send failed: {e}")
            return JsonResponse({
                'error': f'Failed to send email: {str(e)}'
            }, status=500)

    # GET request - show the form
    return render(request, 'dose/gmail_send.html', {
        'user': request.user,
    })
