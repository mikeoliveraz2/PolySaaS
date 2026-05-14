import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

from django.conf import settings
keys = [
    'MATTERMOST_URL', 'MATTERMOST_ADMIN_TOKEN', 'MATTERMOST_BOT_TOKEN',
    'ANTHROPIC_API_KEY', 'XAI_API_KEY', 'GEMINI_API_KEY',
    'BOT_TOKEN_CC', 'BOT_TOKEN_GEM', 'BOT_TOKEN_SUPERGROK',
    'BOT_TOKEN_WSC', 'BOT_TOKEN_KIMI', 'BOT_TOKEN_COPILOT',
    'BOT_TOKEN_CURSOR', 'BOT_TOKEN_GROK',
    'AI_PEERS_WEBHOOK_TOKEN',
]
for k in keys:
    v = getattr(settings, k, '')
    status = 'SET' if v else 'EMPTY'
    print(f'{k}: {status}')
