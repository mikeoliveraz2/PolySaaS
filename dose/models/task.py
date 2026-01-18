from django.db import models
from .tenant_aware_model import TenantAwareModel

class Task(TenantAwareModel):
    title = models.CharField(max_length=100, blank=False, null=False)
    matchingEventKey = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parameters_json = models.JSONField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
