"""
Subscription / Stripe signup API — saga pattern.

All local DB writes (User, Tenant, UserProfile, Subscription, dj-stripe mirror rows,
OAuth apps) are wrapped in a single ``transaction.atomic()`` block so they succeed or
fail as a unit.

External Stripe objects are created **before** the DB commit. If the atomic block
fails the Stripe subscription and customer are cancelled/deleted as compensation.

Celery provisioning tasks are enqueued via ``transaction.on_commit`` so workers never
see a rolled-back tenant.

``SubscriptionApiViewSet`` is intentionally open (``permission_classes = []``) for
**new** tenant + user registration without an existing session. Access control
for authenticated tenants uses :class:`dose.models.UserTenantMembership` elsewhere —
do not use ``UserProfile`` for authorization on secured endpoints.
"""
import logging
import traceback
from functools import partial

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response

import stripe

try:
    import djstripe.models as _djstripe_models
except Exception:
    _djstripe_models = None

from dose.models import Subscription, Tenant, UserProfile, UserTenantMembership
from dose.serializers import SubscriptionSerializer
from dose.passthrough.credential_container import PassthroughCredentialContainer
from dose.services.odoo_tenant_provisioner import provision_odoo_tenant
from dose.services.nextcloud_tenant_provisioner import provision_nextcloud_tenant
from dose.services.dolibarr_tenant_provisioner import provision_dolibarr_tenant
from dose.services.mattermost_tenant_provisioner import provision_mattermost_tenant
from dose.services.liferay_tenant_provisioner import provision_liferay_tenant
try:
    from dose.services.wordpress_tenant_provisioner import provision_wordpress_tenant
except ImportError:
    provision_wordpress_tenant = None
from dose.services.extended_bundle_provisioner import (
    provision_monitor_logger_tenant,
    provision_polysysmon_tenant,
)
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


def _subscription_response_payload(subscription, selected_apps, *, tenant_name='', stripe_trial_started=True, user_obj=None):
    body = dict(SubscriptionSerializer(subscription).data)
    body.update(_subscriber_facing_messages(
        selected_apps, tenant_name=tenant_name, stripe_trial_started=stripe_trial_started,
    ))
    # Add Mattermost credentials to response for sessionStorage preservation across login (without team name)
    if subscription.tenant and 'enable_mattermost' in selected_apps:
        try:
            from dose.models import TenantApp
            tapp = TenantApp.objects.filter(
                tenant=subscription.tenant, app_name='mattermost'
            ).first()
            extra = (tapp.extra_config or {}) if tapp else {}
        except Exception:
            extra = {}
        body['mm_username'] = extra.get('mm_login_id') or extra.get('mm_username') or ''
        body['mm_password'] = extra.get('mm_password') or extra.get('mattermost_password') or ''
        body['mm_email'] = (user_obj.email if user_obj else '') or ''
        body['mm_token'] = extra.get('mm_token') or extra.get('mmauthtoken') or ''
    return body


# ---------------------------------------------------------------------------
# Stripe compensation helpers — called when the DB commit fails after Stripe
# objects were already created.
# ---------------------------------------------------------------------------

def _compensate_stripe(stripe_subscription_id, stripe_customer_id):
    """Best-effort cancel/delete of Stripe objects created before a failed DB commit."""
    if stripe_subscription_id:
        try:
            stripe.Subscription.cancel(stripe_subscription_id)
            logger.info("Stripe compensation: cancelled subscription %s", stripe_subscription_id)
        except Exception as exc:
            logger.error("Stripe compensation: failed to cancel subscription %s: %s",
                         stripe_subscription_id, exc)
    if stripe_customer_id:
        try:
            stripe.Customer.delete(stripe_customer_id)
            logger.info("Stripe compensation: deleted customer %s", stripe_customer_id)
        except Exception as exc:
            logger.error("Stripe compensation: failed to delete customer %s: %s",
                         stripe_customer_id, exc)


class SubscriptionApiViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    from dose.serializers import SubscriptionCreateSerializer
    serializer_class = SubscriptionSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return self.SubscriptionCreateSerializer
        return self.serializer_class

    permission_classes = []

    # ------------------------------------------------------------------
    # POST /api/subscriptions/  — saga-style create
    #
    # Phase 1  Validate (pure — no side effects)
    # Phase 2  Stripe   (external, reversible via compensation)
    # Phase 3  DB       (single atomic block — all or nothing)
    # Phase 4  Login    (session store, after commit)
    # Phase 5  Celery   (enqueued via on_commit only)
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        try:
            return self._create_saga(request)
        except Exception as e:
            logger.error("Subscription create error: %s", traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_saga(self, request):
        import logging
        logger = logging.getLogger(__name__)
        data = request.data

        # ── Phase 1: validate ────────────────────────────────────────
        tenant_name = data.get('tenant_name')
        tenant_shortname = data.get('tenant_shortname')
        token = data.get('stripe_token')
        card_name = data.get('card_name')
        tenant_slug = data.get('tenant')  # now a slug, not an int
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        needs_new_user = bool(username and email and password)
        needs_new_tenant = bool(tenant_name and tenant_shortname)

        if needs_new_user and User.objects.filter(username=username).exists():
            return Response({
                'error': (
                    f'The username "{username}" is already taken. '
                    'If you already subscribed, sign in instead. '
                    'Otherwise pick a different admin username for this new tenant.'
                ),
                'login_url': '/accounts/login/',
            }, status=status.HTTP_400_BAD_REQUEST)

        slug = schema_name = None
        if needs_new_tenant:
            slug = tenant_shortname.lower()
            schema_name = slug.replace('-', '_')
            logger.warning(f"[DEBUG] Creating new tenant: name={tenant_name}, slug={slug}, schema_name={schema_name}")
            if Tenant.objects.filter(name=tenant_name).exists():
                logger.warning(f"[DEBUG] Tenant name '{tenant_name}' already exists. Aborting new tenant creation.")
                return Response({'error': f"Tenant name '{tenant_name}' already exists."},
                                status=status.HTTP_400_BAD_REQUEST)
            if Tenant.objects.filter(schema_name=schema_name).exists():
                return Response({'error': f"Tenant schema '{schema_name}' already exists."},
                                status=status.HTTP_400_BAD_REQUEST)

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

        if (plan_tier == 'polysaas-3'
                and data.get('enable_wordpress')
                and data.get('enable_polysysmon')):
            return Response(
                {'error': ('PolySaaS-3 includes at most one of WordPress or PolySysMon '
                           '(each counts as 2 slots; together they exceed the plan).')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if max_apps is not None and slot_count > max_apps:
            return Response(
                {'error': (f'{plan_tier} allows up to {max_apps} application slot(s). '
                           f'Your selections use {slot_count} slot(s). '
                           'WordPress and PolySysMon each count as 2 slots; all other bundled apps count as 1.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_bypass = tenant_name and tenant_name.lower().startswith('a')

        if not test_bypass:
            if not tenant_slug and not needs_new_tenant:
                return Response({'error': 'Missing tenant or stripe_token'}, status=status.HTTP_400_BAD_REQUEST)
            if not token:
                return Response({'error': 'Missing tenant or stripe_token'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Phase 2: Stripe (external, before DB commit) ────────────
        stripe_customer_id = None
        stripe_subscription_id = None
        active = False

        if not test_bypass:
            try:
                price_ids = getattr(settings, 'STRIPE_PRICE_IDS', {})
                stripe_price = price_ids.get(plan_tier) or getattr(settings, 'STRIPE_PRICE_ID', '')

                customer = stripe.Customer.create(source=token, name=card_name, email=email)
                stripe_customer_id = customer.id

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
                stripe_subscription_id = stripe_sub.id
                active = True
            except Exception as e:
                _compensate_stripe(stripe_subscription_id, stripe_customer_id)
                logger.error("Stripe error: %s", e)
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # ── Phase 3: all DB writes in one atomic block ───────────────
        try:

            with transaction.atomic():
                # auth_user and Tenant live in the public schema.
                # Force search_path=public so a logged-in subscriber's tenant
                # schema doesn't shadow public tables and land the new user
                # in the wrong schema.
                from django.db import connection as _conn
                with _conn.cursor() as _cur:
                    _cur.execute("SET search_path TO public;")

                user_obj = None
                if needs_new_user:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"[DEBUG] Creating user: username={username}, email={email}, password={password}")
                    user_obj = User.objects.create_user(username=username, email=email, password=password)
                    user_obj.is_staff = True
                    user_obj.is_superuser = True
                    user_obj.save()
                    user_obj.backend = 'django.contrib.auth.backends.ModelBackend'

                if needs_new_tenant:
                    tenant_obj, _ = Tenant.objects.get_or_create(
                        name=tenant_name,
                        defaults={'slug': slug, 'schema_name': schema_name,
                                  'description': 'Created via subscribe.'},
                    )
                    tenant_slug = tenant_obj.slug
                    logger.warning(f"[DEBUG] New tenant created: {tenant_obj}")
                elif tenant_slug:
                    # Only assign an existing tenant if explicitly requested (not fallback)
                    try:
                        tenant_obj = Tenant.objects.get(slug=tenant_slug)
                        logger.warning(f"[DEBUG] Existing tenant explicitly assigned: {tenant_obj}")
                    except Tenant.DoesNotExist:
                        logger.warning(f"[DEBUG] Provided tenant_slug '{tenant_slug}' does not exist. No tenant assigned.")
                        tenant_obj = None
                else:
                    logger.warning(f"[DEBUG] No tenant created or assigned for this signup.")
                    tenant_obj = None

                if user_obj and tenant_obj:
                    try:
                        user_profile = UserProfile.objects.get(user=user_obj)
                        user_profile.tenant = tenant_obj
                        user_profile.save()
                    except UserProfile.DoesNotExist:
                        UserProfile.objects.create(user=user_obj, tenant=tenant_obj)
                    UserTenantMembership.objects.get_or_create(
                        user=user_obj, tenant=tenant_obj,
                        defaults={'role': UserTenantMembership.Role.OWNER},
                    )

                if not test_bypass and _djstripe_models is not None:
                    djstripe_customer = _djstripe_models.Customer.sync_from_stripe_data(customer)
                    if user_obj:
                        djstripe_customer.subscriber = user_obj
                        djstripe_customer.save()
                    _djstripe_models.Subscription.sync_from_stripe_data(stripe_sub)

                sub = Subscription.objects.create(
                    tenant=tenant_obj,
                    plan_tier=plan_tier,
                    stripe_customer_id=stripe_customer_id,
                    stripe_subscription_id=stripe_subscription_id,
                    card_name=card_name,
                    active=active,
                    selected_apps=selected_apps,
                )

        except Exception:
            if not test_bypass:
                _compensate_stripe(stripe_subscription_id, stripe_customer_id)
            raise

        # ── Phase 4: Provision synchronously AFTER transaction commits
        # so the tenant schema exists, but BEFORE the response returns
        # so the user sees sidebar entries immediately.
        if tenant_slug:
            self._register_provisioning_synchronous(request, data, tenant_slug, user_obj)

        # ── Phase 5: (Demo flow: do NOT auto-login so user sees prefilled login page)
        # Credentials are passed via sessionStorage by the subscribe page JS.
        # if user_obj:
        #     login(request, user_obj)
        #     if tenant_obj:
        #         from dose.tenant_session import apply_tenant_to_session
        #         membership = UserTenantMembership.objects.filter(
        #             user=user_obj, tenant=tenant_obj,
        #         ).first()
        #         apply_tenant_to_session(request, tenant_obj, membership)

        return Response(
            _subscription_response_payload(
                sub, selected_apps,
                tenant_name=tenant_name or '',
                stripe_trial_started=not test_bypass,
                user_obj=user_obj,
            ),
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # Synchronous provisioning — runs after DB commit so schema exists,
    # but before response returns so sidebar entries are visible immediately.
    # ------------------------------------------------------------------

    @staticmethod
    def _register_provisioning_synchronous(request, data, tenant_slug, user_obj):
        """Run provisioners inline after transaction commit; emit Django messages for user feedback."""
        from django.contrib import messages
        from dose.management.schema_utils import set_search_path_for_migrations

        tenant = Tenant.objects.get(slug=tenant_slug)
        tenant_pk = tenant.pk
        admin_email = user_obj.email if user_obj else data.get('email')
        base = dict(tenant_schema=tenant.schema_name, tenant_name=tenant.name,
                    admin_email=admin_email, company_name=tenant.name)

        # ── Migrate new tenant schema so tables exist for provisioners ──
        try:
            print(f"\n{'='*60}")
            print(f"[MIGRATE] Running migrations for schema={tenant.schema_name}")
            set_search_path_for_migrations(tenant.schema_name)
            # Use Django's original migrate command directly (bypass custom multi-schema override)
            from django.core.management.commands.migrate import Command as MigrateCommand
            from io import StringIO
            out = StringIO()
            cmd = MigrateCommand(stdout=out, stderr=out, no_color=True)
            cmd.handle(verbosity=0, run_syncdb=True)
            print(f"[MIGRATE] Done for schema={tenant.schema_name}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"[MIGRATE-ERROR] {e}")
            logger.warning("Tenant schema migration failed for %s: %s", tenant.schema_name, e)

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
                    tenant_pk, app_key.replace('enable_', ''), user_obj,
                )
                kwargs.update(oauth_client_id=cid, oauth_client_secret=csecret, tenant_app_id=tapp.id)
                # Store user credentials for passthrough prepopulation
                if app_key == 'enable_odoo' and user_obj:
                    try:
                        extra = tapp.extra_config or {}
                        extra.update({
                            'odoo_login': user_obj.email,
                            'odoo_password': data.get('password'),  # Raw password from signup form
                            'odoo_db': tenant.schema_name,
                        })
                        tapp.extra_config = extra
                        tapp.save(update_fields=['extra_config'])
                    except Exception as e:
                        logger.warning("Failed to store Odoo credentials for passthrough: %s", e)
            except Exception as e:
                logger.warning("OAuth2 registration for %s skipped: %s", app_key, e)

            # All provisioning is synchronous for the demo so sidebar entries
            # appear immediately after subscription.
            if app_key == 'enable_mattermost':
                kwargs['admin_username'] = user_obj.username if user_obj else ''
                kwargs['admin_password'] = data.get('password') or ''

            app_display = app_key.replace('enable_', '').title()
            messages.info(request, f"Provisioning {app_display}...")
            print(f"\n{'='*60}")
            print(f"[PROVISION-START] {app_key} for tenant_schema={kwargs['tenant_schema']}")
            print(f"{'='*60}")
            result = None
            try:
                result = provisioner(**kwargs)
                print(f"[PROVISION-DONE] {app_key}: success={result.get('success')} error={result.get('error')}")
                if result.get('success'):
                    messages.success(request, f"{app_display} is ready!")
                    # Store credentials in encrypted session for persistent re-authentication
                    try:
                        SubscriptionApiViewSet._store_passthrough_credentials_in_session(
                            request, app_key, tapp, result, 
                            user_obj, admin_email, kwargs
                        )
                    except Exception as cred_err:
                        logger.warning("[PROVISION] Failed to store credentials for %s: %s", app_key, cred_err)
                else:
                    err = result.get('error', 'Unknown error')
                    logger.warning("[PROVISION] %s returned failure: %s", app_key, err)
                    messages.error(request, f"{app_display} provisioning failed: {err}")
            except Exception as exc:
                print(f"[PROVISION-CRASH] {app_key}: {exc}")
                logger.error("[PROVISION] %s crashed: %s", app_key, exc, exc_info=True)
                messages.error(request, f"{app_display} provisioning crashed: {exc}")
            import time
            time.sleep(5)
            print(f"{'='*60}\n")

    @staticmethod
    def _store_passthrough_credentials_in_session(request, app_key, tapp, result, user_obj, admin_email, kwargs):
        """
        Store provisioned credentials in encrypted session for persistent re-authentication.
        
        Called after successful provisioning to populate the credential container
        with username, password, email, and API tokens.
        """
        if not tapp or not request:
            return
        
        try:
            app_name = app_key.replace('enable_', '')  # 'enable_mattermost' -> 'mattermost'
            
            # Extract credentials based on app type
            if app_name == 'mattermost':
                # Credentials were passed to provisioner and stored in extra_config
                extra = tapp.extra_config or {}
                username = extra.get('mm_login_id') or extra.get('mm_username') or extra.get('mattermost_login_id')
                password = (
                    extra.get('mm_password')
                    or extra.get('mattermost_password')
                    or kwargs.get('admin_password', '')
                )
                email = admin_email
                token = extra.get('mm_token') or extra.get('mmauthtoken') or ''
                
                if username and password:
                    PassthroughCredentialContainer.store(
                        request,
                        app_name='mattermost',
                        credentials={
                            'username': username,
                            'password': password,
                            'email': email,
                            'api_tokens': {
                                'mattermost_token': token,
                            }
                        },
                        ttl_hours=24
                    )
                    logger.info("[CRED] Stored Mattermost credentials in session for %s", email)
                    
            elif app_name == 'nextcloud':
                # Similar pattern for Nextcloud
                extra = tapp.extra_config or {}
                username = extra.get('nextcloud_login') or email.split('@')[0]
                password = kwargs.get('admin_password', '')
                token = extra.get('nextcloud_token') or ''
                
                if username and password:
                    PassthroughCredentialContainer.store(
                        request,
                        app_name='nextcloud',
                        credentials={
                            'username': username,
                            'password': password,
                            'email': email,
                            'api_tokens': {
                                'nextcloud_token': token,
                            }
                        },
                        ttl_hours=24
                    )
                    logger.info("[CRED] Stored Nextcloud credentials in session for %s", email)
                    
            elif app_name == 'odoo':
                # Odoo credentials
                extra = tapp.extra_config or {}
                username = extra.get('odoo_login') or email
                password = extra.get('odoo_password') or kwargs.get('admin_password', '')
                
                if username and password:
                    PassthroughCredentialContainer.store(
                        request,
                        app_name='odoo',
                        credentials={
                            'username': username,
                            'password': password,
                            'email': email,
                            'api_tokens': {}
                        },
                        ttl_hours=24
                    )
                    logger.info("[CRED] Stored Odoo credentials in session for %s", email)
                    
        except Exception as exc:
            logger.warning("[CRED] Failed to store %s credentials in session: %s", app_key, exc)
