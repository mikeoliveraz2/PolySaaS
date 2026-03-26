"""
Machine Learning Studio Admin Configuration

This module registers proxy models so they appear grouped under
the "Machine Learning Studio" section in Django admin.
"""

from django.contrib import admin
from .models import MLEngineProxy, MLTaxonomyProxy, MLDatasetProxy, MLPromptProxy


@admin.register(MLEngineProxy)
class MLEngineStudioAdmin(admin.ModelAdmin):
    """Admin for ML Engines in Machine Learning Studio"""
    list_display = ('engineName', 'engineEndPoint', 'matchingEventKey', 'description')
    list_filter = ('engineName',)
    search_fields = ('engineName', 'description', 'engineEndPoint')
    fieldsets = [
        ('Engine Configuration', {
            'fields': ['engineName', 'engineEndPoint', 'matchingEventKey', 'description']
        }),
        ('Parameters', {
            'fields': ['parameters_json'],
            'classes': ('collapse',)
        }),
    ]


@admin.register(MLTaxonomyProxy)
class MLTaxonomyStudioAdmin(admin.ModelAdmin):
    """Admin for ML Taxonomies in Machine Learning Studio"""
    list_display = ('id', 'description', 'matchingEventKey', 'pub_date')
    list_filter = ('pub_date',)
    search_fields = ('description', 'matchingEventKey')
    fieldsets = [
        ('Taxonomy Configuration', {
            'fields': ['matchingEventKey', 'description', 'content_json']
        }),
    ]


@admin.register(MLDatasetProxy)
class MLDatasetStudioAdmin(admin.ModelAdmin):
    """Admin for ML Datasets in Machine Learning Studio"""
    list_display = ('id', 'description', 'matchingEventKey', 'isTraining', 'pub_date')
    list_filter = ('isTraining', 'pub_date')
    search_fields = ('description', 'matchingEventKey')
    fieldsets = [
        ('Dataset Configuration', {
            'fields': ['matchingEventKey', 'description', 'isTraining', 'content_json']
        }),
    ]


@admin.register(MLPromptProxy)
class MLPromptStudioAdmin(admin.ModelAdmin):
    """Admin for ML Prompts in Machine Learning Studio"""
    list_display = ('user', 'prompt', 'response', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('prompt', 'response', 'user__username')
    readonly_fields = ('response', 'created_at', 'updated_at')
    fieldsets = [
        ('Prompt', {
            'fields': ['user', 'prompt']
        }),
        ('Response', {
            'fields': ['response'],
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ('collapse',)
        }),
    ]
