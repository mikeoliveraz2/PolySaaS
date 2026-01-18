from django.db import models
from .tenant_aware_model import TenantAwareModel
from django.utils.translation import gettext_lazy as _
import datetime
from django.utils import timezone

class Instruction(TenantAwareModel):
    class METHODS(models.TextChoices):
        GET = 'GET', _('GET')
        POST = 'POST', _('POST')
        PUT = 'PUT', _('PUT')
        DELETE = 'DELETE', _('DELETE')
        EVAL = 'EVAL', _('EVAL')
    class DIRECTION(models.TextChoices):
        REQ = 'REQ', _('REQUEST')
        RES = 'RES', _('RESPONSE')
    id = models.BigAutoField(primary_key=True)
    eventKey = models.CharField(max_length=100, blank=True, null=True)
    requestpath = models.CharField(max_length=200)
    requestmethod = models.CharField(max_length=6, choices=METHODS.choices, default=METHODS.GET)
    direction = models.CharField(max_length=3, choices=DIRECTION.choices, default=DIRECTION.REQ)
    urllist = models.CharField(max_length=200, default='', null=True, blank=True, help_text="The urllist can be a local or remote URL with the full path. If specifying more than one, separate multiple URLs with a comma.")
    appusername = models.CharField(max_length=200, default='appusername')
    executescript = models.CharField(max_length=200, default='', null=True, blank=True)
    description = models.CharField(max_length=255, default='Description')
    parameters_json = models.JSONField(null=True, blank=True)
    save_callbackdata = models.BooleanField(default=False, help_text="If true, save response content to callbackdata.")
    pub_date = models.DateTimeField('date published', default=datetime.datetime.now)
    def __str__(self):
        return self.requestpath
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    class Meta:
        verbose_name = "Instruction"
        verbose_name_plural = "Instructions"
