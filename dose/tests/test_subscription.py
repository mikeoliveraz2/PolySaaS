from decimal import Decimal

from django.test import SimpleTestCase

from dose.models import PromoCode
from dose.services.subscription_pricing import build_subscription_pricing, get_volume_discount_percent


class SubscriptionPricingTests(SimpleTestCase):
	def test_volume_discount_brackets(self):
		self.assertEqual(get_volume_discount_percent(1), 10)
		self.assertEqual(get_volume_discount_percent(10), 10)
		self.assertEqual(get_volume_discount_percent(11), 20)
		self.assertEqual(get_volume_discount_percent(20), 20)
		self.assertEqual(get_volume_discount_percent(21), 30)

	def test_monthly_total_uses_seat_count_and_volume_discount(self):
		pricing = build_subscription_pricing('polysaas-3', user_count=3)
		self.assertEqual(pricing['discounted_price_per_user'], Decimal('44.10'))
		self.assertEqual(pricing['monthly_subtotal'], Decimal('132.30'))
		self.assertEqual(pricing['estimated_monthly_total'], Decimal('132.30'))

	def test_percentage_promo_applies_to_discounted_monthly_total(self):
		promo = PromoCode(code='HALF', discount_type='percentage', discount_value=Decimal('50.00'))
		pricing = build_subscription_pricing('polysaas-3', user_count=3, promo_code=promo)
		self.assertEqual(pricing['promo_discount_amount'], Decimal('66.15'))
		self.assertEqual(pricing['estimated_monthly_total'], Decimal('66.15'))
		self.assertEqual(pricing['effective_price_per_user'], Decimal('22.05'))
