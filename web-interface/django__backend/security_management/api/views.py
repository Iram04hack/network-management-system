"""
APIs REST sophistiquées pour le module security_management avec intégration Docker.

Ce module contient les vues API pour :
- La détection de conflits entre règles de sécurité
- L'analyse d'impact des règles
- La surveillance des services Docker
- La validation avancée des règles
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Q, Count, Avg

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import SecurityRuleModel, SecurityAlertModel, AuditLogModel
from ..domain.entities import SecurityRule, SecurityAlert
from ..domain.conflict_detector_factory import conflict_detector_factory
from ..application.detect_rule_conflicts_use_case import DetectRuleConflictsUseCase
from ..domain.impact_analysis import DockerMetricsCollector, AdvancedRuleMetricsCalculator
from ..infrastructure.repositories import (
    DjangoSecurityRuleRepository, DjangoSecurityAlertRepository, DjangoAuditLogRepository
)
from ..infrastructure.docker_integration import (
    SuricataDockerAdapter, Fail2BanDockerAdapter, TrafficControlDockerAdapter
)
from .serializers import (
    SecurityRuleSerializer, SecurityAlertSerializer, RuleConflictSerializer,
    ImpactAnalysisSerializer, DockerServiceStatusSerializer
)

logger = logging.getLogger(__name__)


def security_api_root(request):
    """Vue racine de l'API Security Management avec informations sur les modules disponibles."""
    from django.http import JsonResponse
    
    return JsonResponse({
        "message": "✅ Module Security Management - API REST",
        "module": "security_management", 
        "status": "OK",
        "description": "Interface REST complète pour la gestion de la sécurité avec détection de conflits et intégration Docker",
        "core_features": {
            "conflict_detection": "Détection automatique de conflits entre règles de sécurité",
            "impact_analysis": "Analyse d'impact sophistiquée des règles",
            "docker_integration": "Intégration complète avec Suricata, Fail2Ban et Traffic Control",
            "rule_validation": "Validation avancée des règles via Docker",
            "anomaly_detection": "Détection d'anomalies et corrélation d'événements",
            "performance_monitoring": "Surveillance en temps réel des services de sécurité"
        },
        "endpoints": {
            "dashboard": "/api/security/dashboard/ - Tableau de bord unifié de sécurité",
            "status": "/api/security/status/ - Statut temps réel des services de sécurité",
            "analysis": "/api/security/analysis/ - Analyse de sécurité approfondie",
            "events": "/api/security/events/process/ - Traitement des événements de sécurité",
            "alerts": "/api/security/alerts/ - Gestion des alertes de sécurité",
            "rules": "/api/security/rules/ - Gestion des règles de sécurité",
            "vulnerabilities": "/api/security/vulnerabilities/ - Analyse des vulnérabilités",
            "metrics": "/api/security/metrics/ - Métriques de performance de sécurité"
        },
        "advanced_endpoints": {
            "conflicts": "/api/security/conflicts/ - Détection de conflits entre règles",
            "impact_analysis": "/api/security/impact-analysis/ - Analyse d'impact des règles",
            "docker_services": "/api/security/docker/services/ - Surveillance des services Docker",
            "validation": "/api/security/validate/ - Validation avancée des règles",
            "event_analysis": "/api/security/events/analysis/ - Analyse d'événements sophistiquée",
            "anomaly_detection": "/api/security/anomalies/detection/ - Détection d'anomalies",
            "correlation": "/api/security/correlation/analysis/ - Corrélation d'événements"
        },
        "administration": {
            "admin_dashboard": "/api/security/admin/dashboard/ - Dashboard administrateur",
            "health_check": "/api/security/admin/health/ - Contrôle de santé des services",
            "bulk_operations": "/api/security/bulk-operations/ - Opérations en lot",
            "export_import": {
                "export": "/api/security/export/ - Export des règles",
                "import": "/api/security/import/ - Import des règles"
            },
            "reports": {
                "conflicts": "/api/security/reports/conflicts/ - Rapports de conflits",
                "performance": "/api/security/reports/performance/ - Rapports de performance",
                "security": "/api/security/reports/security/ - Rapports de sécurité"
            }
        },
        "crud_operations": {
            "rules_crud": "/api/security/crud/rules/ - CRUD complet des règles de sécurité"
        },
        "integration": {
            "suricata": "IDS/IPS avec détection d'intrusion en temps réel",
            "fail2ban": "Protection contre les attaques par force brute",
            "traffic_control": "Contrôle et limitation du trafic réseau",
            "gns3": "Intégration avec topologies réseau GNS3"
        },
        "capabilities": {
            "real_time_monitoring": "Surveillance temps réel des événements de sécurité",
            "intelligent_alerting": "Système d'alertes intelligent avec corrélation",
            "automated_response": "Réponses automatisées aux incidents de sécurité",
            "compliance_reporting": "Rapports de conformité automatisés",
            "threat_intelligence": "Intégration de renseignements sur les menaces"
        }
    })


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination personnalisée pour les APIs."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class SecurityRuleConflictAPIView(APIView):
    """
    API pour la détection avancée de conflits entre règles de sécurité.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @property
    def rule_repository(self):
        """Repository des règles de sécurité (lazy loading)."""
        if not hasattr(self, '_rule_repository'):
            self._rule_repository = DjangoSecurityRuleRepository()
        return self._rule_repository
    
    @property
    def conflict_use_case(self):
        """Use case de détection de conflits (lazy loading)."""
        if not hasattr(self, '_conflict_use_case'):
            self._conflict_use_case = DetectRuleConflictsUseCase(
                rule_repository=self.rule_repository,
                conflict_detector_factory=conflict_detector_factory
            )
        return self._conflict_use_case
    
    def post(self, request):
        """
        Détecte les conflits pour une nouvelle règle de sécurité.
        
        Expected payload:
        {
            "rule_type": "firewall|ids|access_control",
            "content": "contenu de la règle",
            "metadata": {...}
        }
        """
        try:
            rule_type = request.data.get('rule_type')
            rule_content = request.data.get('content')
            metadata = request.data.get('metadata', {})
            
            if not rule_type or not rule_content:
                return Response(
                    {'error': 'rule_type et content sont requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer une entité règle temporaire pour l'analyse
            temp_rule_data = {
                'id': 0,  # ID temporaire
                'type': rule_type,
                'content': rule_content,
                'metadata': metadata
            }
            
            # Détecter les conflits
            conflicts = self.conflict_use_case.detect_conflicts_for_new_rule(
                temp_rule_data, rule_type
            )
            
            # Sérialiser les résultats
            serialized_conflicts = RuleConflictSerializer(conflicts, many=True).data
            
            return Response({
                'conflicts_detected': len(conflicts),
                'conflicts': serialized_conflicts,
                'analysis_timestamp': timezone.now().isoformat(),
                'rule_validated': True
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection de conflits: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Analyse complète des conflits pour toutes les règles existantes.
        """
        try:
            rule_type = request.query_params.get('rule_type')
            include_resolved = request.query_params.get('include_resolved', 'false').lower() == 'true'
            
            # Obtenir les conflits pour l'ensemble de règles
            all_conflicts = self.conflict_use_case.analyze_ruleset_conflicts(rule_type)
            
            if not include_resolved:
                # Filtrer les conflits non résolus
                all_conflicts = [c for c in all_conflicts if not getattr(c, 'resolved', False)]
            
            # Statistiques des conflits
            conflict_stats = self._generate_conflict_statistics(all_conflicts)
            
            # Sérialiser les résultats
            serialized_conflicts = RuleConflictSerializer(all_conflicts, many=True).data
            
            return Response({
                'total_conflicts': len(all_conflicts),
                'statistics': conflict_stats,
                'conflicts': serialized_conflicts,
                'analysis_timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des conflits: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_conflict_statistics(self, conflicts: List) -> Dict[str, Any]:
        """Génère des statistiques détaillées sur les conflits."""
        stats = {
            'by_type': {},
            'by_severity': {},
            'most_problematic_rules': {},
            'resolution_suggestions': []
        }
        
        # Statistiques par type
        for conflict in conflicts:
            conflict_type = getattr(conflict, 'conflict_type', 'unknown')
            stats['by_type'][conflict_type] = stats['by_type'].get(conflict_type, 0) + 1
        
        # Statistiques par sévérité
        for conflict in conflicts:
            severity = getattr(conflict, 'severity', 'unknown')
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # Règles les plus problématiques
        rule_conflict_count = {}
        for conflict in conflicts:
            rule1_id = getattr(conflict, 'rule1_id', None)
            rule2_id = getattr(conflict, 'rule2_id', None)
            
            if rule1_id:
                rule_conflict_count[rule1_id] = rule_conflict_count.get(rule1_id, 0) + 1
            if rule2_id:
                rule_conflict_count[rule2_id] = rule_conflict_count.get(rule2_id, 0) + 1
        
        # Top 5 des règles les plus problématiques
        stats['most_problematic_rules'] = dict(
            sorted(rule_conflict_count.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        
        return stats


class SecurityRuleImpactAnalysisAPIView(APIView):
    """
    API pour l'analyse d'impact sophistiquée des règles de sécurité.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @property
    def metrics_collector(self):
        """Collecteur de métriques Docker (lazy loading)."""
        if not hasattr(self, '_metrics_collector'):
            self._metrics_collector = DockerMetricsCollector()
        return self._metrics_collector
    
    @property
    def metrics_calculator(self):
        """Calculateur de métriques avancées (lazy loading)."""
        if not hasattr(self, '_metrics_calculator'):
            self._metrics_calculator = AdvancedRuleMetricsCalculator()
        return self._metrics_calculator
    
    def post(self, request):
        """
        Analyse l'impact d'une règle de sécurité proposée.
        
        Expected payload:
        {
            "rule_type": "firewall|ids|access_control",
            "content": "contenu de la règle",
            "scope": "performance|security|operational|all"
        }
        """
        try:
            rule_type = request.data.get('rule_type')
            rule_content = request.data.get('content')
            analysis_scope = request.data.get('scope', 'all')
            
            if not rule_type or not rule_content:
                return Response(
                    {'error': 'rule_type et content sont requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Collecter les métriques actuelles des services Docker
            current_metrics = self.metrics_collector.collect_all_metrics()
            
            # Analyser l'impact de la règle
            impact_analysis = self.metrics_calculator.calculate_rule_impact(
                rule_type=rule_type,
                rule_content=rule_content,
                current_metrics=current_metrics,
                scope=analysis_scope
            )
            
            # Sérialiser les résultats
            serialized_analysis = ImpactAnalysisSerializer(impact_analysis).data
            
            return Response({
                'impact_analysis': serialized_analysis,
                'analysis_timestamp': timezone.now().isoformat(),
                'metrics_timestamp': current_metrics.get('timestamp', timezone.now().isoformat())
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'impact: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, rule_id=None):
        """
        Récupère l'analyse d'impact pour une règle existante.
        """
        try:
            if rule_id:
                # Analyse pour une règle spécifique
                try:
                    rule = SecurityRuleModel.objects.get(id=rule_id)
                except SecurityRuleModel.DoesNotExist:
                    return Response(
                        {'error': 'Règle non trouvée'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Analyser l'impact de la règle existante
                current_metrics = self.metrics_collector.collect_all_metrics()
                impact_analysis = self.metrics_calculator.calculate_rule_impact(
                    rule_type=rule.rule_type,
                    rule_content=rule.content,
                    current_metrics=current_metrics
                )
                
                serialized_analysis = ImpactAnalysisSerializer(impact_analysis).data
                
                return Response({
                    'rule_id': rule_id,
                    'impact_analysis': serialized_analysis,
                    'analysis_timestamp': timezone.now().isoformat()
                })
            else:
                # Analyse globale d'impact pour toutes les règles
                global_impact = self._analyze_global_rule_impact()
                
                return Response({
                    'global_impact_analysis': global_impact,
                    'analysis_timestamp': timezone.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'analyse d'impact: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _analyze_global_rule_impact(self) -> Dict[str, Any]:
        """Analyse l'impact global de toutes les règles actives."""
        try:
            # Obtenir toutes les règles actives
            active_rules = SecurityRuleModel.objects.filter(is_active=True)
            
            # Collecter les métriques actuelles
            current_metrics = self.metrics_collector.collect_all_metrics()
            
            # Analyser l'impact cumulé
            cumulative_impact = {
                'total_rules': active_rules.count(),
                'performance_impact': {
                    'cpu_overhead_percent': 0.0,
                    'memory_overhead_mb': 0.0,
                    'latency_increase_ms': 0.0
                },
                'security_effectiveness': {
                    'coverage_score': 0.0,
                    'detection_accuracy': 0.0,
                    'threat_mitigation': 0.0
                },
                'operational_metrics': {
                    'maintenance_complexity': 0.0,
                    'alert_volume_per_hour': 0,
                    'false_positive_rate': 0.0
                },
                'rule_distribution': {}
            }
            
            # Calculer les métriques cumulées
            for rule in active_rules:
                rule_impact = self.metrics_calculator.calculate_rule_impact(
                    rule_type=rule.rule_type,
                    rule_content=rule.content,
                    current_metrics=current_metrics
                )
                
                # Accumuler les impacts
                if hasattr(rule_impact, 'performance_metrics'):
                    perf = rule_impact.performance_metrics
                    cumulative_impact['performance_impact']['cpu_overhead_percent'] += getattr(perf, 'cpu_usage_percent', 0)
                    cumulative_impact['performance_impact']['memory_overhead_mb'] += getattr(perf, 'memory_usage_mb', 0)
                    cumulative_impact['performance_impact']['latency_increase_ms'] += getattr(perf, 'network_latency_ms', 0)
                
                # Distribution par type de règle
                rule_type = rule.rule_type
                cumulative_impact['rule_distribution'][rule_type] = cumulative_impact['rule_distribution'].get(rule_type, 0) + 1
            
            return cumulative_impact
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'impact global: {str(e)}")
            return {'error': str(e)}


class DockerServiceMonitoringAPIView(APIView):
    """
    API pour la surveillance des services Docker de sécurité.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @property
    def docker_services(self):
        """Services Docker adaptateurs (lazy loading)."""
        if not hasattr(self, '_docker_services'):
            self._docker_services = {
                'suricata': SuricataDockerAdapter(),
                'fail2ban': Fail2BanDockerAdapter(),
                'traffic_control': TrafficControlDockerAdapter()
            }
        return self._docker_services
    
    def get(self, request):
        """
        Récupère le statut de tous les services Docker de sécurité.
        """
        try:
            service_name = request.query_params.get('service')
            include_metrics = request.query_params.get('include_metrics', 'false').lower() == 'true'
            
            if service_name:
                # Statut d'un service spécifique
                if service_name not in self.docker_services:
                    return Response(
                        {'error': f'Service {service_name} non trouvé'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                service_status = self._get_service_detailed_status(
                    service_name, self.docker_services[service_name], include_metrics
                )
                
                return Response({
                    'service': service_name,
                    'status': service_status,
                    'timestamp': timezone.now().isoformat()
                })
            else:
                # Statut de tous les services
                all_services_status = {}
                
                for name, adapter in self.docker_services.items():
                    all_services_status[name] = self._get_service_detailed_status(
                        name, adapter, include_metrics
                    )
                
                # Calculer le statut global
                global_status = self._calculate_global_service_status(all_services_status)
                
                return Response({
                    'global_status': global_status,
                    'services': all_services_status,
                    'timestamp': timezone.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la surveillance des services Docker: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Effectue des actions sur les services Docker (restart, health check, etc.).
        
        Expected payload:
        {
            "action": "health_check|restart|status|validate_config",
            "service": "suricata|fail2ban|traffic_control|all",
            "parameters": {...}
        }
        """
        try:
            action = request.data.get('action')
            service_name = request.data.get('service')
            parameters = request.data.get('parameters', {})
            
            if not action:
                return Response(
                    {'error': 'action est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if service_name == 'all':
                # Exécuter l'action sur tous les services
                results = {}
                for name, adapter in self.docker_services.items():
                    results[name] = self._execute_service_action(name, adapter, action, parameters)
                
                return Response({
                    'action': action,
                    'results': results,
                    'timestamp': timezone.now().isoformat()
                })
            else:
                # Exécuter l'action sur un service spécifique
                if service_name not in self.docker_services:
                    return Response(
                        {'error': f'Service {service_name} non trouvé'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                result = self._execute_service_action(
                    service_name, self.docker_services[service_name], action, parameters
                )
                
                return Response({
                    'service': service_name,
                    'action': action,
                    'result': result,
                    'timestamp': timezone.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution d'action sur les services Docker: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_service_detailed_status(self, service_name: str, adapter, include_metrics: bool = False) -> Dict[str, Any]:
        """Obtient le statut détaillé d'un service Docker."""
        try:
            # Vérifier la connexion
            is_connected = adapter.test_connection()
            
            # Obtenir le statut du service
            service_status = adapter.get_service_status() if hasattr(adapter, 'get_service_status') else {}
            
            status_info = {
                'connected': is_connected,
                'service_status': service_status,
                'last_check': timezone.now().isoformat()
            }
            
            if include_metrics and hasattr(adapter, 'get_metrics'):
                # Inclure les métriques si demandées
                status_info['metrics'] = adapter.get_metrics()
            
            if hasattr(adapter, 'get_health_check'):
                # Ajouter les informations de santé
                status_info['health'] = adapter.get_health_check()
            
            return status_info
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }
    
    def _calculate_global_service_status(self, all_services_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule le statut global de tous les services."""
        total_services = len(all_services_status)
        connected_services = sum(1 for status in all_services_status.values() if status.get('connected', False))
        
        health_percentage = (connected_services / total_services) * 100 if total_services > 0 else 0
        
        global_status = {
            'overall_health': 'healthy' if health_percentage == 100 else 'degraded' if health_percentage >= 50 else 'unhealthy',
            'health_percentage': health_percentage,
            'total_services': total_services,
            'connected_services': connected_services,
            'disconnected_services': total_services - connected_services
        }
        
        return global_status
    
    def _execute_service_action(self, service_name: str, adapter, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une action sur un service Docker."""
        try:
            if action == 'health_check':
                if hasattr(adapter, 'get_health_check'):
                    return adapter.get_health_check()
                else:
                    return {'connected': adapter.test_connection()}
            
            elif action == 'status':
                return adapter.get_service_status() if hasattr(adapter, 'get_service_status') else {}
            
            elif action == 'validate_config':
                config_content = parameters.get('config_content')
                if config_content and hasattr(adapter, 'validate_configuration'):
                    return adapter.validate_configuration(config_content)
                else:
                    return {'error': 'Configuration ou méthode de validation non disponible'}
            
            elif action == 'restart':
                if hasattr(adapter, 'restart_service'):
                    return adapter.restart_service()
                else:
                    return {'error': 'Redémarrage non supporté pour ce service'}
            
            else:
                return {'error': f'Action {action} non supportée'}
                
        except Exception as e:
            return {'error': str(e)}


# API de validation avancée des règles
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_security_rule(request):
    """
    Valide une règle de sécurité via les services Docker appropriés.
    
    Expected payload:
    {
        "rule_type": "firewall|ids|access_control",
        "content": "contenu de la règle",
        "strict_validation": true|false
    }
    """
    try:
        rule_type = request.data.get('rule_type')
        rule_content = request.data.get('content')
        strict_validation = request.data.get('strict_validation', True)
        
        if not rule_type or not rule_content:
            return Response(
                {'error': 'rule_type et content sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sélectionner le détecteur approprié
        detector = conflict_detector_factory.get_detector(rule_type)
        if not detector:
            return Response(
                {'error': f'Type de règle {rule_type} non supporté'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Effectuer la validation via Docker si disponible
        validation_result = {
            'rule_type': rule_type,
            'content': rule_content,
            'is_valid': True,
            'validation_details': {},
            'warnings': [],
            'errors': []
        }
        
        # Validation spécifique selon le type de règle
        if rule_type == 'firewall' and hasattr(detector, '_validate_rule_via_docker'):
            docker_result = detector._validate_rule_via_docker(rule_content)
            validation_result['validation_details']['docker_validation'] = docker_result
            
            if not docker_result.get('valid', True):
                validation_result['is_valid'] = False
                validation_result['errors'].append(docker_result.get('error', 'Validation Docker échouée'))
        
        elif rule_type == 'ids' and hasattr(detector, '_validate_rule_via_docker'):
            docker_result = detector._validate_rule_via_docker(rule_content)
            validation_result['validation_details']['docker_validation'] = docker_result
            
            if not docker_result.get('valid', True):
                validation_result['is_valid'] = False
                validation_result['errors'].append(docker_result.get('error', 'Validation Docker échouée'))
        
        # Validation syntaxique locale
        if rule_type == 'firewall' and hasattr(detector, '_parse_iptables_rule'):
            parsed_rule = detector._parse_iptables_rule(rule_content)
            if not parsed_rule:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Syntaxe de règle iptables invalide')
            else:
                validation_result['validation_details']['parsed_rule'] = parsed_rule
        
        elif rule_type == 'ids' and hasattr(detector, '_parse_ids_rule'):
            parsed_rule = detector._parse_ids_rule(rule_content)
            if not parsed_rule:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Syntaxe de règle IDS invalide')
            else:
                validation_result['validation_details']['parsed_rule'] = parsed_rule
        
        # En mode strict, vérifier les conflits potentiels
        if strict_validation and validation_result['is_valid']:
            temp_rule_data = {
                'id': 0,
                'type': rule_type,
                'content': rule_content
            }
            
            conflicts = detector.detect_conflicts(temp_rule_data, [])
            if conflicts:
                validation_result['warnings'].append(f'{len(conflicts)} conflits potentiels détectés')
                validation_result['validation_details']['potential_conflicts'] = len(conflicts)
        
        return Response({
            'validation_result': validation_result,
            'validation_timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation de règle: {str(e)}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# API pour les suggestions de résolution de conflits
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conflict_resolution_suggestions(request, conflict_id):
    """
    Récupère des suggestions de résolution pour un conflit spécifique.
    """
    try:
        # Pour l'instant, retourner des suggestions basiques
        # Dans une implémentation complète, cela utiliserait un système d'IA/ML
        suggestions = {
            'conflict_id': conflict_id,
            'automated_resolutions': [
                {
                    'type': 'merge_rules',
                    'description': 'Fusionner les règles redondantes',
                    'confidence': 0.85,
                    'impact': 'low'
                },
                {
                    'type': 'reorder_rules',
                    'description': 'Réordonner les règles pour éviter le masquage',
                    'confidence': 0.92,
                    'impact': 'medium'
                }
            ],
            'manual_recommendations': [
                'Examiner la logique métier derrière les règles conflictuelles',
                'Consulter l\'équipe de sécurité pour validation',
                'Tester les modifications dans un environnement de test'
            ],
            'risk_assessment': {
                'modification_risk': 'medium',
                'business_impact': 'low',
                'security_impact': 'low'
            }
        }
        
        return Response({
            'suggestions': suggestions,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de suggestions: {str(e)}")
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ViewSet pour la gestion CRUD complète des règles de sécurité
class SecurityRuleViewSet(ModelViewSet):
    """
    ViewSet complet pour la gestion des règles de sécurité avec détection de conflits.
    
    Fonctionnalités disponibles:
    - CRUD complet des règles de sécurité
    - Détection automatique de conflits à la création
    - Analyse d'impact des règles
    - Surveillance des services Docker
    """
    queryset = SecurityRuleModel.objects.all()
    serializer_class = SecurityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @property
    def rule_repository(self):
        """Repository des règles de sécurité (lazy loading)."""
        if not hasattr(self, '_rule_repository'):
            self._rule_repository = DjangoSecurityRuleRepository()
        return self._rule_repository
    
    @property
    def conflict_use_case(self):
        """Use case de détection de conflits (lazy loading)."""
        if not hasattr(self, '_conflict_use_case'):
            self._conflict_use_case = DetectRuleConflictsUseCase(self.rule_repository)
        return self._conflict_use_case
    
    def get_queryset(self):
        """Filtrage avancé du queryset."""
        # Gestion Swagger : retourner un queryset vide si c'est une vue factice
        if getattr(self, 'swagger_fake_view', False):
            return SecurityRuleModel.objects.none()
            
        queryset = super().get_queryset()
        
        # Filtres disponibles (vérifier que self.request n'est pas None)
        rule_type = self.request.query_params.get('rule_type') if self.request else None
        is_active = self.request.query_params.get('is_active') if self.request else None
        has_conflicts = self.request.query_params.get('has_conflicts') if self.request else None
        search = self.request.query_params.get('search') if self.request else None
        
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        
        if is_active is not None:
            queryset = queryset.filter(enabled=is_active.lower() == 'true')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(content__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-creation_date')
    
    @swagger_auto_schema(
        operation_summary="Lister les règles de sécurité",
        operation_description="Récupère la liste paginée des règles de sécurité avec filtres avancés",
        manual_parameters=[
            openapi.Parameter('rule_type', openapi.IN_QUERY, description="Type de règle", type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Règle active", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('has_conflicts', openapi.IN_QUERY, description="Règles avec conflits", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Recherche textuelle", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Liste des règles de sécurité",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            )
        },
        tags=['Security Management']
    )
    def list(self, request, *args, **kwargs):
        """Liste les règles de sécurité avec filtres."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Créer une nouvelle règle de sécurité",
        operation_description="Crée une nouvelle règle de sécurité avec détection automatique de conflits",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la règle"),
                'rule_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de règle"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Contenu de la règle"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description")
            },
            required=['name', 'rule_type', 'content']
        ),
        responses={
            201: openapi.Response(
                description="Règle créée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'rule': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Détails de la règle créée"
                        ),
                        'conflicts_detected': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'conflicts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                    }
                )
            ),
            409: openapi.Response(description="Conflits critiques détectés"),
            400: openapi.Response(description="Données invalides")
        },
        tags=['Security Management']
    )
    def create(self, request, *args, **kwargs):
        """Création d'une règle avec détection automatique de conflits."""
        with transaction.atomic():
            # Validation et sérialisation
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Détecter les conflits avant création
            rule_data = {
                'id': 0,  # ID temporaire
                'type': serializer.validated_data['rule_type'],
                'content': serializer.validated_data['content']
            }
            
            conflicts = self.conflict_use_case.detect_conflicts_for_new_rule(
                rule_data, serializer.validated_data['rule_type']
            )
            
            # Si des conflits critiques sont détectés, les signaler
            critical_conflicts = [c for c in conflicts if getattr(c, 'severity', '') == 'critical']
            if critical_conflicts and not request.data.get('force_create', False):
                return Response({
                    'error': 'Conflits critiques détectés. Utilisez force_create=true pour forcer la création.',
                    'conflicts': RuleConflictSerializer(critical_conflicts, many=True).data
                }, status=status.HTTP_409_CONFLICT)
            
            # Créer la règle
            rule = serializer.save()
            
            # Enregistrer les conflits détectés
            # Note: Dans une implémentation complète, on enregistrerait les conflits en base
            
            headers = self.get_success_headers(serializer.data)
            return Response({
                'rule': serializer.data,
                'conflicts_detected': len(conflicts),
                'conflicts': RuleConflictSerializer(conflicts, many=True).data if conflicts else []
            }, status=status.HTTP_201_CREATED, headers=headers)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Analyser les conflits d'une règle",
        operation_description="Analyse et retourne tous les conflits détectés pour une règle de sécurité spécifique",
        responses={
            200: openapi.Response(
                description="Conflits analysés avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'rule_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'conflicts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'total_conflicts': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            404: openapi.Response(description="Règle non trouvée")
        },
        tags=['Security Management']
    )
    @action(detail=True, methods=['get'])
    def conflicts(self, request, pk=None):
        """Récupère les conflits pour une règle spécifique."""
        rule = self.get_object()
        
        # Convertir en format attendu par le use case
        rule_data = {
            'id': rule.id,
            'type': rule.rule_type,
            'content': rule.content
        }
        
        # Obtenir toutes les autres règles du même type
        other_rules = SecurityRuleModel.objects.filter(
            rule_type=rule.rule_type
        ).exclude(id=rule.id).values('id', 'content', 'rule_type')
        
        other_rules_data = [
            {'id': r['id'], 'content': r['content'], 'type': r['rule_type']}
            for r in other_rules
        ]
        
        # Détecter les conflits
        detector = conflict_detector_factory.get_detector(rule.rule_type)
        if detector:
            conflicts = detector.detect_conflicts(rule_data, other_rules_data)
        else:
            conflicts = []
        
        return Response({
            'rule_id': rule.id,
            'conflicts': RuleConflictSerializer(conflicts, many=True).data,
            'total_conflicts': len(conflicts)
        })
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Analyser l'impact d'une règle",
        operation_description="Effectue une analyse d'impact détaillée pour une règle de sécurité, incluant les métriques Docker et les prédictions de performance",
        responses={
            200: openapi.Response(
                description="Analyse d'impact terminée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Résultat de l'analyse d'impact"
                )
            ),
            404: openapi.Response(description="Règle non trouvée"),
            500: openapi.Response(description="Erreur lors de l'analyse")
        },
        tags=['Security Management']
    )
    @action(detail=True, methods=['get'])
    def impact_analysis(self, request, pk=None):
        """Analyse d'impact pour une règle spécifique."""
        rule = self.get_object()
        
        try:
            metrics_collector = DockerMetricsCollector()
            metrics_calculator = AdvancedRuleMetricsCalculator()
            
            # Collecter les métriques actuelles
            current_metrics = metrics_collector.collect_all_metrics()
            
            # Analyser l'impact de la règle
            impact_analysis = metrics_calculator.calculate_rule_impact(
                rule_type=rule.rule_type,
                rule_content=rule.content,
                current_metrics=current_metrics
            )
            
            serialized_analysis = ImpactAnalysisSerializer(impact_analysis).data
            
            return Response({
                'rule_id': rule.id,
                'impact_analysis': serialized_analysis,
                'analysis_timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'impact pour la règle {rule.id}: {str(e)}")
            return Response(
                {'error': f'Erreur lors de l\'analyse d\'impact: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )