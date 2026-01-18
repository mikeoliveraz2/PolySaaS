from django.db import models
from django.utils import timezone
from .navigation_panel import NavigationPanel

class NavigationItem(models.Model):
    """
    Individual navigation items within a navigation panel.
    Each item represents a link, button, or action that users can interact with.
    """
    ITEM_TYPE_CHOICES = [
        ('link', '🔗 External Link - URL to external system'),
        ('internal', '🏠 Internal Page - Django view or URL pattern'),
        ('api', '🌐 API Endpoint - Direct API call or integration'),
        ('modal', '🪟 Modal Content - Pop-up dialog or form'),
        ('download', '📥 File Download - Document or resource download'),
        ('mailto', '📧 Email Link - Open email client'),
        ('tel', '📞 Phone Link - Trigger phone call'),
        ('custom', '⚡ Custom Action - JavaScript or special behavior'),
    ]
    panel = models.ForeignKey(
        NavigationPanel,
        on_delete=models.CASCADE,
        related_name='navigation_items',
        help_text="Panel this item belongs to"
    )
    title = models.CharField(max_length=100, help_text="Link title/label (e.g., 'Customer Portal', 'Generate Report')")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='link', help_text="Type of navigation item")
    url = models.CharField(max_length=500, help_text="URL, endpoint, or action target")
    description = models.TextField(blank=True, help_text="Item description or tooltip text")
    icon_style = models.CharField(max_length=20, choices=NavigationPanel.ICON_STYLE_CHOICES, default='emoji', help_text="Icon display style")
    icon_value = models.CharField(max_length=100, blank=True, help_text="Icon value (emoji, FA class, image URL, etc.)")
    target = models.CharField(max_length=10, choices=NavigationPanel.TARGET_CHOICES, default='_self', help_text="How the link should open")
    requires_authentication = models.BooleanField(default=True, help_text="Whether user must be logged in to access this item")
    requires_permissions = models.CharField(max_length=200, blank=True, help_text="Comma-separated list of required permissions (e.g., 'dose.view_task,dose.add_instruction')")
    is_active = models.BooleanField(default=True, help_text="Whether this item is visible and clickable")
    sort_order = models.PositiveIntegerField(default=100, help_text="Display order within the panel (lower numbers appear first)")
    item_css_class = models.CharField(max_length=100, blank=True, help_text="Additional CSS classes for custom styling")
    button_color = models.CharField(max_length=7, blank=True, help_text="Hex color code for button/link color (e.g., #007bff)")
    click_count = models.PositiveIntegerField(default=0, help_text="Number of times this item has been clicked")
    last_clicked = models.DateTimeField(null=True, blank=True, help_text="When this item was last clicked")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.panel.title} - {self.title}"
    def get_tenant(self):
        return self.panel.tenant
    def has_permission(self, user):
        if not self.requires_authentication:
            return True
        if not user.is_authenticated:
            return False
        if not self.requires_permissions:
            return True
        required_perms = [perm.strip() for perm in self.requires_permissions.split(',') if perm.strip()]
        return user.has_perms(required_perms)
    def increment_click_count(self):
        self.click_count += 1
        self.last_clicked = timezone.now()
        self.save(update_fields=['click_count', 'last_clicked'])
    class Meta:
        verbose_name = "Navigation Item"
        verbose_name_plural = "Navigation Items"
