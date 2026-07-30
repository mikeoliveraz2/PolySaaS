"""
Founder Beta Circle provisioning service.
Creates tenant, admin user, and subscriptions after Lemon Squeezy payment.
"""
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from celery import shared_task

from dose.models import FounderSignup, Tenant, Subscription, UserProfile, UserTenantMembership

logger = logging.getLogger(__name__)
User = get_user_model()

FOUNDERS_PLAN_TIER = 'polysaas-unlimited'
FOUNDERS_FREE_PERIOD_MONTHS = 12
FOUNDERS_APPS = {
    'enable_odoo': 'Odoo ERP',
    'enable_nextcloud': 'Nextcloud',
    'enable_dolibarr': 'Dolibarr',
    'enable_mattermost': 'Mattermost',
    'enable_wordpress': 'WordPress',
    'enable_liferay': 'Liferay',
    'enable_monitor_logger': 'Monitor Logger',
    'enable_polysysmon': 'PolySysMon',
}


def get_founder_free_period_end(start=None):
    start = start or timezone.now()
    try:
        return start.replace(year=start.year + 1)
    except ValueError:
        return start.replace(year=start.year + 1, day=28)


@shared_task
def provision_founder_tenant(founder_id):
    """
    Celery task: Provision founder tenant after successful payment.
    Creates Tenant, admin User, Subscription, and optionally enqueues app provisioning.
    """
    try:
        founder_signup = FounderSignup.objects.get(id=founder_id)
        
        if founder_signup.status == 'provisioned':
            logger.info(f'Founder {founder_id} already provisioned.')
            return
        
        logger.info(f'Starting provisioning for founder {founder_id} ({founder_signup.company_slug})')
        
        with transaction.atomic():
            # Create Tenant
            tenant = Tenant.objects.create(
                name=founder_signup.company_name,
                slug=founder_signup.company_slug,
                schema_name=f'tenant_{founder_signup.company_slug}',
            )
            logger.info(f'Created tenant {tenant.id} ({founder_signup.company_slug})')
            
            # Create admin User
            admin_user = User.objects.create_user(
                username=founder_signup.admin_username,
                email=founder_signup.admin_email,
                is_staff=True,
                is_superuser=True,
            )
            logger.info(f'Created admin user {admin_user.id} ({founder_signup.admin_username})')
            
            # Create UserProfile
            user_profile = UserProfile.objects.create(
                user=admin_user,
                tenant=tenant,
                role='admin',
            )
            logger.info(f'Created user profile {user_profile.id}')
            
            # Create UserTenantMembership
            membership = UserTenantMembership.objects.create(
                user=admin_user,
                tenant=tenant,
                role='admin',
            )
            logger.info(f'Created membership {membership.id}')
            
            # Create Subscription
            subscription = Subscription.objects.create(
                tenant=tenant,
                plan_tier=FOUNDERS_PLAN_TIER,
                user_count=1,
                active=True,
                selected_apps=list(FOUNDERS_APPS.keys()),
                free_period_ends_at=get_founder_free_period_end(),
            )
            subscription.mark_active()
            logger.info(f'Created subscription {subscription.id} (plan={FOUNDERS_PLAN_TIER})')
            
            # Mark founder signup as provisioned
            founder_signup.mark_provisioned(tenant, admin_user)
            logger.info(f'Marked founder signup {founder_id} as provisioned')
            
            # Trigger app provisioning (optional: can be done later)
            # enqueue_founder_app_provisioning.delay(founder_id, tenant.id)
        
        logger.info(f'Successfully provisioned founder tenant for {founder_signup.company_slug}')
        
        # Send welcome email (optional)
        try:
            send_founder_welcome_email(founder_signup, admin_user)
        except Exception as e:
            logger.warning(f'Failed to send welcome email: {e}')
    
    except FounderSignup.DoesNotExist:
        logger.error(f'FounderSignup {founder_id} not found')
    except Exception as e:
        logger.exception(f'Error provisioning founder tenant: {e}')
        try:
            founder_signup = FounderSignup.objects.get(id=founder_id)
            founder_signup.mark_failed()
        except:
            pass


def send_founder_welcome_email(founder_signup, admin_user):
    """
    Send welcome email to founder with login credentials and next steps.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    subject = f'Welcome to PolySaaS Founder Beta Circle, {founder_signup.company_name}!'
    
    context = {
        'company_name': founder_signup.company_name,
        'company_slug': founder_signup.company_slug,
        'admin_username': founder_signup.admin_username,
        'login_url': f'https://polysaas.online/login/',
        'apps': list(FOUNDERS_APPS.values()),
        'app_count': len(FOUNDERS_APPS),
    }
    
    html_message = render_to_string('dose/emails/founder_welcome.html', context)
    
    send_mail(
        subject,
        f'Welcome to PolySaaS Founder Beta Circle! Your tenant {founder_signup.company_slug} is ready.',
        settings.DEFAULT_FROM_EMAIL,
        [founder_signup.admin_email],
        html_message=html_message,
        fail_silently=True,
    )
    
    logger.info(f'Welcome email sent to {founder_signup.admin_email}')
