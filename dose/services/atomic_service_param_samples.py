"""
Sample parameters_json templates for Instruction.executescript (admin + orchestration embed).
"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit PENDING
from __future__ import annotations

from typing import Any, Dict, Optional

# Keys = registry class names (Instruction.executescript values).
ATOMIC_SERVICE_PARAM_SAMPLES: Dict[str, Dict[str, Any]] = {
    'PublishToPubSubService': {
        'topic': 'polysaas-orchestration',
        'payload': {
            'event': 'orchestration.demo',
            'source': 'passthrough',
        },
        'attributes': {'event_key': 'polysaas.demo'},
        'include_request': True,
    },
    'EmailToSelfService': {
        'subject': 'PolySaaS orchestration alert',
        'message': 'Instruction matched. Review the action path and callback data in admin.',
        'from_email': 'noreply@polysaas.online',
    },
    'AddToMLDatasetService': {
        'dataset_key': 'conversations',
        'filename': 'demo_conversations.jsonl',
        'record': {
            'prompt': 'User navigated to Town Square',
            'response': '',
            'labels': ['orchestration', 'mattermost'],
        },
    },
    'ExportToRESTAPIService': {
        'url': 'https://hooks.example.com/polysaas/orchestration',
        'method': 'POST',
        'headers': {'Content-Type': 'application/json'},
        'body': {'event': 'instruction_matched', 'tenant': '{{tenant}}'},
        'timeout': 30,
    },
    'CreateGitHubIssueService': {
        'repo': 'mikeoliveraz2/PolySaaS',
        'title': 'Orchestration: action path matched',
        'body': 'Auto-created from PolySaaS orchestration bar demo.',
        'labels': ['orchestration', 'demo'],
    },
    'NotifyAIPeersService': {
        'channel_id': 'REPLACE_WITH_MATTERMOST_CHANNEL_ID',
        'peers': ['grok', 'copilot', 'gemini'],
        'message': 'Orchestration instruction matched — AI peers please acknowledge.',
    },
    'CreateCeleryTaskService': {
        'task': 'parameters.tasks.add',
        'args': [1, 2],
        'kwargs': {},
    },
    'WriteToBigQueryService': {
        'project_id': 'application-integration-4524',
        'dataset_id': 'polysaas',
        'table_id': 'orchestration_events',
        'event_type': 'instruction.matched',
        'source_system': 'polysaas',
        'event_data': {'demo': True},
    },
    'GenerateImageAndExportService': {
        'prompt': 'PolySaaS orchestration dashboard hero illustration, modern SaaS',
        'filename': 'orch_demo.png',
        'export_url': '',
        'export_method': 'POST',
    },
    'CopilotQueryService': {
        'prompt': 'Summarize what happened on this orchestration path.',
    },
    'EndpointDataExtractorService': {
        'note': 'Uses request body + mapping/catalog; parameters_json optional for overrides.',
    },
    'AtomicServiceSendApprovalEmail': {
        'recipient_email': 'user@example.com',
        'subject': 'Approval required',
        'message': 'Please review this orchestration instruction.',
        'from_email': 'Dose2 <mo.gsssol@gmail.com>',
    },
    'MattermostProvisioningService': {
        'note': 'Configure Parameters row matchingKey=MattermostProvisioningService (mm_url, admin_token, team_type).',
    },
    'OdooInvoiceNotifierService': {
        'mm_channel': 'town-square',
        'note': 'Triggered from MQ; uses TenantApp.extra_config for mm_url/mm_token when not in JSON.',
    },
    'OdooCustomerSyncService': {
        'odoo_url': 'https://polysaas-odoo2.onrender.com',
        'odoo_db': 'odoo',
        'note': 'MQ message body carries customer payload; optional Odoo connection overrides here.',
    },
    'GmailProxyService': {
        'note': 'Uses OAuth session; parameters_json rarely needed.',
    },
    'AtomicService1': {
        'MatchingKey': 'AtomicService1',
        'demo': True,
    },
    'AtomicServiceChoice': {
        'choice': 'option_a',
    },
    'HelloWorld': {
        'message': 'Hello from orchestration',
    },
}


def get_sample_parameters_json(service_name: str) -> Optional[Dict[str, Any]]:
    name = (service_name or '').strip()
    if not name:
        return None
    sample = ATOMIC_SERVICE_PARAM_SAMPLES.get(name)
    if sample is not None:
        return sample
    return {
        '_service': name,
        'note': f'Add parameters_json fields required by {name}.',
    }
