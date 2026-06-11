"""
EmailToSelfService — send a formatted email to the authenticated user.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit PENDING
import logging

from django.conf import settings
from django.core.mail import send_mail

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    filter_parameters,
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
)

logger = logging.getLogger(__name__)


class EmailToSelfService(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='EmailToSelfService'):
        return filter_parameters(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return service_result('EmailToSelfService', status='error', error='not_authenticated')

        recipient = getattr(user, 'email', '') or ''
        if not recipient:
            return service_result('EmailToSelfService', status='error', error='no_user_email')

        cfg = instruction_config(instruction_row)
        snap = request_snapshot(request)
        subject = cfg.get('subject') or f"PolySaaS orchestration — {snap.get('path', 'event')}"
        message_body = cfg.get('message') or cfg.get('body') or (
            f"Orchestration instruction fired.\n\n"
            f"Path: {snap.get('path')}\n"
            f"Method: {snap.get('method')}\n"
            f"Tenant: {snap.get('tenant')}\n"
        )
        from_email = (
            cfg.get('from_email')
            or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            or 'noreply@polysaas.online'
        )

        try:
            send_mail(subject, message_body, from_email, [recipient], fail_silently=False)
            result = service_result(
                'EmailToSelfService',
                recipient=recipient,
                subject=subject,
            )
        except Exception as exc:
            logger.error('[EmailToSelf] send failed: %s', exc)
            result = service_result('EmailToSelfService', status='error', error=str(exc))

        maybe_save_callback(request, instruction_row, result)
        return result
