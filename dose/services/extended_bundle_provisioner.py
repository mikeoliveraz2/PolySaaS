"""
Celery tasks for Liferay, Monitor Logger, and PolySysMon.

Full automation can be wired later; for now tasks log and return success so
subscribe flow and OAuth app registration complete while ops finish setup.
"""
import logging
from typing import Any, Dict

from celery import shared_task

logger = logging.getLogger(__name__)


def _log_queued(service: str, tenant_schema: str, tenant_name: str, admin_email: str) -> None:
    logger.info(
        "%s provisioning queued (finish setup in ops): schema=%s tenant=%s email=%s",
        service,
        tenant_schema,
        tenant_name,
        admin_email,
    )


@shared_task
def provision_liferay_tenant(
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    _log_queued('Liferay', tenant_schema, tenant_name, admin_email)
    return {'success': True, 'message': 'Liferay provisioning queued'}


@shared_task
def provision_monitor_logger_tenant(
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    _log_queued('Monitor Logger', tenant_schema, tenant_name, admin_email)
    return {'success': True, 'message': 'Monitor Logger provisioning queued'}


@shared_task
def provision_polysysmon_tenant(
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    _log_queued('PolySysMon', tenant_schema, tenant_name, admin_email)
    return {'success': True, 'message': 'PolySysMon provisioning queued'}
