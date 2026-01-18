from django.db import models
from .tenant_aware_model import TenantAwareModel
from .tenant import Tenant

class PolySnifferRun(TenantAwareModel):
    # TenantAwareModel already has tenant field, so we don't need to define it again
    run_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="completed")
    packets_captured = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    raw_data_summary = models.TextField(blank=True)

    def __str__(self):
        return f"PolySniffer Run {self.id} — {self.run_timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-run_timestamp']
        verbose_name = "PolySniffer Run"
        verbose_name_plural = "PolySniffer Runs"