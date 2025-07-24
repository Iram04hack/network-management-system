"""
Serializers pour les alertes.
"""

from rest_framework import serializers


class AlertSerializer(serializers.Serializer):
    """Serializer pour les alertes."""
    
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    severity = serializers.CharField(max_length=50)
    status = serializers.CharField(max_length=50, default="active")
    source_type = serializers.CharField(max_length=50, required=False, allow_null=True)
    source_id = serializers.IntegerField(required=False, allow_null=True)
    device_id = serializers.IntegerField(required=False, allow_null=True)
    details = serializers.JSONField(required=False, allow_null=True)
    acknowledged_by = serializers.IntegerField(read_only=True, required=False, allow_null=True)
    acknowledged_at = serializers.DateTimeField(read_only=True, required=False)
    resolved_by = serializers.IntegerField(read_only=True, required=False, allow_null=True)
    resolved_at = serializers.DateTimeField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class AlertCommentSerializer(serializers.Serializer):
    """Serializer pour les commentaires d'alerte."""
    
    id = serializers.IntegerField(read_only=True)
    alert_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    comment = serializers.CharField(max_length=1000)
    created_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    user = serializers.SerializerMethodField(read_only=True)
    
    def get_user(self, obj):
        """Récupère l'utilisateur associé."""
        if hasattr(obj, 'user'):
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None


class AlertHistorySerializer(serializers.Serializer):
    """Serializer pour l'historique des alertes."""
    
    id = serializers.IntegerField(read_only=True)
    alert_id = serializers.IntegerField()
    action = serializers.CharField(max_length=50)
    previous_status = serializers.CharField(max_length=50, required=False, allow_null=True)
    new_status = serializers.CharField(max_length=50, required=False, allow_null=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)
    
    # Relations
    user = serializers.SerializerMethodField(read_only=True)
    
    def get_user(self, obj):
        """Récupère l'utilisateur associé."""
        if hasattr(obj, 'user'):
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None 