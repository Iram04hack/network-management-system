"""
Serializers pour les vérifications de service.
"""

from rest_framework import serializers


class ServiceCheckSerializer(serializers.Serializer):
    """Serializer pour les vérifications de service."""
    
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    check_type = serializers.CharField(max_length=50)
    check_config = serializers.JSONField()
    category = serializers.CharField(max_length=50, required=False, allow_null=True)
    compatible_device_types = serializers.ListField(child=serializers.CharField(), required=False)
    enabled = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DeviceServiceCheckSerializer(serializers.Serializer):
    """Serializer pour les vérifications de service d'équipement."""
    
    id = serializers.IntegerField(read_only=True)
    device_id = serializers.IntegerField()
    service_check_id = serializers.IntegerField()
    name = serializers.CharField(max_length=100, required=False)
    specific_config = serializers.JSONField(required=False, allow_null=True)
    check_interval = serializers.IntegerField(default=300)
    is_active = serializers.BooleanField(default=True)
    last_check_time = serializers.DateTimeField(read_only=True, required=False)
    last_status = serializers.CharField(read_only=True, required=False)
    last_message = serializers.CharField(read_only=True, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    service_check = serializers.SerializerMethodField(read_only=True)
    
    def get_service_check(self, obj):
        """Récupère la vérification de service associée."""
        if hasattr(obj, 'service_check'):
            return ServiceCheckSerializer(obj.service_check).data
        return None


class CheckResultSerializer(serializers.Serializer):
    """Serializer pour les résultats de vérification."""
    
    id = serializers.IntegerField(read_only=True)
    device_service_check_id = serializers.IntegerField()
    status = serializers.CharField(max_length=50)
    execution_time = serializers.FloatField()
    message = serializers.CharField(required=False, allow_null=True)
    details = serializers.JSONField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True) 