"""
Management command to set up the Dolibarr -> RabbitMQ -> Odoo cross-app sync demo.

Creates:
  1. PassThroughEndpoints for Dolibarr and Odoo
  2. MQConfig for RabbitMQ
  3. Instructions for extraction and sync
  4. Verifies connectivity to all services

Usage:
  python manage.py setup_demo_sync
  python manage.py setup_demo_sync --check     (verify services are running)
  python manage.py setup_demo_sync --test      (send a test customer through the pipeline)
"""
from django.core.management.base import BaseCommand
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Set up the Dolibarr -> RabbitMQ -> Odoo cross-app sync demo"

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help="Only check service connectivity")
        parser.add_argument('--test', action='store_true', help="Send a test customer through the pipeline")
        parser.add_argument('--odoo-url', default='http://localhost:8069', help="Odoo URL")
        parser.add_argument('--dolibarr-url', default='http://localhost:8889', help="Dolibarr URL")
        parser.add_argument('--rabbit-host', default='localhost', help="RabbitMQ host")
        parser.add_argument('--rabbit-port', type=int, default=5672, help="RabbitMQ port")

    def handle(self, *args, **options):
        if options['check']:
            self._check_services(options)
            return

        if options['test']:
            self._test_pipeline(options)
            return

        self._setup_all(options)

    def _check_services(self, options):
        """Check connectivity to Dolibarr, Odoo, and RabbitMQ."""
        import requests

        self.stdout.write("\nChecking service connectivity...\n")

        # Dolibarr
        try:
            r = requests.get(f"{options['dolibarr_url']}/", timeout=5)
            self.stdout.write(self.style.SUCCESS(f"  Dolibarr: UP ({r.status_code})"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Dolibarr: DOWN ({e})"))

        # Odoo
        try:
            r = requests.get(f"{options['odoo_url']}/web/login", timeout=5)
            self.stdout.write(self.style.SUCCESS(f"  Odoo: UP ({r.status_code})"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Odoo: DOWN ({e})"))

        # RabbitMQ
        try:
            import pika
            credentials = pika.PlainCredentials('polysaas', 'polysaas123')
            params = pika.ConnectionParameters(
                host=options['rabbit_host'],
                port=options['rabbit_port'],
                credentials=credentials,
            )
            conn = pika.BlockingConnection(params)
            conn.close()
            self.stdout.write(self.style.SUCCESS("  RabbitMQ: UP"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  RabbitMQ: DOWN ({e})"))

    def _setup_all(self, options):
        """Set up everything for the demo."""
        from dose.models.pass_through_endpoint import PassThroughEndpoint
        from dose.models.mq_config import MQConfig
        from dose.models import Instruction

        self.stdout.write("\n=== Setting up Cross-App Sync Demo ===\n")

        # 1. PassThroughEndpoint for Dolibarr
        ep_dolibarr, created = PassThroughEndpoint.objects.update_or_create(
            trigger_path='dolibarr',
            defaults={
                'endpoint_url': options['dolibarr_url'],
                'description': 'Dolibarr CRM/ERP',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{options['dolibarr_url']}/api/index.php",
                'show_in_menu': True,
                'menu_title': 'Dolibarr',
                'menu_icon': 'chart',
                'menu_sort_order': 30,
            }
        )
        self.stdout.write(self.style.SUCCESS(
            f"  {'Created' if created else 'Updated'} PassThroughEndpoint: Dolibarr -> {options['dolibarr_url']}"
        ))

        # 2. PassThroughEndpoint for Odoo
        ep_odoo, created = PassThroughEndpoint.objects.update_or_create(
            trigger_path='odoo',
            defaults={
                'endpoint_url': options['odoo_url'],
                'description': 'Odoo ERP',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{options['odoo_url']}/xmlrpc/2",
                'show_in_menu': True,
                'menu_title': 'Odoo',
                'menu_icon': 'building',
                'menu_sort_order': 20,
                'auth_username': 'admin',
                'auth_password': 'admin',
            }
        )
        self.stdout.write(self.style.SUCCESS(
            f"  {'Created' if created else 'Updated'} PassThroughEndpoint: Odoo -> {options['odoo_url']}"
        ))

        # 3. MQConfig for RabbitMQ
        mq_config, created = MQConfig.objects.update_or_create(
            name='PolySaaS Demo RabbitMQ',
            defaults={
                'provider': 'rabbitmq',
                'is_active': True,
                'rabbitmq_host': options['rabbit_host'],
                'rabbitmq_port': options['rabbit_port'],
                'rabbitmq_username': 'polysaas',
                'rabbitmq_password': 'polysaas123',
                'rabbitmq_vhost': '/',
                'rabbitmq_exchange': 'polysaas.events',
                'rabbitmq_queue': 'polysaas.crossapp.sync',
                'rabbitmq_routing_key': 'polysaas.#',
                'description': 'RabbitMQ broker for cross-app sync demo (Dolibarr->Odoo)',
            }
        )
        self.stdout.write(self.style.SUCCESS(
            f"  {'Created' if created else 'Updated'} MQConfig: RabbitMQ at {options['rabbit_host']}:{options['rabbit_port']}"
        ))

        # 4. Instructions for extraction (Dolibarr API POST -> extract -> publish)
        instr_extract, created = Instruction.objects.update_or_create(
            eventKey='dolibarr.api.post',
            executescript='EndpointDataExtractorService',
            defaults={
                'requestpath': '/admin/dolibarr/api/index.php',
                'requestmethod': 'POST',
                'direction': 'REQ',
                'description': 'Extract entity data from Dolibarr API POST -> publish to RabbitMQ',
                'save_callbackdata': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(
            f"  {'Created' if created else 'Updated'} Instruction: Dolibarr POST -> EndpointDataExtractorService"
        ))

        # 5. Instructions for sync (RabbitMQ -> Odoo)
        instr_sync, created = Instruction.objects.update_or_create(
            eventKey='sync.dolibarr.customer.to.odoo',
            executescript='OdooCustomerSyncService',
            defaults={
                'requestpath': '/mq/polysaas.dolibarr.customer',
                'requestmethod': 'POST',
                'direction': 'REQ',
                'description': 'Sync Dolibarr customer -> Odoo partner (create/update)',
                'save_callbackdata': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(
            f"  {'Created' if created else 'Updated'} Instruction: MQ customer -> OdooCustomerSyncService"
        ))

        self.stdout.write(self.style.SUCCESS("\n=== Demo setup complete ==="))
        self.stdout.write("""
Flow:
  1. User creates customer in Dolibarr (http://localhost:8889)
  2. POST intercepted by DoseRequestController
  3. EndpointDataExtractorService extracts & normalizes customer data
  4. Published to RabbitMQ topic: polysaas.dolibarr.customer.created
  5. MQQueueMonitor picks up message
  6. OdooCustomerSyncService creates/updates partner in Odoo

Management UI:
  - RabbitMQ: http://localhost:15672 (polysaas / polysaas123)
  - Dolibarr: http://localhost:8889 (admin / admin)
  - Odoo:     http://localhost:8069 (admin / admin after setup)

Next steps:
  1. Start containers:  docker-compose -f docker-compose.demo-sync.yml up -d
  2. Check services:    python manage.py setup_demo_sync --check
  3. Test pipeline:     python manage.py setup_demo_sync --test
""")

    def _test_pipeline(self, options):
        """Send a test customer through the full pipeline."""
        self.stdout.write("\n=== Sending test customer through pipeline ===\n")

        test_customer = {
            "source_app": "dolibarr",
            "entity": "customer",
            "action": "created",
            "topic": "polysaas.dolibarr.customer.created",
            "timestamp": "2026-03-21T10:00:00",
            "normalized_data": {
                "name": "Demo Corp International",
                "email": "contact@democorp.com",
                "phone": "+1-555-0199",
                "address": "742 Evergreen Terrace",
                "zip": "62701",
                "town": "Springfield",
                "country_code": "US",
                "customer_type": "1",
            },
            "raw_data": {
                "name": "Demo Corp International",
                "email": "contact@democorp.com",
                "phone": "+1-555-0199",
                "address": "742 Evergreen Terrace",
                "zip": "62701",
                "town": "Springfield",
                "country_code": "US",
                "client": "1",
                "code_client": "CU-DEMO-001",
            },
            "metadata": {
                "request_path": "/admin/dolibarr/api/index.php/thirdparties",
                "request_method": "POST",
                "user": "admin",
                "tenant": "default",
            }
        }

        # Publish to RabbitMQ
        try:
            import pika

            credentials = pika.PlainCredentials('polysaas', 'polysaas123')
            params = pika.ConnectionParameters(
                host=options['rabbit_host'],
                port=options['rabbit_port'],
                credentials=credentials,
            )
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(exchange='polysaas.events', exchange_type='topic', durable=True)
            channel.queue_declare(queue='polysaas.crossapp.sync', durable=True)
            channel.queue_bind(
                exchange='polysaas.events',
                queue='polysaas.crossapp.sync',
                routing_key='polysaas.#',
            )

            channel.basic_publish(
                exchange='polysaas.events',
                routing_key='polysaas.dolibarr.customer.created',
                body=json.dumps(test_customer),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                ),
            )

            connection.close()
            self.stdout.write(self.style.SUCCESS(
                f"  Published test customer 'Demo Corp International' to RabbitMQ"
            ))
            self.stdout.write(
                "  Check RabbitMQ UI: http://localhost:15672\n"
                "  MQQueueMonitor will pick up and sync to Odoo\n"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error publishing to RabbitMQ: {e}"))
            self.stdout.write("  Make sure RabbitMQ is running: docker-compose -f docker-compose.demo-sync.yml up -d")
