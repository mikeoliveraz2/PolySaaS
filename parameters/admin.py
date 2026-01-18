from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Parameter


class ParameterAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for Parameter model
    """
    fieldsets = [
        ('Basic Information', {
            'fields': ['matchingKey', 'sequence', 'description']
        }),
        ('Parameter Values', {
            'fields': [
                'param1', 'param2', 'param3', 'param4', 'param5',
                'param6', 'param7', 'param8', 'param9', 'param10'
            ],
            'classes': ['collapse']
        }),
        ('Advanced Configuration', {
            'fields': ['param_kwargs_json'],
            'classes': ['collapse'],
            'description': 'JSON data for additional configuration parameters'
        }),
        ('Audit Information', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
    
    list_display = ('matchingKey', 'sequence', 'description', 'created_at', 'created_by')
    list_filter = ['created_at', 'sequence', 'created_by']
    search_fields = ['matchingKey', 'description', 'param1', 'param2', 'param3']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    def save_model(self, request, obj, form, change):
        """
        Set created_by field when saving
        """
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def response_add(self, request, obj, post_url_override=None):
        """
        Override to prevent popup and redirect properly
        """
        if '_popup' in request.POST:
            return HttpResponseRedirect(
                reverse('admin:parameters_parameter_changelist')
            )
        return super().response_add(request, obj, post_url_override)
    
    def response_change(self, request, obj):
        """
        Override to prevent popup and redirect properly
        """
        if '_popup' in request.POST:
            return HttpResponseRedirect(
                reverse('admin:parameters_parameter_changelist')
            )
        return super().response_change(request, obj)


admin.site.register(Parameter, ParameterAdmin)