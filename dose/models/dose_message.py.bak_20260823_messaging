from django.db import models
from django.contrib.auth.models import User

class DoseMessage(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.level}] {self.message[:50]}..."
