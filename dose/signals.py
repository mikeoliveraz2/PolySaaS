from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login, social_account_added
import logging

logger = logging.getLogger(__name__)


@receiver(pre_social_login)
def log_pre_social_login(sender, request, sociallogin, **kwargs):
    """Log when OAuth login is about to happen"""
    logger.info("=" * 80)
    logger.info("PRE_SOCIAL_LOGIN signal received")
    logger.info(f"  User: {sociallogin.user}")
    logger.info(f"  Provider: {sociallogin.account.provider}")
    logger.info(f"  UID: {sociallogin.account.uid}")
    logger.info(f"  Is existing: {sociallogin.is_existing}")
    logger.info(f"  Token exists: {hasattr(sociallogin, 'token') and sociallogin.token is not None}")
    if hasattr(sociallogin, 'token') and sociallogin.token:
        logger.info(f"  Access token: {sociallogin.token.token[:20] if sociallogin.token.token else 'None'}...")
    logger.info("=" * 80)


@receiver(social_account_added)
def log_social_account_added(sender, request, sociallogin, **kwargs):
    """Log when social account is added and ensure tokens are saved"""
    logger.info("=" * 80)
    logger.info("SOCIAL_ACCOUNT_ADDED signal received")
    logger.info(f"  User: {sociallogin.user}")
    logger.info(f"  Provider: {sociallogin.account.provider}")
    logger.info(f"  UID: {sociallogin.account.uid}")
    logger.info(f"  Is existing: {sociallogin.is_existing}")

    # CRITICAL: Ensure token is saved for existing users (process=connect)
    # For existing users, django-allauth might not call save_user, so we need to save the token here
    if hasattr(sociallogin, 'token') and sociallogin.token:
        try:
            from allauth.socialaccount.models import SocialToken
            # Check if token already exists
            existing_token = SocialToken.objects.filter(
                account=sociallogin.account
            ).first()

            if existing_token:
                # Update existing token
                existing_token.token = sociallogin.token.token
                existing_token.token_secret = sociallogin.token.token_secret
                existing_token.expires_at = sociallogin.token.expires_at
                existing_token.save()
                logger.info(f"[SIGNAL] ✅ Updated existing token for user {sociallogin.user.username}")
            else:
                # Create new token
                SocialToken.objects.create(
                    account=sociallogin.account,
                    token=sociallogin.token.token,
                    token_secret=sociallogin.token.token_secret,
                    expires_at=sociallogin.token.expires_at
                )
                logger.info(f"[SIGNAL] ✅ Created new token for user {sociallogin.user.username}")

            # Verify it was saved
            saved_token = SocialToken.objects.filter(account=sociallogin.account).first()
            if saved_token:
                logger.info(f"[SIGNAL] ✅ Token verified in database: {saved_token.token[:20]}...")
            else:
                logger.error(f"[SIGNAL] ❌ Token NOT found in database after save attempt!")
        except Exception as e:
            logger.error(f"[SIGNAL] ❌ Error saving token: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.warning(f"[SIGNAL] ⚠️ No token in sociallogin for user {sociallogin.user.username}")

    # Allowlist promotion: Google email may not be on User.email yet; match provider bundle too.
    try:
        from dose.adapters import _maybe_promote_superuser_from_settings

        _maybe_promote_superuser_from_settings(sociallogin.user, sociallogin)
    except Exception as e:
        logger.warning("[SIGNAL] superuser allowlist promotion skipped: %s", e)

    logger.info("=" * 80)


@receiver(user_logged_in)
def set_tenant_in_session(sender, user, request, **kwargs):
    try:
        from dose.models import UserTenantMembership
        from dose.tenant_session import apply_tenant_to_session

        # Try to get UserProfile and tenant
        profile = getattr(user, 'userprofile', None)
        if profile and profile.tenant:
            tenant = profile.tenant
            m = UserTenantMembership.objects.filter(user=user, tenant=tenant).first()
            if not m:
                m, _ = UserTenantMembership.objects.get_or_create(
                    user=user,
                    tenant=tenant,
                    defaults={"role": UserTenantMembership.Role.MEMBER},
                )
            apply_tenant_to_session(request, tenant, m)
            print(f"set_tenant_in_session: Set session for user {user.username} with tenant {tenant.name} (Slug: {tenant.slug})")
        else:
            print(
                f"set_tenant_in_session: No UserProfile/tenant for user {user.username}; "
                f"session left without tenant (assign a tenant or create a Tenant row)"
            )
    except Exception as e:
        print(f"set_tenant_in_session: Error setting tenant session for user {user.username}: {e}")


@receiver(user_logged_in)
def promote_superuser_from_allowlist_on_login(sender, user, request, **kwargs):
    """Re-check allowlist after login (covers paths where adapter hooks did not see provider email)."""
    try:
        from dose.adapters import _maybe_promote_superuser_from_settings

        _maybe_promote_superuser_from_settings(user, None)
    except Exception as e:
        logger.warning("[SIGNAL] superuser allowlist on user_logged_in skipped: %s", e)


# --- Theme persistence: UserProfile signals ---
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from dose.models import UserProfile, UserTenantMembership

@receiver(post_save, sender=UserProfile)
def sync_membership_from_user_profile(sender, instance, **kwargs):
    """Keep user_tenant_memberships aligned when UserProfile.tenant changes."""
    UserTenantMembership.objects.get_or_create(
        user=instance.user,
        tenant=instance.tenant,
        defaults={"role": UserTenantMembership.Role.MEMBER},
    )


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Attach a UserProfile to a real tenant workspace. Never create slug/schema 'public'
    (PostgreSQL public is the shared catalog, not a tenant).
    """
    from dose.tenant_utils import tenants_for_user_assignment

    if UserProfile.objects.filter(user=instance).exists():
        logger.info(
            "create_or_update_user_profile: profile already exists for %s",
            instance.username,
        )
        return

    default_tenant = tenants_for_user_assignment().order_by("pk").first()
    if not default_tenant:
        logger.warning(
            "create_or_update_user_profile: no assignable tenant in DB; "
            "skipping UserProfile auto-create for %s (create a Tenant in admin first)",
            instance.username,
        )
        return

    UserProfile.objects.create(user=instance, tenant=default_tenant)
    UserTenantMembership.objects.get_or_create(
        user=instance,
        tenant=default_tenant,
        defaults={"role": UserTenantMembership.Role.MEMBER},
    )
    logger.info(
        "create_or_update_user_profile: created UserProfile for %s -> tenant %s (%s)",
        instance.username,
        default_tenant.name,
        default_tenant.schema_name,
    )


# ---------------------------------------------------------------------------
# PolySniffer: auto-create stream actions on new POST traffic
# ---------------------------------------------------------------------------

def _on_trafficlog_created(sender, instance, created, **kwargs):
    """
    When a new POST TrafficLog is saved, immediately create (or ensure) the
    matching Instruction + MQOutput for that path.

    The Instruction's executescript is set to EndpointDataExtractorService so
    DoseRequestController triggers Pub/Sub publishing on live passthrough POSTs.
    """
    if not created or instance.method != "POST":
        return

    try:
        from dose.models.pass_through_endpoint import PassThroughEndpoint
        from dose.models.tenant import Tenant
        from dose.services.sniffer_stream_actions import (
            _topic_name,
            _resolve_pubsub_defaults,
        )
        from dose.models.instruction import Instruction
        from dose.models.mq_output import MQOutput
        from django.db import transaction

        endpoint_name = (instance.endpoint_name or "").strip()
        if not endpoint_name:
            return

        ep = PassThroughEndpoint.objects.filter(
            trigger_path__iexact=endpoint_name
        ).order_by("-id").first()
        if not ep:
            ep = PassThroughEndpoint.objects.filter(
                trigger_path__icontains=endpoint_name
            ).order_by("-id").first()
        if not ep:
            return

        from django.db import connection
        schema = connection.settings_dict.get("SEARCH_PATH") or "public"
        tenant = Tenant.objects.filter(schema_name=schema).first()
        if not tenant:
            tenant = Tenant.objects.order_by("pk").first()
        if not tenant:
            return

        trigger = (ep.trigger_path or "").strip("/")
        path = (instance.path or "/").strip()
        topic = _topic_name(trigger, path)
        instruction_path = (
            f"/{trigger}/{path.lstrip('/')}"
            if not path.startswith(f"/{trigger}")
            else path
        )

        pubsub_defaults = _resolve_pubsub_defaults(tenant)

        with transaction.atomic():
            Instruction.objects.get_or_create(
                tenant=tenant,
                requestpath=instruction_path,
                requestmethod="POST",
                defaults={
                    "eventKey": topic,
                    "description": f"Auto-generated from sniffer: {ep.get_menu_title()} POST {path}",
                    "direction": "REQ",
                    "executescript": "EndpointDataExtractorService",
                    "appusername": "sniffer",
                    "urllist": ep.endpoint_url,
                    "save_callbackdata": True,
                },
            )
            MQOutput.objects.get_or_create(
                tenant=tenant,
                name=f"sniffer-{topic}"[:200],
                defaults={
                    "provider": "google_pubsub",
                    "is_active": True,
                    "instruction_path": instruction_path,
                    "pubsub_project_id": pubsub_defaults.get("pubsub_project_id", ""),
                    "pubsub_topic": topic,
                    "pubsub_credentials_json": pubsub_defaults.get("pubsub_credentials_json", ""),
                    "message_format": "json",
                    "include_request_metadata": True,
                    "include_response_data": False,
                    "description": (
                        f"Auto-generated: publish {ep.get_menu_title()} "
                        f"POST {path} as JSON to Pub/Sub topic '{topic}'"
                    ),
                },
            )

        logger.info(
            "[sniffer] stream action ensured: endpoint=%s path=%s topic=%s provider=google_pubsub",
            trigger, path, topic,
        )

    except Exception:
        # Never let a signal crash a live request
        logger.exception("[sniffer] on_trafficlog_created failed — skipping stream action creation")


# Connect after the model is ready (avoids AppRegistryNotReady at import time)
try:
    from dose.polysniffer.models import TrafficLog as _TrafficLog
    post_save.connect(_on_trafficlog_created, sender=_TrafficLog, weak=False)
except Exception:
    pass  # polysniffer not yet migrated — signal will be unavailable