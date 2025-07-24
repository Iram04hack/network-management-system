# reporting/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Report, ReportTemplate, ScheduledReport

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']
        ref_name = 'ReportingUser'

class ReportTemplateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les modèles de rapport."""
    
    class Meta:
        model = ReportTemplate
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les rapports."""
    template = ReportTemplateSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'generated_at', 'status', 'error_message', 'file', 'file_url']
    
    def get_file_url(self, obj):
        """Récupère l'URL du fichier"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class ScheduledReportSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les rapports planifiés."""
    report = ReportSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    recipients = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = ScheduledReport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'created_by']
