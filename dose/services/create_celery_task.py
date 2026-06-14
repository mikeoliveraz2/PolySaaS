"""
CreateCeleryTask — queue a Celery background task by name.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.atomic_service_utils import (
    instruction_config,
    maybe_save_callback,
    service_result,
)

logger = logging.getLogger(__name__)


class CreateCeleryTask(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='CreateCeleryTask'):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        task_name = cfg.get('task') or cfg.get('task_name')
        if not task_name:
            return service_result('CreateCeleryTask', status='error', error='missing_task_name')

        args = cfg.get('args') or []
        kwargs = cfg.get('kwargs') or {}
        if not isinstance(args, list):
            args = [args]
        if not isinstance(kwargs, dict):
            kwargs = {}

        countdown = cfg.get('countdown')
        eta = cfg.get('eta')

        try:
            from celery import current_app
            async_result = current_app.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                countdown=countdown,
                eta=eta,
            )
            result = service_result(
                'CreateCeleryTask',
                task=task_name,
                task_id=str(async_result.id),
                state=async_result.state,
            )
        except Exception as exc:
            logger.error('[CreateCeleryTask] queue failed: %s', exc)
            result = service_result(
                'CreateCeleryTask',
                status='error',
                task=task_name,
                error=str(exc),
            )

        maybe_save_callback(request, instruction_row, result)
        return result
