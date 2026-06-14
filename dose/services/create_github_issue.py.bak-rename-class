"""
CreateGitHubIssueService — create an issue in a configured GitHub repository.
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
import logging

import requests
from django.conf import settings

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    filter_parameters,
    instruction_config,
    maybe_save_callback,
    request_snapshot,
    service_result,
)

logger = logging.getLogger(__name__)


class CreateGitHubIssueService(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='CreateGitHubIssueService'):
        return filter_parameters(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        cfg = instruction_config(instruction_row)
        token = cfg.get('token') or getattr(settings, 'GITHUB_TOKEN', '') or getattr(settings, 'GITHUB_API_TOKEN', '')
        if not token:
            return service_result('CreateGitHubIssueService', status='error', error='GITHUB_TOKEN not configured')

        repo = cfg.get('repo') or getattr(settings, 'GITHUB_REPO', 'mikeoliveraz2/PolySaaS')
        snap = request_snapshot(request)
        title = cfg.get('title') or f"Orchestration: {snap.get('path', 'event')}"
        body = cfg.get('body') or (
            f"Auto-created by PolySaaS orchestration.\n\n"
            f"**Path:** `{snap.get('path')}`\n"
            f"**Method:** {snap.get('method')}\n"
            f"**User:** {snap.get('user')}\n"
            f"**Tenant:** {snap.get('tenant')}\n"
        )
        labels = cfg.get('labels') or []

        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        payload = {'title': title, 'body': body}
        if labels:
            payload['labels'] = labels

        try:
            resp = requests.post(
                f'https://api.github.com/repos/{repo}/issues',
                headers=headers,
                json=payload,
                timeout=30,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                result = service_result(
                    'CreateGitHubIssueService',
                    status='error',
                    http_status=resp.status_code,
                    repo=repo,
                    error=data.get('message', resp.text[:500]),
                )
            else:
                result = service_result(
                    'CreateGitHubIssueService',
                    repo=repo,
                    issue_number=data.get('number'),
                    issue_url=data.get('html_url'),
                    issue_id=data.get('id'),
                )
        except Exception as exc:
            logger.error('[CreateGitHubIssue] failed: %s', exc)
            result = service_result('CreateGitHubIssueService', status='error', error=str(exc))

        maybe_save_callback(request, instruction_row, result)
        return result
