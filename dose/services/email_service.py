"""
Email Service Implementation - Gmail
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from google.auth.transport.requests import Request
# from google.oauth2.service_account import Credentials
# from google.api_core.gapic_v1 import client_info as grpc_client_info  # Commented out due to grpc incompatibility with Python 3.13
import base64
from typing import Dict, List, Optional


class GmailEmailService:
    """Send emails via Gmail API"""

    def __init__(self, credentials_file: str):
        """
        Initialize Gmail service
        Args:
            credentials_file: Path to Google service account JSON
        """
        self.credentials_file = credentials_file
        self.credentials = self._load_credentials()

    def _load_credentials(self):
        """Load Google service account credentials"""
        from google.oauth2 import service_account
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_file,
            scopes=SCOPES
        )
        return credentials

    def send_email(self, to_email: str, subject: str, body: str,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> Dict:
        """
        Send email via Gmail API
        """
        try:
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            # Refresh credentials if needed
            request = Request()
            self.credentials.refresh(request)

            # Build Gmail service
            service = build('gmail', 'v1', credentials=self.credentials)

            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['Subject'] = subject

            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)

            # Attach body
            part = MIMEText(body, 'html')
            message.attach(part)

            # Send via Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}

            result = service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            return {
                'success': True,
                'message_id': result.get('id'),
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

    def send_notification(self, event_type: str, contact_data: Dict) -> Dict:
        """Send notification email for contact events"""

        templates = {
            'contact_created': {
                'subject': f"New Contact: {contact_data.get('name')}",
                'body': f"""
                <h2>New Contact Created</h2>
                <p><strong>Name:</strong> {contact_data.get('name')}</p>
                <p><strong>Email:</strong> {contact_data.get('email')}</p>
                <p><strong>Phone:</strong> {contact_data.get('phone')}</p>
                <p><strong>Company:</strong> {contact_data.get('company')}</p>
                """
            },
            'contact_updated': {
                'subject': f"Contact Updated: {contact_data.get('name')}",
                'body': f"""
                <h2>Contact Updated</h2>
                <p><strong>Name:</strong> {contact_data.get('name')}</p>
                <p><strong>Email:</strong> {contact_data.get('email')}</p>
                """
            },
            'contact_deleted': {
                'subject': f"Contact Deleted: {contact_data.get('name')}",
                'body': f"""
                <h2>Contact Deleted</h2>
                <p><strong>Name:</strong> {contact_data.get('name')}</p>
                """
            }
        }

        template = templates.get(event_type, {})

        return self.send_email(
            to_email=contact_data.get('email', 'admin@dose.local'),
            subject=template.get('subject', 'Contact Notification'),
            body=template.get('body', '')
        )
