"""
Notion Integration Service
Connects PolySaaS atomic services to Notion SaaS
- Monitor Notion database for new entries
- Trigger email notifications
- Sync to osTicket
- Log to BigQuery
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json
import time


class NotionService:
    """Integrate with Notion API"""

    NOTION_API_VERSION = '2022-06-28'

    def __init__(self, api_key: str):
        """
        Initialize Notion service
        Args:
            api_key: Notion integration token (from notion.so/integrations)
        """
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Notion-Version': self.NOTION_API_VERSION,
            'Content-Type': 'application/json'
        }

    def get_database(self, database_id: str) -> Dict:
        """
        Get database metadata
        Args:
            database_id: Notion database ID
        Returns:
            Database metadata
        """
        try:
            url = f"{self.base_url}/databases/{database_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Notion API error: {response.status_code}")

        except Exception as e:
            print(f"Error getting database: {e}")
            return {}

    def query_database(self, database_id: str, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Query Notion database
        Args:
            database_id: Notion database ID
            filter_dict: Optional filter criteria
        Returns:
            List of pages/records
        """
        try:
            url = f"{self.base_url}/databases/{database_id}/query"
            payload = {}

            if filter_dict:
                payload['filter'] = filter_dict

            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                raise Exception(f"Notion API error: {response.status_code}")

        except Exception as e:
            print(f"Error querying database: {e}")
            return []

    def create_page(self, database_id: str, properties: Dict) -> Dict:
        """
        Create new page in Notion database
        Args:
            database_id: Notion database ID
            properties: Page properties (fields)
        Returns:
            {'success': bool, 'page_id': str, 'error': str}
        """
        try:
            url = f"{self.base_url}/pages"
            payload = {
                'parent': {'database_id': database_id},
                'properties': properties
            }

            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                page_id = data['id']
                return {
                    'success': True,
                    'page_id': page_id,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'page_id': None,
                    'error': f"Notion API error: {response.status_code}"
                }

        except Exception as e:
            return {
                'success': False,
                'page_id': None,
                'error': str(e)
            }

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """
        Update existing page
        Args:
            page_id: Notion page ID
            properties: Updated properties
        Returns:
            {'success': bool, 'page_id': str, 'error': str}
        """
        try:
            url = f"{self.base_url}/pages/{page_id}"
            payload = {'properties': properties}

            response = requests.patch(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                return {
                    'success': True,
                    'page_id': page_id,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'page_id': None,
                    'error': f"Notion API error: {response.status_code}"
                }

        except Exception as e:
            return {
                'success': False,
                'page_id': None,
                'error': str(e)
            }

    def get_page_content(self, page_id: str) -> Dict:
        """Extract properties from page"""
        try:
            url = f"{self.base_url}/pages/{page_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                return {
                    'id': data['id'],
                    'properties': data.get('properties', {}),
                    'created_time': data.get('created_time'),
                    'last_edited_time': data.get('last_edited_time')
                }
            else:
                raise Exception(f"Notion API error: {response.status_code}")

        except Exception as e:
            print(f"Error getting page: {e}")
            return {}


class NotionToAtomicServiceBridge:
    """
    Bridge between Notion and atomic services
    Monitors Notion database and triggers services
    """

    def __init__(self, notion_svc, email_svc, sync_svc, logging_svc):
        """
        Initialize bridge
        Args:
            notion_svc: NotionService instance
            email_svc: Email service (Gmail)
            sync_svc: Sync service (OSTicket)
            logging_svc: Logging service (BigQuery)
        """
        self.notion = notion_svc
        self.email = email_svc
        self.sync = sync_svc
        self.logging = logging_svc
        self.processed_pages = set()

    def poll_for_new_contacts(self, database_id: str, interval_seconds: int = 10):
        """
        Poll Notion for new contact entries
        Args:
            database_id: Notion database ID
            interval_seconds: Poll interval
        """
        print(f"Starting Notion poller (checking every {interval_seconds}s)...")

        while True:
            try:
                # Query database
                pages = self.notion.query_database(database_id)

                for page in pages:
                    page_id = page['id']

                    if page_id not in self.processed_pages:
                        self._process_new_contact(page)
                        self.processed_pages.add(page_id)

                time.sleep(interval_seconds)

            except Exception as e:
                print(f"Error polling Notion: {e}")
                time.sleep(interval_seconds)

    def _process_new_contact(self, page: Dict):
        """
        Process new Notion page as contact
        Flow:
        1. Extract contact info from page properties
        2. Log to BigQuery
        3. Send email notification
        4. Sync to osTicket
        """
        try:
            page_id = page['id']
            properties = page.get('properties', {})

            print(f"\n[NOTION] New contact: {page_id}")

            # Extract contact data from Notion properties
            # Notion stores properties as complex objects, we need to parse them
            contact_data = self._parse_notion_properties(page_id, properties)

            print(f"  Contact: {contact_data.get('name')} ({contact_data.get('email')})")

            # Step 1: Log event
            self.logging.log_event(
                event_type='contact_created',
                event_data={
                    'id': page_id,
                    'source': 'notion',
                    'contact': contact_data
                },
                source_system='notion'
            )

            # Step 2: Send email notification
            if contact_data.get('email'):
                email_result = self.email.send_notification('contact_created', contact_data)
                print(f"  ✓ Email sent: {email_result['success']}")

            # Step 3: Sync to osTicket
            if contact_data.get('email'):
                sync_result = self.sync.sync_contact(contact_data, source_system='notion')
                print(f"  ✓ Synced to osTicket: {sync_result['success']}")

                # Log sync event
                if sync_result['success']:
                    self.logging.log_event(
                        event_type='contact_synced',
                        event_data={
                            'notion_page_id': page_id,
                            'osticket_id': sync_result.get('osticket_id'),
                            'contact_name': contact_data.get('name')
                        },
                        source_system='notion_to_osticket'
                    )

            print(f"  ✓ Contact processed successfully")

        except Exception as e:
            print(f"  ✗ Error processing contact: {e}")
            self.logging.log_event(
                event_type='contact_processing_error',
                event_data={'error': str(e), 'page_id': page.get('id')},
                source_system='notion'
            )

    def _parse_notion_properties(self, page_id: str, properties: Dict) -> Dict:
        """
        Parse Notion page properties into contact data
        Notion properties are complex objects, need to extract values
        """
        try:
            # Get full page content for property values
            page_content = self.notion.get_page_content(page_id)
            props = page_content.get('properties', {})

            contact_data = {
                'id': page_id,
                'name': self._extract_property_value(props, 'Name', 'title'),
                'email': self._extract_property_value(props, 'Email', 'email'),
                'phone': self._extract_property_value(props, 'Phone', 'phone_number'),
                'company': self._extract_property_value(props, 'Company', 'rich_text'),
                'source': 'notion'
            }

            return contact_data

        except Exception as e:
            print(f"Error parsing properties: {e}")
            return {'id': page_id, 'source': 'notion'}

    def _extract_property_value(self, properties: Dict, field_name: str,
                                field_type: str) -> str:
        """
        Extract value from Notion property
        Notion properties have different structures based on type
        """
        try:
            prop = properties.get(field_name, {})

            if field_type == 'title':
                # Title fields contain array of text objects
                title_array = prop.get('title', [])
                if title_array:
                    return title_array[0].get('plain_text', '')

            elif field_type == 'email':
                # Email fields are simple strings
                return prop.get('email', '')

            elif field_type == 'phone_number':
                # Phone fields are simple strings
                return prop.get('phone_number', '')

            elif field_type == 'rich_text':
                # Rich text fields contain array of text objects
                rich_text_array = prop.get('rich_text', [])
                if rich_text_array:
                    return rich_text_array[0].get('plain_text', '')

            elif field_type == 'select':
                # Select fields have a name
                select_obj = prop.get('select', {})
                return select_obj.get('name', '')

            return ''

        except Exception as e:
            print(f"Error extracting {field_name}: {e}")
            return ''


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def demo_notion_integration():
    """
    Example: Setup Notion → Gmail → osTicket → BigQuery pipeline
    """
    from dose.services.email_to import GmailEmail
    from dose.services.sync_service import OSTicketContactSyncService
    from dose.services.logging import BigQueryLogging

    # Get credentials from config
    NOTION_API_KEY = 'ntn_YOUR_INTEGRATION_TOKEN'  # Get from notion.so/integrations
    NOTION_DATABASE_ID = 'YOUR_DATABASE_ID'  # Get from Notion database URL

    # Initialize services
    notion = NotionService(api_key=NOTION_API_KEY)

    email = GmailEmail(credentials_file='gmail_creds.json')
    sync = OSTicketContactSyncService(
        osticket_url='https://tickets.company.com',
        osticket_api_key='YOUR_OSTICKET_API_KEY'
    )
    logging = BigQueryLogging(
        project_id='my-gcp-project',
        dataset_id='dose_logs',
        gcp_credentials='gcp_creds.json'
    )

    # Create bridge
    bridge = NotionToAtomicServiceBridge(notion, email, sync, logging)

    # Start polling for new contacts
    print("Starting Notion → Gmail + osTicket + BigQuery pipeline...")
    print(f"Monitoring Notion database: {NOTION_DATABASE_ID}")
    bridge.poll_for_new_contacts(database_id=NOTION_DATABASE_ID, interval_seconds=5)


if __name__ == '__main__':
    demo_notion_integration()
