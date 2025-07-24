"""
Module de configuration de l'interface d'administration Django pour le module Network Management.

Configuration complète de tous les modèles pour une gestion optimale.
"""

from django.contrib import admin
from .infrastructure.models import (
    # Modèles principaux
    NetworkDevice,
    NetworkInterface,
    DeviceConfiguration,
    NetworkConnection,
    
    # Modèles de configuration et templates
    ConfigurationTemplate,
    CompliancePolicy,
    ComplianceCheck,
    
    # Modèles de monitoring et alerting
    Alert,
    Metric,
    Log,
    
    # Modèles de topologie et dashboard
    Topology,
    NetworkTopology,
    DashboardConfiguration
)


@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les équipements réseau.
    """
    list_display = ('name', 'ip_address', 'device_type', 'vendor', 'is_active', 'created_at', 'updated_at')
    list_filter = ('device_type', 'vendor', 'is_active')
    search_fields = ('name', 'ip_address', 'vendor')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'hostname', 'ip_address', 'device_type', 'vendor', 'is_active')
        }),
        ('Informations détaillées', {
            'fields': ('manufacturer', 'model', 'os', 'os_version', 'location', 'description')
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'is_virtual', 'management_interface', 'created_at', 'updated_at')
        }),
    )


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les interfaces réseau.
    """
    list_display = ('name', 'device', 'ip_address', 'mac_address', 'interface_type', 'status')
    list_filter = ('interface_type', 'status', 'device')
    search_fields = ('name', 'ip_address', 'mac_address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'device', 'status')
        }),
        ('Informations réseau', {
            'fields': ('ip_address', 'subnet_mask', 'mac_address', 'interface_type', 'speed', 'mtu')
        }),
        ('Informations complémentaires', {
            'fields': ('description',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(DeviceConfiguration)
class DeviceConfigurationAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les configurations d'équipements.
    """
    list_display = ('device', 'version', 'is_active', 'status', 'created_by', 'created_at', 'applied_at')
    list_filter = ('is_active', 'status', 'device')
    search_fields = ('device__name', 'version', 'created_by')
    readonly_fields = ('created_at', 'applied_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('device', 'version', 'is_active', 'status')
        }),
        ('Configuration', {
            'fields': ('content', 'comment', 'created_by', 'parent')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'applied_at')
        }),
    )


@admin.register(NetworkConnection)
class NetworkConnectionAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les connexions entre équipements.
    """
    list_display = ('source_interface', 'target_interface', 'connection_type', 'status')
    list_filter = ('connection_type', 'status')
    search_fields = ('source_interface__name', 'target_interface__name', 'source_device__name', 'target_device__name')
    fieldsets = (
        ('Informations générales', {
            'fields': ('connection_type', 'status')
        }),
        ('Interfaces', {
            'fields': ('source_device', 'source_interface', 'target_device', 'target_interface')
        }),
        ('Informations complémentaires', {
            'fields': ('description',)
        }),
    )


@admin.register(Topology)
class TopologyAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les topologies réseau.
    """
    list_display = ('name', 'description', 'is_auto_discovered', 'created_by', 'created_at')
    list_filter = ('is_auto_discovered', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    # Le champ created_by n'est pas une ForeignKey dans ce modèle
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'is_auto_discovered')
        }),
        ('Données', {
            'fields': ('layout', 'devices', 'connections', 'tags')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(NetworkTopology)
class NetworkTopologyAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les topologies réseau GNS3.
    """
    list_display = ('name', 'topology_type', 'gns3_project_id', 'is_active', 'last_sync', 'created_at')
    list_filter = ('topology_type', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'gns3_project_id')
    readonly_fields = ('created_at', 'updated_at', 'last_sync')
    raw_id_fields = ('created_by',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'topology_type', 'is_active')
        }),
        ('Intégration GNS3', {
            'fields': ('gns3_project_id', 'last_sync')
        }),
        ('Données', {
            'fields': ('topology_data', 'layout_data', 'devices')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ConfigurationTemplate)
class ConfigurationTemplateAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les templates de configuration.
    """
    list_display = ('name', 'device_type', 'vendor', 'os_version', 'created_by', 'created_at')
    list_filter = ('device_type', 'vendor', 'created_at')
    search_fields = ('name', 'description', 'device_type', 'vendor')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description')
        }),
        ('Compatibilité', {
            'fields': ('device_type', 'vendor', 'os_version')
        }),
        ('Configuration', {
            'fields': ('content', 'variables', 'tags')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(CompliancePolicy)
class CompliancePolicyAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les politiques de conformité.
    """
    list_display = ('name', 'device_type', 'vendor', 'severity', 'created_by', 'created_at')
    list_filter = ('device_type', 'vendor', 'severity', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'severity')
        }),
        ('Applicabilité', {
            'fields': ('device_type', 'vendor')
        }),
        ('Règles', {
            'fields': ('rules',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les vérifications de conformité.
    """
    list_display = ('device', 'policy', 'is_compliant', 'checked_at', 'checked_by')
    list_filter = ('is_compliant', 'checked_at', 'policy')
    search_fields = ('device__name', 'policy__name', 'checked_by')
    readonly_fields = ('checked_at',)
    raw_id_fields = ('device', 'policy', 'configuration')
    fieldsets = (
        ('Vérification', {
            'fields': ('device', 'policy', 'configuration')
        }),
        ('Résultats', {
            'fields': ('is_compliant', 'results')
        }),
        ('Métadonnées', {
            'fields': ('checked_at', 'checked_by')
        }),
    )


@admin.register(Alert)
class NetworkAlertAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les alertes réseau.
    """
    list_display = ('title', 'device', 'interface', 'severity', 'status', 'source', 'created_at')
    list_filter = ('severity', 'status', 'source', 'category', 'acknowledged', 'created_at')
    search_fields = ('title', 'message', 'device__name', 'interface__name')
    readonly_fields = ('created_at', 'updated_at', 'acknowledged_at')
    raw_id_fields = ('device', 'interface')
    date_hierarchy = 'created_at'
    actions = ['acknowledge_alerts', 'resolve_alerts']
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'message', 'severity', 'status')
        }),
        ('Source', {
            'fields': ('source', 'category', 'device', 'interface')
        }),
        ('Détails', {
            'fields': ('details',)
        }),
        ('Prise en compte', {
            'fields': ('acknowledged', 'acknowledged_by', 'acknowledged_at', 'acknowledgement_comment')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def acknowledge_alerts(self, request, queryset):
        """Action pour prendre en compte plusieurs alertes."""
        count = 0
        for alert in queryset:
            if not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_by = request.user.username
                alert.save()
                count += 1
        self.message_user(request, f"{count} alertes ont été prises en compte.")
    acknowledge_alerts.short_description = "Prendre en compte les alertes sélectionnées"
    
    def resolve_alerts(self, request, queryset):
        """Action pour résoudre plusieurs alertes."""
        count = 0
        for alert in queryset:
            if alert.status != 'resolved':
                alert.status = 'resolved'
                alert.save()
                count += 1
        self.message_user(request, f"{count} alertes ont été résolues.")
    resolve_alerts.short_description = "Résoudre les alertes sélectionnées"


@admin.register(Metric)
class NetworkMetricAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les métriques réseau.
    """
    list_display = ('name', 'device', 'interface', 'value', 'unit', 'category', 'timestamp')
    list_filter = ('category', 'unit', 'timestamp', 'device')
    search_fields = ('name', 'device__name', 'interface__name', 'category')
    readonly_fields = ('timestamp',)
    raw_id_fields = ('device', 'interface')
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('Métrique', {
            'fields': ('name', 'value', 'unit', 'category')
        }),
        ('Source', {
            'fields': ('device', 'interface')
        }),
        ('Détails', {
            'fields': ('tags',)
        }),
        ('Métadonnées', {
            'fields': ('timestamp',)
        }),
    )


@admin.register(Log)
class NetworkLogAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les logs réseau.
    """
    list_display = ('device', 'level', 'message', 'source', 'timestamp')
    list_filter = ('level', 'source', 'timestamp', 'device')
    search_fields = ('message', 'device__name', 'source')
    readonly_fields = ('timestamp', 'created_at')
    raw_id_fields = ('device',)
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('Log', {
            'fields': ('device', 'level', 'message', 'source')
        }),
        ('Détails', {
            'fields': ('details',)
        }),
        ('Métadonnées', {
            'fields': ('timestamp', 'created_at')
        }),
    )


@admin.register(DashboardConfiguration)
class DashboardConfigurationAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour les configurations de dashboard.
    """
    list_display = ('user', 'dashboard_type', 'is_active', 'is_default', 'created_at')
    list_filter = ('dashboard_type', 'is_active', 'is_default', 'created_at')
    search_fields = ('user__username', 'dashboard_type')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    fieldsets = (
        ('Configuration', {
            'fields': ('user', 'dashboard_type', 'is_active', 'is_default')
        }),
        ('Données', {
            'fields': ('configuration',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    ) 