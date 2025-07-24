from django.contrib import admin
from django.utils.html import format_html
from .models import (
    QoSPolicy, 
    TrafficClass, 
    TrafficClassifier, 
    InterfaceQoSPolicy, 
    SLAComplianceRecord,
    QoSStatistics,
    QoSRecommendation,
    PolicyApplicationLog
)

@admin.register(QoSPolicy)
class QoSPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'policy_type', 'priority', 'bandwidth_limit', 'status')
    list_filter = ('policy_type', 'status', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-priority', 'name')

@admin.register(TrafficClass)
class TrafficClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'policy', 'priority', 'bandwidth', 'bandwidth_percent')
    list_filter = ('policy', 'priority', 'created_at')
    search_fields = ('name', 'description', 'policy__name')
    ordering = ('policy', 'priority')

@admin.register(TrafficClassifier)
class TrafficClassifierAdmin(admin.ModelAdmin):
    list_display = ('traffic_class', 'protocol', 'source_ip', 'destination_ip')
    list_filter = ('protocol', 'traffic_class', 'created_at')
    search_fields = ('description', 'traffic_class__name', 'protocol')

@admin.register(InterfaceQoSPolicy)
class InterfaceQoSPolicyAdmin(admin.ModelAdmin):
    list_display = ('interface_name', 'policy', 'direction', 'applied_at')
    list_filter = ('direction', 'policy', 'applied_at')
    search_fields = ('interface_name', 'policy__name')

@admin.register(SLAComplianceRecord)
class SLAComplianceRecordAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'device_id', 'timestamp', 'period', 'compliance_percentage', 'is_compliant')
    list_filter = ('period', 'timestamp')
    search_fields = ('device_name',)
    readonly_fields = ('compliance_percentage', 'is_compliant')
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('Informations de base', {
            'fields': ('device_id', 'device_name', 'timestamp', 'period', 'overall_compliance')
        }),
        ('Métriques', {
            'fields': ('compliance_percentage', 'is_compliant', 'service_class_compliances', 'metrics')
        }),
        ('Analyse', {
            'fields': ('issues', 'recommendations'),
            'classes': ('collapse',)
        })
    )


@admin.register(QoSStatistics)
class QoSStatisticsAdmin(admin.ModelAdmin):
    """Interface d'administration pour les statistiques QoS."""
    list_display = ('interface_name', 'timestamp', 'utilization_display', 'congestion_display', 'packets_dropped', 'overlimits')
    list_filter = ('timestamp', 'congestion_level', 'interface_name', 'device_id')
    search_fields = ('interface_name',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def utilization_display(self, obj):
        """Affiche l'utilisation avec couleur."""
        if obj.utilization_percentage > 80:
            color = 'red'
        elif obj.utilization_percentage > 60:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, obj.utilization_percentage)
    utilization_display.short_description = 'Utilisation'
    
    def congestion_display(self, obj):
        """Affiche le niveau de congestion avec couleur."""
        colors = {'critical': 'red', 'high': 'orange', 'medium': 'yellow', 'low': 'blue', 'normal': 'green'}
        color = colors.get(obj.congestion_level, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_congestion_level_display())
    congestion_display.short_description = 'Congestion'
    
    def has_add_permission(self, request):
        """Les statistiques sont collectées automatiquement."""
        return False


@admin.register(QoSRecommendation)
class QoSRecommendationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les recommandations QoS."""
    list_display = ('title', 'recommendation_type', 'priority_display', 'status', 'interface_name', 'generated_at')
    list_filter = ('recommendation_type', 'priority', 'status', 'generated_at')
    search_fields = ('title', 'description', 'interface_name')
    readonly_fields = ('generated_at', 'applied_at', 'generated_by_engine')
    date_hierarchy = 'generated_at'
    
    def priority_display(self, obj):
        """Affiche la priorité avec couleur."""
        colors = {'critical': 'red', 'high': 'orange', 'medium': 'blue', 'low': 'green'}
        color = colors.get(obj.priority, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_priority_display())
    priority_display.short_description = 'Priorité'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'recommendation_type', 'priority', 'status')
        }),
        ('Détails techniques', {
            'fields': ('description', 'interface_name', 'recommended_action', 'recommended_configuration')
        }),
        ('Métriques et impact', {
            'fields': ('confidence_score', 'expected_improvement', 'effectiveness_score')
        }),
        ('Métadonnées', {
            'fields': ('generated_at', 'generated_by_engine', 'applied_at', 'applied_by'),
            'classes': ('collapse',)
        })
    )


@admin.register(PolicyApplicationLog)
class PolicyApplicationLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'application de politiques QoS."""
    list_display = ('policy', 'interface_name', 'action_type', 'success_display', 'applied_at', 'applied_by')
    list_filter = ('action_type', 'trigger_source', 'success', 'applied_at')
    search_fields = ('policy__name', 'interface_name', 'applied_by')
    readonly_fields = ('applied_at', 'execution_time_ms', 'celery_task_id')
    date_hierarchy = 'applied_at'
    
    def success_display(self, obj):
        """Affiche le succès avec couleur."""
        if obj.success:
            return format_html('<span style="color: green; font-weight: bold;">✅ Succès</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">❌ Échec</span>')
    success_display.short_description = 'Statut'
    
    def has_add_permission(self, request):
        """Les logs sont créés automatiquement lors de l'application de politiques."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les logs ne doivent pas être modifiés."""
        return False
    
    fieldsets = (
        ('Application de politique', {
            'fields': ('policy', 'interface_name', 'action_type', 'trigger_source', 'success')
        }),
        ('Détails de l\'exécution', {
            'fields': ('applied_configuration', 'previous_configuration', 'error_message', 'execution_time_ms')
        }),
        ('Performance', {
            'fields': ('performance_before', 'performance_after'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('applied_at', 'applied_by', 'celery_task_id', 'additional_metadata'),
            'classes': ('collapse',)
        })
    ) 