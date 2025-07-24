"""
Configuration de l'interface d'administration Django pour le module monitoring.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    # Alertes
    Alert, AlertComment, AlertHistory,
    
    # Métriques
    MetricsDefinition, DeviceMetric, MetricValue, 
    ThresholdRule, AnomalyDetectionConfig, MetricThreshold,
    
    # Vérifications de service
    MonitoringTemplate, ServiceCheck, DeviceServiceCheck, CheckResult,
    
    # Notifications
    Notification, NotificationChannel, NotificationRule,
    
    # Tableaux de bord
    Dashboard, DashboardWidget, SavedView, BusinessKPI, KPIHistory
)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Configuration admin pour les alertes."""
    list_display = ['id', 'device', 'severity', 'status', 'message', 'created_at']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['device__name', 'message']
    readonly_fields = ['created_at', 'updated_at', 'acknowledged_at', 'resolved_at']
    date_hierarchy = 'created_at'
    fieldsets = [
        ('Général', {'fields': ['device', 'message', 'severity', 'status', 'value']}),
        ('Relations', {'fields': ['service_check', 'metric']}),
        ('Dates', {'fields': ['created_at', 'updated_at', 'acknowledged_at', 'resolved_at']}),
        ('Utilisateurs', {'fields': ['acknowledged_by', 'resolved_by']}),
        ('Commentaires', {'fields': ['acknowledgement_comment', 'resolution_comment']}),
    ]
    raw_id_fields = ['device', 'service_check', 'metric', 'acknowledged_by', 'resolved_by']
    actions = ['acknowledge_alerts', 'resolve_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        """Action pour prendre en compte plusieurs alertes."""
        count = 0
        for alert in queryset:
            if alert.status == 'active':
                alert.acknowledge(user=request.user)
                count += 1
        self.message_user(request, f"{count} alertes ont été prises en compte.")
    acknowledge_alerts.short_description = "Prendre en compte les alertes sélectionnées"
    
    def resolve_alerts(self, request, queryset):
        """Action pour résoudre plusieurs alertes."""
        count = 0
        for alert in queryset:
            if alert.status in ['active', 'acknowledged']:
                alert.resolve(user=request.user)
                count += 1
        self.message_user(request, f"{count} alertes ont été résolues.")
    resolve_alerts.short_description = "Résoudre les alertes sélectionnées"


@admin.register(MetricsDefinition)
class MetricsDefinitionAdmin(admin.ModelAdmin):
    """Configuration admin pour les définitions de métriques."""
    list_display = ['name', 'metric_type', 'collection_method', 'unit', 'is_active']
    list_filter = ['metric_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    fieldsets = [
        ('Général', {'fields': ['name', 'description', 'metric_type', 'unit']}),
        ('Collecte', {'fields': ['collection_method', 'collection_parameters']}),
        ('Configuration', {'fields': ['is_active', 'retention_days']}),
        ('Seuils', {'fields': ['warning_threshold', 'critical_threshold']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DeviceMetric)
class DeviceMetricAdmin(admin.ModelAdmin):
    """Configuration admin pour les métriques d'équipement."""
    list_display = ['id', 'device', 'metric', 'interface', 'is_active', 'last_collection']
    list_filter = ['is_active', 'metric', 'created_at']
    search_fields = ['device__name', 'metric__name']
    raw_id_fields = ['device', 'metric', 'interface']
    fieldsets = [
        ('Général', {'fields': ['device', 'metric', 'interface']}),
        ('Configuration', {'fields': ['is_active', 'collection_interval', 'custom_parameters']}),
        ('Collecte', {'fields': ['last_collection', 'next_collection']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['last_collection', 'next_collection', 'created_at', 'updated_at']


@admin.register(MonitoringTemplate)
class MonitoringTemplateAdmin(admin.ModelAdmin):
    """Configuration admin pour les templates de surveillance."""
    list_display = ['name', 'check_interval', 'retry_interval', 'max_check_attempts', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    fieldsets = [
        ('Général', {'fields': ['name', 'description']}),
        ('Configuration', {'fields': ['check_interval', 'retry_interval', 'max_check_attempts']}),
        ('Options', {'fields': ['is_active', 'notification_enabled']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ServiceCheck)
class ServiceCheckAdmin(admin.ModelAdmin):
    """Configuration admin pour les vérifications de service."""
    list_display = ['name', 'check_type', 'template', 'is_active']
    list_filter = ['check_type', 'template', 'is_active']
    search_fields = ['name', 'description', 'check_command']
    raw_id_fields = ['template']
    fieldsets = [
        ('Général', {'fields': ['name', 'description']}),
        ('Type et commande', {'fields': ['check_type', 'check_command', 'check_parameters']}),
        ('Template', {'fields': ['template']}),
        ('Seuils', {'fields': ['warning_threshold', 'critical_threshold']}),
        ('Options', {'fields': ['is_active']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DeviceServiceCheck)
class DeviceServiceCheckAdmin(admin.ModelAdmin):
    """Configuration admin pour les vérifications de service d'équipement."""
    list_display = ['id', 'device', 'service_check', 'last_status', 'is_active', 'last_check_time']
    list_filter = ['is_active', 'last_status', 'service_check']
    search_fields = ['device__name', 'service_check__name']
    raw_id_fields = ['device', 'service_check']
    fieldsets = [
        ('Général', {'fields': ['device', 'service_check']}),
        ('Configuration', {'fields': ['is_active', 'override_parameters']}),
        ('Statut', {'fields': ['last_status', 'last_check_output', 'current_check_attempt']}),
        ('Planification', {'fields': ['last_check_time', 'next_check_time']}),
        ('Options', {'fields': ['notification_enabled']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['last_check_time', 'next_check_time', 'last_status', 'last_check_output', 
                      'current_check_attempt', 'created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Configuration admin pour les notifications."""
    list_display = ['id', 'user', 'title', 'level', 'source', 'is_read', 'created_at']
    list_filter = ['level', 'source', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    raw_id_fields = ['user', 'alert', 'device']
    fieldsets = [
        ('Général', {'fields': ['user', 'title', 'message']}),
        ('Détails', {'fields': ['level', 'source']}),
        ('Statut', {'fields': ['is_read', 'read_at']}),
        ('Relations', {'fields': ['alert', 'device']}),
        ('Actions', {'fields': ['action_url', 'action_text']}),
        ('Méta', {'fields': ['metadata']}),
        ('Dates', {'fields': ['created_at']}),
    ]
    readonly_fields = ['created_at', 'read_at']
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        """Action pour marquer plusieurs notifications comme lues."""
        count = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        self.message_user(request, f"{count} notifications ont été marquées comme lues.")
    mark_as_read.short_description = "Marquer les notifications sélectionnées comme lues"


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Configuration admin pour les tableaux de bord."""
    list_display = ['title', 'is_default', 'is_public', 'owner', 'created_at']
    list_filter = ['is_default', 'is_public', 'category']
    search_fields = ['title', 'description', 'uid']
    raw_id_fields = ['owner']
    fieldsets = [
        ('Général', {'fields': ['title', 'description', 'uid']}),
        ('Configuration', {'fields': ['layout', 'category']}),
        ('Options', {'fields': ['is_default', 'is_public']}),
        ('Relations', {'fields': ['owner']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['created_at', 'updated_at']


class ThresholdRuleInline(admin.TabularInline):
    """Règles de seuil inline pour les métriques d'équipement."""
    model = ThresholdRule
    extra = 1
    fields = ['name', 'warning_threshold', 'critical_threshold', 'comparison_operator', 'is_active']


class AnomalyDetectionConfigInline(admin.TabularInline):
    """Configuration de détection d'anomalies inline pour les métriques d'équipement."""
    model = AnomalyDetectionConfig
    extra = 0
    fields = ['name', 'algorithm', 'sensitivity', 'is_active']


# Ajouter les inlines à DeviceMetricAdmin
DeviceMetricAdmin.inlines = [ThresholdRuleInline, AnomalyDetectionConfigInline]


# Configuration des modèles de commentaires et historique d'alertes
@admin.register(AlertComment)
class AlertCommentAdmin(admin.ModelAdmin):
    """Configuration admin pour les commentaires d'alertes."""
    list_display = ['id', 'alert', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment', 'alert__message', 'user__username']
    raw_id_fields = ['alert', 'user']
    readonly_fields = ['created_at']


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    """Configuration admin pour l'historique des alertes."""
    list_display = ['id', 'alert', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['alert__message', 'user__username', 'details']
    raw_id_fields = ['alert', 'user']
    readonly_fields = ['timestamp']


@admin.register(MetricThreshold)
class MetricThresholdAdmin(admin.ModelAdmin):
    """Configuration admin pour les seuils de métriques."""
    list_display = ['id', 'metrics_definition', 'threshold_type', 'warning_value', 'critical_value']
    list_filter = ['threshold_type', 'comparison']
    search_fields = ['metrics_definition__name']
    raw_id_fields = ['metrics_definition']


# Configuration avancée pour les modèles de valeurs de métriques
@admin.register(MetricValue)
class MetricValueAdmin(admin.ModelAdmin):
    """Configuration admin pour les valeurs de métriques."""
    list_display = ['id', 'device_metric', 'value', 'timestamp']
    list_filter = ['timestamp', 'device_metric__metric']
    search_fields = ['device_metric__device__name', 'device_metric__metric__name']
    raw_id_fields = ['device_metric']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    """Configuration admin pour les résultats de vérifications."""
    list_display = ['id', 'device_service_check', 'status', 'execution_time', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['device_service_check__device__name', 'output']
    raw_id_fields = ['device_service_check']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


# Configuration avancée pour les règles de seuil
@admin.register(ThresholdRule)
class ThresholdRuleAdmin(admin.ModelAdmin):
    """Configuration admin pour les règles de seuil."""
    list_display = ['name', 'device_metric', 'warning_threshold', 'critical_threshold', 'is_active']
    list_filter = ['comparison_operator', 'is_active']
    search_fields = ['name', 'device_metric__device__name']
    raw_id_fields = ['device_metric']


@admin.register(AnomalyDetectionConfig)
class AnomalyDetectionConfigAdmin(admin.ModelAdmin):
    """Configuration admin pour la configuration de détection d'anomalies."""
    list_display = ['name', 'device_metric', 'algorithm', 'sensitivity', 'is_active']
    list_filter = ['algorithm', 'is_active']
    search_fields = ['name', 'device_metric__device__name']
    raw_id_fields = ['device_metric']


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Configuration admin pour les canaux de notification."""
    list_display = ['name', 'channel_type', 'is_active']
    list_filter = ['channel_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    """Configuration admin pour les règles de notification."""
    list_display = ['name', 'severity_threshold', 'is_active']
    list_filter = ['severity_threshold', 'is_active']
    search_fields = ['name', 'description']


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """Configuration admin pour les widgets de tableau de bord."""
    list_display = ['title', 'dashboard', 'widget_type', 'position']
    list_filter = ['widget_type', 'dashboard']
    search_fields = ['title', 'dashboard__title']
    raw_id_fields = ['dashboard']


@admin.register(SavedView)
class SavedViewAdmin(admin.ModelAdmin):
    """Configuration admin pour les vues sauvegardées."""
    list_display = ['name', 'user', 'view_type', 'created_at']
    list_filter = ['view_type', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    raw_id_fields = ['user']
    readonly_fields = ['created_at']


@admin.register(BusinessKPI)
class BusinessKPIAdmin(admin.ModelAdmin):
    """Configuration admin pour les KPI métier."""
    list_display = ['name', 'category', 'target_value', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']


@admin.register(KPIHistory)
class KPIHistoryAdmin(admin.ModelAdmin):
    """Configuration admin pour l'historique des KPI."""
    list_display = ['id', 'kpi', 'calculated_value', 'target_achievement', 'status', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['kpi__name']
    raw_id_fields = ['kpi']
    readonly_fields = ['timestamp', 'calculated_value', 'target_achievement']
    date_hierarchy = 'timestamp' 