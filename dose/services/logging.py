"""
Logging Service Implementation - BigQuery
"""
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime
from typing import Dict, List, Optional
import json


class BigQueryLogging:
    """Log events to BigQuery"""

    TABLE_SCHEMA = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_system", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("contact_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("event_data", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("error_message", "STRING", mode="NULLABLE"),
    ]

    def __init__(self, project_id: str, dataset_id: str, gcp_credentials: str):
        """
        Initialize BigQuery logging service
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            gcp_credentials: Path to service account JSON
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.gcp_credentials = gcp_credentials
        self.client = self._init_client()
        self.table_id = 'dose_events'
        self._ensure_table_exists()

    def _init_client(self) -> bigquery.Client:
        """Initialize BigQuery client"""
        credentials = service_account.Credentials.from_service_account_file(
            self.gcp_credentials
        )
        return bigquery.Client(
            project=self.project_id,
            credentials=credentials
        )

    def _ensure_table_exists(self):
        """Create table if it doesn't exist"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"

            # Check if table exists
            try:
                self.client.get_table(table_id)
            except Exception:
                # Table doesn't exist, create it
                table = bigquery.Table(table_id, schema=self.TABLE_SCHEMA)
                self.client.create_table(table)
                print(f"Created table {table_id}")

        except Exception as e:
            print(f"Error ensuring table exists: {e}")

    def log_event(self, event_type: str, event_data: Dict,
                  source_system: str, timestamp: Optional[datetime] = None) -> Dict:
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
        try:
            import uuid

            if timestamp is None:
                timestamp = datetime.utcnow()

            row = {
                'event_id': str(uuid.uuid4()),
                'timestamp': timestamp.isoformat(),
                'event_type': event_type,
                'source_system': source_system,
                'contact_id': event_data.get('id'),
                'event_data': json.dumps(event_data),
                'status': 'success',
                'error_message': None
            }

            # Insert into BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            errors = self.client.insert_rows_json(table_id, [row])

            if errors:
                return {
                    'success': False,
                    'row_id': None,
                    'error': str(errors)
                }

            return {
                'success': True,
                'row_id': row['event_id'],
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'row_id': None,
                'error': str(e)
            }

    def log_contact_change(self, contact_id: str, source_system: str,
                          changes: List[str], before: Dict, after: Dict) -> Dict:
        """Log contact modifications"""

        event_data = {
            'id': contact_id,
            'changes': changes,
            'before': before,
            'after': after
        }

        return self.log_event(
            event_type='contact_updated',
            event_data=event_data,
            source_system=source_system
        )

    def log_sync_event(self, from_system: str, to_system: str,
                      contacts_synced: int, status: str) -> Dict:
        """Log sync operations"""

        event_data = {
            'from_system': from_system,
            'to_system': to_system,
            'contacts_synced': contacts_synced,
            'status': status
        }

        return self.log_event(
            event_type='sync_completed',
            event_data=event_data,
            source_system=f"{from_system}_to_{to_system}"
        )

    def query_events(self, event_type: Optional[str] = None,
                    source_system: Optional[str] = None,
                    limit: int = 100) -> List[Dict]:
        """Query logged events"""

        query = f"""
            SELECT * FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        """

        conditions = []
        if event_type:
            conditions.append(f"event_type = '{event_type}'")
        if source_system:
            conditions.append(f"source_system = '{source_system}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY timestamp DESC LIMIT {limit}"

        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error querying events: {e}")
            return []
