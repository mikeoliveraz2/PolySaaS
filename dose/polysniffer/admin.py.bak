"""
PolySniffer Admin
"""
from django.contrib import admin
from .models import TrafficLog


@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = ('method', 'path', 'status_code', 'endpoint_name', 'user', 'captured_at', 'duration_ms')
    list_filter = ('method', 'status_code', 'endpoint_name', 'captured_at')
    search_fields = ('url', 'path', 'endpoint_name', 'user__username')
    readonly_fields = (
        'method', 'url', 'path', 'headers', 'cookies', 'query_params', 'body',
        'status_code', 'response_headers', 'response_body', 'response_size',
        'endpoint_name', 'user', 'captured_at', 'duration_ms', 'har_data'
    )
    ordering = ['-captured_at']

    fieldsets = [
        ('Request', {
            'fields': ('method', 'url', 'path', 'headers', 'cookies', 'query_params', 'body')
        }),
        ('Response', {
            'fields': ('status_code', 'response_headers', 'response_body', 'response_size')
        }),
        ('Metadata', {
            'fields': ('endpoint_name', 'user', 'captured_at', 'duration_ms')
        }),
        ('HAR Data', {
            'fields': ('har_data',),
            'classes': ('collapse',)
        }),
    ]

    def has_add_permission(self, request):
        # Logs are created automatically, not manually
        return False

