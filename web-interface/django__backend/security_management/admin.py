"""
Configuration de l'interface d'administration pour le module Security Management.

Ce fichier définit comment les modèles du module Security Management sont
affichés et gérés dans l'interface d'administration Django.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .infrastructure.models import (
    SecurityRuleModel,
    SecurityAlertModel,
    CorrelationRuleModel,
    CorrelationRuleMatchModel,
    TrafficBaselineModel,
    TrafficAnomalyModel,
    IPReputationModel,
    SecurityPolicyModel,
    VulnerabilityModel,
    ThreatIntelligenceModel,
    IncidentResponseWorkflowModel,
    IncidentResponseExecutionModel,
    SecurityReportModel,
    AuditLogModel,
    SuricataAlert,
    SecurityEvent,
    AutoSecurityReport,
    AutoReportAlert,
    SecurityMonitoringMetrics
)


@admin.register(SecurityRuleModel)
class SecurityRuleAdmin(admin.ModelAdmin):
    """Interface d'administration pour les règles de sécurité."""
    list_display = ('name', 'rule_type', 'priority', 'enabled', 'action', 'trigger_count', 'creation_date')
    list_filter = ('rule_type', 'enabled', 'action', 'protocol', 'creation_date')
    search_fields = ('name', 'description', 'source_ip', 'destination_ip')
    readonly_fields = ('creation_date', 'last_modified', 'trigger_count')
    ordering = ('priority', 'name')


@admin.register(SecurityAlertModel)
class SecurityAlertAdmin(admin.ModelAdmin):
    """Interface d'administration pour les alertes de sécurité."""
    list_display = ('title', 'severity', 'status', 'source_ip', 'destination_ip', 'detection_time', 'false_positive')
    list_filter = ('severity', 'status', 'false_positive', 'detection_time', 'protocol')
    search_fields = ('title', 'description', 'source_ip', 'destination_ip')
    readonly_fields = ('detection_time',)
    date_hierarchy = 'detection_time'


@admin.register(CorrelationRuleModel)
class CorrelationRuleAdmin(admin.ModelAdmin):
    """Interface d'administration pour les règles de corrélation."""
    list_display = ('name', 'threshold', 'time_window', 'severity', 'enabled', 'trigger_count', 'last_triggered')
    list_filter = ('enabled', 'severity', 'creation_date')
    search_fields = ('name', 'description')
    readonly_fields = ('creation_date', 'last_modified', 'last_triggered', 'trigger_count')


@admin.register(CorrelationRuleMatchModel)
class CorrelationRuleMatchAdmin(admin.ModelAdmin):
    """Interface d'administration pour les correspondances de règles de corrélation."""
    list_display = ('rule', 'matched_at')
    list_filter = ('matched_at', 'rule')
    search_fields = ('rule__name',)
    readonly_fields = ('matched_at',)
    date_hierarchy = 'matched_at'


@admin.register(TrafficBaselineModel)
class TrafficBaselineAdmin(admin.ModelAdmin):
    """Interface d'administration pour les baselines de trafic."""
    list_display = ('name', 'network_segment', 'service', 'avg_requests_per_minute', 'is_learning', 'last_updated')
    list_filter = ('is_learning', 'last_updated')
    search_fields = ('name', 'network_segment', 'service')
    readonly_fields = ('last_updated', 'creation_date')


@admin.register(TrafficAnomalyModel)
class TrafficAnomalyAdmin(admin.ModelAdmin):
    """Interface d'administration pour les anomalies de trafic."""
    list_display = ('baseline', 'anomaly_type', 'severity', 'source_ip', 'timestamp')
    list_filter = ('anomaly_type', 'severity', 'timestamp')
    search_fields = ('source_ip', 'baseline__name')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(IPReputationModel)
class IPReputationAdmin(admin.ModelAdmin):
    """Interface d'administration pour la réputation IP."""
    list_display = ('ip_address', 'reputation_score', 'classification', 'is_blacklisted', 'last_seen')
    list_filter = ('classification', 'is_blacklisted', 'is_whitelisted', 'last_seen')
    search_fields = ('ip_address',)
    readonly_fields = ('first_seen', 'last_seen')


@admin.register(SecurityPolicyModel)
class SecurityPolicyAdmin(admin.ModelAdmin):
    """Interface d'administration pour les politiques de sécurité."""
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VulnerabilityModel)
class VulnerabilityAdmin(admin.ModelAdmin):
    """Interface d'administration pour les vulnérabilités."""
    list_display = ('title', 'cve_id', 'severity', 'cvss_score', 'status', 'discovered_date')
    list_filter = ('severity', 'status', 'discovered_date')
    search_fields = ('cve_id', 'title', 'description')
    readonly_fields = ('discovered_date', 'published_date', 'patched_date')
    date_hierarchy = 'discovered_date'


@admin.register(ThreatIntelligenceModel)
class ThreatIntelligenceAdmin(admin.ModelAdmin):
    """Interface d'administration pour la threat intelligence."""
    list_display = ('indicator_type', 'indicator_value', 'threat_type', 'confidence', 'first_seen')
    list_filter = ('indicator_type', 'threat_type', 'confidence', 'first_seen')
    search_fields = ('indicator_value', 'description')
    readonly_fields = ('first_seen', 'last_seen')


@admin.register(IncidentResponseWorkflowModel)
class IncidentResponseWorkflowAdmin(admin.ModelAdmin):
    """Interface d'administration pour les workflows de réponse aux incidents."""
    list_display = ('name', 'trigger_type', 'status', 'auto_execute', 'created_at')
    list_filter = ('trigger_type', 'status', 'auto_execute', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'execution_count', 'success_count', 'last_executed')


@admin.register(IncidentResponseExecutionModel)
class IncidentResponseExecutionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les exécutions de réponse aux incidents."""
    list_display = ('workflow', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at', 'workflow')
    search_fields = ('workflow__name',)
    readonly_fields = ('started_at', 'completed_at')
    date_hierarchy = 'started_at'


@admin.register(SecurityReportModel)
class SecurityReportAdmin(admin.ModelAdmin):
    """Interface d'administration pour les rapports de sécurité."""
    list_display = ('name', 'report_type', 'status', 'generated_at', 'created_at')
    list_filter = ('report_type', 'status', 'generated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('generated_at', 'created_at')
    date_hierarchy = 'generated_at'


@admin.register(AuditLogModel)
class AuditLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'audit."""
    list_display = ('user', 'action', 'entity_type', 'entity_id', 'timestamp', 'ip_address')
    list_filter = ('action', 'entity_type', 'timestamp')
    search_fields = ('user', 'entity_id', 'ip_address')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel de logs d'audit."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification des logs d'audit."""
        return False


@admin.register(SuricataAlert)
class SuricataAlertAdmin(admin.ModelAdmin):
    """Interface d'administration pour les alertes Suricata."""
    list_display = ('alert_id', 'signature_short', 'severity_display', 'source_ip', 'destination_ip', 'timestamp', 'processed', 'auto_report_triggered')
    list_filter = ('severity', 'processed', 'auto_report_triggered', 'timestamp', 'category')
    search_fields = ('alert_id', 'signature', 'source_ip', 'destination_ip')
    readonly_fields = ('alert_id', 'timestamp', 'created_at', 'processed_at')
    date_hierarchy = 'timestamp'
    
    def signature_short(self, obj):
        """Affiche une version courte de la signature."""
        return obj.signature[:50] + "..." if len(obj.signature) > 50 else obj.signature
    signature_short.short_description = 'Signature'
    
    def severity_display(self, obj):
        """Affiche la sévérité avec des couleurs."""
        colors = {1: 'red', 2: 'orange', 3: 'yellow', 4: 'green'}
        color = colors.get(obj.severity, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_severity_display())
    severity_display.short_description = 'Sévérité'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Interface d'administration pour les événements de sécurité."""
    list_display = ('title', 'event_type', 'severity', 'source_ip', 'destination_ip', 'detected_at')
    list_filter = ('event_type', 'severity', 'detected_at')
    search_fields = ('title', 'description', 'source_ip', 'destination_ip')
    readonly_fields = ('detected_at', 'processed_at')
    date_hierarchy = 'detected_at'


@admin.register(AutoSecurityReport)
class AutoSecurityReportAdmin(admin.ModelAdmin):
    """Interface d'administration pour les rapports automatiques de sécurité."""
    list_display = ('session_id', 'title', 'report_type', 'status', 'total_alerts', 'critical_alerts', 'created_at')
    list_filter = ('report_type', 'status', 'created_at', 'email_sent', 'telegram_sent')
    search_fields = ('session_id', 'title', 'description')
    readonly_fields = ('session_id', 'created_at', 'generated_at', 'sent_at', 'generation_task_id', 'notification_task_id')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        """Les rapports automatiques sont générés par le système."""
        return False


@admin.register(AutoReportAlert)
class AutoReportAlertAdmin(admin.ModelAdmin):
    """Interface d'administration pour les liaisons rapport-alerte."""
    list_display = ('report', 'alert', 'included_at')
    list_filter = ('included_at',)
    search_fields = ('report__session_id', 'alert__alert_id')
    readonly_fields = ('included_at',)
    date_hierarchy = 'included_at'
    
    def has_add_permission(self, request):
        """Les liaisons sont créées automatiquement."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les liaisons ne doivent pas être modifiées."""
        return False


@admin.register(SecurityMonitoringMetrics)
class SecurityMonitoringMetricsAdmin(admin.ModelAdmin):
    """Interface d'administration pour les métriques de monitoring de sécurité."""
    list_display = ('scan_timestamp', 'new_alerts_found', 'critical_alerts', 'high_alerts', 'reports_triggered', 'elasticsearch_available')
    list_filter = ('scan_timestamp', 'elasticsearch_available', 'suricata_running', 'celery_worker_available')
    readonly_fields = ('scan_timestamp', 'scan_duration_seconds', 'average_response_time')
    date_hierarchy = 'scan_timestamp'
    
    def has_add_permission(self, request):
        """Les métriques sont générées automatiquement."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les métriques ne doivent pas être modifiées."""
        return False