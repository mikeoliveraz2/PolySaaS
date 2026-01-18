from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from .tenant_aware_model import TenantAwareModel

User = get_user_model()

class DashboardButton(TenantAwareModel):
    """
    User-customizable dashboard buttons (Big Ass Buttons) for the landing page.
    Each user can create, customize, and arrange their own set of dashboard buttons
    for quick access to their most-used features and external systems.
    """
    BUTTON_TYPE_CHOICES = [
        ('link', '🔗 External Link - URL to external system'),
        ('internal', '🏠 Internal Page - Django view or URL pattern'),
        ('api', '🌐 API Endpoint - Direct API call or integration'),
        ('modal', '🪟 Modal Content - Pop-up dialog or form'),
        ('download', '📥 File Download - Document or resource download'),
        ('mailto', '📧 Email Link - Open email client'),
        ('tel', '📞 Phone Link - Trigger phone call'),
        ('custom', '⚡ Custom Action - JavaScript or special behavior'),
    ]
    SIZE_CHOICES = [
        ('small', 'Small Button (1 grid unit)'),
        ('medium', 'Medium Button (2 grid units)'),
        ('large', 'Large Button (3 grid units)'),
        ('full', 'Full Width Button (spans entire row)'),
    ]
    ICON_STYLE_CHOICES = [
        ('emoji', '😊 Emoji Icons'),
        ('fontawesome', '🎨 Font Awesome'),
        ('bootstrap', '🅱️ Bootstrap Icons'),
        ('custom', '🖼️ Custom Image'),
        ('none', '⭕ No Icon'),
    ]
    TARGET_CHOICES = [
        ('_self', 'Same Window/Tab'),
        ('_blank', 'New Window/Tab'),
        ('_parent', 'Parent Frame'),
        ('modal', 'Modal Dialog'),
        ('iframe', 'Embedded Frame'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User who owns this dashboard button")
    title = models.CharField(max_length=100, help_text="Button title/label (e.g., 'Customer Portal', 'Generate Report')")
    description = models.TextField(blank=True, help_text="Button description or subtitle")
    url = models.CharField(max_length=500, help_text="URL, endpoint, or action target")
    button_type = models.CharField(max_length=20, choices=BUTTON_TYPE_CHOICES, default='link', help_text="Type of button action")
    icon_style = models.CharField(max_length=20, choices=ICON_STYLE_CHOICES, default='emoji', help_text="Icon display style")
    icon_value = models.CharField(max_length=100, blank=True, help_text="Icon value (emoji, FA class, image URL, etc.)")
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='_self', help_text="How the link should open")
    color = models.CharField(max_length=50, blank=True, help_text="Button color (CSS color or hex code, e.g., #007bff, blue, var(--dose-primary))")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium', help_text="Button size on the dashboard")
    is_active = models.BooleanField(default=True, help_text="Whether this button is visible on the dashboard")
    sort_order = models.PositiveIntegerField(default=100, help_text="Display order (lower numbers appear first)")
    button_css_class = models.CharField(max_length=100, blank=True, help_text="Additional CSS classes for custom styling")
    click_count = models.PositiveIntegerField(default=0, help_text="Number of times this button has been clicked")
    last_clicked = models.DateTimeField(null=True, blank=True, help_text="When this button was last clicked")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    def increment_click_count(self):
        self.click_count += 1
        self.last_clicked = timezone.now()
        self.save(update_fields=['click_count', 'last_clicked'])
    def get_icon_display(self):
        if self.icon_style == 'emoji' and self.icon_value:
            return self.icon_value
        elif self.icon_style == 'fontawesome' and self.icon_value:
            return f'<i class="fa {self.icon_value}"></i>'
        elif self.icon_style == 'bootstrap' and self.icon_value:
            return f'<i class="bi {self.icon_value}"></i>'
        elif self.icon_style == 'custom' and self.icon_value:
            return f'<img src="{self.icon_value}" alt="{self.title}" class="custom-button-icon">'
        else:
            return '🔘'
    def get_size_class(self):
        size_classes = {
            'small': 'button-small',
            'medium': 'button-medium', 
            'large': 'button-large',
            'full': 'button-full'
        }
        return size_classes.get(self.size, 'button-medium')
    class Meta:
        verbose_name = "Dashboard Button"
        verbose_name_plural = "Dashboard Buttons"
