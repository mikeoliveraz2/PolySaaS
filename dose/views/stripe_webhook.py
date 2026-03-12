import json
import logging
import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.models import Subscription

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

TIER_BY_PRICE = None


def _get_tier_by_price():
    """Build reverse lookup: price_id -> tier name. Cached after first call."""
    global TIER_BY_PRICE
    if TIER_BY_PRICE is None:
        price_ids = getattr(settings, 'STRIPE_PRICE_IDS', {})
        TIER_BY_PRICE = {v: k for k, v in price_ids.items() if v}
    return TIER_BY_PRICE


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    if not endpoint_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not configured — skipping signature verification")
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid payload')
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            logger.error("Stripe webhook: invalid payload")
            return HttpResponseBadRequest('Invalid payload')
        except stripe.error.SignatureVerificationError:
            logger.error("Stripe webhook: invalid signature")
            return HttpResponseBadRequest('Invalid signature')

    event_type = event.get('type', '')
    data = event.get('data', {}).get('object', {})
    logger.info(f"Stripe webhook received: {event_type}")

    if event_type == 'customer.subscription.updated':
        _handle_subscription_updated(data)
    elif event_type == 'customer.subscription.deleted':
        _handle_subscription_deleted(data)
    elif event_type == 'invoice.paid':
        _handle_invoice_paid(data)
    elif event_type == 'invoice.payment_failed':
        _handle_invoice_payment_failed(data)
    else:
        logger.info(f"Stripe webhook: unhandled event type '{event_type}'")

    return HttpResponse(status=200)


def _handle_subscription_updated(data):
    stripe_sub_id = data.get('id')
    if not stripe_sub_id:
        return

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
    except Subscription.DoesNotExist:
        logger.warning(f"Webhook: subscription {stripe_sub_id} not found in DB")
        return

    status = data.get('status', '')
    sub.active = status in ('active', 'trialing')

    items = data.get('items', {}).get('data', [])
    if items:
        current_price_id = items[0].get('price', {}).get('id', '')
        tier_map = _get_tier_by_price()
        new_tier = tier_map.get(current_price_id)
        if new_tier and new_tier != sub.plan_tier:
            logger.info(f"Webhook: tier change {sub.plan_tier} -> {new_tier} for {stripe_sub_id}")
            sub.plan_tier = new_tier

    sub.save()
    logger.info(f"Webhook: subscription {stripe_sub_id} updated (active={sub.active}, tier={sub.plan_tier})")


def _handle_subscription_deleted(data):
    stripe_sub_id = data.get('id')
    if not stripe_sub_id:
        return

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        sub.active = False
        sub.save()
        logger.info(f"Webhook: subscription {stripe_sub_id} marked inactive (deleted)")
    except Subscription.DoesNotExist:
        logger.warning(f"Webhook: subscription {stripe_sub_id} not found for deletion")


def _handle_invoice_paid(data):
    stripe_sub_id = data.get('subscription')
    if not stripe_sub_id:
        return

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        if not sub.active:
            sub.active = True
            sub.save()
            logger.info(f"Webhook: subscription {stripe_sub_id} reactivated after invoice.paid")
    except Subscription.DoesNotExist:
        logger.warning(f"Webhook: invoice.paid for unknown subscription {stripe_sub_id}")


def _handle_invoice_payment_failed(data):
    stripe_sub_id = data.get('subscription')
    if not stripe_sub_id:
        return

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        logger.warning(f"Webhook: payment failed for subscription {stripe_sub_id} (tenant={sub.tenant.name})")
    except Subscription.DoesNotExist:
        logger.warning(f"Webhook: invoice.payment_failed for unknown subscription {stripe_sub_id}")
