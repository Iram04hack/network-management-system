"""
Sérialiseurs sophistiqués pour les APIs REST du module security_management.

Ce module contient les sérialiseurs pour :
- Les règles de sécurité avec validation avancée
- Les conflits détectés et leur résolution
- L'analyse d'impact avec métriques Docker
- Le statut des services Docker
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ..models import SecurityRuleModel, SecurityAlertModel, AuditLogModel
from ..domain.entities import RuleType, SeverityLevel, AlertStatus
from ..domain.interfaces import RuleConflict, ImpactAnalysisResult


class SecurityRuleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les règles de sécurité avec validation sophistiquée.
    """
    
    # Champs calculés
    conflict_count = serializers.SerializerMethodField()
    last_validation = serializers.SerializerMethodField()
    impact_score = serializers.SerializerMethodField()
    docker_service_status = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityRuleModel
        fields = [
            'id', 'name', 'description', 'rule_type', 'content',
            'enabled', 'priority', 'creation_date', 'last_modified',
            'source_ip', 'destination_ip', 'source_port', 'destination_port',
            'protocol', 'action', 'trigger_count', 'tags',
            'conflict_count', 'last_validation',
            'impact_score', 'docker_service_status'
        ]
        read_only_fields = ['id', 'creation_date', 'last_modified']
    
    def get_conflict_count(self, obj) -> int:
        """Retourne le nombre de conflits pour cette règle."""
        # Dans une implémentation complète, cela interrogerait la base des conflits
        return getattr(obj, '_conflict_count', 0)
    
    def get_last_validation(self, obj) -> Optional[str]:
        """Retourne la date de dernière validation."""
        # Dans une implémentation complète, cela serait stocké en base
        return getattr(obj, '_last_validation', None)
    
    def get_impact_score(self, obj) -> float:
        """Retourne le score d'impact calculé."""
        # Dans une implémentation complète, cela serait calculé dynamiquement
        return getattr(obj, '_impact_score', 0.5)
    
    def get_docker_service_status(self, obj) -> str:
        """Retourne le statut du service Docker associé."""
        service_map = {
            'firewall': 'traffic_control',
            'ids': 'suricata',
            'access_control': 'fail2ban'
        }
        service_name = service_map.get(obj.rule_type, 'unknown')
        # Dans une implémentation complète, cela vérifierait le statut réel
        return getattr(obj, '_docker_status', 'unknown')
    
    def validate_rule_type(self, value):
        """Valide le type de règle."""
        valid_types = ['firewall', 'ids', 'access_control', 'suricata', 'fail2ban']
        if value not in valid_types:
            raise ValidationError(f"Type de règle invalide. Types valides: {', '.join(valid_types)}")
        return value
    
    def validate_content(self, value):
        """Valide le contenu de la règle selon son type."""
        if not value or not value.strip():
            raise ValidationError("Le contenu de la règle ne peut pas être vide.")
        
        # Le type de règle sera disponible dans self.initial_data
        rule_type = self.initial_data.get('rule_type')
        
        if rule_type == 'firewall':
            return self._validate_firewall_rule(value)
        elif rule_type == 'ids':
            return self._validate_ids_rule(value)
        elif rule_type == 'access_control':
            return self._validate_access_control_rule(value)
        
        return value
    
    def _validate_firewall_rule(self, content: str) -> str:
        """Valide une règle de pare-feu iptables."""
        # Vérifications basiques pour iptables
        if not content.strip().startswith('iptables'):
            raise ValidationError("Les règles firewall doivent commencer par 'iptables'")
        
        # Vérifier la présence des éléments obligatoires
        required_elements = ['-A', '-j']
        for element in required_elements:
            if element not in content:
                raise ValidationError(f"Élément obligatoire manquant: {element}")
        
        # Vérifier les actions valides
        action_match = re.search(r'-j\s+(\w+)', content)
        if action_match:
            action = action_match.group(1)
            valid_actions = ['ACCEPT', 'DROP', 'REJECT', 'LOG', 'RETURN']
            if action not in valid_actions:
                raise ValidationError(f"Action invalide: {action}. Actions valides: {', '.join(valid_actions)}")
        
        return content
    
    def _validate_ids_rule(self, content: str) -> str:
        """Valide une règle IDS Suricata/Snort."""
        # Vérifier le format de base d'une règle IDS
        ids_pattern = r'^(alert|drop|pass|reject)\s+\w+\s+.+\s+->\s+.+\s+\(.+\)$'
        if not re.match(ids_pattern, content.strip()):
            raise ValidationError("Format de règle IDS invalide. Format attendu: action protocol src_addr src_port -> dst_addr dst_port (options)")
        
        # Vérifier la présence du SID
        if 'sid:' not in content:
            raise ValidationError("SID obligatoire manquant dans la règle IDS")
        
        # Extraire et valider le SID
        sid_match = re.search(r'sid:\s*(\d+)', content)
        if sid_match:
            sid = int(sid_match.group(1))
            if sid <= 0:
                raise ValidationError("SID doit être un nombre positif")
        
        return content
    
    def _validate_access_control_rule(self, content: str) -> str:
        """Valide une règle de contrôle d'accès."""
        # Validation basique pour les règles de contrôle d'accès
        if len(content.strip()) < 10:
            raise ValidationError("Règle de contrôle d'accès trop courte")
        
        return content
    
    def validate(self, attrs):
        """Validation globale des attributs."""
        # Vérifier la cohérence entre le nom et le type de règle
        if 'name' in attrs and 'rule_type' in attrs:
            name = attrs['name'].lower()
            rule_type = attrs['rule_type']
            
            # Suggestions de nommage
            type_prefixes = {
                'firewall': ['fw', 'firewall', 'iptables'],
                'ids': ['ids', 'suricata', 'snort'],
                'access_control': ['ac', 'access', 'fail2ban']
            }
            
            prefixes = type_prefixes.get(rule_type, [])
            if not any(prefix in name for prefix in prefixes):
                # C'est juste un avertissement, pas une erreur bloquante
                pass
        
        return attrs


class RuleConflictSerializer(serializers.Serializer):
    """
    Sérialiseur pour les conflits entre règles de sécurité.
    """
    
    conflict_id = serializers.CharField(max_length=255)
    rule1_id = serializers.IntegerField()
    rule2_id = serializers.IntegerField()
    conflict_type = serializers.CharField(max_length=50)
    severity = serializers.CharField(max_length=20)
    description = serializers.CharField()
    recommendation = serializers.CharField()
    detected_at = serializers.DateTimeField(default=datetime.now)
    resolved = serializers.BooleanField(default=False)
    resolution_details = serializers.JSONField(required=False)
    
    # Champs calculés
    rule1_details = serializers.SerializerMethodField()
    rule2_details = serializers.SerializerMethodField()
    impact_assessment = serializers.SerializerMethodField()
    auto_resolution_available = serializers.SerializerMethodField()
    
    def get_rule1_details(self, obj) -> Dict[str, Any]:
        """Retourne les détails de la première règle."""
        rule1_id = getattr(obj, 'rule1_id', None)
        if rule1_id:
            try:
                rule = SecurityRuleModel.objects.get(id=rule1_id)
                return {
                    'id': rule.id,
                    'name': rule.name,
                    'type': rule.rule_type,
                    'content_preview': rule.content[:100] + '...' if len(rule.content) > 100 else rule.content
                }
            except SecurityRuleModel.DoesNotExist:
                pass
        return {'id': rule1_id, 'name': 'Règle non trouvée'}
    
    def get_rule2_details(self, obj) -> Dict[str, Any]:
        """Retourne les détails de la seconde règle."""
        rule2_id = getattr(obj, 'rule2_id', None)
        if rule2_id:
            try:
                rule = SecurityRuleModel.objects.get(id=rule2_id)
                return {
                    'id': rule.id,
                    'name': rule.name,
                    'type': rule.rule_type,
                    'content_preview': rule.content[:100] + '...' if len(rule.content) > 100 else rule.content
                }
            except SecurityRuleModel.DoesNotExist:
                pass
        return {'id': rule2_id, 'name': 'Règle non trouvée'}
    
    def get_impact_assessment(self, obj) -> Dict[str, Any]:
        """Évalue l'impact du conflit."""
        severity = getattr(obj, 'severity', 'unknown')
        conflict_type = getattr(obj, 'conflict_type', 'unknown')
        
        impact_scores = {
            'critical': {'performance': 0.8, 'security': 0.9, 'operational': 0.7},
            'high': {'performance': 0.6, 'security': 0.7, 'operational': 0.5},
            'medium': {'performance': 0.4, 'security': 0.5, 'operational': 0.3},
            'low': {'performance': 0.2, 'security': 0.3, 'operational': 0.1},
            'warning': {'performance': 0.1, 'security': 0.2, 'operational': 0.1}
        }
        
        return impact_scores.get(severity, {'performance': 0.0, 'security': 0.0, 'operational': 0.0})
    
    def get_auto_resolution_available(self, obj) -> bool:
        """Indique si une résolution automatique est disponible."""
        conflict_type = getattr(obj, 'conflict_type', '')
        # Certains types de conflits peuvent être résolus automatiquement
        auto_resolvable = ['redundant', 'generalization']
        return conflict_type in auto_resolvable


class ImpactAnalysisSerializer(serializers.Serializer):
    """
    Sérialiseur pour les résultats d'analyse d'impact.
    """
    
    rule_id = serializers.IntegerField(required=False, allow_null=True)
    analysis_type = serializers.CharField(max_length=50, default='comprehensive')
    overall_impact_score = serializers.FloatField()
    
    # Métriques de performance
    performance_metrics = serializers.JSONField()
    
    # Métriques de sécurité
    security_metrics = serializers.JSONField()
    
    # Métriques opérationnelles
    operational_metrics = serializers.JSONField()
    
    # Recommandations
    recommendations = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False
    )
    
    # Prédictions
    predicted_impact = serializers.JSONField(required=False)
    
    # Métadonnées
    analysis_timestamp = serializers.DateTimeField(default=datetime.now)
    docker_services_status = serializers.JSONField(required=False)
    confidence_score = serializers.FloatField(min_value=0.0, max_value=1.0, default=0.75)
    
    def validate_overall_impact_score(self, value):
        """Valide le score d'impact global."""
        if not 0.0 <= value <= 1.0:
            raise ValidationError("Le score d'impact doit être entre 0.0 et 1.0")
        return value
    
    def validate_performance_metrics(self, value):
        """Valide les métriques de performance."""
        required_fields = ['cpu_usage_percent', 'memory_usage_mb', 'network_latency_ms']
        for field in required_fields:
            if field not in value:
                raise ValidationError(f"Champ requis manquant dans performance_metrics: {field}")
        return value
    
    def validate_security_metrics(self, value):
        """Valide les métriques de sécurité."""
        required_fields = ['coverage_score', 'detection_accuracy', 'threat_level_reduction']
        for field in required_fields:
            if field not in value:
                raise ValidationError(f"Champ requis manquant dans security_metrics: {field}")
        return value


class SecurityAlertSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les alertes de sécurité.
    """
    
    # Champs calculés
    related_rules_count = serializers.SerializerMethodField()
    correlation_score = serializers.SerializerMethodField()
    threat_intelligence = serializers.SerializerMethodField()
    resolution_time = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityAlertModel
        fields = [
            'id', 'title', 'description', 'severity', 'status',
            'rule_id', 'source_ip', 'destination_ip', 'alert_data',
            'created_at', 'updated_at', 'resolved_at',
            'related_rules_count', 'correlation_score',
            'threat_intelligence', 'resolution_time'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_related_rules_count(self, obj) -> int:
        """Retourne le nombre de règles associées."""
        return getattr(obj, '_related_rules_count', 0)
    
    def get_correlation_score(self, obj) -> float:
        """Retourne le score de corrélation avec d'autres alertes."""
        return getattr(obj, '_correlation_score', 0.0)
    
    def get_threat_intelligence(self, obj) -> Dict[str, Any]:
        """Retourne les informations de threat intelligence."""
        return getattr(obj, '_threat_intelligence', {})
    
    def get_resolution_time(self, obj) -> Optional[str]:
        """Calcule le temps de résolution de l'alerte."""
        if obj.resolved_at and obj.created_at:
            delta = obj.resolved_at - obj.created_at
            return str(delta)
        return None


class DockerServiceStatusSerializer(serializers.Serializer):
    """
    Sérialiseur pour le statut des services Docker.
    """
    
    service_name = serializers.CharField(max_length=100)
    status = serializers.CharField(max_length=50)
    health = serializers.CharField(max_length=50, required=False)
    last_check = serializers.DateTimeField()
    response_time_ms = serializers.IntegerField(required=False)
    version = serializers.CharField(max_length=50, required=False)
    uptime = serializers.CharField(max_length=100, required=False)
    
    # Métriques du service
    metrics = serializers.JSONField(required=False)
    
    # Configuration
    configuration = serializers.JSONField(required=False)
    
    # Erreurs
    error_message = serializers.CharField(max_length=500, required=False)
    consecutive_failures = serializers.IntegerField(default=0)
    
    # Statistiques
    requests_per_minute = serializers.IntegerField(required=False)
    success_rate = serializers.FloatField(required=False)


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les logs d'audit.
    """
    
    # Champs calculés
    action_category = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLogModel
        fields = [
            'id', 'action', 'target_type', 'target_id',
            'user_id', 'ip_address', 'user_agent',
            'details', 'timestamp',
            'action_category', 'risk_level', 'user_details'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_action_category(self, obj) -> str:
        """Catégorise l'action d'audit."""
        action = obj.action.lower()
        
        if action in ['create', 'add', 'insert']:
            return 'creation'
        elif action in ['update', 'modify', 'edit']:
            return 'modification'
        elif action in ['delete', 'remove']:
            return 'deletion'
        elif action in ['view', 'read', 'access']:
            return 'access'
        else:
            return 'other'
    
    def get_risk_level(self, obj) -> str:
        """Évalue le niveau de risque de l'action."""
        action = obj.action.lower()
        target_type = obj.target_type.lower()
        
        # Actions à haut risque
        high_risk_actions = ['delete', 'disable', 'remove']
        high_risk_targets = ['security_rule', 'admin_user']
        
        if action in high_risk_actions or target_type in high_risk_targets:
            return 'high'
        elif action in ['create', 'update', 'modify']:
            return 'medium'
        else:
            return 'low'
    
    def get_user_details(self, obj) -> Dict[str, Any]:
        """Retourne les détails de l'utilisateur."""
        # Dans une implémentation complète, cela interrogerait le modèle User
        return {
            'user_id': obj.user_id,
            'username': 'N/A',  # À remplacer par la vraie logique
            'is_admin': False   # À remplacer par la vraie logique
        }


class BulkRuleOperationSerializer(serializers.Serializer):
    """
    Sérialiseur pour les opérations en lot sur les règles.
    """
    
    operation = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete', 'validate', 'analyze_conflicts']
    )
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    parameters = serializers.JSONField(required=False, default=dict)
    force = serializers.BooleanField(default=False)
    
    def validate_rule_ids(self, value):
        """Valide que toutes les règles existent."""
        existing_ids = set(
            SecurityRuleModel.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise ValidationError(f"Règles non trouvées: {list(missing_ids)}")
        
        return value


class ConflictResolutionSerializer(serializers.Serializer):
    """
    Sérialiseur pour la résolution de conflits.
    """
    
    conflict_id = serializers.CharField(max_length=255)
    resolution_type = serializers.ChoiceField(
        choices=[
            'merge_rules', 'reorder_rules', 'disable_rule', 
            'modify_rule', 'ignore_conflict', 'manual_review'
        ]
    )
    parameters = serializers.JSONField(required=False, default=dict)
    justification = serializers.CharField(max_length=1000, required=False)
    auto_apply = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validation globale de la résolution."""
        resolution_type = attrs.get('resolution_type')
        parameters = attrs.get('parameters', {})
        
        # Validation spécifique selon le type de résolution
        if resolution_type == 'merge_rules':
            if 'target_rule_id' not in parameters:
                raise ValidationError("target_rule_id requis pour merge_rules")
        
        elif resolution_type == 'reorder_rules':
            if 'new_order' not in parameters:
                raise ValidationError("new_order requis pour reorder_rules")
        
        elif resolution_type == 'modify_rule':
            if 'modifications' not in parameters:
                raise ValidationError("modifications requises pour modify_rule")
        
        return attrs


class SecurityDashboardSerializer(serializers.Serializer):
    """
    Sérialiseur pour le dashboard de sécurité.
    """
    
    # Statistiques générales
    total_rules = serializers.IntegerField()
    active_rules = serializers.IntegerField()
    total_conflicts = serializers.IntegerField()
    unresolved_conflicts = serializers.IntegerField()
    total_alerts = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    
    # Distribution par type
    rules_by_type = serializers.JSONField()
    conflicts_by_severity = serializers.JSONField()
    alerts_by_severity = serializers.JSONField()
    
    # Tendances
    daily_stats = serializers.JSONField()
    weekly_trends = serializers.JSONField()
    
    # Statut des services Docker
    docker_services_health = serializers.JSONField()
    
    # Métriques de performance
    average_response_time = serializers.FloatField()
    system_health_score = serializers.FloatField()
    
    # Dernière mise à jour
    last_updated = serializers.DateTimeField()