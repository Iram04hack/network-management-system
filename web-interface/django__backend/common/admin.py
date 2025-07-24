"""
Configuration de l'interface d'administration pour le module Common - Infrastructure.

Ce fichier définit comment les modèles du module Common sont
affichés et gérés dans l'interface d'administration Django.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    GNS3ServerConfig,
    GNS3EventLog,
    GNS3ModuleSubscription,
    GNS3ServiceMetrics,
    GNS3WebSocketConnection
)


@admin.register(GNS3ServerConfig)
class GNS3ServerConfigAdmin(admin.ModelAdmin):
    """Interface d'administration pour la configuration des serveurs GNS3."""
    list_display = ('name', 'host', 'port', 'protocol', 'is_active', 'is_default', 'connection_status', 'last_connection_test')
    list_filter = ('is_active', 'is_default', 'connection_status', 'protocol')
    search_fields = ('name', 'host', 'username')
    readonly_fields = ('created_at', 'updated_at', 'last_connection_test')
    ordering = ('-is_default', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active', 'is_default')
        }),
        (_('Configuration de connexion'), {
            'fields': ('host', 'port', 'protocol', 'username', 'password', 'verify_ssl', 'timeout')
        }),
        (_('Statut'), {
            'fields': ('connection_status', 'last_connection_test')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_connection_status_display(self, obj):
        """Affichage coloré du statut de connexion."""
        colors = {
            'connected': 'green',
            'disconnected': 'red',
            'error': 'orange',
            'unknown': 'gray'
        }
        color = colors.get(obj.connection_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_connection_status_display()
        )
    get_connection_status_display.short_description = 'Statut de connexion'


@admin.register(GNS3EventLog)
class GNS3EventLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'événements GNS3."""
    list_display = ('event_type', 'source', 'priority', 'delivery_status', 'project_id', 'node_id', 'created_at')
    list_filter = ('event_type', 'priority', 'delivery_status', 'source', 'created_at')
    search_fields = ('event_id', 'event_type', 'project_id', 'node_id', 'correlation_id')
    readonly_fields = ('created_at', 'processed_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('event_id', 'event_type', 'source', 'priority')
        }),
        (_('Contexte GNS3'), {
            'fields': ('project_id', 'node_id', 'target_modules')
        }),
        (_('Données'), {
            'fields': ('data', 'correlation_id')
        }),
        (_('Livraison'), {
            'fields': ('delivery_status', 'retry_count')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel de logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification des logs."""
        return False


@admin.register(GNS3ModuleSubscription)
class GNS3ModuleSubscriptionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les abonnements des modules GNS3."""
    list_display = ('module_name', 'is_active', 'events_received_count', 'events_processed_count', 'events_failed_count', 'last_event_received')
    list_filter = ('is_active', 'created_at', 'last_event_received')
    search_fields = ('module_name', 'callback_url')
    readonly_fields = ('created_at', 'updated_at', 'last_event_received', 'events_received_count', 'events_processed_count', 'events_failed_count')
    
    fieldsets = (
        (None, {
            'fields': ('module_name', 'is_active', 'callback_url')
        }),
        (_('Abonnements'), {
            'fields': ('subscription_types',)
        }),
        (_('Statistiques'), {
            'fields': ('events_received_count', 'events_processed_count', 'events_failed_count', 'last_event_received'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_success_rate(self, obj):
        """Calcule et affiche le taux de succès."""
        if obj.events_received_count == 0:
            return "N/A"
        success_rate = (obj.events_processed_count / obj.events_received_count) * 100
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            'green' if success_rate >= 95 else 'orange' if success_rate >= 80 else 'red',
            success_rate
        )
    get_success_rate.short_description = 'Taux de succès'


@admin.register(GNS3ServiceMetrics)
class GNS3ServiceMetricsAdmin(admin.ModelAdmin):
    """Interface d'administration pour les métriques du service GNS3."""
    list_display = ('timestamp', 'service_status', 'gns3_server_connected', 'nodes_total', 'nodes_running', 'projects_total', 'cache_hit_ratio')
    list_filter = ('service_status', 'gns3_server_connected', 'redis_cache_available', 'timestamp')
    readonly_fields = ('timestamp', 'service_status', 'gns3_server_connected', 'redis_cache_available', 
                      'websocket_connections_active', 'events_processed_total', 'api_calls_total', 
                      'cache_hits_total', 'cache_misses_total', 'cache_hit_ratio', 'nodes_total', 
                      'nodes_running', 'projects_total', 'projects_active', 'uptime_seconds')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        (_('Statut du service'), {
            'fields': ('timestamp', 'service_status', 'gns3_server_connected', 'redis_cache_available', 'websocket_connections_active')
        }),
        (_('Métriques d\'événements'), {
            'fields': ('events_processed_total', 'events_processed_last_hour', 'events_failed_total', 'events_retried_total')
        }),
        (_('Métriques API'), {
            'fields': ('api_calls_total', 'api_calls_last_hour', 'api_errors_total', 'average_response_time_ms')
        }),
        (_('Métriques de cache'), {
            'fields': ('cache_hits_total', 'cache_misses_total', 'cache_hit_ratio')
        }),
        (_('Métriques réseau'), {
            'fields': ('nodes_total', 'nodes_running', 'projects_total', 'projects_active')
        }),
        (_('Informations système'), {
            'fields': ('uptime_seconds', 'memory_usage_mb', 'cpu_usage_percent')
        })
    )
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel de métriques."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification des métriques."""
        return False
    
    def get_cache_hit_ratio_display(self, obj):
        """Affichage coloré du taux de cache hit."""
        ratio = obj.cache_hit_ratio
        color = 'green' if ratio >= 80 else 'orange' if ratio >= 60 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            ratio
        )
    get_cache_hit_ratio_display.short_description = 'Taux de cache hit'


@admin.register(GNS3WebSocketConnection)
class GNS3WebSocketConnectionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les connexions WebSocket GNS3."""
    list_display = ('connection_id', 'user', 'client_ip', 'is_active', 'connected_at', 'last_heartbeat', 'events_sent')
    list_filter = ('is_active', 'connected_at', 'last_heartbeat')
    search_fields = ('connection_id', 'user__username', 'client_ip')
    readonly_fields = ('connected_at', 'last_heartbeat', 'disconnected_at', 'events_sent', 'messages_received')
    date_hierarchy = 'connected_at'
    ordering = ('-connected_at',)
    
    fieldsets = (
        (None, {
            'fields': ('connection_id', 'channel_name', 'user', 'is_active')
        }),
        (_('Informations client'), {
            'fields': ('client_ip', 'user_agent')
        }),
        (_('Abonnements'), {
            'fields': ('subscriptions',)
        }),
        (_('Statistiques'), {
            'fields': ('events_sent', 'messages_received')
        }),
        (_('Métadonnées'), {
            'fields': ('connected_at', 'last_heartbeat', 'disconnected_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel de connexions."""
        return False
    
    def get_connection_duration(self, obj):
        """Calcule la durée de connexion."""
        if obj.disconnected_at:
            duration = obj.disconnected_at - obj.connected_at
        else:
            from django.utils import timezone
            duration = timezone.now() - obj.connected_at
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    get_connection_duration.short_description = 'Durée de connexion'