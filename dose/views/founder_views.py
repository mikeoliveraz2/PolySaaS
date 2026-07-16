"""
Founder Beta Circle signup and Lemon Squeezy webhook handling.
REST API for WordPress integration.
"""
import logging
import hashlib
import hmac
import json
from decimal import Decimal

from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from dose.models import FounderSignup, Tenant, Subscription, UserProfile, UserTenantMembership

logger = logging.getLogger(__name__)
User = get_user_model()

# Founder tier: $100 lifetime, includes 8 apps + 1 user
FOUNDERS_PRICE_USD = Decimal('100.00')
FOUNDERS_PLAN_TIER = 'polysaas-unlimited'
FOUNDERS_APPS = [
    'enable_odoo',
    'enable_nextcloud',
    'enable_dolibarr',
    'enable_mattermost',
    'enable_wordpress',
    'enable_liferay',
    'enable_monitor_logger',
    'enable_polysysmon',
]


@api_view(['POST'])
@permission_classes([AllowAny])
def founders_signup_api(request):
    """
    REST API endpoint for Founder Beta Circle signup.
    Called from WordPress form via JavaScript.
    
    Request body:
    {
        "company_name": "Acme Corp",
        "company_slug": "acme-corp",
        "admin_username": "john.smith",
        "admin_email": "john@acme.com"
    }
    
    Response:
    {
        "success": true,
        "checkout_url": "https://lemonsqueezy.com/checkout/...",
        "founder_id": 123
    }
    Or:
    {
        "success": false,
        "errors": {"company_slug": "Already taken"}
    }
    """
    try:
        data = request.data
        company_name = (data.get('company_name') or '').strip()
        company_slug = (data.get('company_slug') or '').strip().lower()
        admin_username = (data.get('admin_username') or '').strip()
        admin_email = (data.get('admin_email') or '').strip()
        
        # Validation
        errors = {}
        if not company_name:
            errors['company_name'] = 'Company name is required.'
        if not company_slug or not company_slug.replace('-', '').replace('_', '').isalnum():
            errors['company_slug'] = 'Slug must be alphanumeric (hyphens/underscores allowed).'
        if FounderSignup.objects.filter(company_slug=company_slug).exists():
            errors['company_slug'] = 'This slug is already taken.'
        if Tenant.objects.filter(slug=company_slug).exists():
            errors['company_slug'] = 'This slug is already in use.'
        if not admin_username or len(admin_username) < 3:
            errors['admin_username'] = 'Username must be at least 3 characters.'
        if not admin_email or '@' not in admin_email:
            errors['admin_email'] = 'Valid email is required.'
        
        if errors:
            return Response({'success': False, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create pending FounderSignup record
        founder_signup, created = FounderSignup.objects.get_or_create(
            company_slug=company_slug,
            defaults={
                'company_name': company_name,
                'admin_username': admin_username,
                'admin_email': admin_email,
                'status': 'pending',
            }
        )
        
        if not created and founder_signup.status != 'pending':
            return Response(
                {'success': False, 'errors': {'company_slug': 'This company has already signed up.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build Lemon Squeezy checkout URL
        api_key = settings.LEMON_SQUEEZY_API_KEY
        product_id = settings.LEMON_SQUEEZY_PRODUCT_ID
        
        if not api_key or not product_id:
            logger.error('Lemon Squeezy API key or product ID not configured.')
            return Response(
                {'success': False, 'errors': {'_': 'Payment system not configured. Please contact support.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Build checkout URL with custom metadata
        checkout_url = (
            f"https://lemonsqueezy.com/checkout/{product_id}"
            f"?checkout[email]={admin_email}"
            f"&checkout[custom][founder_id]={founder_signup.id}"
            f"&checkout[custom][company]={company_slug}"
        )
        
        logger.info(f'Founder signup API: created {founder_signup.id} ({company_slug})')
        
        return Response({
            'success': True,
            'checkout_url': checkout_url,
            'founder_id': founder_signup.id,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.exception(f'Founder signup API error: {e}')
        return Response(
            {'success': False, 'errors': {'_': 'An error occurred. Please try again.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_view(['POST'])
@permission_classes([AllowAny])
def lemon_squeezy_webhook(request):
    """
    Lemon Squeezy webhook handler for order completion.
    
    Webhook events:
    - order:created
    - order:refunded
    
    On successful order: marks FounderSignup as completed and enqueues provisioning.
    """
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Signature', '')
        body = request.body
        
        secret = settings.LEMON_SQUEEZY_WEBHOOK_SECRET
        if not verify_lemon_squeezy_signature(signature, body, secret):
            logger.warning('Invalid Lemon Squeezy webhook signature')
            return Response({'error': 'Invalid signature'}, status=401)
        
        data = json.loads(body)
        event_type = data.get('meta', {}).get('event_name', '')
        
        if event_type == 'order:completed':
            return handle_order_completed(data)
        elif event_type == 'order:refunded':
            return handle_order_refunded(data)
        else:
            logger.debug(f'Ignoring Lemon Squeezy event: {event_type}')
            return Response({'ok': True})
    
    except Exception as e:
        logger.exception(f'Lemon Squeezy webhook error: {e}')
        return Response({'error': str(e)}, status=500)


def verify_lemon_squeezy_signature(signature, body, secret):
    """
    Verify Lemon Squeezy webhook signature.
    Signature is HMAC-SHA256 of body with webhook secret.
    """
    if not signature or not secret:
        return False
    
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


def handle_order_completed(webhook_data):
    """
    Process completed Lemon Squeezy order.
    Extract founder_id from custom data, mark signup as completed, and provision tenant.
    """
    try:
        custom_data = webhook_data.get('data', {}).get('attributes', {}).get('custom_data') or {}
        founder_id = custom_data.get('founder_id')
        order_id = webhook_data.get('data', {}).get('id')
        
        if not founder_id or not order_id:
            logger.warning(f'Missing founder_id or order_id in webhook: {webhook_data}')
            return Response({'error': 'Missing founder_id'}, status=400)
        
        founder_signup = FounderSignup.objects.get(id=founder_id)
        
        if founder_signup.status == 'provisioned':
            logger.info(f'Founder {founder_id} already provisioned, skipping.')
            return Response({'ok': True})
        
        # Mark payment completed
        founder_signup.mark_payment_completed(order_id)
        logger.info(f'Marked founder signup {founder_id} as payment completed')
        
        # Provision tenant asynchronously
        from dose.services.founder_provisioner import provision_founder_tenant
        provision_founder_tenant.delay(founder_id)
        
        return Response({'ok': True})
    
    except FounderSignup.DoesNotExist:
        logger.warning(f'FounderSignup not found for webhook')
        return Response({'error': 'Founder signup not found'}, status=404)
    except Exception as e:
        logger.exception(f'Error processing order completion: {e}')
        return Response({'error': str(e)}, status=500)


def handle_order_refunded(webhook_data):
    """
    Handle refunded orders (cleanup if needed).
    """
    try:
        custom_data = webhook_data.get('data', {}).get('attributes', {}).get('custom_data') or {}
        founder_id = custom_data.get('founder_id')
        
        if not founder_id:
            return Response({'ok': True})
        
        founder_signup = FounderSignup.objects.get(id=founder_id)
        logger.info(f'Order refunded for founder {founder_id}')
        
        # Mark as failed if not yet provisioned
        if founder_signup.status != 'provisioned':
            founder_signup.mark_failed()
        
        return Response({'ok': True})
    except FounderSignup.DoesNotExist:
        return Response({'ok': True})
    except Exception as e:
        logger.exception(f'Error processing refund: {e}')
        return Response({'error': str(e)}, status=500)
