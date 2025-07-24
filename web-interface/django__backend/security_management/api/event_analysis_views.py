"""
APIs REST sophistiquées pour l'analyse d'événements et la détection d'anomalies.

Ce module contient les vues API pour :
- L'analyse en temps réel des événements de sécurité
- La détection d'anomalies avec machine learning
- La corrélation d'événements multi-sources
- L'enrichissement via services Docker
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.db.models import Q, Count, Avg, Sum

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from ..models import SecurityAlertModel, AuditLogModel
from ..domain.services import (
    SecurityCorrelationEngine, AnomalyDetectionService, SecurityEvent
)
from ..domain.entities import SecurityAlert, TrafficAnomaly, TrafficBaseline
from ..infrastructure.repositories import (
    DjangoSecurityAlertRepository, DjangoAuditLogRepository
)
from ..infrastructure.docker_integration import (
    SuricataDockerAdapter, Fail2BanDockerAdapter, TrafficControlDockerAdapter
)
from .serializers import SecurityAlertSerializer

logger = logging.getLogger(__name__)


class SecurityEventAnalysisAPIView(APIView):
    """
    API pour l'analyse sophistiquée des événements de sécurité en temps réel.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @property
    def correlation_engine(self):
        """Moteur de corrélation (lazy loading)."""
        if not hasattr(self, '_correlation_engine'):
            self._correlation_engine = SecurityCorrelationEngine()
        return self._correlation_engine
    
    @property
    def anomaly_service(self):
        """Service de détection d'anomalies (lazy loading)."""
        if not hasattr(self, '_anomaly_service'):
            self._anomaly_service = AnomalyDetectionService()
        return self._anomaly_service
    
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
    
    def post(self, request):
        """
        Analyse un événement de sécurité en temps réel.
        
        Expected payload:
        {
            "event_type": "alert|intrusion|anomaly|traffic",
            "source_ip": "192.168.1.100",
            "destination_ip": "10.0.0.1",
            "timestamp": "2023-12-01T10:30:00Z",
            "severity": "low|medium|high|critical",
            "raw_data": {...},
            "metadata": {...}
        }
        """
        try:
            # Validation des données d'entrée
            required_fields = ['event_type', 'source_ip', 'timestamp']
            for field in required_fields:
                if field not in request.data:
                    return Response(
                        {'error': f'Champ requis manquant: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Créer l'objet événement
            event = SecurityEvent(
                event_type=request.data['event_type'],
                source_ip=request.data['source_ip'],
                destination_ip=request.data.get('destination_ip'),
                timestamp=datetime.fromisoformat(request.data['timestamp'].replace('Z', '+00:00')),
                severity=request.data.get('severity', 'medium'),
                raw_data=request.data.get('raw_data', {}),
                metadata=request.data.get('metadata', {})
            )
            
            # Enrichir l'événement via les services Docker
            enrichment_results = self._enrich_event_via_docker(event)
            
            # Analyser l'événement avec le moteur de corrélation
            correlation_results = self.correlation_engine.analyze_event(event)
            
            # Détecter les anomalies
            anomaly_results = self.anomaly_service.detect_anomalies([event])
            
            # Générer des alertes si nécessaire
            alerts_generated = self._generate_alerts_if_needed(
                event, correlation_results, anomaly_results
            )
            
            # Construire la réponse
            analysis_result = {
                'event_id': event.event_id,
                'analysis_timestamp': timezone.now().isoformat(),
                'enrichment': enrichment_results,
                'correlation': {
                    'correlated_events': len(correlation_results.get('related_events', [])),
                    'correlation_score': correlation_results.get('score', 0.0),
                    'correlation_patterns': correlation_results.get('patterns', []),
                    'threat_indicators': correlation_results.get('indicators', [])
                },
                'anomaly_detection': {
                    'is_anomalous': len(anomaly_results) > 0,
                    'anomaly_count': len(anomaly_results),
                    'anomaly_types': [a.anomaly_type for a in anomaly_results],
                    'confidence_scores': [a.confidence for a in anomaly_results]
                },
                'alerts_generated': alerts_generated,
                'risk_assessment': self._calculate_risk_score(
                    event, correlation_results, anomaly_results
                ),
                'recommended_actions': self._generate_recommendations(
                    event, correlation_results, anomaly_results
                )
            }
            
            return Response(analysis_result)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'événement: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Récupère l'historique des analyses d'événements avec filtrage.
        """
        try:
            # Paramètres de filtrage
            event_type = request.query_params.get('event_type')
            severity = request.query_params.get('severity')
            source_ip = request.query_params.get('source_ip')
            time_range = request.query_params.get('time_range', '24h')
            
            # Calculer la période
            now = timezone.now()
            if time_range == '1h':
                start_time = now - timedelta(hours=1)
            elif time_range == '24h':
                start_time = now - timedelta(days=1)
            elif time_range == '7d':
                start_time = now - timedelta(days=7)
            else:
                start_time = now - timedelta(days=1)
            
            # Récupérer les alertes de sécurité comme proxy des événements analysés
            queryset = SecurityAlertModel.objects.filter(
                created_at__gte=start_time
            ).order_by('-created_at')
            
            # Appliquer les filtres
            if event_type:
                queryset = queryset.filter(alert_data__contains={'event_type': event_type})
            if severity:
                queryset = queryset.filter(severity=severity)
            if source_ip:
                queryset = queryset.filter(source_ip=source_ip)
            
            # Pagination
            paginator = PageNumberPagination()
            paginator.page_size = 50
            paginated_alerts = paginator.paginate_queryset(queryset, request)
            
            # Sérialiser et enrichir avec des données d'analyse
            serialized_alerts = SecurityAlertSerializer(paginated_alerts, many=True).data
            
            # Ajouter des métadonnées d'analyse pour chaque alerte
            for alert_data in serialized_alerts:
                alert_data['analysis_metadata'] = {
                    'correlation_score': 0.75,  # Simulation
                    'anomaly_detected': False,
                    'enrichment_sources': ['suricata', 'fail2ban'],
                    'risk_score': 'medium'
                }
            
            # Statistiques de la période
            period_stats = {
                'total_events': queryset.count(),
                'by_severity': dict(
                    queryset.values('severity').annotate(count=Count('id')).values_list('severity', 'count')
                ),
                'unique_source_ips': queryset.values('source_ip').distinct().count(),
                'alerts_generated': queryset.count(),
                'anomalies_detected': queryset.filter(
                    alert_data__contains={'anomaly_detected': True}
                ).count()
            }
            
            return paginator.get_paginated_response({
                'events': serialized_alerts,
                'period_statistics': period_stats,
                'analysis_metadata': {
                    'time_range': time_range,
                    'period': {
                        'start': start_time.isoformat(),
                        'end': now.isoformat()
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des analyses d'événements: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _enrich_event_via_docker(self, event: SecurityEvent) -> Dict[str, Any]:
        """Enrichit un événement via les services Docker."""
        enrichment = {
            'ip_reputation': {},
            'geo_location': {},
            'threat_intelligence': {},
            'validation_results': {}
        }
        
        try:
            # Enrichissement via Suricata (threat intelligence)
            if self.docker_services['suricata'].test_connection():
                suricata_data = self.docker_services['suricata'].call_api(
                    f"/threat-intel/ip/{event.source_ip}",
                    method="GET"
                )
                if 'error' not in suricata_data:
                    enrichment['threat_intelligence']['suricata'] = suricata_data
            
            # Enrichissement via Fail2Ban (IP reputation)
            if self.docker_services['fail2ban'].test_connection():
                fail2ban_data = self.docker_services['fail2ban'].call_api(
                    f"/reputation/check/{event.source_ip}",
                    method="GET"
                )
                if 'error' not in fail2ban_data:
                    enrichment['ip_reputation']['fail2ban'] = fail2ban_data
            
            # Enrichissement via Traffic Control (géolocalisation)
            if self.docker_services['traffic_control'].test_connection():
                geo_data = self.docker_services['traffic_control'].call_api(
                    f"/geoip/{event.source_ip}",
                    method="GET"
                )
                if 'error' not in geo_data:
                    enrichment['geo_location']['traffic_control'] = geo_data
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'enrichissement: {str(e)}")
            enrichment['enrichment_error'] = str(e)
        
        return enrichment
    
    def _generate_alerts_if_needed(
        self, 
        event: SecurityEvent, 
        correlation_results: Dict[str, Any], 
        anomaly_results: List
    ) -> List[Dict[str, Any]]:
        """Génère des alertes si les seuils sont dépassés."""
        alerts = []
        
        # Seuils configurables
        correlation_threshold = 0.7
        anomaly_threshold = 0.8
        
        # Alerte basée sur la corrélation
        correlation_score = correlation_results.get('score', 0.0)
        if correlation_score > correlation_threshold:
            alerts.append({
                'type': 'correlation_alert',
                'severity': 'high',
                'message': f'Événement corrélé avec un score de {correlation_score}',
                'related_events_count': len(correlation_results.get('related_events', []))
            })
        
        # Alertes basées sur les anomalies
        for anomaly in anomaly_results:
            if anomaly.confidence > anomaly_threshold:
                alerts.append({
                    'type': 'anomaly_alert',
                    'severity': 'critical' if anomaly.confidence > 0.9 else 'high',
                    'message': f'Anomalie détectée: {anomaly.anomaly_type}',
                    'confidence': anomaly.confidence,
                    'anomaly_details': anomaly.details
                })
        
        # Alerte basée sur la sévérité de l'événement
        if event.severity in ['high', 'critical']:
            alerts.append({
                'type': 'severity_alert',
                'severity': event.severity,
                'message': f'Événement de sévérité {event.severity} détecté',
                'source_ip': event.source_ip
            })
        
        return alerts
    
    def _calculate_risk_score(
        self, 
        event: SecurityEvent, 
        correlation_results: Dict[str, Any], 
        anomaly_results: List
    ) -> Dict[str, Any]:
        """Calcule un score de risque global."""
        base_score = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.7,
            'critical': 0.9
        }.get(event.severity, 0.5)
        
        # Ajustements basés sur la corrélation
        correlation_score = correlation_results.get('score', 0.0)
        correlation_adjustment = correlation_score * 0.3
        
        # Ajustements basés sur les anomalies
        anomaly_adjustment = 0.0
        if anomaly_results:
            max_anomaly_confidence = max(a.confidence for a in anomaly_results)
            anomaly_adjustment = max_anomaly_confidence * 0.4
        
        # Score final
        final_score = min(1.0, base_score + correlation_adjustment + anomaly_adjustment)
        
        risk_level = 'low'
        if final_score > 0.8:
            risk_level = 'critical'
        elif final_score > 0.6:
            risk_level = 'high'
        elif final_score > 0.4:
            risk_level = 'medium'
        
        return {
            'score': final_score,
            'level': risk_level,
            'factors': {
                'base_severity': base_score,
                'correlation_boost': correlation_adjustment,
                'anomaly_boost': anomaly_adjustment
            }
        }
    
    def _generate_recommendations(
        self, 
        event: SecurityEvent, 
        correlation_results: Dict[str, Any], 
        anomaly_results: List
    ) -> List[Dict[str, Any]]:
        """Génère des recommandations d'action."""
        recommendations = []
        
        # Recommandations basées sur la sévérité
        if event.severity in ['high', 'critical']:
            recommendations.append({
                'action': 'immediate_investigation',
                'priority': 'high',
                'description': 'Investigation immédiate requise pour cet événement critique',
                'estimated_time': '15 minutes'
            })
        
        # Recommandations basées sur les corrélations
        if correlation_results.get('score', 0.0) > 0.7:
            recommendations.append({
                'action': 'correlation_analysis',
                'priority': 'medium',
                'description': 'Analyser les événements corrélés pour identifier un pattern d\'attaque',
                'estimated_time': '30 minutes'
            })
        
        # Recommandations basées sur les anomalies
        if anomaly_results:
            recommendations.append({
                'action': 'anomaly_investigation',
                'priority': 'high',
                'description': 'Investiguer les anomalies détectées pour identifier la cause racine',
                'estimated_time': '45 minutes'
            })
        
        # Recommandations basées sur l'IP source
        if event.source_ip:
            recommendations.append({
                'action': 'ip_analysis',
                'priority': 'low',
                'description': f'Analyser l\'historique de l\'IP {event.source_ip}',
                'estimated_time': '10 minutes'
            })
        
        return recommendations


class AnomalyDetectionAPIView(APIView):
    """
    API spécialisée pour la détection d'anomalies avec machine learning.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @property
    def anomaly_service(self):
        """Service de détection d'anomalies (lazy loading)."""
        if not hasattr(self, '_anomaly_service'):
            self._anomaly_service = AnomalyDetectionService()
        return self._anomaly_service
    
    def post(self, request):
        """
        Lance une analyse d'anomalies sur un dataset d'événements.
        
        Expected payload:
        {
            "analysis_type": "realtime|batch|scheduled",
            "time_range": "1h|24h|7d|30d",
            "anomaly_types": ["traffic", "behavioral", "statistical"],
            "sensitivity": 0.8,
            "events": [...] // optionnel pour realtime
        }
        """
        try:
            analysis_type = request.data.get('analysis_type', 'realtime')
            time_range = request.data.get('time_range', '24h')
            anomaly_types = request.data.get('anomaly_types', ['traffic', 'behavioral'])
            sensitivity = request.data.get('sensitivity', 0.8)
            
            # Calculer la période d'analyse
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
            
            # Récupérer les événements à analyser
            if analysis_type == 'realtime' and 'events' in request.data:
                # Utiliser les événements fournis
                events_data = request.data['events']
                security_events = []
                for event_data in events_data:
                    event = SecurityEvent(
                        event_type=event_data.get('event_type', 'unknown'),
                        source_ip=event_data.get('source_ip'),
                        destination_ip=event_data.get('destination_ip'),
                        timestamp=datetime.fromisoformat(
                            event_data.get('timestamp', timezone.now().isoformat()).replace('Z', '+00:00')
                        ),
                        severity=event_data.get('severity', 'medium'),
                        raw_data=event_data.get('raw_data', {})
                    )
                    security_events.append(event)
            else:
                # Récupérer les événements de la base de données
                alerts = SecurityAlertModel.objects.filter(
                    created_at__gte=start_time
                ).order_by('-created_at')
                
                security_events = []
                for alert in alerts:
                    event = SecurityEvent(
                        event_type='alert',
                        source_ip=alert.source_ip,
                        destination_ip=alert.destination_ip,
                        timestamp=alert.created_at,
                        severity=alert.severity,
                        raw_data=alert.alert_data or {}
                    )
                    security_events.append(event)
            
            # Détecter les anomalies
            anomaly_results = self.anomaly_service.detect_anomalies(
                security_events, 
                sensitivity=sensitivity
            )
            
            # Analyser les patterns d'anomalies
            anomaly_patterns = self._analyze_anomaly_patterns(anomaly_results)
            
            # Calculer les statistiques
            anomaly_stats = self._calculate_anomaly_statistics(
                security_events, anomaly_results
            )
            
            # Générer les recommandations
            recommendations = self._generate_anomaly_recommendations(anomaly_results)
            
            result = {
                'analysis_metadata': {
                    'analysis_type': analysis_type,
                    'time_range': time_range,
                    'period': {
                        'start': start_time.isoformat(),
                        'end': now.isoformat()
                    },
                    'total_events_analyzed': len(security_events),
                    'anomaly_types_checked': anomaly_types,
                    'sensitivity': sensitivity,
                    'analysis_timestamp': timezone.now().isoformat()
                },
                'anomaly_detection_results': {
                    'total_anomalies': len(anomaly_results),
                    'anomalies_by_type': {},
                    'severity_distribution': {},
                    'confidence_distribution': {},
                    'detected_anomalies': []
                },
                'anomaly_patterns': anomaly_patterns,
                'statistics': anomaly_stats,
                'recommendations': recommendations
            }
            
            # Traiter les résultats d'anomalies
            for anomaly in anomaly_results:
                anomaly_type = anomaly.anomaly_type
                result['anomaly_detection_results']['anomalies_by_type'][anomaly_type] = \
                    result['anomaly_detection_results']['anomalies_by_type'].get(anomaly_type, 0) + 1
                
                severity = 'high' if anomaly.confidence > 0.8 else 'medium' if anomaly.confidence > 0.6 else 'low'
                result['anomaly_detection_results']['severity_distribution'][severity] = \
                    result['anomaly_detection_results']['severity_distribution'].get(severity, 0) + 1
                
                confidence_range = f"{int(anomaly.confidence * 10) * 10}-{int(anomaly.confidence * 10) * 10 + 10}%"
                result['anomaly_detection_results']['confidence_distribution'][confidence_range] = \
                    result['anomaly_detection_results']['confidence_distribution'].get(confidence_range, 0) + 1
                
                result['anomaly_detection_results']['detected_anomalies'].append({
                    'anomaly_id': anomaly.anomaly_id,
                    'type': anomaly.anomaly_type,
                    'confidence': anomaly.confidence,
                    'severity': severity,
                    'description': anomaly.description,
                    'detected_at': anomaly.detected_at.isoformat(),
                    'details': anomaly.details,
                    'affected_entities': getattr(anomaly, 'affected_entities', [])
                })
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Récupère l'historique des anomalies détectées.
        """
        try:
            # Paramètres de filtrage
            anomaly_type = request.query_params.get('type')
            severity = request.query_params.get('severity')
            time_range = request.query_params.get('time_range', '7d')
            confidence_min = float(request.query_params.get('confidence_min', 0.0))
            
            # Pour cette implémentation, on simule les données historiques
            # Dans une implémentation complète, cela interrogerait une table d'anomalies
            
            # Calculer la période
            now = timezone.now()
            if time_range == '24h':
                start_time = now - timedelta(days=1)
            elif time_range == '7d':
                start_time = now - timedelta(days=7)
            elif time_range == '30d':
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(days=7)
            
            # Simuler des données d'anomalies historiques
            historical_anomalies = self._generate_historical_anomalies(
                start_time, now, anomaly_type, severity, confidence_min
            )
            
            # Pagination
            paginator = PageNumberPagination()
            paginator.page_size = 25
            paginated_anomalies = paginator.paginate_queryset(historical_anomalies, request)
            
            # Statistiques de la période
            period_stats = {
                'total_anomalies': len(historical_anomalies),
                'by_type': {},
                'by_severity': {},
                'average_confidence': 0.0,
                'trend': 'stable'
            }
            
            if historical_anomalies:
                # Calculer les statistiques
                for anomaly in historical_anomalies:
                    anom_type = anomaly['type']
                    period_stats['by_type'][anom_type] = period_stats['by_type'].get(anom_type, 0) + 1
                    
                    anom_severity = anomaly['severity']
                    period_stats['by_severity'][anom_severity] = period_stats['by_severity'].get(anom_severity, 0) + 1
                
                period_stats['average_confidence'] = statistics.mean(
                    [a['confidence'] for a in historical_anomalies]
                )
            
            return paginator.get_paginated_response({
                'anomalies': paginated_anomalies,
                'period_statistics': period_stats,
                'query_metadata': {
                    'time_range': time_range,
                    'filters_applied': {
                        'type': anomaly_type,
                        'severity': severity,
                        'confidence_min': confidence_min
                    },
                    'period': {
                        'start': start_time.isoformat(),
                        'end': now.isoformat()
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des anomalies: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _analyze_anomaly_patterns(self, anomaly_results: List) -> Dict[str, Any]:
        """Analyse les patterns dans les anomalies détectées."""
        patterns = {
            'temporal_patterns': {},
            'source_ip_patterns': {},
            'anomaly_clusters': [],
            'recurring_anomalies': []
        }
        
        # Analyser les patterns temporels
        if anomaly_results:
            timestamps = [a.detected_at for a in anomaly_results]
            
            # Grouper par heure
            hourly_counts = {}
            for ts in timestamps:
                hour = ts.hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            patterns['temporal_patterns']['hourly_distribution'] = hourly_counts
            patterns['temporal_patterns']['peak_hour'] = max(hourly_counts, key=hourly_counts.get) if hourly_counts else None
        
        return patterns
    
    def _calculate_anomaly_statistics(
        self, 
        events: List[SecurityEvent], 
        anomalies: List
    ) -> Dict[str, Any]:
        """Calcule des statistiques détaillées sur les anomalies."""
        stats = {
            'detection_rate': 0.0,
            'false_positive_estimate': 0.0,
            'confidence_statistics': {},
            'performance_metrics': {}
        }
        
        if events:
            stats['detection_rate'] = len(anomalies) / len(events)
        
        if anomalies:
            confidences = [a.confidence for a in anomalies]
            stats['confidence_statistics'] = {
                'mean': statistics.mean(confidences),
                'median': statistics.median(confidences),
                'std_dev': statistics.stdev(confidences) if len(confidences) > 1 else 0.0,
                'min': min(confidences),
                'max': max(confidences)
            }
            
            # Estimation des faux positifs basée sur la confiance
            low_confidence_count = sum(1 for c in confidences if c < 0.6)
            stats['false_positive_estimate'] = low_confidence_count / len(anomalies)
        
        return stats
    
    def _generate_anomaly_recommendations(self, anomalies: List) -> List[Dict[str, Any]]:
        """Génère des recommandations basées sur les anomalies détectées."""
        recommendations = []
        
        if not anomalies:
            recommendations.append({
                'action': 'baseline_review',
                'priority': 'low',
                'description': 'Aucune anomalie détectée. Considérer la révision des baselines.',
                'category': 'maintenance'
            })
            return recommendations
        
        # Recommandations basées sur le nombre d'anomalies
        if len(anomalies) > 10:
            recommendations.append({
                'action': 'threshold_adjustment',
                'priority': 'medium',
                'description': 'Nombre élevé d\'anomalies détectées. Considérer l\'ajustement des seuils.',
                'category': 'tuning'
            })
        
        # Recommandations basées sur la confiance
        high_confidence_anomalies = [a for a in anomalies if a.confidence > 0.8]
        if high_confidence_anomalies:
            recommendations.append({
                'action': 'immediate_investigation',
                'priority': 'high',
                'description': f'{len(high_confidence_anomalies)} anomalies à haute confiance nécessitent une investigation.',
                'category': 'investigation'
            })
        
        return recommendations
    
    def _generate_historical_anomalies(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        anomaly_type: Optional[str] = None,
        severity: Optional[str] = None,
        confidence_min: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Génère des données d'anomalies historiques simulées."""
        anomalies = []
        
        # Générer des anomalies simulées
        import random
        
        types = ['traffic', 'behavioral', 'statistical', 'temporal']
        severities = ['low', 'medium', 'high', 'critical']
        
        # Nombre d'anomalies basé sur la période
        days = (end_time - start_time).days
        num_anomalies = random.randint(max(1, days), days * 3)
        
        for i in range(num_anomalies):
            anomaly_timestamp = start_time + timedelta(
                seconds=random.randint(0, int((end_time - start_time).total_seconds()))
            )
            
            anom_type = random.choice(types)
            anom_severity = random.choice(severities)
            anom_confidence = random.uniform(0.3, 0.95)
            
            # Appliquer les filtres
            if anomaly_type and anom_type != anomaly_type:
                continue
            if severity and anom_severity != severity:
                continue
            if anom_confidence < confidence_min:
                continue
            
            anomalies.append({
                'anomaly_id': f'anom_{i+1:04d}',
                'type': anom_type,
                'severity': anom_severity,
                'confidence': round(anom_confidence, 3),
                'detected_at': anomaly_timestamp.isoformat(),
                'description': f'Anomalie {anom_type} détectée avec confiance {anom_confidence:.2f}',
                'details': {
                    'metric_value': random.uniform(0.1, 10.0),
                    'baseline_value': random.uniform(0.1, 5.0),
                    'deviation_score': random.uniform(1.0, 5.0)
                },
                'source_ip': f"192.168.1.{random.randint(1, 254)}",
                'affected_entities': [f'entity_{random.randint(1, 100)}']
            })
        
        return sorted(anomalies, key=lambda x: x['detected_at'], reverse=True)