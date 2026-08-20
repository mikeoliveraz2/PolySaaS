"""
Management command to start the webhook mailbox consumer.
Run with: python manage.py start_mailbox_consumer
"""
from django.core.management.base import BaseCommand
from dose.webhook_mailbox_consumer import WebhookMailboxConsumer


class Command(BaseCommand):
    help = 'Start the webhook mailbox consumer (processes events from mailbox)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--poll-interval',
            type=float,
            default=2.0,
            help='Seconds between polls (default: 2.0)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Max events per poll (default: 10)'
        )

    def handle(self, *args, **options):
        poll_interval = options['poll_interval']
        batch_size = options['batch_size']
        
        self.stdout.write(self.style.SUCCESS(
            f'Starting webhook mailbox consumer...'
        ))
        self.stdout.write(f'  Poll interval: {poll_interval}s')
        self.stdout.write(f'  Batch size: {batch_size}')
        self.stdout.write(f'  Press Ctrl+C to stop')
        
        consumer = WebhookMailboxConsumer(
            poll_interval=poll_interval,
            batch_size=batch_size
        )
        
        try:
            consumer.start()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping consumer...'))
            consumer.stop()
            self.stdout.write(self.style.SUCCESS('Consumer stopped'))
