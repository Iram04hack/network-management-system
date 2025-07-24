"""
Serializers pour les notifications.
"""

from rest_framework import serializers

from .alert_serializers import AlertSerializer


class NotificationChannelSerializer(serializers.Serializer):
    """Serializer pour les canaux de notification."""
    
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    channel_type = serializers.CharField(max_length=50)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    config = serializers.JSONField()
    created_by_id = serializers.IntegerField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    is_shared = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    created_by = serializers.SerializerMethodField(read_only=True)
    
    def get_created_by(self, obj):
        """Récupère l'utilisateur qui a créé le canal."""
        if hasattr(obj, 'created_by') and obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email
            }
        return None


class NotificationSerializer(serializers.Serializer):
    """Serializer pour les notifications."""
    
    id = serializers.IntegerField(read_only=True)
    channel_id = serializers.IntegerField()
    subject = serializers.CharField(max_length=200, required=False, allow_blank=True)
    message = serializers.CharField(max_length=2000)
    recipients = serializers.ListField(child=serializers.CharField(), required=False)
    user_recipients = serializers.ListField(child=serializers.IntegerField(), required=False)
    alert_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(max_length=50, default="pending")
    error_message = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    details = serializers.JSONField(required=False, allow_null=True)
    sent_at = serializers.DateTimeField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    channel = serializers.SerializerMethodField(read_only=True)
    alert = serializers.SerializerMethodField(read_only=True)
    
    def get_channel(self, obj):
        """Récupère le canal de notification associé."""
        if hasattr(obj, 'channel'):
            return NotificationChannelSerializer(obj.channel).data
        return None
    
    def get_alert(self, obj):
        """Récupère l'alerte associée."""
        if hasattr(obj, 'alert') and obj.alert:
            return AlertSerializer(obj.alert).data
        return None


class UserNotificationSerializer(serializers.Serializer):
    """Serializer pour les notifications utilisateur."""
    
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField()
    notification_id = serializers.IntegerField()
    is_read = serializers.BooleanField(default=False)
    read_at = serializers.DateTimeField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    notification = serializers.SerializerMethodField(read_only=True)
    
    def get_notification(self, obj):
        """Récupère la notification associée."""
        if hasattr(obj, 'notification'):
            return NotificationSerializer(obj.notification).data
        return None


class NotificationPreferenceSerializer(serializers.Serializer):
    """Serializer pour les préférences de notification."""
    
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField()
    notification_type = serializers.CharField(max_length=50)
    channel_id = serializers.IntegerField(required=False, allow_null=True)
    enabled = serializers.BooleanField(default=True)
    settings = serializers.JSONField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    channel = serializers.SerializerMethodField(read_only=True)
    
    def get_channel(self, obj):
        """Récupère le canal de notification associé."""
        if hasattr(obj, 'channel') and obj.channel:
            return NotificationChannelSerializer(obj.channel).data
        return None


class NotificationRuleSerializer(serializers.Serializer):
    """Serializer pour les règles de notification."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    event_type = serializers.CharField(max_length=50)
    channel_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    user_id = serializers.IntegerField()
    conditions = serializers.JSONField(required=False, allow_null=True)
    is_enabled = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # Relations
    channels = serializers.SerializerMethodField(read_only=True)

    def get_channels(self, obj):
        """Récupère les canaux de notification associés."""
        if hasattr(obj, 'channels') and obj.channels:
            return [NotificationChannelSerializer(channel).data for channel in obj.channels]
        return []