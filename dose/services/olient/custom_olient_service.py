# dose/services/olient/custom_olient_service.py
"""
Custom atomic service for olient tenant.
This service extends or overrides global services for the olient tenant specifically.
"""
from dose.services.atomic_service_base import AtomicServiceBase


class CustomOlient(AtomicServiceBase):
    """
    Example custom service for olient tenant.
    This demonstrates how tenant-specific services can extend or override global services.
    """

    @staticmethod
    def execute_and_save(request, instruction_row):
        """
        Execute custom olient-specific logic.
        This could integrate with olient-specific APIs, workflows, or business rules.
        """
        # Custom logic for olient tenant
        result = {
            'tenant': 'olient',
            'custom_action': 'executed',
            'timestamp': '2025-12-05',
            'message': 'Custom olient service executed successfully'
        }

        # Save to CallBackData or custom olient-specific storage
        # ... implementation ...

        return result

    @staticmethod
    def get_parameters(parameters, key):
        """
        Get olient-specific parameters.
        """
        # Custom parameter lookup for olient tenant
        olient_params = {
            'api_endpoint': 'https://olient-api.polysaas.online',
            'custom_setting': 'olient_value'
        }
        return olient_params.get(key)