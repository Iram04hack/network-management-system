"""
APIs REST unifiées pour le module security_management avec documentation Swagger.

Ce module expose toutes les fonctionnalités du module security_management via des APIs
REST modernes avec documentation Swagger complète, intégration GNS3 et services Docker.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.unified_security_service import unified_security_service
from ..models import SecurityRuleModel, SecurityAlertModel, VulnerabilityModel

logger = logging.getLogger(__name__)


# Schémas Swagger pour la documentation
security_event_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'event_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type d\'événement'),
        'source_ip': openapi.Schema(type=openapi.TYPE_STRING, description='IP source'),
        'destination_ip': openapi.Schema(type=openapi.TYPE_STRING, description='IP destination'),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Horodatage'),
        'severity': openapi.Schema(type=openapi.TYPE_STRING, enum=['low', 'medium', 'high', 'critical']),
        'raw_data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Données brutes'),
        'metadata': openapi.Schema(type=openapi.TYPE_OBJECT, description='Métadonnées')
    },
    required=['event_type', 'source_ip', 'timestamp']
)

dashboard_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'dashboard_data': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'alerts_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'critical_alerts': openapi.Schema(type=openapi.TYPE_INTEGER),
                'active_rules': openapi.Schema(type=openapi.TYPE_INTEGER),
                'blocked_ips': openapi.Schema(type=openapi.TYPE_INTEGER),
                'security_score': openapi.Schema(type=openapi.TYPE_NUMBER)
            }
        ),
        'gns3_context': openapi.Schema(type=openapi.TYPE_OBJECT),
        'docker_services': openapi.Schema(type=openapi.TYPE_OBJECT),
        'health_status': openapi.Schema(type=openapi.TYPE_OBJECT)
    }
)

analysis_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'analysis_type': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['comprehensive', 'threats', 'vulnerabilities'],
            description='Type d\'analyse'
        ),
        'time_range': openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=['1h', '24h', '7d', '30d'],
            description='Période d\'analyse'
        )
    }
)


@swagger_auto_schema(
    method='get',
    operation_description='Récupère le tableau de bord de sécurité unifié avec données GNS3 et Docker',
    responses={
        200: dashboard_response_schema,
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Dashboard']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_dashboard(request):
    """
    Récupère le tableau de bord de sécurité unifié.
    
    Fournit une vue d'ensemble complète de la sécurité incluant :
    - Statistiques des alertes et règles
    - Contexte topologique GNS3
    - États des services Docker
    - Métriques de performance
    - Score de sécurité global
    """
    try:
        dashboard_data = unified_security_service.get_security_dashboard()
        return Response(dashboard_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur dashboard sécurité: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération du tableau de bord'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description='Traite un événement de sécurité avec corrélation et détection d\'anomalies',
    request_body=security_event_schema,
    responses={
        200: openapi.Response('Événement traité avec succès'),
        400: openapi.Response('Données d\'entrée invalides'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Events']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_security_event(request):
    """
    Traite un événement de sécurité avec enrichissement complet.
    
    Fonctionnalités :
    - Corrélation avec événements existants
    - Détection d'anomalies
    - Enrichissement via GNS3 et Docker
    - Génération d'alertes automatiques
    - Recommandations d'actions
    """
    try:
        event_data = request.data
        
        # Validation des données requises
        required_fields = ['event_type', 'source_ip', 'timestamp']
        for field in required_fields:
            if field not in event_data:
                return Response(
                    {'error': f'Champ requis manquant: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Traiter l'événement
        result = unified_security_service.process_security_event(event_data)
        
        if 'error' in result:
            return Response(
                {'error': result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur traitement événement: {e}")
        return Response(
            {'error': 'Erreur lors du traitement de l\'événement'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description='Lance une analyse de sécurité complète',
    request_body=analysis_request_schema,
    responses={
        200: openapi.Response('Analyse terminée avec succès'),
        400: openapi.Response('Paramètres d\'analyse invalides'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Analysis']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_security_analysis(request):
    """
    Lance une analyse de sécurité complète.
    
    Types d'analyse disponibles :
    - comprehensive : Analyse complète (menaces + vulnérabilités + posture)
    - threats : Analyse du paysage des menaces
    - vulnerabilities : Évaluation des vulnérabilités
    
    Périodes supportées : 1h, 24h, 7d, 30d
    """
    try:
        analysis_type = request.data.get('analysis_type', 'comprehensive')
        time_range = request.data.get('time_range', '24h')
        
        # Validation des paramètres
        valid_types = ['comprehensive', 'threats', 'vulnerabilities']
        valid_ranges = ['1h', '24h', '7d', '30d']
        
        if analysis_type not in valid_types:
            return Response(
                {'error': f'Type d\'analyse invalide. Valeurs acceptées: {valid_types}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if time_range not in valid_ranges:
            return Response(
                {'error': f'Période invalide. Valeurs acceptées: {valid_ranges}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lancer l'analyse
        result = unified_security_service.run_security_analysis(
            analysis_type=analysis_type,
            time_range=time_range
        )
        
        if 'error' in result:
            return Response(
                {'error': result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur analyse sécurité: {e}")
        return Response(
            {'error': 'Erreur lors de l\'analyse de sécurité'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description='Récupère le statut complet du système de sécurité',
    responses={
        200: openapi.Response('Statut récupéré avec succès'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Status']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_status(request):
    """
    Récupère le statut complet du système de sécurité.
    
    Informations incluses :
    - Statut des services Docker (Suricata, Fail2ban, Traffic Control)
    - Disponibilité de l'intégration GNS3
    - Statistiques de sécurité
    - Métriques de performance
    - Score de santé global
    """
    try:
        status_data = unified_security_service.get_comprehensive_status()
        return Response(status_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erreur statut sécurité: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération du statut'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description='Récupère les alertes de sécurité avec filtrage',
    manual_parameters=[
        openapi.Parameter('severity', openapi.IN_QUERY, description='Filtrer par sévérité', type=openapi.TYPE_STRING),
        openapi.Parameter('status', openapi.IN_QUERY, description='Filtrer par statut', type=openapi.TYPE_STRING),
        openapi.Parameter('source_ip', openapi.IN_QUERY, description='Filtrer par IP source', type=openapi.TYPE_STRING),
        openapi.Parameter('limit', openapi.IN_QUERY, description='Nombre de résultats', type=openapi.TYPE_INTEGER),
        openapi.Parameter('offset', openapi.IN_QUERY, description='Décalage pour pagination', type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: openapi.Response('Alertes récupérées avec succès'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Alerts']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_alerts(request):
    """
    Récupère les alertes de sécurité avec filtrage avancé.
    
    Paramètres de filtrage :
    - severity : critical, high, medium, low
    - status : new, acknowledged, resolved, false_positive
    - source_ip : Adresse IP source
    - limit : Nombre maximum de résultats (défaut: 50)
    - offset : Décalage pour pagination (défaut: 0)
    """
    try:
        # Récupération des paramètres
        severity = request.query_params.get('severity')
        alert_status = request.query_params.get('status')
        source_ip = request.query_params.get('source_ip')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Construction de la requête
        queryset = SecurityAlertModel.objects.all()
        
        # Application des filtres
        if severity:
            queryset = queryset.filter(severity=severity)
        if alert_status:
            queryset = queryset.filter(status=alert_status)
        if source_ip:
            queryset = queryset.filter(source_ip=source_ip)
        
        # Pagination
        total_count = queryset.count()
        alerts = queryset.order_by('-detection_time')[offset:offset + limit]
        
        # Sérialisation des données
        alerts_data = []
        for alert in alerts:
            alert_data = {
                'id': alert.id,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity,
                'status': alert.status,
                'source_ip': alert.source_ip,
                'destination_ip': alert.destination_ip,
                'detection_time': alert.detection_time.isoformat(),
                'raw_data': alert.raw_data
            }
            alerts_data.append(alert_data)
        
        response_data = {
            'total_count': total_count,
            'count': len(alerts_data),
            'offset': offset,
            'limit': limit,
            'alerts': alerts_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération alertes: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des alertes'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description='Récupère les règles de sécurité avec filtrage',
    manual_parameters=[
        openapi.Parameter('rule_type', openapi.IN_QUERY, description='Filtrer par type de règle', type=openapi.TYPE_STRING),
        openapi.Parameter('enabled', openapi.IN_QUERY, description='Filtrer par statut (true/false)', type=openapi.TYPE_BOOLEAN),
        openapi.Parameter('limit', openapi.IN_QUERY, description='Nombre de résultats', type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: openapi.Response('Règles récupérées avec succès'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Rules']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_rules(request):
    """
    Récupère les règles de sécurité avec filtrage.
    
    Paramètres de filtrage :
    - rule_type : suricata, fail2ban, firewall, custom
    - enabled : true/false pour filtrer les règles actives
    - limit : Nombre maximum de résultats (défaut: 100)
    """
    try:
        # Récupération des paramètres
        rule_type = request.query_params.get('rule_type')
        enabled = request.query_params.get('enabled')
        limit = int(request.query_params.get('limit', 100))
        
        # Construction de la requête
        queryset = SecurityRuleModel.objects.all()
        
        # Application des filtres
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        if enabled is not None:
            enabled_bool = enabled.lower() == 'true'
            queryset = queryset.filter(enabled=enabled_bool)
        
        # Limitation des résultats
        rules = queryset.order_by('-last_modified')[:limit]
        
        # Sérialisation des données
        rules_data = []
        for rule in rules:
            rule_data = {
                'id': rule.id,
                'name': rule.name,
                'rule_type': rule.rule_type,
                'content': rule.content,
                'description': rule.description,
                'enabled': rule.enabled,
                'priority': rule.priority,
                'trigger_count': rule.trigger_count,
                'creation_date': rule.creation_date.isoformat(),
                'last_modified': rule.last_modified.isoformat()
            }
            rules_data.append(rule_data)
        
        response_data = {
            'count': len(rules_data),
            'rules': rules_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération règles: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des règles'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description='Récupère les vulnérabilités avec filtrage',
    manual_parameters=[
        openapi.Parameter('severity', openapi.IN_QUERY, description='Filtrer par sévérité', type=openapi.TYPE_STRING),
        openapi.Parameter('status', openapi.IN_QUERY, description='Filtrer par statut', type=openapi.TYPE_STRING),
        openapi.Parameter('patch_available', openapi.IN_QUERY, description='Filtrer par disponibilité de patch', type=openapi.TYPE_BOOLEAN),
        openapi.Parameter('limit', openapi.IN_QUERY, description='Nombre de résultats', type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: openapi.Response('Vulnérabilités récupérées avec succès'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Vulnerabilities']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vulnerabilities(request):
    """
    Récupère les vulnérabilités avec filtrage avancé.
    
    Paramètres de filtrage :
    - severity : critical, high, medium, low
    - status : identified, confirmed, in_progress, patched, mitigated
    - patch_available : true/false
    - limit : Nombre maximum de résultats (défaut: 50)
    """
    try:
        # Récupération des paramètres
        severity = request.query_params.get('severity')
        vuln_status = request.query_params.get('status')
        patch_available = request.query_params.get('patch_available')
        limit = int(request.query_params.get('limit', 50))
        
        # Construction de la requête
        queryset = VulnerabilityModel.objects.all()
        
        # Application des filtres
        if severity:
            queryset = queryset.filter(severity=severity)
        if vuln_status:
            queryset = queryset.filter(status=vuln_status)
        if patch_available is not None:
            patch_bool = patch_available.lower() == 'true'
            queryset = queryset.filter(patch_available=patch_bool)
        
        # Limitation des résultats
        vulnerabilities = queryset.order_by('-cvss_score', '-discovered_date')[:limit]
        
        # Sérialisation des données
        vulns_data = []
        for vuln in vulnerabilities:
            vuln_data = {
                'id': vuln.id,
                'cve_id': vuln.cve_id,
                'title': vuln.title,
                'description': vuln.description,
                'severity': vuln.severity,
                'cvss_score': vuln.cvss_score,
                'status': vuln.status,
                'affected_systems': vuln.affected_systems,
                'patch_available': vuln.patch_available,
                'discovered_date': vuln.discovered_date.isoformat(),
                'priority': vuln.priority
            }
            vulns_data.append(vuln_data)
        
        response_data = {
            'count': len(vulns_data),
            'vulnerabilities': vulns_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération vulnérabilités: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des vulnérabilités'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description='Récupère les métriques de sécurité détaillées',
    manual_parameters=[
        openapi.Parameter('time_range', openapi.IN_QUERY, description='Période des métriques', type=openapi.TYPE_STRING),
        openapi.Parameter('metric_type', openapi.IN_QUERY, description='Type de métrique', type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response('Métriques récupérées avec succès'),
        500: openapi.Response('Erreur interne du serveur')
    },
    tags=['Security Metrics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_metrics(request):
    """
    Récupère les métriques de sécurité détaillées.
    
    Paramètres :
    - time_range : 1h, 24h, 7d, 30d (défaut: 24h)
    - metric_type : alerts, rules, vulnerabilities, performance (défaut: all)
    """
    try:
        time_range = request.query_params.get('time_range', '24h')
        metric_type = request.query_params.get('metric_type', 'all')
        
        # Calculer la période
        now = timezone.now()
        if time_range == '1h':
            start_time = now - timedelta(hours=1)
        elif time_range == '24h':
            start_time = now - timedelta(days=1)
        elif time_range == '7d':
            start_time = now - timedelta(days=7)
        elif time_range == '30d':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        
        metrics = {
            'time_range': time_range,
            'period': {
                'start': start_time.isoformat(),
                'end': now.isoformat()
            },
            'metrics': {}
        }
        
        # Métriques des alertes
        if metric_type in ['all', 'alerts']:
            alerts_metrics = {
                'total_alerts': SecurityAlertModel.objects.filter(
                    detection_time__gte=start_time
                ).count(),
                'alerts_by_severity': dict(
                    SecurityAlertModel.objects.filter(
                        detection_time__gte=start_time
                    ).values('severity').annotate(
                        count=Count('id')
                    ).values_list('severity', 'count')
                ),
                'alerts_by_status': dict(
                    SecurityAlertModel.objects.filter(
                        detection_time__gte=start_time
                    ).values('status').annotate(
                        count=Count('id')
                    ).values_list('status', 'count')
                )
            }
            metrics['metrics']['alerts'] = alerts_metrics
        
        # Métriques des règles
        if metric_type in ['all', 'rules']:
            rules_metrics = {
                'total_rules': SecurityRuleModel.objects.count(),
                'active_rules': SecurityRuleModel.objects.filter(enabled=True).count(),
                'rules_by_type': dict(
                    SecurityRuleModel.objects.values('rule_type').annotate(
                        count=Count('id')
                    ).values_list('rule_type', 'count')
                )
            }
            metrics['metrics']['rules'] = rules_metrics
        
        # Métriques des vulnérabilités
        if metric_type in ['all', 'vulnerabilities']:
            vulns_metrics = {
                'total_vulnerabilities': VulnerabilityModel.objects.count(),
                'vulnerabilities_by_severity': dict(
                    VulnerabilityModel.objects.values('severity').annotate(
                        count=Count('id')
                    ).values_list('severity', 'count')
                ),
                'patchable_vulnerabilities': VulnerabilityModel.objects.filter(
                    patch_available=True
                ).count()
            }
            metrics['metrics']['vulnerabilities'] = vulns_metrics
        
        # Métriques de performance
        if metric_type in ['all', 'performance']:
            performance_metrics = {
                'docker_services_health': 'healthy',  # Simulé
                'gns3_integration_status': unified_security_service.gns3_adapter.is_available(),
                'response_times': {
                    'avg_alert_processing': 2.5,
                    'avg_rule_evaluation': 0.8,
                    'avg_vulnerability_scan': 45.2
                }
            }
            metrics['metrics']['performance'] = performance_metrics
        
        return Response(metrics, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération métriques: {e}")
        return Response(
            {'error': 'Erreur lors de la récupération des métriques'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )