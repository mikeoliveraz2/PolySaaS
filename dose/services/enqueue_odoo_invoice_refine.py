"""Thin alias for older Instructions that still name EnqueueOdooInvoiceRefine.

Type 3 is one atomic: RefineOdooInvoiceDescription. A live Confirm POST queues
the Note refine; the mailbox replay cleans narration. This class only forwards
so existing rows keep working.
"""
from __future__ import annotations

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.refine_odoo_invoice_description import (
    RefineOdooInvoiceDescription,
    _extract_move_ids,
    _is_invoice_action_post,
)

__all__ = [
    "EnqueueOdooInvoiceRefine",
    "_extract_move_ids",
    "_is_invoice_action_post",
]


class EnqueueOdooInvoiceRefine(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "write"

    @staticmethod
    def get_parameters(parameters, key="EnqueueOdooInvoiceRefine"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        return RefineOdooInvoiceDescription.execute_and_save(request, instruction_row)
