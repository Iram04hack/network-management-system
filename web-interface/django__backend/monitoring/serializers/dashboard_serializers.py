"""
Serializers pour les tableaux de bord.
"""

from rest_framework import serializers


class DashboardWidgetSerializer(serializers.Serializer):
    """Serializer pour les widgets de tableau de bord."""
    
    class Meta:
        ref_name = 'MonitoringDashboardWidget'
    
    id = serializers.IntegerField(read_only=True)
    dashboard_id = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    widget_type = serializers.CharField(max_length=50)
    position = serializers.JSONField()
    size = serializers.JSONField()
    data_source = serializers.JSONField(required=False, allow_null=True)
    config = serializers.JSONField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DashboardSerializer(serializers.Serializer):
    """Serializer pour les tableaux de bord."""
    
    class Meta:
        ref_name = 'MonitoringDashboard'
    
    id = serializers.IntegerField(read_only=True)
    uid = serializers.CharField(max_length=50, read_only=True)
    title = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    owner_id = serializers.IntegerField()
    is_public = serializers.BooleanField(default=False)
    is_default = serializers.BooleanField(default=False)
    layout_config = serializers.JSONField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    widgets = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    
    def get_widgets(self, obj):
        """Récupère les widgets du tableau de bord."""
        if hasattr(obj, 'widgets'):
            return DashboardWidgetSerializer(obj.widgets, many=True).data
        return []
    
    def get_owner(self, obj):
        """Récupère le propriétaire du tableau de bord."""
        if hasattr(obj, 'owner'):
            return {
                'id': obj.owner.id,
                'username': obj.owner.username,
                'email': obj.owner.email
            }
        return None


class DashboardShareSerializer(serializers.Serializer):
    """Serializer pour les partages de tableau de bord."""
    
    class Meta:
        ref_name = 'MonitoringDashboardShare'
    
    id = serializers.IntegerField(read_only=True)
    dashboard_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    can_edit = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)
    
    # Relations
    dashboard = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    
    def get_dashboard(self, obj):
        """Récupère le tableau de bord associé."""
        if hasattr(obj, 'dashboard'):
            return {
                'id': obj.dashboard.id,
                'uid': obj.dashboard.uid,
                'title': obj.dashboard.title
            }
        return None
    
    def get_user(self, obj):
        """Récupère l'utilisateur associé."""
        if hasattr(obj, 'user'):
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None 