"""
Atomic Service for OSTicket Tenant and User Creation
Creates a new tenant and named user when someone subscribes with OSTicket enabled
"""

import logging
from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from dose.models import PassThroughEndpoint, UserProfile

logger = logging.getLogger(__name__)


class OSTicketTenantService:
    """
    Atomic service to create tenant and user for OSTicket subscription
    Since this is session-based multi-tenancy, "tenant" refers to a logical grouping
    """

    def __init__(self, subscription_data):
        """
        Initialize with subscription data
        Expected keys: email, first_name, last_name, company_name, osticket_enabled
        """
        self.email = subscription_data.get('email')
        self.first_name = subscription_data.get('first_name', '')
        self.last_name = subscription_data.get('last_name', '')
        self.company_name = subscription_data.get('company_name', '')
        self.osticket_enabled = subscription_data.get('osticket_enabled', False)

    @transaction.atomic
    def create_tenant_and_user(self):
        """
        Atomically create user and OSTicket endpoint for subscription
        Returns: (user, osticket_endpoint) or raises exception
        """
        if not self.osticket_enabled:
            raise ValidationError("OSTicket not enabled for this subscription")

        # Create user
        user = self._create_user()

        # Create OSTicket endpoint (acts as "tenant" identifier)
        osticket_endpoint = self._create_osticket_endpoint(user)

        logger.info(f"Created OSTicket user and endpoint: {user.username} - {osticket_endpoint.trigger_path}")

        return user, osticket_endpoint

    def _create_user(self):
        """Create user"""
        username = self.email.split('@')[0]
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            is_active=True
        )

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            # Add any theme preferences if needed
        )

        return user

    def _create_osticket_endpoint(self, user):
        """Create PassThroughEndpoint for OSTicket"""
        tenant_name = self.company_name or f"{self.first_name} {self.last_name}"
        trigger_path = f"/admin/osticket-{user.id}/"

        endpoint = PassThroughEndpoint.objects.create(
            name=f"OSTicket - {tenant_name}",
            trigger_path=trigger_path,
            endpoint_url="http://localhost:8080",  # Docker container URL
            is_enabled=True,
            description=f"OSTicket integration for {tenant_name}"
        )
        return endpoint