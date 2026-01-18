from django.db import models
from django.contrib.auth import get_user_model
from .tenant_aware_model import TenantAwareModel

User = get_user_model()

class RequestLog(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    body = models.JSONField(null=True, blank=True, help_text="Request body/payload as JSON")
    def __str__(self):
        return f"{self.tenant.name} {self.method} {self.path} @ {self.timestamp}"
    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"

class ErrorLog(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField()
    path = models.CharField(max_length=255, blank=True, null=True)
    status_code = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.tenant.name} ERROR {self.status_code}: {self.error_message[:50]}"
    class Meta:
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
