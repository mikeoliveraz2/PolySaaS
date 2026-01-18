from django.db import models
import datetime
from .tenant_aware_model import TenantAwareModel

class MLDataset(TenantAwareModel):
    id = models.BigAutoField(primary_key=True)
    matchingEventKey = models.CharField(max_length=100, blank=True, null=True)
    isTraining = models.BooleanField(default=True)
    description = models.CharField(max_length=255, default='Description')
    content_json = models.JSONField(null=True, blank=True)
    pub_date = models.DateTimeField('date published', default=datetime.datetime.now)
    
    def __str__(self):
        return f"Dataset {self.id} - {self.description}"
