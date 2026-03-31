import logging
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

import djstripe.models

from dose.models import Subscription
from dose.utils import get_current_tenant

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

TIER_ORDER = ['starter', 'team', 'unlimited']


def _get_subscription_for_user(request):
    tenant = get_current_tenant(request)
    if not tenant:
        return None, None
    try:
        sub = Subscription.objects.get(tenant=tenant)
        return tenant, sub
    except Subscription.DoesNotExist:
        return tenant, None


@login_required
def upgrade_view(request):
    tenant, sub = _get_subscription_for_user(request)

    if not sub:
        messages.warning(request, 'No active subscription found. Please subscribe first.')
        return redirect('dose:subscribe')

    current_idx = TIER_ORDER.index(sub.plan_tier) if sub.plan_tier in TIER_ORDER else 0
    plan_prices = getattr(settings, 'PLAN_PRICES', {})
    plan_max_users = getattr(settings, 'PLAN_MAX_USERS', {})

    plans = []
    for tier in TIER_ORDER:
        tier_idx = TIER_ORDER.index(tier)
        plans.append({
            'tier': tier,
            'label': sub.get_plan_tier_display() if tier == sub.plan_tier else dict(Subscription.PLAN_TIER_CHOICES).get(tier, tier),
            'price': plan_prices.get(tier, 0),
            'max_users': plan_max_users.get(tier),
            'is_current': tier == sub.plan_tier,
            'is_upgrade': tier_idx > current_idx,
            'is_downgrade': tier_idx < current_idx,
        })

    if request.method == 'POST':
        new_tier = request.POST.get('new_tier')
        if new_tier not in TIER_ORDER:
            messages.error(request, 'Invalid plan selected.')
            return redirect('dose:upgrade')

        new_idx = TIER_ORDER.index(new_tier)
        if new_idx <= current_idx:
            messages.error(request, 'You can only upgrade to a higher plan.')
            return redirect('dose:upgrade')

        price_ids = getattr(settings, 'STRIPE_PRICE_IDS', {})
        new_price_id = price_ids.get(new_tier)
        if not new_price_id:
            messages.error(request, 'This plan is not yet available. Please contact support.')
            return redirect('dose:upgrade')

        if not sub.stripe_subscription_id:
            messages.error(request, 'No Stripe subscription found. Please contact support.')
            return redirect('dose:upgrade')

        try:
            stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
            current_item_id = stripe_sub['items']['data'][0].id

            modified = stripe.Subscription.modify(
                sub.stripe_subscription_id,
                items=[{'id': current_item_id, 'price': new_price_id}],
                proration_behavior='create_prorations',
            )
            djstripe.models.Subscription.sync_from_stripe_data(modified)

            old_tier = sub.plan_tier
            sub.plan_tier = new_tier
            sub.save()

            logger.info(f"Subscription upgraded: tenant={tenant.name}, {old_tier} -> {new_tier}")
            messages.success(
                request,
                f'Successfully upgraded to {dict(Subscription.PLAN_TIER_CHOICES).get(new_tier, new_tier)}! '
                f'Prorated charges have been applied to your next invoice.'
            )
            return redirect('dose:upgrade')

        except stripe.error.CardError as e:
            logger.error(f"Card error during upgrade: {e}")
            messages.error(request, f'Payment failed: {e.user_message}')
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during upgrade: {e}")
            messages.error(request, 'An error occurred processing your upgrade. Please try again or contact support.')
        except Exception as e:
            logger.error(f"Unexpected error during upgrade: {e}")
            messages.error(request, 'An unexpected error occurred. Please contact support.')

        return redirect('dose:upgrade')

    return render(request, 'dose/upgrade.html', {
        'subscription': sub,
        'plans': plans,
        'tenant': tenant,
    })
