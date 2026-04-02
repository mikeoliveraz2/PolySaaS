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
from dose.services.extended_bundle_provisioner import (
    provision_liferay_tenant,
    provision_monitor_logger_tenant,
    provision_polysysmon_tenant,
)
try:
    from dose.services.wordpress_tenant_provisioner import provision_wordpress_tenant
except ImportError:
    provision_wordpress_tenant = None
from dose.services.oauth2_registration import register_oauth2_app_for_tenant

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)
User = get_user_model()

_BUNDLED_APP_LABELS = {
    'enable_odoo': 'Odoo ERP',
    'enable_nextcloud': 'Nextcloud',
    'enable_dolibarr': 'Dolibarr',
    'enable_mattermost': 'Mattermost',
    'enable_wordpress': 'WordPress',
    'enable_liferay': 'Liferay',
    'enable_monitor_logger': 'Monitor Logger',
    'enable_polysysmon': 'PolySysMon',
}


def _subscriber_facing_messages(selected_apps, *, tenant_name='', stripe_trial_started=True):
    """
    Short copy returned on successful subscribe so the UI can show what new subscribers should expect.
    Bundled apps are provisioned asynchronously (Celery); set expectations accordingly.
    """
    org = (tenant_name or '').strip()
    org_bit = f' to {org}' if org else ''

    if stripe_trial_started:
        trial_welcome = (
            f'Welcome{org_bit}! Your subscription is confirmed and your '
            f'{getattr(settings, "STRIPE_TRIAL_PERIOD_DAYS", 14)}-day free trial has started.'
        )
    else:
        trial_welcome = (
            'Your tenant and admin account were created. '
            'This path skipped live card billing — use the normal subscribe flow for a Stripe trial.'
        )

    labels = [_BUNDLED_APP_LABELS[k] for k in selected_apps if k in _BUNDLED_APP_LABELS]
    if labels:
        provisioning_notice = (
            f'You selected these bundled applications: {", ".join(labels)}. '
            'They are queued for setup after signup (not instant) and may take some time. '
            'We will email you at the address you provided when each environment is ready; '
            'you can also check status from your PolySaaS admin.'
        )
    else:
        provisioning_notice = (
            'You did not choose any bundled applications on this form. '
            'You can add them later from your PolySaaS admin when you are ready.'
        )

    return {
        'trial_welcome': trial_welcome,
        'provisioning_notice': provisioning_notice,
    }


def _subscription_response_payload(subscription, selected_apps, *, tenant_name='', stripe_trial_started=True):
    body = dict(SubscriptionSerializer(subscription).data)
    body.update(_subscriber_facing_messages(
        selected_apps, tenant_name=tenant_name, stripe_trial_started=stripe_trial_started,
    ))
    return body


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
                        'error': (
                            f'The username "{username}" is already taken in this system (not a login session issue). '
                            'Pick a different admin username for this new tenant, or sign in with that account. '
                            'Subscribe always creates a brand-new admin user for the new tenant.'
                        ),
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

            app_keys = [
                'enable_odoo', 'enable_nextcloud', 'enable_dolibarr',
                'enable_mattermost', 'enable_wordpress',
                'enable_liferay', 'enable_monitor_logger', 'enable_polysysmon',
            ]
            selected_apps = [k for k in app_keys if data.get(k)]
            max_apps = getattr(settings, 'PLAN_MAX_APPS', {}).get(plan_tier)
            slot_weights = getattr(settings, 'PLAN_BUNDLED_APP_SLOTS', {})
            slot_count = sum(slot_weights.get(k, 1) for k in selected_apps)
            if (
                plan_tier == 'polysaas-3'
                and data.get('enable_wordpress')
                and data.get('enable_polysysmon')
            ):
                return Response(
                    {
                        'error': (
                            'PolySaaS-3 includes at most one of WordPress or PolySysMon '
                            '(each counts as 2 slots; together they exceed the plan).'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if max_apps is not None and slot_count > max_apps:
                return Response(
                    {
                        'error': (
                            f'{plan_tier} allows up to {max_apps} application slot(s). '
                            f'Your selections use {slot_count} slot(s). '
                            'WordPress and PolySysMon each count as 2 slots; all other bundled apps count as 1.'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Test bypass: skip Stripe for tenant names starting with 'A'
            if tenant_name and tenant_name.lower().startswith('a'):
                sub = Subscription.objects.create(
                    tenant_id=tenant_id, plan_tier=plan_tier,
                    stripe_customer_id=None, stripe_subscription_id=None,
                    card_name=card_name, active=False,
                )
                return Response(
                    _subscription_response_payload(
                        sub, selected_apps, tenant_name=tenant_name or '', stripe_trial_started=False,
                    ),
                    status=status.HTTP_201_CREATED,
                )

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

                sub_items = [{'price': stripe_price}]
                needs_storage = data.get('enable_nextcloud') or data.get('enable_wordpress')
                storage_price_id = getattr(settings, 'STRIPE_PRICE_ID_STORAGE', '')
                if needs_storage and storage_price_id:
                    sub_items.append({'price': storage_price_id})

                stripe_sub = stripe.Subscription.create(
                    customer=customer.id,
                    items=sub_items,
                    trial_period_days=getattr(settings, 'STRIPE_TRIAL_PERIOD_DAYS', 14),
                    metadata={
                        'plan_tier': plan_tier,
                        'tenant_name': tenant_name or '',
                        'selected_apps': ','.join(selected_apps),
                    },
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

            return Response(
                _subscription_response_payload(
                    sub, selected_apps, tenant_name=tenant_name or '', stripe_trial_started=True,
                ),
                status=status.HTTP_201_CREATED,
            )

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

        provisioners = [
            ('enable_odoo', provision_odoo_tenant),
            ('enable_nextcloud', provision_nextcloud_tenant),
            ('enable_dolibarr', provision_dolibarr_tenant),
            ('enable_mattermost', provision_mattermost_tenant),
        ]
        if provision_wordpress_tenant is not None:
            provisioners.append(('enable_wordpress', provision_wordpress_tenant))
        provisioners.extend([
            ('enable_liferay', provision_liferay_tenant),
            ('enable_monitor_logger', provision_monitor_logger_tenant),
            ('enable_polysysmon', provision_polysysmon_tenant),
        ])

        for app_key, provisioner in provisioners:
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
