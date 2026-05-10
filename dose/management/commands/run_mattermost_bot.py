"""
Management command: run_mattermost_bot

Usage:
    python manage.py run_mattermost_bot
    python manage.py run_mattermost_bot --retry-delay 15

Required settings (.env):
    MATTERMOST_URL         https://polysaas-mattermost.onrender.com
    MATTERMOST_BOT_TOKEN   personal-access-token for the listening account
    BOT_TOKEN_GROK         token for @grok bot account
    BOT_TOKEN_GEMINI       token for @gemini bot account
    BOT_TOKEN_WINDSURF     token for @windsurf bot account (optional)
    XAI_API_KEY            xAI Grok key
    GEMINI_API_KEY         Google Gemini key
    WINDSURF_API_KEY       Windsurf key (optional)
"""
import logging
import time

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the PolySaaS Mattermost AI-as-Peers WebSocket bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retry-delay', type=int, default=10,
            help='Seconds between reconnect attempts (default: 10)',
        )
        parser.add_argument(
            '--max-retries', type=int, default=0,
            help='Max reconnect attempts — 0 means unlimited (default: 0)',
        )

    def handle(self, *args, **options):
        retry_delay = options['retry_delay']
        max_retries = options['max_retries']
        attempt = 0

        self.stdout.write(self.style.SUCCESS('🤖 Starting PolySaaS Mattermost Bot…'))

        while True:
            try:
                from dose.mattermost_bot.bot import PolySaaSMattermostBot
                bot = PolySaaSMattermostBot()
                bot.start()   # blocks on WebSocket until disconnect
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n⛔ Bot stopped by user.'))
                break
            except Exception as exc:
                attempt += 1
                logger.error('[MM Bot] Disconnected (attempt %d): %s', attempt, exc)
                self.stdout.write(self.style.ERROR(f'❌ Bot error (attempt {attempt}): {exc}'))
                if max_retries and attempt >= max_retries:
                    self.stdout.write(self.style.ERROR('Max retries reached — exiting.'))
                    break
                self.stdout.write(f'↩️  Reconnecting in {retry_delay}s…')
                time.sleep(retry_delay)
