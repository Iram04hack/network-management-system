"""
Sérialiseurs pour le module monitoring.
Ces sérialiseurs permettent la conversion entre les modèles Django et les formats d'API (JSON).
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    # Alertes
    Alert,
    
    # Métriques
    MetricsDefinition, DeviceMetric, MetricValue, 
    ThresholdRule, AnomalyDetectionConfig,
    
    # Vérifications de service
    MonitoringTemplate, ServiceCheck, DeviceServiceCheck, CheckResult,
    
    # Notifications
    Notification, NotificationChannel, NotificationRule,
    
    # Tableaux de bord
    Dashboard, DashboardWidget, SavedView, BusinessKPI, KPIHistory
)

User = get_user_model()


# Sérialiseurs pour les alertes

class UserBasicSerializer(serializers.ModelSerializer):
    """Sérialiseur basique pour les utilisateurs."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class AlertSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les alertes (liste)."""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'device', 'device_name', 'severity', 'status', 
            'message', 'value', 'created_at', 'updated_at'
        ]


class AlertDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les détails d'une alerte."""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    service_check_name = serializers.CharField(source='service_check.name', read_only=True, allow_null=True)
    metric_name = serializers.CharField(source='metric.name', read_only=True, allow_null=True)
    acknowledged_by = UserBasicSerializer(read_only=True)
    resolved_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'


class AlertStatusUpdateSerializer(serializers.Serializer):
    """Sérialiseur pour la mise à jour du statut d'une alerte."""
    
    comment = serializers.CharField(required=False, allow_blank=True)


# Sérialiseurs pour les métriques

class MetricsDefinitionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les définitions de métriques."""
    
    class Meta:
        model = MetricsDefinition
        fields = '__all__'


class DeviceMetricSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les métriques d'équipement."""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    metric_name = serializers.CharField(source='metric.name', read_only=True)
    interface_name = serializers.CharField(source='interface.name', read_only=True, allow_null=True)
    
    class Meta:
        model = DeviceMetric
        fields = [
            'id', 'device', 'device_name', 'metric', 'metric_name',
            'interface', 'interface_name', 'collection_interval',
            'last_collection', 'next_collection', 'is_active',
            'custom_parameters', 'created_at', 'updated_at'
        ]


# MetricValueSerializer est défini dans serializers/metrics_serializers.py pour éviter les conflits


class ThresholdRuleSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les règles de seuil."""
    
    class Meta:
        model = ThresholdRule
        fields = '__all__'


class AnomalyDetectionConfigSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les configurations de détection d'anomalies."""
    
    class Meta:
        model = AnomalyDetectionConfig
        fields = '__all__'


# Sérialiseurs pour les vérifications de service

class MonitoringTemplateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les templates de surveillance."""
    
    class Meta:
        model = MonitoringTemplate
        fields = '__all__'


class ServiceCheckSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les vérifications de service."""
    
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ServiceCheck
        fields = '__all__'


class DeviceServiceCheckSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les vérifications de service d'équipement."""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    service_check_name = serializers.CharField(source='service_check.name', read_only=True)
    
    class Meta:
        model = DeviceServiceCheck
        fields = '__all__'


class CheckResultSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les résultats de vérification."""
    
    class Meta:
        model = CheckResult
        fields = '__all__'


# Sérialiseurs pour les notifications

class NotificationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les notifications."""
    
    class Meta:
        model = Notification
        fields = '__all__'


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les canaux de notification."""
    
    class Meta:
        model = NotificationChannel
        fields = '__all__'


class NotificationRuleSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les règles de notification."""
    
    class Meta:
        model = NotificationRule
        fields = '__all__'


# Sérialiseurs pour les tableaux de bord

class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les widgets de tableau de bord."""
    
    class Meta:
        model = DashboardWidget
        fields = '__all__'


class DashboardSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les tableaux de bord."""
    
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'title', 'description', 'layout', 'is_default', 
            'is_public', 'uid', 'category', 'owner', 'owner_name',
            'created_at', 'updated_at', 'widgets'
        ]


class SavedViewSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les vues sauvegardées."""
    
    class Meta:
        model = SavedView
        fields = '__all__'


class BusinessKPISerializer(serializers.ModelSerializer):
    """Sérialiseur pour les KPIs métier."""
    
    class Meta:
        model = BusinessKPI
        fields = '__all__'


class KPIHistorySerializer(serializers.ModelSerializer):
    """Sérialiseur pour l'historique des KPIs."""
    
    class Meta:
        model = KPIHistory
        fields = '__all__' 