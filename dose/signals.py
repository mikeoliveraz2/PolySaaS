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

    logger.info("=" * 80)


@receiver(user_logged_in)
def set_tenant_in_session(sender, user, request, **kwargs):
    try:
        # Try to get UserProfile and tenant
        profile = getattr(user, 'userprofile', None)
        if profile and profile.tenant:
            tenant = profile.tenant
            request.session['tenant_id'] = tenant.id
            request.session['tenant_name'] = tenant.name
            request.session['tenant_slug'] = tenant.slug
            request.session['tenant_description'] = getattr(tenant, 'description', '')
            if hasattr(tenant, 'logo') and tenant.logo:
                request.session['tenant_logo_url'] = tenant.logo.url
            print(f"set_tenant_in_session: Set session for user {user.username} with tenant {tenant.name} (ID: {tenant.id})")
        else:
            print(f"set_tenant_in_session: No tenant found for user {user.username}, using public schema")
    except Exception as e:
        print(f"set_tenant_in_session: Error setting tenant session for user {user.username}: {e}")
        # Continue without setting tenant - will default to public schema

# --- Theme persistence: UserProfile signals ---
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from dose.models import UserProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    from dose.models import Tenant

    # Get or create default tenant
    default_tenant, _ = Tenant.objects.get_or_create(
        slug='public',
        defaults={
            'name': 'Public Tenant',
            'description': 'Default tenant for all users',
            'is_active': True
        }
    )

    # Always use get_or_create to avoid duplicate key errors
    # This handles both new users and existing users being edited
    profile, created_profile = UserProfile.objects.get_or_create(
        user=instance,
        defaults={'tenant': default_tenant}
    )

    if created_profile:
        print(f"create_or_update_user_profile: Created UserProfile for {instance.username} with tenant {default_tenant.name}")
    else:
        print(f"create_or_update_user_profile: UserProfile already exists for {instance.username}")