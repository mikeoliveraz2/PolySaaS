from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


_CENT = Decimal('0.01')
_ZERO = Decimal('0.00')

# Assumption: contiguous gates are intended here: 1-10, 11-20, 21+.
USER_DISCOUNT_BRACKETS = (
    (1, 10, Decimal('0.10')),
    (11, 20, Decimal('0.20')),
    (21, None, Decimal('0.30')),
)


def _money(value):
    return Decimal(str(value)).quantize(_CENT, rounding=ROUND_HALF_UP)


def normalize_user_count(user_count):
    try:
        count = int(user_count)
    except (TypeError, ValueError):
        return 1
    return max(1, count)


def get_plan_base_price(plan_tier):
    plan_prices = getattr(settings, 'PLAN_PRICES', {})
    return _money(plan_prices.get(plan_tier, 26.00))


def get_volume_discount_rate(user_count):
    count = normalize_user_count(user_count)
    for minimum, maximum, rate in USER_DISCOUNT_BRACKETS:
        if count >= minimum and (maximum is None or count <= maximum):
            return rate
    return Decimal('0.10')


def get_volume_discount_percent(user_count):
    return int(get_volume_discount_rate(user_count) * 100)


def build_subscription_pricing(plan_tier, user_count=1, promo_code=None):
    count = normalize_user_count(user_count)
    base_price_per_user = get_plan_base_price(plan_tier)
    volume_discount_rate = get_volume_discount_rate(count)
    discounted_price_per_user = _money(base_price_per_user * (Decimal('1.00') - volume_discount_rate))
    monthly_subtotal = _money(discounted_price_per_user * count)

    promo_discount_amount = _ZERO
    if promo_code is not None:
        promo_discount_amount = _money(promo_code.calculate_discount(monthly_subtotal))
        if promo_discount_amount > monthly_subtotal:
            promo_discount_amount = monthly_subtotal

    estimated_monthly_total = _money(monthly_subtotal - promo_discount_amount)
    effective_price_per_user = _money(estimated_monthly_total / count)

    return {
        'plan_tier': plan_tier,
        'user_count': count,
        'base_price_per_user': base_price_per_user,
        'volume_discount_rate': volume_discount_rate,
        'volume_discount_percent': int(volume_discount_rate * 100),
        'discounted_price_per_user': discounted_price_per_user,
        'monthly_subtotal': monthly_subtotal,
        'promo_discount_amount': promo_discount_amount,
        'estimated_monthly_total': estimated_monthly_total,
        'effective_price_per_user': effective_price_per_user,
    }


def pricing_payload(pricing):
    return {
        'plan_tier': pricing['plan_tier'],
        'user_count': pricing['user_count'],
        'base_price_per_user': float(pricing['base_price_per_user']),
        'volume_discount_percent': pricing['volume_discount_percent'],
        'discounted_price_per_user': float(pricing['discounted_price_per_user']),
        'monthly_subtotal': float(pricing['monthly_subtotal']),
        'promo_discount_amount': float(pricing['promo_discount_amount']),
        'estimated_monthly_total': float(pricing['estimated_monthly_total']),
        'effective_price_per_user': float(pricing['effective_price_per_user']),
    }


def promo_explanation_lines(promo_code, pricing):
    count = pricing['user_count']
    users_label = 'user' if count == 1 else 'users'
    discount_summary = (
        f'{pricing["volume_discount_percent"]}% volume discount is already applied for '
        f'{count} {users_label}.'
    )
    rate_line = (
        f'List price is ${pricing["base_price_per_user"]:.2f}/user/month and your billed rate '
        f'before the promo is ${pricing["discounted_price_per_user"]:.2f}/user/month.'
    )
    promo_line = (
        f'This promo reduces the discounted monthly total by ${pricing["promo_discount_amount"]:.2f}, '
        f'bringing the estimate to ${pricing["estimated_monthly_total"]:.2f}/month '
        f'(${pricing["effective_price_per_user"]:.2f}/user/month) before storage.'
    )

    if getattr(promo_code, 'discount_type', '') == 'percentage':
        promo_line = (
            f'This promo takes {promo_code.discount_value}% off the discounted monthly total, '
            f'bringing the estimate to ${pricing["estimated_monthly_total"]:.2f}/month '
            f'(${pricing["effective_price_per_user"]:.2f}/user/month) before storage.'
        )

    return [
        (promo_code.description or f'Promo code {promo_code.code} applied.').strip(),
        discount_summary,
        rate_line,
        promo_line,
        'Tenant admins can add more seats later; the same volume pricing schedule will apply.',
    ]