"""
Serializers pour les métriques.
"""

from rest_framework import serializers


class MetricsDefinitionSerializer(serializers.Serializer):
    """Serializer pour les définitions de métriques."""
    
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    metric_type = serializers.CharField(max_length=50)
    unit = serializers.CharField(max_length=50)
    collection_method = serializers.CharField(max_length=50)
    collection_config = serializers.JSONField()
    category = serializers.CharField(max_length=50, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DeviceMetricSerializer(serializers.Serializer):
    """Serializer pour les métriques d'équipement."""
    
    id = serializers.IntegerField(read_only=True)
    device_id = serializers.IntegerField()
    metric_id = serializers.IntegerField()
    name = serializers.CharField(max_length=100, required=False)
    specific_config = serializers.JSONField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    last_collection_status = serializers.BooleanField(read_only=True, required=False)
    last_collection_time = serializers.DateTimeField(read_only=True, required=False)
    last_value = serializers.FloatField(read_only=True, required=False)
    last_message = serializers.CharField(read_only=True, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    metric = serializers.SerializerMethodField(read_only=True)
    
    def get_metric(self, obj):
        """Récupère la définition de métrique associée."""
        if hasattr(obj, 'metric'):
            return MetricsDefinitionSerializer(obj.metric).data
        return None


class MetricValueSerializer(serializers.Serializer):
    """Serializer pour les valeurs de métriques."""
    
    id = serializers.IntegerField(read_only=True)
    device_metric_id = serializers.IntegerField()
    value = serializers.FloatField()
    timestamp = serializers.DateTimeField(required=False)
    created_at = serializers.DateTimeField(read_only=True) 