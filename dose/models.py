# ...existing imports...
class PassThroughEndpoint(models.Model):
    trigger_path = models.CharField(max_length=100, unique=True, help_text="Path used to match passthrough requests (e.g. 'polysysmon')")
    endpoint_url = models.URLField(max_length=300, help_text="External service URL (e.g. http://localhost:9001)")
    is_enabled = models.BooleanField(default=True, help_text="Enable passthrough endpoint")
    show_in_menu = models.BooleanField(default=True, help_text="Show in admin navigation menu")
    menu_title = models.CharField(max_length=100, default="", blank=True, help_text="Menu display name")
    menu_icon = models.CharField(max_length=50, default="", blank=True, help_text="Menu icon (emoji or CSS class)")
    passthrough_type = models.CharField(max_length=50, default="scraper", help_text="Type of passthrough (e.g. 'scraper', 'api')")
    bypass_middleware = models.BooleanField(default=False, help_text="Bypass custom middleware")
    provider = models.CharField(max_length=50, default="custom", help_text="Provider name")
    integration_mode = models.CharField(max_length=50, default="web_only", help_text="Integration mode")
    description = models.TextField(default="", blank=True, help_text="Description of the endpoint")

    def __str__(self):
        return f"{self.menu_title or self.trigger_path} → {self.endpoint_url}"

    class Meta:
        verbose_name = "PassThrough Endpoint"
        verbose_name_plural = "PassThrough Endpoints"
# Generic passthrough shell model for admin sidebar anchoring
class PassthroughApp(models.Model):
    name = models.CharField(max_length=64, default="Passthrough")
    class Meta:
        verbose_name = "Passthrough App"
        verbose_name_plural = "Passthrough Apps"
    def __str__(self):
        return self.name
# DO NOT MODIFY: Critical system file. Ask before making changes.
import requests
from django.db import models



# --- Signals: Automatically create UserProfile for new users ---
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import datetime

from django.core.validators import FileExtensionValidator
from django.contrib.postgres.fields import JSONField

import shutil
import importlib.util
import sys
import os
from django.core.exceptions import ValidationError

# class AtomicService(models.Model):
#     service_name = models.CharField(max_length=100, unique=True, help_text="Service name (used for registration and lookup)")
#     python_file = models.FileField(
#         upload_to='services/',
#         validators=[FileExtensionValidator(['py'])],
#         help_text="Python file implementing the atomic service. Must extend AtomicServiceBase."
#     )
#     description = models.TextField(blank=True, help_text="Description of the atomic service")
#     def default_config_json():
#         return {'name': 'value'}

# --- Theme persistence: UserProfile model ---


# class Tenant(models.Model):
#     """
#     Simple tenant model for session-based multi-tenancy with schema separation
#     """
#     name = models.CharField(max_length=100, help_text="Tenant organization name")
#     slug = models.SlugField(
#         max_length=50,
#         help_text="Unique identifier for the tenant",
#         default="default"  # Default value for existing rows
#     )
#     schema_name = models.CharField(
#         max_length=63,
#         unique=True,
#         help_text="PostgreSQL schema name for this tenant (auto-generated from slug)",
#         blank=True
#     )
#     description = models.TextField(
#         blank=True,
#         default="",
#         help_text="Tenant description or details"
#     )
#     tagline = models.CharField(
#         max_length=200,
#         blank=True,
#         default="",
#         help_text="Tenant tagline or slogan"
#     )
#     logo = models.ImageField(
#         upload_to='tenant_logos/',
#         blank=True,
#         null=True,
#         help_text="Tenant logo image"
#     )
#     created_at = models.DateTimeField(
#         null=True,
#         blank=True,
#         help_text="When this tenant was created"
#     )
#     is_active = models.BooleanField(default=True)
#
#     def save(self, *args, **kwargs):
#         # Auto-generate schema_name from slug if not provided
#         if not self.schema_name and self.slug:
#             # Convert slug to valid PostgreSQL schema name
#             self.schema_name = self.slug.replace('-', '_').lower()
#
#         is_new = self.pk is None
#         super().save(*args, **kwargs)
#
#
#         # Automatic schema and table creation for PostgreSQL
#         if is_new and self.schema_name:
#             from dose.utils import create_schema_and_copy_tables
#             create_schema_and_copy_tables(self.schema_name)
#
#         # To use the tenant's schema in a user session:
#         # request.session['schema_name'] = self.schema_name
#         # Then, set the schema for each request using connection.cursor().execute(f"SET search_path TO {schema_name}")
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = "Tenant"
#         verbose_name_plural = "Tenants"



# --- Dashboard Analytics Models ---
# class Subscription(TenantAwareModel):
#     tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE)
#     stripe_customer_id = models.CharField(max_length=128, blank=True, null=True)
#     stripe_subscription_id = models.CharField(max_length=128, blank=True, null=True)
#     card_name = models.CharField(max_length=128, blank=True, null=True, help_text="Name on card")
#     active = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"Subscription for {self.tenant} (Active: {self.active})"
#
#     def is_active(self):
#         return self.active
#
#     def mark_active(self):
#         self.active = True
#         self.save()
#
#     def mark_inactive(self):
#         self.active = False
#         self.save()
#
#     # Add more Stripe logic as needed

# class RequestLog(TenantAwareModel):
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     path = models.CharField(max_length=255)
#     method = models.CharField(max_length=10)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     body = models.JSONField(null=True, blank=True, help_text="Request body/payload as JSON")
#     def __str__(self):
#         return f"{self.tenant.name} {self.method} {self.path} @ {self.timestamp}"
#     class Meta:
#         verbose_name = "Request Log"
#         verbose_name_plural = "Request Logs"
#
# class ErrorLog(TenantAwareModel):
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     error_message = models.TextField()
#     path = models.CharField(max_length=255, blank=True, null=True)
#     status_code = models.IntegerField(blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     def __str__(self):
#         return f"{self.tenant.name} ERROR {self.status_code}: {self.error_message[:50]}"
#     class Meta:
#         verbose_name = "Error Log"
#         verbose_name_plural = "Error Logs"
#
# class Instruction(TenantAwareModel):
#     class METHODS(models.TextChoices):
#         GET = 'GET', _('GET')
#         POST = 'POST', _('POST')
#         PUT = 'PUT', _('PUT')
#         DELETE = 'DELETE', _('DELETE')
#         EVAL = 'EVAL', _('EVAL')
#     class DIRECTION(models.TextChoices):
#         REQ = 'REQ', _('REQUEST')
#         RES = 'RES', _('RESPONSE')
#     id = models.BigAutoField(primary_key=True)
#     eventKey = models.CharField(max_length=100, blank=True, null=True)
#     requestpath = models.CharField(max_length=200)
#     requestmethod = models.CharField(max_length=6, choices=METHODS.choices, default=METHODS.GET)
#     direction = models.CharField(max_length=3, choices=DIRECTION.choices, default=DIRECTION.REQ)
#     urllist = models.CharField(max_length=200, default='', null=True, blank=True, help_text="The urllist can be a local or remote URL with the full path. If specifying more than one, separate multiple URLs with a comma.")
#     appusername = models.CharField(max_length=200, default='appusername')
#     executescript = models.CharField(max_length=200, default='', null=True, blank=True)
#     description = models.CharField(max_length=255, default='Description')
#     parameters_json = models.JSONField(null=True, blank=True)
#     pub_date = models.DateTimeField('date published', default=datetime.datetime.now)
#     def __str__(self):
#         return self.requestpath
#     def was_published_recently(self):
#         now = timezone.now()
#         return now - datetime.timedelta(days=1) <= self.pub_date <= now
#     class Meta:
#         verbose_name = "Instruction"
#         verbose_name_plural = "Instructions"
#
# class Task(TenantAwareModel):
#     title = models.CharField(max_length=100, blank=False, null=False)
#     matchingEventKey = models.CharField(max_length=100, blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     parameters_json = models.JSONField(null=True, blank=True)
#     completed = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     completed_at = models.DateTimeField(null=True, blank=True)
#     def __str__(self):
#         return self.title
#     class Meta:
#         verbose_name = "Task"
#         verbose_name_plural = "Tasks"

# class NavigationPanel(TenantAwareModel):
#     """
#     Table-driven navigation panel configuration for tenant landing pages.
#     Each tenant can customize their navigation panel with custom links,
#     integrations, and external/internal system connections.
#     """
#     PANEL_TYPE_CHOICES = [
#         ('quick_actions', '⚡ Quick Actions - Common tasks and shortcuts'),
#         ('integrations', '🔗 System Integrations - External systems and APIs'),
#         ('analytics', '📊 Analytics & Reports - Data visualization and reporting'),
#         ('workflows', '🔄 Workflows & Automation - Process management'),
#         ('documentation', '📚 Documentation & Help - Knowledge base and guides'),
#         ('administration', '⚙️ Administration - System settings and management'),
#         ('custom', '🎯 Custom Panel - Fully customizable content'),
#     ]
#     TARGET_CHOICES = [
#         ('_self', 'Same Window/Tab'),
#         ('_blank', 'New Window/Tab'),
#         ('_parent', 'Parent Frame'),
#         ('modal', 'Modal Dialog'),
#         ('iframe', 'Embedded Frame'),
#     ]
#     ICON_STYLE_CHOICES = [
#         ('emoji', '😊 Emoji Icons'),
#         ('fontawesome', '🎨 Font Awesome'),
#         ('bootstrap', '🅱️ Bootstrap Icons'),
#         ('custom', '🖼️ Custom Image'),
#         ('none', '⭕ No Icon'),
#     ]
#     title = models.CharField(max_length=100, help_text="Panel title (e.g., 'Quick Actions', 'External Systems')")
#     panel_type = models.CharField(max_length=20, choices=PANEL_TYPE_CHOICES, default='custom', help_text="Type of panel for categorization and styling")
#     description = models.TextField(blank=True, help_text="Panel description or subtitle")
#     is_active = models.BooleanField(default=True, help_text="Whether this panel is visible on the landing page")
#     sort_order = models.PositiveIntegerField(default=100, help_text="Display order (lower numbers appear first)")
#     panel_css_class = models.CharField(max_length=100, blank=True, help_text="Additional CSS classes for custom styling")
#     panel_background_color = models.CharField(max_length=7, blank=True, help_text="Hex color code for panel background (e.g., #f0f8ff)")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     def __str__(self):
#         return f"{self.tenant.name} - {self.title}"
#     class Meta:
#         verbose_name = "Navigation Panel"
#         verbose_name_plural = "Navigation Panels"
#         ordering = ['sort_order', 'title']
#         indexes = [
#             models.Index(fields=['tenant', 'is_active', 'sort_order']),
#         ]

# class NavigationItem(models.Model):
#     """
#     Individual navigation items within a navigation panel.
#     Each item represents a link, button, or action that users can interact with.
#     """
#     ITEM_TYPE_CHOICES = [
#         ('link', '🔗 External Link - URL to external system'),
#         ('internal', '🏠 Internal Page - Django view or URL pattern'),
#         ('api', '🌐 API Endpoint - Direct API call or integration'),
#         ('modal', '🪟 Modal Content - Pop-up dialog or form'),
#         ('download', '📥 File Download - Document or resource download'),
#         ('mailto', '📧 Email Link - Open email client'),
#         ('tel', '📞 Phone Link - Trigger phone call'),
#         ('custom', '⚡ Custom Action - JavaScript or special behavior'),
#     ]
#     panel = models.ForeignKey(
#         NavigationPanel,
#         on_delete=models.CASCADE,
#         related_name='navigation_items',
#         help_text="Panel this item belongs to"
#     )
#     title = models.CharField(max_length=100, help_text="Link title/label (e.g., 'Customer Portal', 'Generate Report')")
#     item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='link', help_text="Type of navigation item")
#     url = models.CharField(max_length=500, help_text="URL, endpoint, or action target")
#     description = models.TextField(blank=True, help_text="Item description or tooltip text")
#     icon_style = models.CharField(max_length=20, choices=NavigationPanel.ICON_STYLE_CHOICES, default='emoji', help_text="Icon display style")
#     icon_value = models.CharField(max_length=100, blank=True, help_text="Icon value (emoji, FA class, image URL, etc.)")
#     target = models.CharField(max_length=10, choices=NavigationPanel.TARGET_CHOICES, default='_self', help_text="How the link should open")
#     requires_authentication = models.BooleanField(default=True, help_text="Whether user must be logged in to access this item")
#     requires_permissions = models.CharField(max_length=200, blank=True, help_text="Comma-separated list of required permissions (e.g., 'dose.view_task,dose.add_instruction')")
#     is_active = models.BooleanField(default=True, help_text="Whether this item is visible and clickable")
#     sort_order = models.PositiveIntegerField(default=100, help_text="Display order within the panel (lower numbers appear first)")
#     item_css_class = models.CharField(max_length=100, blank=True, help_text="Additional CSS classes for custom styling")
#     button_color = models.CharField(max_length=7, blank=True, help_text="Hex color code for button/link color (e.g., #007bff)")
#     click_count = models.PositiveIntegerField(default=0, help_text="Number of times this item has been clicked")
#     last_clicked = models.DateTimeField(null=True, blank=True, help_text="When this item was last clicked")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     def __str__(self):
#         return f"{self.panel.title} - {self.title}"
#     def get_tenant(self):
#         return self.panel.tenant
#     def has_permission(self, user):
#         if not self.requires_authentication:
#             return True
#         if not user.is_authenticated:
#             return False
#         if not self.requires_permissions:
#             return True
#         required_perms = [perm.strip() for perm in self.requires_permissions.split(',') if perm.strip()]
#         return user.has_perms(required_perms)
#     def increment_click_count(self):
#         self.click_count += 1
#         self.last_clicked = timezone.now()
#         self.save(update_fields=['click_count', 'last_clicked'])
#     class Meta:
#         verbose_name = "Navigation Item"
#         verbose_name_plural = "Navigation Items"
#         ordering = ['panel', 'sort_order', 'title']
#         indexes = [
#             models.Index(fields=['panel', 'is_active', 'sort_order']),
#             models.Index(fields=['item_type', 'is_active']),
#         ]

# class DashboardButton(TenantAwareModel):
#     """
#     User-customizable dashboard buttons (Big Ass Buttons) for the landing page.
#     Each user can create, customize, and arrange their own set of dashboard buttons
#     for quick access to their most-used features and external systems.
#     """
#     BUTTON_TYPE_CHOICES = [
#         ('link', '🔗 External Link - URL to external system'),
#         ('internal', '🏠 Internal Page - Django view or URL pattern'),
#         ('api', '🌐 API Endpoint - Direct API call or integration'),
#         ('modal', '🪟 Modal Content - Pop-up dialog or form'),
#         ('download', '📥 File Download - Document or resource download'),
#         ('mailto', '📧 Email Link - Open email client'),
#         ('tel', '📞 Phone Link - Trigger phone call'),
#         ('custom', '⚡ Custom Action - JavaScript or special behavior'),
#     ]
#     SIZE_CHOICES = [
#         ('small', 'Small Button (1 grid unit)'),
#         ('medium', 'Medium Button (2 grid units)'),
#         ('large', 'Large Button (3 grid units)'),
#         ('full', 'Full Width Button (spans entire row)'),
#     ]
#     ICON_STYLE_CHOICES = [
#         ('emoji', '😊 Emoji Icons'),
#         ('fontawesome', '🎨 Font Awesome'),
#         ('bootstrap', '🅱️ Bootstrap Icons'),
#         ('custom', '🖼️ Custom Image'),
#         ('none', '⭕ No Icon'),
#     ]
#     TARGET_CHOICES = [
#         ('_self', 'Same Window/Tab'),
#         ('_blank', 'New Window/Tab'),
#         ('_parent', 'Parent Frame'),
#         ('modal', 'Modal Dialog'),
#         ('iframe', 'Embedded Frame'),
#     ]
#     user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User who owns this dashboard button")
#     title = models.CharField(max_length=100, help_text="Button title/label (e.g., 'Customer Portal', 'Generate Report')")
#     description = models.TextField(blank=True, help_text="Button description or subtitle")
#     url = models.CharField(max_length=500, help_text="URL, endpoint, or action target")
#     button_type = models.CharField(max_length=20, choices=BUTTON_TYPE_CHOICES, default='link', help_text="Type of button action")
#     icon_style = models.CharField(max_length=20, choices=ICON_STYLE_CHOICES, default='emoji', help_text="Icon display style")
#     icon_value = models.CharField(max_length=100, blank=True, help_text="Icon value (emoji, FA class, image URL, etc.)")
#     target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='_self', help_text="How the link should open")
#     color = models.CharField(max_length=50, blank=True, help_text="Button color (CSS color or hex code, e.g., #007bff, blue, var(--dose-primary))")
#     size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium', help_text="Button size on the dashboard")
#     is_active = models.BooleanField(default=True, help_text="Whether this button is visible on the dashboard")
#     sort_order = models.PositiveIntegerField(default=100, help_text="Display order (lower numbers appear first)")
#     button_css_class = models.CharField(max_length=100, blank=True, help_text="Additional CSS classes for custom styling")
#     click_count = models.PositiveIntegerField(default=0, help_text="Number of times this button has been clicked")
#     last_clicked = models.DateTimeField(null=True, blank=True, help_text="When this button was last clicked")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     def __str__(self):
#         return f"{self.user.username} - {self.title}"
#     def increment_click_count(self):
#         self.click_count += 1
#         self.last_clicked = timezone.now()
#         self.save(update_fields=['click_count', 'last_clicked'])
#     def get_icon_display(self):
#         if self.icon_style == 'emoji' and self.icon_value:
#             return self.icon_value
#         elif self.icon_style == 'fontawesome' and self.icon_value:
#             return f'<i class="fa {self.icon_value}"></i>'
#         elif self.icon_style == 'bootstrap' and self.icon_value:
#             return f'<i class="bi {self.icon_value}"></i>'
#         elif self.icon_style == 'custom' and self.icon_value:
#             return f'<img src="{self.icon_value}" alt="{self.title}" class="custom-button-icon">'
#         else:
#             return '🔘'  # Default icon
#     def get_size_class(self):
#         size_classes = {
#             'small': 'button-small',
#             'medium': 'button-medium',
#             'large': 'button-large',
#             'full': 'button-full'
#         }
#         return size_classes.get(self.size, 'button-medium')
#     class Meta:
#         verbose_name = "Dashboard Button"
#         verbose_name_plural = "Dashboard Buttons"
#         ordering = ['user', 'sort_order', 'title']
#         indexes = [
            models.Index(fields=['user', 'tenant', 'is_active']),
            models.Index(fields=['user', 'sort_order']),
        ]



    # ...existing code...

    # ...existing code...

# PolySniffer Run Logging Model
# Moved to separate file: models/polysniffer_run.py
