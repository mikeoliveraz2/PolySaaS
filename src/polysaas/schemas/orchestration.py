"""Orchestration schemas."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class OrchestrationStatus(str, Enum):
    """Orchestration task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationTaskCreate(BaseModel):
    """Schema for creating an orchestration task."""

    name: str = Field(..., description="Task name", min_length=1, max_length=255)
    description: str | None = Field(None, description="Task description", max_length=1000)
    parameters: dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    priority: int = Field(default=0, description="Task priority", ge=0, le=10)


class OrchestrationTaskResponse(BaseModel):
    """Schema for orchestration task response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task-123",
                "name": "example-orchestration",
                "description": "Example orchestration task",
                "status": "running",
                "parameters": {"key": "value"},
                "priority": 5,
                "created_at": "2025-12-23T06:10:00Z",
                "updated_at": "2025-12-23T06:15:00Z",
                "completed_at": None,
                "error_message": None,
            }
        }
    )

    task_id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    description: str | None = Field(None, description="Task description")
    status: OrchestrationStatus = Field(..., description="Current task status")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    priority: int = Field(default=0, description="Task priority")
    created_at: str = Field(..., description="Task creation timestamp")
    updated_at: str | None = Field(None, description="Task last update timestamp")
    completed_at: str | None = Field(None, description="Task completion timestamp")
    error_message: str | None = Field(None, description="Error message if task failed")
