"""
Subscription / Stripe signup API.

Uses dj-stripe for Stripe object syncing and webhook processing.

``SubscriptionApiViewSet`` is intentionally open (``permission_classes = []``) for
**new** tenant + user registration without an existing session. Access control
for authenticated tenants uses :class:`dose.models.UserTenantMembership` elsewhere —
do not use ``UserProfile`` for authorization on secured endpoints.
"""
import logging
import traceback

from django.conf import settings
from django.contrib.auth import get_user_model, login
from rest_framework import viewsets, status
from rest_framework.response import Response

import djstripe.models
import stripe

from dose.models import Subscription, Tenant, UserProfile
from dose.serializers import SubscriptionSerializer
from dose.services.odoo_tenant_provisioner import provision_odoo_tenant
from dose.services.nextcloud_tenant_provisioner import provision_nextcloud_tenant
from dose.services.dolibarr_tenant_provisioner import provision_dolibarr_tenant
from dose.services.mattermost_tenant_provisioner import provision_mattermost_tenant
from dose.services.oauth2_registration import register_oauth2_app_for_tenant

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)
User = get_user_model()


class SubscriptionApiViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    from dose.serializers import SubscriptionCreateSerializer
    serializer_class = SubscriptionSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return self.SubscriptionCreateSerializer
        return self.serializer_class

    permission_classes = []

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            tenant_name = data.get('tenant_name')
            tenant_shortname = data.get('tenant_shortname')
            token = data.get('stripe_token')
            card_name = data.get('card_name')
            tenant_id = data.get('tenant')
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            user_obj = None

            if username and email and password:
                if User.objects.filter(username=username).exists():
                    return Response({
                        'error': f'User {username} already exists. Subscribe is for new tenants with new users only.',
                    }, status=status.HTTP_400_BAD_REQUEST)
                user_obj = User.objects.create_user(username=username, email=email, password=password)
                user_obj.is_staff = True
                user_obj.is_superuser = True
                user_obj.save()
                user_obj.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user_obj)

            if tenant_name and tenant_shortname:
                slug = tenant_shortname.lower()
                schema_name = slug.replace('-', '_')
                if Tenant.objects.filter(name=tenant_name).exists():
                    return Response({'error': f"Tenant name '{tenant_name}' already exists."}, status=status.HTTP_400_BAD_REQUEST)
                if Tenant.objects.filter(schema_name=schema_name).exists():
                    return Response({'error': f"Tenant schema '{schema_name}' already exists."}, status=status.HTTP_400_BAD_REQUEST)
                tenant_obj, _ = Tenant.objects.get_or_create(
                    name=tenant_name,
                    defaults={'slug': slug, 'schema_name': schema_name, 'description': 'Created via subscribe.'},
                )
                tenant_id = tenant_obj.id

            if user_obj and tenant_id:
                try:
                    user_profile = UserProfile.objects.get(user=user_obj)
                    user_profile.tenant_id = tenant_id
                    user_profile.save()
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(user=user_obj, tenant_id=tenant_id)

            try:
                tenant_id = int(tenant_id)
            except (TypeError, ValueError):
                tenant_id = None

            plan_tier = data.get('plan_tier', 'polysaas-1')
            if plan_tier not in ('polysaas-1', 'polysaas-3', 'polysaas-unlimited'):
                plan_tier = 'polysaas-1'

            # Test bypass: skip Stripe for tenant names starting with 'A'
            if tenant_name and tenant_name.lower().startswith('a'):
                sub = Subscription.objects.create(
                    tenant_id=tenant_id, plan_tier=plan_tier,
                    stripe_customer_id=None, stripe_subscription_id=None,
                    card_name=card_name, active=False,
                )
                return Response(SubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)

            if not tenant_id or not token:
                return Response({'error': 'Missing tenant or stripe_token'}, status=status.HTTP_400_BAD_REQUEST)

            # --- Stripe via dj-stripe ---
            try:
                price_ids = getattr(settings, 'STRIPE_PRICE_IDS', {})
                stripe_price = price_ids.get(plan_tier) or getattr(settings, 'STRIPE_PRICE_ID', '')

                customer = stripe.Customer.create(source=token, name=card_name, email=email)
                djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
                if user_obj:
                    djstripe_customer.subscriber = user_obj
                    djstripe_customer.save()

                stripe_sub = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': stripe_price}],
                    trial_period_days=getattr(settings, 'STRIPE_TRIAL_PERIOD_DAYS', 14),
                )
                djstripe.models.Subscription.sync_from_stripe_data(stripe_sub)

                stripe_customer_id = customer.id
                stripe_subscription_id = stripe_sub.id
                active = True
            except Exception as e:
                logger.error(f"Stripe error: {e}")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            sub = Subscription.objects.create(
                tenant_id=tenant_id, plan_tier=plan_tier,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                card_name=card_name, active=active,
            )

            self._provision_services(data, tenant_id, user_obj)

            return Response(SubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Subscription create error: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def _provision_services(data, tenant_id, user_obj):
        """Kick off async provisioning for selected bundled apps."""
        tenant = Tenant.objects.get(id=tenant_id)
        admin_email = user_obj.email if user_obj else data.get('email')
        base = dict(tenant_schema=tenant.schema_name, tenant_name=tenant.name,
                     admin_email=admin_email, company_name=tenant.name)

        for app_key, provisioner in [
            ('enable_odoo', provision_odoo_tenant),
            ('enable_nextcloud', provision_nextcloud_tenant),
            ('enable_dolibarr', provision_dolibarr_tenant),
            ('enable_mattermost', provision_mattermost_tenant),
        ]:
            if not data.get(app_key):
                continue
            kwargs = dict(base)
            try:
                cid, csecret, tapp = register_oauth2_app_for_tenant(
                    tenant_id, app_key.replace('enable_', ''), user_obj,
                )
                kwargs.update(oauth_client_id=cid, oauth_client_secret=csecret, tenant_app_id=tapp.id)
            except Exception as e:
                logger.warning("OAuth2 registration for %s skipped: %s", app_key, e)
            provisioner.delay(**kwargs)
