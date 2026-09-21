# Import all models for backward compatibility
from django.db import models

from .tenant import Tenant
from .subscription import Subscription
from .promo_code import PromoCode
from .user_profile import UserProfile
from .user_tenant_membership import UserTenantMembership
from .atomic_service import AtomicService
from .dashboard_button import DashboardButton
from .navigation_panel import NavigationPanel
from .navigation_item import NavigationItem
from .request_log import RequestLog
from .request_log import ErrorLog
from .user_request_tracker import UserRequestTracker
from .instruction import Instruction
from .task import Task
from .ml_engine import MLEngine
from .ml_taxonomy import MLTaxonomy
from .ml_dataset import MLDataset
from .ml_prompt import MLPrompt
from .callback_data import CallBackData
from .dose_message import DoseMessage
from .deepseek_prompt import DeepSeekPrompt
from .ignore_path import IgnorePath
from .pass_through_endpoint import PassThroughEndpoint
from .tenant_aware_model import TenantAwareModel
from .mq_input import MQInput
from .mq_output import MQOutput
from .mq_config import MQConfig
from .polysniffer_run import PolySnifferRun
from .tenant_app import TenantApp
from .mapping import Mapping, InstructionMapping
from .app_credential import AppCredential
from .hubspot_portlet import HubSpotPortletDefinition, UserHubSpotPortlet
from .founder_signup import FounderSignup
from .webhook_mailbox import WebhookMailbox
from .topic_report import (
    InventoryProductReport,
    SnmpTelemetryReport,
    MaintenanceEquipmentReport,
)
from .endpoint_bookmark import EndpointBookmark
