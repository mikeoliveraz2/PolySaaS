from django import template
from dose.models import AppCredential

register = template.Library()

@register.simple_tag
def get_app_credentials():
    """Return all stored app credentials for the dev helper card."""
    return list(AppCredential.objects.all())
