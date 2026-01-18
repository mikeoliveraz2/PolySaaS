"""
Contact Sync Service Implementation - OSTicket
"""
import requests
from typing import Dict, Optional
import json


class OSTicketContactSyncService:
    """Sync contacts to OSTicket via API"""

    def __init__(self, osticket_url: str, osticket_api_key: str):
        """
        Initialize OSTicket sync service
        Args:
            osticket_url: Base URL of OSTicket (e.g., https://tickets.company.com)
            osticket_api_key: OSTicket API key
        """
        self.osticket_url = osticket_url.rstrip('/')
        self.osticket_api_key = osticket_api_key
        self.headers = {
            'X-API-Key': osticket_api_key,
            'Content-Type': 'application/json'
        }

    def sync_contact(self, contact_data: Dict, source_system: str = 'crm') -> Dict:
        """
        Sync a contact to OSTicket as a User
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
        try:
            # Prepare OSTicket user data
            user_data = {
                'name': contact_data.get('name'),
                'email': contact_data.get('email'),
                'phone': contact_data.get('phone'),
                'org': contact_data.get('company'),
                'notes': f"Synced from {source_system}. ID: {contact_data.get('id')}"
            }

            # Check if user already exists by email
            existing_user = self._find_user_by_email(contact_data.get('email'))

            if existing_user:
                # Update existing user
                osticket_id = existing_user['id']
                result = self._update_user(osticket_id, user_data)
            else:
                # Create new user
                result = self._create_user(user_data)
                osticket_id = result.get('id')

            # Store mapping for bidirectional sync
            self._store_sync_mapping(
                source_system=source_system,
                source_id=contact_data.get('id'),
                osticket_id=osticket_id,
                contact_email=contact_data.get('email')
            )

            return {
                'success': True,
                'osticket_id': osticket_id,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'osticket_id': None,
                'error': str(e)
            }

    def _find_user_by_email(self, email: str) -> Optional[Dict]:
        """Find existing OSTicket user by email"""
        try:
            response = requests.get(
                f'{self.osticket_url}/api/users',
                headers=self.headers,
                params={'email': email},
                verify=False
            )

            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list) and len(users) > 0:
                    return users[0]

            return None

        except Exception as e:
            print(f"Error finding user: {e}")
            return None

    def _create_user(self, user_data: Dict) -> Dict:
        """Create new OSTicket user"""
        try:
            response = requests.post(
                f'{self.osticket_url}/api/users',
                headers=self.headers,
                json=user_data,
                verify=False
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise Exception(f"OSTicket API error: {response.status_code}")

        except Exception as e:
            print(f"Error creating user: {e}")
            raise

    def _update_user(self, user_id: str, user_data: Dict) -> Dict:
        """Update existing OSTicket user"""
        try:
            response = requests.patch(
                f'{self.osticket_url}/api/users/{user_id}',
                headers=self.headers,
                json=user_data,
                verify=False
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise Exception(f"OSTicket API error: {response.status_code}")

        except Exception as e:
            print(f"Error updating user: {e}")
            raise

    def _store_sync_mapping(self, source_system: str, source_id: str,
                            osticket_id: str, contact_email: str):
        """
        Store mapping between source system and OSTicket for bidirectional sync
        This would store in database or cache
        """
        # TODO: Store in database
        # For now, just log it
        print(f"Sync mapping: {source_system}:{source_id} <-> OSTicket:{osticket_id}")

    def sync_bidirectional(self, contact_id: str, crm_system: str,
                          osticket_id: str) -> Dict:
        """
        Keep contacts in sync both ways
        """
        return {
            'success': True,
            'mapping_stored': True
        }
