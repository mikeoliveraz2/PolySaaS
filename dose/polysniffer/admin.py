"""
PolySniffer Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import TrafficCapture, TrafficLog
from .schema_patch import ensure_trafficlog_capture_columns


@admin.register(TrafficCapture)
class TrafficCaptureAdmin(admin.ModelAdmin):
    list_display = ('capture_name', 'tenant', 'is_active', 'created_at', 'expires_at', 'log_count_display')
    list_filter = ('tenant', 'is_active', 'created_at')
    search_fields = ('capture_name', 'description')
    readonly_fields = ('created_at',)
    actions = ['start_capture', 'stop_capture']

    def log_count_display(self, obj):
        count = obj.logs.count()
        if count:
            return format_html('<a href="/admin/dose/trafficlog/?capture_session__id={}">{} logs</a>', obj.id, count)
        return '0'
    log_count_display.short_description = "Logs"

    def start_capture(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_active=True, expires_at=timezone.now() + timezone.timedelta(hours=8))
    start_capture.short_description = "Start / extend selected captures"

    def stop_capture(self, request, queryset):
        queryset.update(is_active=False)
    stop_capture.short_description = "Stop selected captures"


@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = (
        'method', 'path', 'capture_source', 'service', 'status_code',
        'duration_ms', 'captured_at', 'user',
    )
    list_filter = (
        'method', 'status_code', 'capture_source', 'service',
        'endpoint_name', 'captured_at', 'capture_session',
    )
    search_fields = ('url', 'path', 'endpoint_name', 'correlation_id', 'user__username')
    readonly_fields = (
        'method', 'url', 'path', 'client_path', 'capture_source', 'service', 'correlation_id',
        'headers', 'cookies', 'query_params', 'body',
        'status_code', 'response_headers', 'response_body', 'response_size',
        'endpoint_name', 'capture_session', 'user', 'captured_at', 'duration_ms', 'har_data'
    )
    ordering = ['-captured_at']

    fieldsets = [
        ('Request', {
            'fields': ('method', 'url', 'path', 'client_path', 'capture_source', 'service', 'correlation_id',
                      'headers', 'cookies', 'query_params', 'body')
        }),
        ('Response', {
            'fields': ('status_code', 'response_headers', 'response_body', 'response_size')
        }),
        ('Metadata', {
            'fields': ('endpoint_name', 'capture_session', 'user', 'captured_at', 'duration_ms')
        }),
        ('HAR Data', {
            'fields': ('har_data',),
            'classes': ('collapse',)
        }),
    ]

    def get_queryset(self, request):
        ensure_trafficlog_capture_columns(request)
        return super().get_queryset(request)

    def has_add_permission(self, request):
        # Logs are created automatically, not manually
        return False

