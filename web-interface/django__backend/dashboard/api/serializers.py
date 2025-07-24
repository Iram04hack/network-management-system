"""
Sérialiseurs pour l'API du module Dashboard.

Ce fichier contient les classes de sérialisation pour convertir
les objets du domaine en structures JSON pour l'API.
"""

from rest_framework import serializers
from ..models import UserDashboardConfig, DashboardWidget, DashboardPreset, CustomDashboard


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les widgets de tableau de bord.

    Gère la sérialisation des widgets qui peuvent être placés sur les tableaux de bord.
    Chaque widget a un type spécifique et peut être configuré individuellement.
    """

    class Meta:
        model = DashboardWidget
        fields = ['id', 'config', 'preset', 'widget_type', 'position_x', 'position_y',
                  'width', 'height', 'settings', 'is_active']
        read_only_fields = ['id']
        ref_name = 'DashboardModuleWidget'

    def to_representation(self, instance):
        """Ajoute des informations supplémentaires à la représentation."""
        data = super().to_representation(instance)

        # Ajouter des exemples de configuration selon le type de widget
        widget_type = data.get('widget_type')
        if widget_type == 'system_health':
            data['example_settings'] = {
                'show_cpu': True,
                'show_memory': True,
                'show_disk': True,
                'refresh_interval': 30
            }
        elif widget_type == 'alerts':
            data['example_settings'] = {
                'limit': 5,
                'severity_filter': ['critical', 'warning'],
                'auto_refresh': True
            }
        elif widget_type == 'network_overview':
            data['example_settings'] = {
                'show_topology': True,
                'show_device_count': True,
                'show_link_status': True
            }

        return data


class UserDashboardConfigSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la configuration du tableau de bord utilisateur."""
    
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserDashboardConfig
        fields = ['id', 'user', 'theme', 'layout', 'refresh_interval',
                  'widgets', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        ref_name = 'UserDashboardConfig'


class DashboardPresetSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les préréglages de tableau de bord."""
    
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    
    class Meta:
        model = DashboardPreset
        fields = ['id', 'name', 'description', 'theme', 'layout',
                  'refresh_interval', 'is_default', 'widgets']
        ref_name = 'DashboardPreset'


class AlertSerializer(serializers.Serializer):
    """Sérialiseur pour les alertes."""
    
    id = serializers.IntegerField()
    message = serializers.CharField()
    severity = serializers.CharField()
    timestamp = serializers.DateTimeField()
    status = serializers.CharField()
    source = serializers.CharField()
    metric_name = serializers.CharField(allow_null=True)
    affected_devices = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class SystemHealthMetricsSerializer(serializers.Serializer):
    """Sérialiseur pour les métriques de santé système."""
    
    system_health = serializers.FloatField()
    network_health = serializers.FloatField()
    security_health = serializers.FloatField()


class NetworkOverviewSerializer(serializers.Serializer):
    """Sérialiseur pour la vue d'ensemble du réseau."""
    
    device_count = serializers.IntegerField()
    device_types = serializers.DictField(child=serializers.IntegerField())
    device_status = serializers.DictField(child=serializers.IntegerField())
    interface_count = serializers.IntegerField()
    interface_status = serializers.DictField(child=serializers.IntegerField())
    connection_status = serializers.DictField(child=serializers.IntegerField())
    traffic_stats = serializers.DictField(child=serializers.FloatField())
    qos_stats = serializers.DictField()
    network_health = serializers.FloatField()
    alerts = AlertSerializer(many=True)
    timestamp = serializers.DateTimeField()
    error = serializers.CharField(required=False, allow_null=True)


class DashboardAggregatedDataSerializer(serializers.Serializer):
    """Sérialiseur pour les données agrégées du tableau de bord."""
    
    device_summary = serializers.DictField()
    interface_summary = serializers.DictField()
    system_health = SystemHealthMetricsSerializer()
    alerts = AlertSerializer(many=True)
    performance_metrics = serializers.DictField()
    user_specific_widgets = serializers.DictField(allow_null=True)
    timestamp = serializers.DateTimeField()


class TopologyNodeSerializer(serializers.Serializer):
    """Sérialiseur pour les nœuds de topologie."""
    
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    ip_address = serializers.CharField(allow_null=True)
    position = serializers.DictField()
    metrics = serializers.DictField()
    visual = serializers.DictField(required=False)


class TopologyConnectionSerializer(serializers.Serializer):
    """Sérialiseur pour les connexions de topologie."""
    
    id = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField()
    status = serializers.CharField()
    type = serializers.CharField()
    metrics = serializers.DictField()
    visual = serializers.DictField(required=False)


class TopologyDataSerializer(serializers.Serializer):
    """Sérialiseur pour les données de topologie."""
    
    topology_id = serializers.IntegerField()
    name = serializers.CharField()
    nodes = TopologyNodeSerializer(many=True)
    connections = TopologyConnectionSerializer(many=True)
    health_summary = serializers.DictField()
    last_updated = serializers.DateTimeField()
    visualization_settings = serializers.DictField(required=False)
    error = serializers.CharField(required=False, allow_null=True)


class CustomDashboardSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les tableaux de bord personnalisés."""

    owner_username = serializers.CharField(source='owner.username', read_only=True)
    widget_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomDashboard
        fields = ['id', 'name', 'description', 'owner', 'owner_username',
                  'layout', 'is_default', 'created_at', 'updated_at', 'widget_count']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
        ref_name = 'CustomDashboard'

    def get_widget_count(self, obj):
        """Retourne le nombre de widgets dans ce dashboard."""
        return len(obj.layout.get('widgets', []))

    def validate_name(self, value):
        """Valide que le nom du dashboard est unique pour cet utilisateur."""
        user = self.context['request'].user
        queryset = CustomDashboard.objects.filter(owner=user, name=value)

        # Exclure l'instance actuelle lors de la mise à jour
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Vous avez déjà un dashboard avec ce nom."
            )
        return value