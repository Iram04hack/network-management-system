"""
Sérialiseurs pour l'API REST du module security_management.

Ce fichier contient les sérialiseurs Django REST Framework qui
convertissent les entités du domaine en représentations JSON et vice-versa.
"""

from rest_framework import serializers

from ...domain.entities import RuleType, ActionType, SeverityLevel


class SecurityRuleSerializer(serializers.Serializer):
    """
    Sérialiseur pour les règles de sécurité.
    """
    
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    rule_type = serializers.ChoiceField(choices=[t.value for t in RuleType])
    content = serializers.CharField(required=False, allow_null=True)
    source_ip = serializers.CharField(required=False, allow_null=True)
    destination_ip = serializers.CharField(required=False, allow_null=True)
    source_port = serializers.CharField(required=False, allow_null=True)
    destination_port = serializers.CharField(required=False, allow_null=True)
    protocol = serializers.CharField(required=False, allow_null=True)
    action = serializers.ChoiceField(
        choices=[a.value for a in ActionType],
        required=False,
        allow_null=True
    )
    enabled = serializers.BooleanField(default=True)
    priority = serializers.IntegerField(required=False, default=100)
    creation_date = serializers.DateTimeField(read_only=True)
    last_modified = serializers.DateTimeField(read_only=True)
    trigger_count = serializers.IntegerField(read_only=True, default=0)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class SecurityAlertSerializer(serializers.Serializer):
    """
    Sérialiseur pour les alertes de sécurité.
    """
    
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    source_ip = serializers.CharField(required=False, allow_null=True)
    destination_ip = serializers.CharField(required=False, allow_null=True)
    source_port = serializers.CharField(required=False, allow_null=True)
    destination_port = serializers.CharField(required=False, allow_null=True)
    protocol = serializers.CharField(required=False, allow_null=True)
    detection_time = serializers.DateTimeField()
    severity = serializers.ChoiceField(
        choices=[s.value for s in SeverityLevel],
        default=SeverityLevel.MEDIUM.value
    )
    status = serializers.CharField(default="new")
    source_rule_id = serializers.CharField(required=False, allow_null=True)
    raw_data = serializers.JSONField(required=False, allow_null=True)
    false_positive = serializers.BooleanField(default=False)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    ) 