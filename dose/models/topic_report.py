"""Compatibility shim — use topic_history. History is the real name."""
from dose.models.topic_history import (  # noqa: F401
    ContactHistory,
    ContactReport,
    InventoryProductHistory,
    InventoryProductReport,
    MaintenanceEquipmentHistory,
    MaintenanceEquipmentReport,
    SnmpTelemetryHistory,
    SnmpTelemetryReport,
)
