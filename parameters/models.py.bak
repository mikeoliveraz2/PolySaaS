#/parameters/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Parameter(models.Model):
    """
    Parameter model for storing configurable parameters
    """
    id = models.BigAutoField(primary_key=True)
    matchingKey = models.CharField(
        max_length=200,
        help_text="Unique identifier for this parameter set"
    )
    sequence = models.IntegerField(
        default=1,
        help_text="Order sequence for parameter execution"
    )
    param_kwargs_json = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON data for additional parameters"
    )
    param1 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param2 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param3 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param4 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param5 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param6 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param7 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param8 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param9 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    param10 = models.CharField(max_length=200, null=True, blank=True, default='N/A')
    description = models.CharField(
        max_length=250, 
        null=True, 
        default='N/A',
        help_text="Description of what this parameter set does"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_parameters'
    )

    def __str__(self):
        return f"{self.matchingKey} (Seq: {self.sequence})"

    class Meta:
        ordering = ('matchingKey', 'sequence')
        verbose_name = "Parameter"
        verbose_name_plural = "Parameters"

    def save(self, *args, **kwargs):
        """
        Use the `pygments` library to create a highlighted HTML
        representation of the code snippet.
        """
        super(Parameter, self).save(*args, **kwargs)
