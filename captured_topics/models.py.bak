"""
Proxy model so Captured Topics appears as its own Jazzmin sidebar section
(after Authentication and Authorization), not under Dose Tenant Management.
"""
from dose.models import WebhookMailbox


class CapturedTopic(WebhookMailbox):
    class Meta:
        proxy = True
        verbose_name = 'Captured Topic'
        verbose_name_plural = 'Captured Topics'
