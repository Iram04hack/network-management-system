"""
Configuration de l'interface d'administration pour le module Reporting.

Ce fichier définit comment les modèles du module Reporting sont
affichés et gérés dans l'interface d'administration Django.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Report, ScheduledReport, ReportTemplate


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Interface d'administration pour les rapports."""
    list_display = ('title', 'report_type', 'status', 'created_by', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'report_type')
    list_filter = ('report_type', 'status', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'report_type', 'status')
        }),
        (_('Configuration'), {
            'fields': ('template', 'parameters', 'content')
        }),
        (_('Métadonnées'), {
            'fields': ('created_by', 'created_at', 'updated_at', 'file_path'),
            'classes': ('collapse',)
        })
    )
    
    def get_status_display(self, obj):
        """Affichage coloré du statut."""
        colors = {
            'draft': 'gray',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_display.short_description = 'Statut'


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    """Interface d'administration pour les rapports planifiés."""
    list_display = ('report', 'frequency', 'is_active', 'next_run', 'last_run', 'created_at')
    search_fields = ('report__title', 'report__description')
    list_filter = ('frequency', 'is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'last_run')
    
    fieldsets = (
        (None, {
            'fields': ('report', 'frequency', 'is_active')
        }),
        (_('Planification'), {
            'fields': ('next_run', 'last_run')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates de rapport."""
    list_display = ('name', 'template_type', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'template_type')
    list_filter = ('template_type', 'is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'template_type', 'is_active')
        }),
        (_('Configuration'), {
            'fields': ('template_content', 'default_parameters')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
