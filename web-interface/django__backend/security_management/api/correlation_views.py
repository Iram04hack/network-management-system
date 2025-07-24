"""
APIs REST pour la corrélation d'événements et l'analyse de patterns de sécurité.

Ce module contient les vues API pour :
- La corrélation d'événements multi-sources
- L'analyse de patterns d'attaques
- Le tracking de campagnes de sécurité
- La timeline d'événements corrélés
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

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

from ..models import SecurityAlertModel, AuditLogModel, CorrelationRuleModel
from ..domain.services import SecurityCorrelationEngine, SecurityEvent
from ..domain.entities import CorrelationRule, CorrelationRuleMatch
from ..infrastructure.repositories import (
    DjangoSecurityAlertRepository, DjangoCorrelationRuleRepository,
    DjangoCorrelationRuleMatchRepository
)
from .serializers import SecurityAlertSerializer

logger = logging.getLogger(__name__)


class EventCorrelationAPIView(APIView):
    """
    API pour la corrélation sophistiquée d'événements de sécurité.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @property
    def correlation_engine(self):
        """Moteur de corrélation (lazy loading)."""
        if not hasattr(self, '_correlation_engine'):
            self._correlation_engine = SecurityCorrelationEngine()
        return self._correlation_engine
    
    @property
    def alert_repository(self):
        """Repository des alertes (lazy loading)."""
        if not hasattr(self, '_alert_repository'):
            self._alert_repository = DjangoSecurityAlertRepository()
        return self._alert_repository
    
    @property
    def correlation_repository(self):
        """Repository des règles de corrélation (lazy loading)."""
        if not hasattr(self, '_correlation_repository'):
            self._correlation_repository = DjangoCorrelationRuleRepository()
        return self._correlation_repository
    
    @property
    def match_repository(self):
        """Repository des correspondances (lazy loading)."""
        if not hasattr(self, '_match_repository'):
            self._match_repository = DjangoCorrelationRuleMatchRepository()
        return self._match_repository
    
    def post(self, request):
        """
        Lance une analyse de corrélation sur des événements.
        
        Expected payload:
        {
            "correlation_type": "temporal|spatial|pattern|behavioral",
            "time_window": "5m|15m|1h|6h|24h",
            "events": [...], // optionnel, sinon utilise les événements récents
            "correlation_rules": [...], // optionnel, utilise les règles configurées
            "parameters": {
                "max_time_gap": 300, // secondes
                "min_correlation_score": 0.7,
                "include_low_confidence": false
            }
        }
        """
        try:
            correlation_type = request.data.get('correlation_type', 'temporal')
            time_window = request.data.get('time_window', '1h')
            parameters = request.data.get('parameters', {})
            
            # Paramètres de corrélation
            max_time_gap = parameters.get('max_time_gap', 300)  # 5 minutes par défaut
            min_correlation_score = parameters.get('min_correlation_score', 0.7)
            include_low_confidence = parameters.get('include_low_confidence', False)
            
            # Calculer la fenêtre temporelle
            now = timezone.now()
            if time_window == '5m':
                start_time = now - timedelta(minutes=5)
            elif time_window == '15m':
                start_time = now - timedelta(minutes=15)
            elif time_window == '1h':
                start_time = now - timedelta(hours=1)
            elif time_window == '6h':
                start_time = now - timedelta(hours=6)
            elif time_window == '24h':
                start_time = now - timedelta(days=1)
            else:
                start_time = now - timedelta(hours=1)
            
            # Récupérer ou utiliser les événements fournis
            if 'events' in request.data:
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
                # Récupérer les événements récents de la base de données
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
            
            # Récupérer les règles de corrélation
            correlation_rules = []
            if 'correlation_rules' in request.data:
                # Utiliser les règles fournies
                for rule_data in request.data['correlation_rules']:
                    rule = CorrelationRule(
                        rule_id=rule_data.get('id', 0),
                        name=rule_data.get('name', ''),
                        pattern=rule_data.get('pattern', {}),
                        time_window=rule_data.get('time_window', 300),
                        threshold=rule_data.get('threshold', 2)
                    )
                    correlation_rules.append(rule)
            else:
                # Récupérer les règles configurées en base
                rule_models = CorrelationRuleModel.objects.filter(is_active=True)
                for rule_model in rule_models:
                    rule = CorrelationRule(
                        rule_id=rule_model.id,
                        name=rule_model.name,
                        pattern=rule_model.pattern or {},
                        time_window=rule_model.time_window,
                        threshold=rule_model.threshold
                    )
                    correlation_rules.append(rule)
            
            # Effectuer la corrélation
            correlation_results = self._perform_correlation_analysis(
                security_events,
                correlation_rules,
                correlation_type,
                max_time_gap,
                min_correlation_score
            )
            
            # Analyser les patterns détectés
            pattern_analysis = self._analyze_correlation_patterns(correlation_results)
            
            # Générer des alertes de corrélation
            correlation_alerts = self._generate_correlation_alerts(
                correlation_results, min_correlation_score
            )
            
            # Créer la timeline d'événements corrélés
            correlation_timeline = self._create_correlation_timeline(correlation_results)
            
            result = {
                'correlation_analysis': {
                    'analysis_type': correlation_type,
                    'time_window': time_window,
                    'period': {
                        'start': start_time.isoformat(),
                        'end': now.isoformat()
                    },
                    'events_analyzed': len(security_events),
                    'rules_applied': len(correlation_rules),
                    'correlations_found': len(correlation_results),
                    'analysis_timestamp': timezone.now().isoformat()
                },
                'correlation_results': {
                    'total_correlations': len(correlation_results),
                    'high_confidence_correlations': len([
                        r for r in correlation_results if r.get('score', 0) >= min_correlation_score
                    ]),
                    'correlations_by_type': self._group_correlations_by_type(correlation_results),
                    'detailed_correlations': [
                        self._format_correlation_result(corr) for corr in correlation_results
                    ]
                },
                'pattern_analysis': pattern_analysis,
                'correlation_alerts': correlation_alerts,
                'correlation_timeline': correlation_timeline,
                'recommendations': self._generate_correlation_recommendations(correlation_results)
            }
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de corrélation: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Récupère l'historique des corrélations avec filtrage avancé.
        """
        try:
            # Paramètres de filtrage
            correlation_type = request.query_params.get('type')
            confidence_min = float(request.query_params.get('confidence_min', 0.0))
            time_range = request.query_params.get('time_range', '24h')
            source_ip = request.query_params.get('source_ip')
            pattern = request.query_params.get('pattern')
            
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
            
            # Pour cette implémentation, on simule les données historiques
            # Dans une implémentation complète, cela interrogerait une table de corrélations
            historical_correlations = self._generate_historical_correlations(
                start_time, now, correlation_type, confidence_min, source_ip, pattern
            )
            
            # Pagination
            paginator = PageNumberPagination()
            paginator.page_size = 20
            paginated_correlations = paginator.paginate_queryset(historical_correlations, request)
            
            # Statistiques de la période
            period_stats = {
                'total_correlations': len(historical_correlations),
                'by_type': {},
                'by_confidence_range': {},
                'average_confidence': 0.0,
                'most_common_patterns': [],
                'top_source_ips': {}
            }
            
            if historical_correlations:
                # Calculer les statistiques
                for corr in historical_correlations:
                    corr_type = corr['type']
                    period_stats['by_type'][corr_type] = period_stats['by_type'].get(corr_type, 0) + 1
                    
                    confidence = corr['confidence']
                    if confidence >= 0.8:
                        conf_range = 'high'
                    elif confidence >= 0.6:
                        conf_range = 'medium'
                    else:
                        conf_range = 'low'
                    period_stats['by_confidence_range'][conf_range] = \
                        period_stats['by_confidence_range'].get(conf_range, 0) + 1
                    
                    # Compter les IPs sources
                    if 'source_ips' in corr:
                        for ip in corr['source_ips']:
                            period_stats['top_source_ips'][ip] = \
                                period_stats['top_source_ips'].get(ip, 0) + 1
                
                period_stats['average_confidence'] = sum(
                    c['confidence'] for c in historical_correlations
                ) / len(historical_correlations)
                
                # Top 5 des IPs sources
                period_stats['top_source_ips'] = dict(
                    sorted(period_stats['top_source_ips'].items(), 
                           key=lambda x: x[1], reverse=True)[:5]
                )
            
            return paginator.get_paginated_response({
                'correlations': paginated_correlations,
                'period_statistics': period_stats,
                'query_metadata': {
                    'time_range': time_range,
                    'filters_applied': {
                        'type': correlation_type,
                        'confidence_min': confidence_min,
                        'source_ip': source_ip,
                        'pattern': pattern
                    },
                    'period': {
                        'start': start_time.isoformat(),
                        'end': now.isoformat()
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des corrélations: {str(e)}")
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _perform_correlation_analysis(
        self,
        events: List[SecurityEvent],
        rules: List[CorrelationRule],
        correlation_type: str,
        max_time_gap: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Effectue l'analyse de corrélation sur les événements."""
        correlations = []
        
        if correlation_type == 'temporal':
            correlations.extend(self._temporal_correlation(events, max_time_gap))
        elif correlation_type == 'spatial':
            correlations.extend(self._spatial_correlation(events))
        elif correlation_type == 'pattern':
            correlations.extend(self._pattern_correlation(events, rules))
        elif correlation_type == 'behavioral':
            correlations.extend(self._behavioral_correlation(events))
        else:
            # Analyse complète avec tous les types
            correlations.extend(self._temporal_correlation(events, max_time_gap))
            correlations.extend(self._spatial_correlation(events))
            correlations.extend(self._pattern_correlation(events, rules))
        
        # Filtrer par score minimum
        filtered_correlations = [c for c in correlations if c.get('score', 0) >= min_score]
        
        return filtered_correlations
    
    def _temporal_correlation(self, events: List[SecurityEvent], max_gap: int) -> List[Dict[str, Any]]:
        """Corrélation basée sur la proximité temporelle."""
        correlations = []
        
        # Trier les événements par timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        for i, event1 in enumerate(sorted_events):
            for j, event2 in enumerate(sorted_events[i+1:], i+1):
                time_diff = (event2.timestamp - event1.timestamp).total_seconds()
                
                if time_diff > max_gap:
                    break  # Les événements suivants seront encore plus éloignés
                
                # Calculer le score de corrélation temporelle
                score = max(0.0, 1.0 - (time_diff / max_gap))
                
                # Bonus si même source ou destination IP
                if event1.source_ip == event2.source_ip:
                    score += 0.2
                if event1.destination_ip == event2.destination_ip:
                    score += 0.1
                
                score = min(1.0, score)
                
                if score > 0.5:  # Seuil minimum pour considérer une corrélation
                    correlations.append({
                        'type': 'temporal',
                        'event_ids': [event1.event_id, event2.event_id],
                        'score': score,
                        'time_gap_seconds': time_diff,
                        'description': f'Événements corrélés temporellement (écart: {time_diff:.0f}s)',
                        'details': {
                            'event1': {
                                'timestamp': event1.timestamp.isoformat(),
                                'source_ip': event1.source_ip,
                                'type': event1.event_type
                            },
                            'event2': {
                                'timestamp': event2.timestamp.isoformat(),
                                'source_ip': event2.source_ip,
                                'type': event2.event_type
                            }
                        }
                    })
        
        return correlations
    
    def _spatial_correlation(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Corrélation basée sur la proximité géographique/réseau."""
        correlations = []
        
        # Grouper les événements par IP source
        events_by_source = defaultdict(list)
        for event in events:
            if event.source_ip:
                events_by_source[event.source_ip].append(event)
        
        # Chercher des patterns par IP
        for source_ip, ip_events in events_by_source.items():
            if len(ip_events) > 1:
                # Calculer le score basé sur le nombre d'événements et leur diversité
                event_types = set(e.event_type for e in ip_events)
                score = min(1.0, len(ip_events) / 10.0 + len(event_types) / 5.0)
                
                if score > 0.6:
                    correlations.append({
                        'type': 'spatial',
                        'event_ids': [e.event_id for e in ip_events],
                        'score': score,
                        'source_ip': source_ip,
                        'event_count': len(ip_events),
                        'description': f'Activité corrélée depuis {source_ip} ({len(ip_events)} événements)',
                        'details': {
                            'source_ip': source_ip,
                            'event_types': list(event_types),
                            'time_span': (max(e.timestamp for e in ip_events) - 
                                        min(e.timestamp for e in ip_events)).total_seconds()
                        }
                    })
        
        return correlations
    
    def _pattern_correlation(
        self, 
        events: List[SecurityEvent], 
        rules: List[CorrelationRule]
    ) -> List[Dict[str, Any]]:
        """Corrélation basée sur des patterns prédéfinis."""
        correlations = []
        
        for rule in rules:
            matched_events = []
            
            # Appliquer la règle de corrélation
            for event in events:
                if self._event_matches_pattern(event, rule.pattern):
                    matched_events.append(event)
            
            # Vérifier si le seuil est atteint
            if len(matched_events) >= rule.threshold:
                # Vérifier la fenêtre temporelle
                if matched_events:
                    time_span = (max(e.timestamp for e in matched_events) - 
                               min(e.timestamp for e in matched_events)).total_seconds()
                    
                    if time_span <= rule.time_window:
                        score = min(1.0, len(matched_events) / (rule.threshold * 2))
                        
                        correlations.append({
                            'type': 'pattern',
                            'event_ids': [e.event_id for e in matched_events],
                            'score': score,
                            'rule_id': rule.rule_id,
                            'rule_name': rule.name,
                            'matched_count': len(matched_events),
                            'description': f'Pattern "{rule.name}" détecté ({len(matched_events)} événements)',
                            'details': {
                                'rule_pattern': rule.pattern,
                                'time_window': rule.time_window,
                                'threshold': rule.threshold,
                                'time_span': time_span
                            }
                        })
        
        return correlations
    
    def _behavioral_correlation(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Corrélation basée sur l'analyse comportementale."""
        correlations = []
        
        # Analyser les patterns de comportement suspects
        # Exemple: escalade de privilèges, reconnaissance, exfiltration
        
        # Grouper par source IP et analyser la séquence d'événements
        events_by_source = defaultdict(list)
        for event in events:
            if event.source_ip:
                events_by_source[event.source_ip].append(event)
        
        for source_ip, ip_events in events_by_source.items():
            if len(ip_events) < 3:  # Besoin d'au moins 3 événements pour un pattern comportemental
                continue
            
            # Trier par timestamp
            sorted_events = sorted(ip_events, key=lambda e: e.timestamp)
            
            # Détecter des patterns comportementaux spécifiques
            behavioral_patterns = self._detect_behavioral_patterns(sorted_events)
            
            for pattern in behavioral_patterns:
                correlations.append({
                    'type': 'behavioral',
                    'event_ids': [e.event_id for e in pattern['events']],
                    'score': pattern['score'],
                    'source_ip': source_ip,
                    'pattern_type': pattern['pattern_type'],
                    'description': f'Pattern comportemental "{pattern["pattern_type"]}" détecté depuis {source_ip}',
                    'details': pattern['details']
                })
        
        return correlations
    
    def _event_matches_pattern(self, event: SecurityEvent, pattern: Dict[str, Any]) -> bool:
        """Vérifie si un événement correspond à un pattern."""
        for key, expected_value in pattern.items():
            if key == 'event_type':
                if event.event_type != expected_value:
                    return False
            elif key == 'severity':
                if event.severity != expected_value:
                    return False
            elif key == 'source_ip_range':
                # Vérifier si l'IP source est dans la plage
                # Implémentation simplifiée
                if not self._ip_in_range(event.source_ip, expected_value):
                    return False
            # Ajouter d'autres critères selon les besoins
        
        return True
    
    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Vérifie si une IP est dans une plage donnée."""
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range, strict=False)
        except:
            return False
    
    def _detect_behavioral_patterns(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Détecte des patterns comportementaux dans une séquence d'événements."""
        patterns = []
        
        # Pattern 1: Reconnaissance suivie d'attaque
        if len(events) >= 3:
            # Chercher des événements de reconnaissance suivis d'événements d'attaque
            recon_events = [e for e in events if 'scan' in e.event_type.lower() or 'probe' in e.event_type.lower()]
            attack_events = [e for e in events if e.severity in ['high', 'critical']]
            
            if recon_events and attack_events:
                # Vérifier la séquence temporelle
                last_recon = max(recon_events, key=lambda e: e.timestamp)
                first_attack = min(attack_events, key=lambda e: e.timestamp)
                
                if last_recon.timestamp < first_attack.timestamp:
                    time_gap = (first_attack.timestamp - last_recon.timestamp).total_seconds()
                    if time_gap < 3600:  # Dans l'heure qui suit
                        score = max(0.7, 1.0 - (time_gap / 3600))
                        patterns.append({
                            'pattern_type': 'reconnaissance_to_attack',
                            'events': recon_events + attack_events,
                            'score': score,
                            'details': {
                                'reconnaissance_events': len(recon_events),
                                'attack_events': len(attack_events),
                                'time_gap_seconds': time_gap
                            }
                        })
        
        # Pattern 2: Escalade progressive de sévérité
        if len(events) >= 4:
            severities = [e.severity for e in events]
            severity_values = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            severity_progression = [severity_values.get(s, 1) for s in severities]
            
            # Vérifier si la sévérité augmente progressivement
            increasing_count = sum(1 for i in range(1, len(severity_progression)) 
                                 if severity_progression[i] >= severity_progression[i-1])
            
            if increasing_count >= len(severity_progression) * 0.7:  # 70% d'augmentation
                score = min(1.0, increasing_count / len(severity_progression))
                patterns.append({
                    'pattern_type': 'severity_escalation',
                    'events': events,
                    'score': score,
                    'details': {
                        'severity_progression': severities,
                        'escalation_ratio': increasing_count / len(severity_progression)
                    }
                })
        
        return patterns
    
    def _analyze_correlation_patterns(self, correlations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse les patterns dans les corrélations détectées."""
        analysis = {
            'pattern_summary': {},
            'temporal_distribution': {},
            'source_ip_analysis': {},
            'attack_chains': [],
            'confidence_distribution': {}
        }
        
        if not correlations:
            return analysis
        
        # Analyser la distribution par type
        for corr in correlations:
            corr_type = corr['type']
            analysis['pattern_summary'][corr_type] = analysis['pattern_summary'].get(corr_type, 0) + 1
        
        # Analyser la distribution de confiance
        for corr in correlations:
            score = corr['score']
            if score >= 0.8:
                conf_level = 'high'
            elif score >= 0.6:
                conf_level = 'medium'
            else:
                conf_level = 'low'
            
            analysis['confidence_distribution'][conf_level] = \
                analysis['confidence_distribution'].get(conf_level, 0) + 1
        
        # Analyser les chaînes d'attaque potentielles
        behavioral_correlations = [c for c in correlations if c['type'] == 'behavioral']
        for corr in behavioral_correlations:
            if corr.get('pattern_type') == 'reconnaissance_to_attack':
                analysis['attack_chains'].append({
                    'type': 'recon_to_attack',
                    'source_ip': corr.get('source_ip'),
                    'confidence': corr['score'],
                    'event_count': len(corr['event_ids'])
                })
        
        return analysis
    
    def _generate_correlation_alerts(
        self, 
        correlations: List[Dict[str, Any]], 
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Génère des alertes basées sur les corrélations détectées."""
        alerts = []
        
        for corr in correlations:
            if corr['score'] >= min_score:
                severity = 'critical' if corr['score'] > 0.9 else 'high' if corr['score'] > 0.7 else 'medium'
                
                alerts.append({
                    'alert_type': 'correlation_alert',
                    'correlation_type': corr['type'],
                    'severity': severity,
                    'confidence': corr['score'],
                    'message': corr['description'],
                    'correlated_events': len(corr['event_ids']),
                    'details': corr.get('details', {}),
                    'generated_at': timezone.now().isoformat()
                })
        
        return alerts
    
    def _create_correlation_timeline(self, correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crée une timeline des événements corrélés."""
        timeline_events = []
        
        for corr in correlations:
            if 'details' in corr and corr['type'] == 'temporal':
                details = corr['details']
                
                # Ajouter les événements à la timeline
                if 'event1' in details:
                    timeline_events.append({
                        'timestamp': details['event1']['timestamp'],
                        'event_type': details['event1']['type'],
                        'source_ip': details['event1']['source_ip'],
                        'correlation_id': f"{corr['type']}_{hash(str(corr['event_ids']))}",
                        'correlation_score': corr['score']
                    })
                
                if 'event2' in details:
                    timeline_events.append({
                        'timestamp': details['event2']['timestamp'],
                        'event_type': details['event2']['type'],
                        'source_ip': details['event2']['source_ip'],
                        'correlation_id': f"{corr['type']}_{hash(str(corr['event_ids']))}",
                        'correlation_score': corr['score']
                    })
        
        # Trier par timestamp
        timeline_events.sort(key=lambda x: x['timestamp'])
        
        return timeline_events
    
    def _generate_correlation_recommendations(self, correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Génère des recommandations basées sur les corrélations."""
        recommendations = []
        
        high_confidence_correlations = [c for c in correlations if c['score'] > 0.8]
        
        if high_confidence_correlations:
            recommendations.append({
                'action': 'immediate_investigation',
                'priority': 'high',
                'description': f'{len(high_confidence_correlations)} corrélations à haute confiance nécessitent une investigation.',
                'category': 'investigation'
            })
        
        behavioral_patterns = [c for c in correlations if c['type'] == 'behavioral']
        if behavioral_patterns:
            recommendations.append({
                'action': 'behavioral_analysis',
                'priority': 'medium',
                'description': 'Patterns comportementaux détectés. Analyser pour identifier des campagnes d\'attaque.',
                'category': 'analysis'
            })
        
        temporal_clusters = [c for c in correlations if c['type'] == 'temporal']
        if len(temporal_clusters) > 10:
            recommendations.append({
                'action': 'incident_response',
                'priority': 'high',
                'description': 'Activité temporelle importante détectée. Déclencher la procédure d\'incident.',
                'category': 'response'
            })
        
        return recommendations
    
    def _group_correlations_by_type(self, correlations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Groupe les corrélations par type."""
        groups = {}
        for corr in correlations:
            corr_type = corr['type']
            groups[corr_type] = groups.get(corr_type, 0) + 1
        return groups
    
    def _format_correlation_result(self, correlation: Dict[str, Any]) -> Dict[str, Any]:
        """Formate un résultat de corrélation pour l'API."""
        return {
            'id': f"{correlation['type']}_{hash(str(correlation['event_ids']))}",
            'type': correlation['type'],
            'score': correlation['score'],
            'description': correlation['description'],
            'event_count': len(correlation['event_ids']),
            'details': correlation.get('details', {}),
            'timestamp': timezone.now().isoformat()
        }
    
    def _generate_historical_correlations(
        self,
        start_time: datetime,
        end_time: datetime,
        correlation_type: Optional[str] = None,
        confidence_min: float = 0.0,
        source_ip: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Génère des données de corrélations historiques simulées."""
        correlations = []
        
        import random
        
        types = ['temporal', 'spatial', 'pattern', 'behavioral']
        
        # Nombre de corrélations basé sur la période
        days = (end_time - start_time).days
        num_correlations = random.randint(max(1, days), days * 5)
        
        for i in range(num_correlations):
            corr_timestamp = start_time + timedelta(
                seconds=random.randint(0, int((end_time - start_time).total_seconds()))
            )
            
            corr_type = random.choice(types)
            corr_confidence = random.uniform(0.4, 0.95)
            corr_source_ip = f"192.168.1.{random.randint(1, 254)}"
            
            # Appliquer les filtres
            if correlation_type and corr_type != correlation_type:
                continue
            if corr_confidence < confidence_min:
                continue
            if source_ip and corr_source_ip != source_ip:
                continue
            
            correlations.append({
                'correlation_id': f'corr_{i+1:04d}',
                'type': corr_type,
                'confidence': round(corr_confidence, 3),
                'detected_at': corr_timestamp.isoformat(),
                'description': f'Corrélation {corr_type} détectée avec confiance {corr_confidence:.2f}',
                'event_count': random.randint(2, 8),
                'source_ips': [corr_source_ip] + [f"192.168.1.{random.randint(1, 254)}" for _ in range(random.randint(0, 2))],
                'time_span_seconds': random.randint(60, 3600),
                'details': {
                    'pattern_matched': pattern if pattern else f'pattern_{random.randint(1, 10)}',
                    'severity_levels': random.choice([['low', 'medium'], ['medium', 'high'], ['high', 'critical']]),
                    'attack_chain': random.choice([True, False])
                }
            })
        
        return sorted(correlations, key=lambda x: x['detected_at'], reverse=True)