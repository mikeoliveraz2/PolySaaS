"""
Atomic Services Framework for DoseV3
Reusable services for Email, Contact Sync, and Logging
Works with any CRM (Odoo, Pipedrive, HubSpot, etc.)
"""

# ============================================================================
# SERVICE 1: EMAIL SERVICE (Gmail)
# ============================================================================

class EmailService:
    """
    Atomic service for sending emails via Gmail
    Usage: Send emails when contacts change in CRM
    """
    def __init__(self, credentials_file):
        self.credentials_file = credentials_file

    def send_email(self, to_email, subject, body, cc=None, bcc=None):
        """
        Send email via Gmail
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: CC recipients
            bcc: BCC recipients
        Returns:
            {'success': bool, 'message_id': str, 'error': str}
        """
        pass

    def send_notification(self, event_type, contact_data):
        """
        Send notification email for contact events
        Args:
            event_type: 'contact_created', 'contact_updated', 'contact_deleted'
            contact_data: Contact information dict
        """
        pass


# ============================================================================
# SERVICE 2: CONTACT SYNC SERVICE (OSTicket)
# ============================================================================

class ContactSyncService:
    """
    Atomic service for syncing contacts between systems
    Usage: When contact changes in CRM → sync to OSTicket
    """
    def __init__(self, osticket_url, osticket_api_key):
        self.osticket_url = osticket_url
        self.osticket_api_key = osticket_api_key

    def sync_contact(self, contact_data, source_system='crm'):
        """
        Sync a contact to OSTicket
        Args:
            contact_data: {
                'id': str,
                'name': str,
                'email': str,
                'phone': str,
                'company': str,
                'metadata': dict
            }
            source_system: Where contact came from
        Returns:
            {'success': bool, 'osticket_id': str, 'error': str}
        """
        pass

    def sync_bidirectional(self, contact_id, crm_system, osticket_id):
        """
        Keep contacts in sync both ways
        Track which fields changed where
        """
        pass


# ============================================================================
# SERVICE 3: LOGGING SERVICE (BigQuery)
# ============================================================================

class LoggingService:
    """
    Atomic service for logging all transactions
    Usage: Log every contact change, email sent, sync event
    """
    def __init__(self, project_id, dataset_id, gcp_credentials):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.gcp_credentials = gcp_credentials

    def log_event(self, event_type, event_data, source_system, timestamp=None):
        """
        Log an event to BigQuery
        Args:
            event_type: 'contact_created', 'email_sent', 'sync_started', etc.
            event_data: Detailed event information
            source_system: 'odoo', 'osticket', 'gmail', etc.
            timestamp: Event timestamp (defaults to now)
        Returns:
            {'success': bool, 'row_id': str, 'error': str}
        """
        pass

    def log_contact_change(self, contact_id, source_system, changes, before, after):
        """
        Log contact modifications
        Args:
            contact_id: Unique contact ID
            source_system: System where change occurred
            changes: List of changed fields
            before: State before change
            after: State after change
        """
        pass

    def log_sync_event(self, from_system, to_system, contacts_synced, status):
        """
        Log sync operations
        Args:
            from_system: Source system
            to_system: Destination system
            contacts_synced: Number of contacts synced
            status: 'success', 'partial', 'failed'
        """
        pass


# ============================================================================
# ORCHESTRATOR: Atomic Service Runner
# ============================================================================

class AtomicServiceOrchestrator:
    """
    Coordinates all atomic services
    Example flow:
    1. Contact changes in CRM
    2. Trigger email service → send notification
    3. Trigger sync service → sync to OSTicket
    4. Trigger logging service → log to BigQuery
    """
    def __init__(self, email_service, sync_service, logging_service):
        self.email = email_service
        self.sync = sync_service
        self.logging = logging_service

    def on_contact_created(self, contact_data, source_system='crm'):
        """
        Handle contact creation event
        Flow:
        1. Log creation
        2. Sync to other systems
        3. Send notification emails
        """
        # Log
        self.logging.log_event(
            event_type='contact_created',
            event_data=contact_data,
            source_system=source_system
        )

        # Sync
        self.sync.sync_contact(contact_data, source_system)

        # Email
        self.email.send_notification('contact_created', contact_data)

    def on_contact_updated(self, contact_id, changes, before, after, source_system='crm'):
        """
        Handle contact update event
        """
        # Log
        self.logging.log_contact_change(contact_id, source_system, changes, before, after)

        # Sync
        self.sync.sync_contact(after, source_system)

        # Email (only if important fields changed)
        if self._is_significant_change(changes):
            self.email.send_notification('contact_updated', after)

    def on_contact_deleted(self, contact_id, contact_data, source_system='crm'):
        """
        Handle contact deletion event
        """
        # Log
        self.logging.log_event(
            event_type='contact_deleted',
            event_data=contact_data,
            source_system=source_system
        )

        # Email
        self.email.send_notification('contact_deleted', contact_data)

    def _is_significant_change(self, changes):
        """
        Determine if change is significant enough to email about
        """
        significant_fields = {'name', 'email', 'company', 'status'}
        return bool(significant_fields & set(changes))


# ============================================================================
# EXAMPLE: How to use the framework
# ============================================================================

def example_usage():
    """
    Example of using atomic services with any CRM
    """

    # Initialize services
    email_svc = EmailService(credentials_file='gmail_creds.json')
    sync_svc = ContactSyncService(
        osticket_url='https://tickets.company.com',
        osticket_api_key='api_key_here'
    )
    logging_svc = LoggingService(
        project_id='my-gcp-project',
        dataset_id='dose_logs',
        gcp_credentials='gcp_creds.json'
    )

    # Create orchestrator
    orchestrator = AtomicServiceOrchestrator(email_svc, sync_svc, logging_svc)

    # When contact is created in CRM (Odoo, Pipedrive, HubSpot, etc.)
    new_contact = {
        'id': 'cust_12345',
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1-555-0123',
        'company': 'Acme Corp'
    }

    orchestrator.on_contact_created(new_contact, source_system='odoo')
    # This automatically:
    # - Logs to BigQuery
    # - Syncs to OSTicket
    # - Sends notification email

    # When contact is updated
    updated_contact = {**new_contact, 'email': 'newemail@example.com'}
    changes = ['email']

    orchestrator.on_contact_updated(
        contact_id='cust_12345',
        changes=changes,
        before=new_contact,
        after=updated_contact,
        source_system='odoo'
    )


if __name__ == '__main__':
    example_usage()
