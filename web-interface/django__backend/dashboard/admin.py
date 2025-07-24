"""
Configuration de l'interface d'administration pour le module Dashboard.

Ce fichier définit comment les modèles du module Dashboard sont
affichés et gérés dans l'interface d'administration Django.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    DashboardPreset,
    UserDashboardConfig,
    DashboardWidget,
    CustomDashboard,
    DashboardViewLog
)


class DashboardWidgetInline(admin.TabularInline):
    """Inline pour les widgets dans les configurations et préréglages."""
    model = DashboardWidget
    extra = 1
    fields = ('widget_type', 'position_x', 'position_y', 'width', 'height', 'settings')


@admin.register(DashboardPreset)
class DashboardPresetAdmin(admin.ModelAdmin):
    """Interface d'administration pour les préréglages de tableau de bord."""
    list_display = ('name', 'theme', 'layout', 'is_default', 'created_at')
    list_filter = ('is_default', 'theme', 'layout')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_default')
        }),
        (_('Apparence'), {
            'fields': ('theme', 'layout', 'refresh_interval')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [DashboardWidgetInline]


@admin.register(UserDashboardConfig)
class UserDashboardConfigAdmin(admin.ModelAdmin):
    """Interface d'administration pour les configurations utilisateur."""
    list_display = ('user', 'theme', 'layout', 'refresh_interval', 'updated_at')
    list_filter = ('theme', 'layout')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('Apparence'), {
            'fields': ('theme', 'layout', 'refresh_interval')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [DashboardWidgetInline]


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """Interface d'administration pour les widgets."""
    list_display = ('widget_type', 'config', 'preset', 'position_x', 'position_y', 'width', 'height')
    list_filter = ('widget_type', 'config__user', 'preset')
    search_fields = ('config__user__username', 'preset__name')
    fieldsets = (
        (None, {
            'fields': ('config', 'preset', 'widget_type')
        }),
        (_('Position et taille'), {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        (_('Paramètres'), {
            'fields': ('settings',)
        })
    )


@admin.register(CustomDashboard)
class CustomDashboardAdmin(admin.ModelAdmin):
    """Interface d'administration pour les dashboards personnalisés."""
    list_display = ('name', 'owner', 'is_default', 'is_public', 'created_at', 'updated_at')
    list_filter = ('is_default', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'owner')
        }),
        (_('Configuration'), {
            'fields': ('layout', 'is_default', 'is_public')
        }),
        (_('Métadonnées'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DashboardViewLog)
class DashboardViewLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs de vue."""
    list_display = ('user', 'dashboard', 'timestamp', 'duration', 'ip_address')
    list_filter = ('timestamp', 'dashboard', 'user')
    search_fields = ('user__username', 'dashboard__name', 'ip_address')
    readonly_fields = ('user', 'dashboard', 'timestamp', 'session_id', 'ip_address', 'user_agent', 'duration')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel de logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification des logs."""
        return False 