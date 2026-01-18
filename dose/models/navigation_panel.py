from django.db import models
from .tenant_aware_model import TenantAwareModel

class NavigationPanel(TenantAwareModel):
    """
    Table-driven navigation panel configuration for tenant landing pages.
    Each tenant can customize their navigation panel with custom links,
    integrations, and external/internal system connections.
    """
    PANEL_TYPE_CHOICES = [
        ('quick_actions', '⚡ Quick Actions - Common tasks and shortcuts'),
        ('integrations', '🔗 System Integrations - External systems and APIs'),
        ('analytics', '📊 Analytics & Reports - Data visualization and reporting'),
        ('workflows', '🔄 Workflows & Automation - Process management'),
        ('documentation', '📚 Documentation & Help - Knowledge base and guides'),
        ('administration', '⚙️ Administration - System settings and management'),
        ('custom', '🎯 Custom Panel - Fully customizable content'),
    ]
    TARGET_CHOICES = [
        ('_self', 'Same Window/Tab'),
        ('_blank', 'New Window/Tab'),
        ('_parent', 'Parent Frame'),
        ('modal', 'Modal Dialog'),
        ('iframe', 'Embedded Frame'),
    ]
    ICON_STYLE_CHOICES = [
        ('emoji', '😊 Emoji Icons'),
        ('fontawesome', '🎨 Font Awesome'),
        ('bootstrap', '🅱️ Bootstrap Icons'),
        ('custom', '🖼️ Custom Image'),
        ('none', '⭕ No Icon'),
    ]
    title = models.CharField(max_length=100, help_text="Panel title (e.g., 'Quick Actions', 'External Systems')")
    panel_type = models.CharField(max_length=20, choices=PANEL_TYPE_CHOICES, default='custom', help_text="Type of panel for categorization and styling")
    description = models.TextField(blank=True, help_text="Panel description or subtitle")
    is_active = models.BooleanField(default=True, help_text="Whether this panel is visible on the landing page")
    sort_order = models.PositiveIntegerField(default=100, help_text="Display order (lower numbers appear first)")
    panel_css_class = models.CharField(max_length=100, blank=True, help_text="Additional CSS classes for custom styling")
    panel_background_color = models.CharField(max_length=7, blank=True, help_text="Hex color code for panel background (e.g., #f0f8ff)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.tenant.name} - {self.title}"
    class Meta:
        verbose_name = "Navigation Panel"
        verbose_name_plural = "Navigation Panels"
