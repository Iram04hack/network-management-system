"""
Services du domaine pour le module security_management avec intégration Docker.

Ce fichier contient les implémentations avancées des services métier du domaine,
incluant un moteur de corrélation d'événements sophistiqué, des services de 
détection d'anomalies avec analyse statistique, et des middlewares d'enrichissement
via les services Docker.
"""

import json
import logging
import statistics
import threading
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Callable, Union
import requests
import ipaddress
import re

from django.conf import settings
from django.utils import timezone

from .entities import (
    SecurityRule, SecurityAlert, EntityId, 
    CorrelationRule, CorrelationRuleMatch,
    TrafficBaseline, TrafficAnomaly,
    IPReputation, RuleType, SeverityLevel, AlertStatus
)
from .exceptions import (
    RuleConflictException, SecurityRuleValidationException, 
    CorrelationEngineException
)
from .interfaces import (
    SecurityRuleRepository, SecurityAlertRepository, CorrelationRuleRepository,
    CorrelationRuleMatchRepository, DockerServiceConnector
)

logger = logging.getLogger(__name__)


class SecurityEvent:
    """
    Représente un événement de sécurité enrichi avec métadonnées.
    """
    
    def __init__(self, event_id: str = None, event_type: str = None, 
                 source_ip: str = None, destination_ip: str = None,
                 timestamp: datetime = None, severity: str = 'info',
                 raw_data: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """
        Initialise un événement de sécurité.
        
        Args:
            event_id: Identifiant unique de l'événement
            event_type: Type d'événement (alert, intrusion, anomaly, etc.)
            source_ip: Adresse IP source
            destination_ip: Adresse IP destination
            timestamp: Horodatage de l'événement
            severity: Niveau de sévérité
            raw_data: Données brutes de l'événement
            metadata: Métadonnées enrichies
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.timestamp = timestamp or timezone.now()
        self.severity = severity
        self.raw_data = raw_data or {}
        self.metadata = metadata or {}
        
        # Informations d'enrichissement
        self.ip_reputation = {}
        self.geo_location = {}
        self.docker_validation = {}
        self.correlation_info = {}
    
    def add_enrichment(self, enrichment_type: str, data: Dict[str, Any]):
        """Ajoute des données d'enrichissement à l'événement."""
        if enrichment_type == 'ip_reputation':
            self.ip_reputation.update(data)
        elif enrichment_type == 'geo_location':
            self.geo_location.update(data)
        elif enrichment_type == 'docker_validation':
            self.docker_validation.update(data)
        elif enrichment_type == 'correlation':
            self.correlation_info.update(data)
        else:
            self.metadata[enrichment_type] = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'événement en dictionnaire."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'raw_data': self.raw_data,
            'metadata': self.metadata,
            'ip_reputation': self.ip_reputation,
            'geo_location': self.geo_location,
            'docker_validation': self.docker_validation,
            'correlation_info': self.correlation_info
        }


class SecurityAlert:
    """
    Représente une alerte de sécurité générée par corrélation.
    """
    
    def __init__(self, alert_id: str = None, alert_type: str = None,
                 severity: str = 'medium', title: str = None,
                 description: str = None, source_events: List[SecurityEvent] = None,
                 metadata: Dict[str, Any] = None, remediation_suggestions: List[str] = None):
        """
        Initialise une alerte de sécurité.
        
        Args:
            alert_id: Identifiant unique de l'alerte
            alert_type: Type d'alerte (correlation, anomaly, threat, etc.)
            severity: Niveau de sévérité
            title: Titre de l'alerte
            description: Description détaillée
            source_events: Événements ayant déclenché l'alerte
            metadata: Métadonnées supplémentaires
            remediation_suggestions: Suggestions de remédiation
        """
        self.alert_id = alert_id or str(uuid.uuid4())
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.source_events = source_events or []
        self.metadata = metadata or {}
        self.remediation_suggestions = remediation_suggestions or []
        self.created_at = timezone.now()
        self.status = 'new'
        
        # Informations de corrélation
        self.correlation_score = 0.0
        self.threat_indicators = []
        self.affected_assets = set()
    
    def add_source_event(self, event: SecurityEvent):
        """Ajoute un événement source à l'alerte."""
        self.source_events.append(event)
        
        # Mettre à jour les assets affectés
        if event.source_ip:
            self.affected_assets.add(event.source_ip)
        if event.destination_ip:
            self.affected_assets.add(event.destination_ip)
    
    def calculate_correlation_score(self) -> float:
        """Calcule un score de corrélation basé sur les événements sources."""
        if not self.source_events:
            return 0.0
        
        # Facteurs de corrélation
        time_window_bonus = 0.0
        ip_correlation_bonus = 0.0
        severity_bonus = 0.0
        
        # Bonus pour événements dans une fenêtre temporelle courte
        if len(self.source_events) > 1:
            timestamps = [event.timestamp for event in self.source_events]
            time_span = (max(timestamps) - min(timestamps)).total_seconds()
            if time_span < 300:  # 5 minutes
                time_window_bonus = 0.3
        
        # Bonus pour corrélation d'IPs
        source_ips = {event.source_ip for event in self.source_events if event.source_ip}
        if len(source_ips) == 1 and len(self.source_events) > 1:
            ip_correlation_bonus = 0.2
        
        # Bonus selon la sévérité
        severity_weights = {'critical': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4, 'info': 0.2}
        avg_severity = sum(severity_weights.get(event.severity, 0.5) for event in self.source_events) / len(self.source_events)
        severity_bonus = avg_severity * 0.3
        
        self.correlation_score = min(1.0, time_window_bonus + ip_correlation_bonus + severity_bonus + 0.2)
        return self.correlation_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'alerte en dictionnaire."""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'correlation_score': self.correlation_score,
            'affected_assets': list(self.affected_assets),
            'source_events_count': len(self.source_events),
            'threat_indicators': self.threat_indicators,
            'remediation_suggestions': self.remediation_suggestions,
            'metadata': self.metadata
        }


class EventMiddleware(ABC):
    """
    Interface pour les middlewares de traitement d'événements.
    """
    
    @abstractmethod
    def process(self, event: SecurityEvent) -> SecurityEvent:
        """
        Traite un événement de sécurité.
        
        Args:
            event: Événement à traiter
            
        Returns:
            Événement enrichi
        """
        pass


class DockerIntegrationMiddleware(EventMiddleware):
    """
    Middleware pour enrichir les événements via les services Docker.
    """
    
    def __init__(self):
        """Initialise le middleware avec les connexions Docker."""
        self.services = {
            'suricata': getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068'),
            'fail2ban': getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001'),
            'elasticsearch': getattr(settings, 'ELASTICSEARCH_API_URL', 'http://nms-elasticsearch:9200'),
        }
        self._session = requests.Session()
        self._session.timeout = 10
    
    def process(self, event: SecurityEvent) -> SecurityEvent:
        """Enrichit l'événement avec des données des services Docker."""
        try:
            # Enrichissement Suricata pour les événements IDS
            if event.event_type in ['ids_alert', 'intrusion_attempt']:
                suricata_data = self._get_suricata_context(event)
                if suricata_data:
                    event.add_enrichment('docker_validation', {
                        'suricata_context': suricata_data,
                        'validation_timestamp': timezone.now().isoformat()
                    })
            
            # Enrichissement Fail2Ban pour les événements d'accès
            if event.source_ip and event.event_type in ['failed_login', 'brute_force']:
                fail2ban_data = self._get_fail2ban_status(event.source_ip)
                if fail2ban_data:
                    event.add_enrichment('docker_validation', {
                        'fail2ban_status': fail2ban_data,
                        'ban_recommendation': self._generate_ban_recommendation(fail2ban_data)
                    })
            
            # Enrichissement Elasticsearch pour les événements de log
            if event.raw_data:
                es_context = self._search_elasticsearch_context(event)
                if es_context:
                    event.add_enrichment('docker_validation', {
                        'elasticsearch_context': es_context,
                        'related_events_count': es_context.get('total_hits', 0)
                    })
                    
        except Exception as e:
            logger.warning(f"Erreur dans DockerIntegrationMiddleware: {str(e)}")
            event.add_enrichment('docker_validation', {
                'error': str(e),
                'error_timestamp': timezone.now().isoformat()
            })
        
        return event
    
    def _get_suricata_context(self, event: SecurityEvent) -> Optional[Dict[str, Any]]:
        """Récupère le contexte Suricata pour un événement."""
        try:
            if not event.source_ip:
                return None
                
            response = self._session.get(
                f"{self.services['suricata']}/context",
                params={'source_ip': event.source_ip, 'limit': 10}
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            logger.debug(f"Erreur Suricata context: {str(e)}")
        
        return None
    
    def _get_fail2ban_status(self, ip: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut Fail2Ban pour une IP."""
        try:
            response = self._session.get(
                f"{self.services['fail2ban']}/status/{ip}"
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            logger.debug(f"Erreur Fail2Ban status: {str(e)}")
        
        return None
    
    def _search_elasticsearch_context(self, event: SecurityEvent) -> Optional[Dict[str, Any]]:
        """Recherche le contexte dans Elasticsearch."""
        try:
            query = {
                "query": {
                    "bool": {
                        "should": []
                    }
                },
                "size": 50
            }
            
            # Ajouter des critères de recherche selon les données de l'événement
            if event.source_ip:
                query["query"]["bool"]["should"].append({
                    "term": {"source_ip": event.source_ip}
                })
            
            if event.destination_ip:
                query["query"]["bool"]["should"].append({
                    "term": {"destination_ip": event.destination_ip}
                })
            
            if event.event_type:
                query["query"]["bool"]["should"].append({
                    "term": {"event_type": event.event_type}
                })
            
            # Limiter la recherche aux dernières 24 heures
            query["query"]["bool"]["filter"] = {
                "range": {
                    "@timestamp": {
                        "gte": "now-24h"
                    }
                }
            }
            
            response = self._session.post(
                f"{self.services['elasticsearch']}/_search",
                json=query
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'total_hits': data['hits']['total']['value'],
                    'related_events': [hit['_source'] for hit in data['hits']['hits'][:10]]
                }
                
        except Exception as e:
            logger.debug(f"Erreur Elasticsearch context: {str(e)}")
        
        return None
    
    def _generate_ban_recommendation(self, fail2ban_data: Dict[str, Any]) -> str:
        """Génère une recommandation de bannissement."""
        current_bans = fail2ban_data.get('current_bans', 0)
        failure_count = fail2ban_data.get('failure_count', 0)
        
        if current_bans > 0:
            return "IP déjà bannie dans au moins une prison"
        elif failure_count > 10:
            return "Recommandation: Bannir immédiatement (nombreuses tentatives)"
        elif failure_count > 5:
            return "Recommandation: Surveiller étroitement"
        else:
            return "Activité normale"


class IpReputationMiddleware(EventMiddleware):
    """
    Middleware pour enrichir les événements avec des données de réputation IP.
    """
    
    def __init__(self):
        """Initialise le middleware de réputation IP."""
        self.reputation_cache = {}
        self.cache_timeout = timedelta(hours=4)
        self._reputation_sources = [
            'https://api.abuseipdb.com/api/v2/check',
            # Autres sources de réputation peuvent être ajoutées
        ]
    
    def process(self, event: SecurityEvent) -> SecurityEvent:
        """Enrichit l'événement avec des données de réputation IP."""
        try:
            ips_to_check = []
            if event.source_ip and self._is_public_ip(event.source_ip):
                ips_to_check.append(event.source_ip)
            if event.destination_ip and self._is_public_ip(event.destination_ip):
                ips_to_check.append(event.destination_ip)
            
            for ip in ips_to_check:
                reputation_data = self._get_ip_reputation(ip)
                if reputation_data:
                    event.add_enrichment('ip_reputation', {
                        ip: reputation_data
                    })
                    
                    # Ajouter des indicateurs de menace
                    if reputation_data.get('is_malicious', False):
                        if not hasattr(event, 'threat_indicators'):
                            event.threat_indicators = []
                        event.threat_indicators.append(f"IP malveillante détectée: {ip}")
                        
        except Exception as e:
            logger.warning(f"Erreur dans IpReputationMiddleware: {str(e)}")
        
        return event
    
    def _is_public_ip(self, ip_str: str) -> bool:
        """Vérifie si une IP est publique."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_global
        except ValueError:
            return False
    
    def _get_ip_reputation(self, ip: str) -> Optional[Dict[str, Any]]:
        """Récupère la réputation d'une IP (avec cache)."""
        # Vérifier le cache
        if ip in self.reputation_cache:
            cached_data, cached_time = self.reputation_cache[ip]
            if timezone.now() - cached_time < self.cache_timeout:
                return cached_data
        
        # Simulation de données de réputation (à remplacer par de vraies API)
        reputation_data = {
            'ip': ip,
            'is_malicious': False,
            'confidence': 0.5,
            'categories': [],
            'last_seen': None,
            'sources': []
        }
        
        # Mise en cache
        self.reputation_cache[ip] = (reputation_data, timezone.now())
        
        return reputation_data


class GeoLocationMiddleware(EventMiddleware):
    """
    Middleware pour enrichir les événements avec des données de géolocalisation.
    """
    
    def __init__(self):
        """Initialise le middleware de géolocalisation."""
        self.geo_cache = {}
        self.cache_timeout = timedelta(days=1)
    
    def process(self, event: SecurityEvent) -> SecurityEvent:
        """Enrichit l'événement avec des données de géolocalisation."""
        try:
            ips_to_geolocate = []
            if event.source_ip and self._is_public_ip(event.source_ip):
                ips_to_geolocate.append(event.source_ip)
            if event.destination_ip and self._is_public_ip(event.destination_ip):
                ips_to_geolocate.append(event.destination_ip)
            
            for ip in ips_to_geolocate:
                geo_data = self._get_geo_location(ip)
                if geo_data:
                    event.add_enrichment('geo_location', {
                        ip: geo_data
                    })
                    
        except Exception as e:
            logger.warning(f"Erreur dans GeoLocationMiddleware: {str(e)}")
        
        return event
    
    def _is_public_ip(self, ip_str: str) -> bool:
        """Vérifie si une IP est publique."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_global
        except ValueError:
            return False
    
    def _get_geo_location(self, ip: str) -> Optional[Dict[str, Any]]:
        """Récupère la géolocalisation d'une IP (avec cache)."""
        # Vérifier le cache
        if ip in self.geo_cache:
            cached_data, cached_time = self.geo_cache[ip]
            if timezone.now() - cached_time < self.cache_timeout:
                return cached_data
        
        # Simulation de données de géolocalisation (à remplacer par de vraies API)
        geo_data = {
            'ip': ip,
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'Unknown',
            'city': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'UTC',
            'isp': 'Unknown'
        }
        
        # Mise en cache
        self.geo_cache[ip] = (geo_data, timezone.now())
        
        return geo_data


class SecurityCorrelationEngine:
    """
    Moteur de corrélation sophistiqué pour les événements de sécurité.
    
    Ce moteur traite les événements de sécurité en temps réel, les enrichit
    via des middlewares, applique des règles de corrélation, et génère des
    alertes consolidées avec intégration Docker.
    """
    
    def __init__(self, rule_repository: CorrelationRuleRepository,
                 match_repository: CorrelationRuleMatchRepository,
                 alert_repository: SecurityAlertRepository):
        """
        Initialise le moteur de corrélation.
        
        Args:
            rule_repository: Repository des règles de corrélation
            match_repository: Repository des correspondances de règles
            alert_repository: Repository des alertes de sécurité
        """
        self.rule_repository = rule_repository
        self.match_repository = match_repository
        self.alert_repository = alert_repository
        
        # Configuration du moteur
        self.event_window_minutes = 30
        self.max_events_in_memory = 10000
        self.correlation_threshold = 0.7
        
        # Stockage en mémoire des événements récents
        self.recent_events = deque(maxlen=self.max_events_in_memory)
        self.events_by_ip = defaultdict(list)
        self.events_by_type = defaultdict(list)
        
        # Pipeline de middlewares
        self.middlewares = [
            DockerIntegrationMiddleware(),
            IpReputationMiddleware(),
            GeoLocationMiddleware()
        ]
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistiques
        self.stats = {
            'events_processed': 0,
            'alerts_generated': 0,
            'rules_matched': 0,
            'enrichments_applied': 0
        }
        
        logger.info("SecurityCorrelationEngine initialisé avec %d middlewares", len(self.middlewares))
    
    def process_event(self, event_data: Dict[str, Any]) -> Tuple[SecurityEvent, List[SecurityAlert]]:
        """
        Traite un événement de sécurité complet.
        
        Args:
            event_data: Données brutes de l'événement
            
        Returns:
            Tuple (événement enrichi, alertes générées)
        """
        try:
            with self._lock:
                # Créer l'objet événement
                event = self._create_security_event(event_data)
                
                # Appliquer les middlewares d'enrichissement
                enriched_event = self._apply_middlewares(event)
                
                # Stocker l'événement
                self._store_event(enriched_event)
                
                # Appliquer les règles de corrélation
                alerts = self._apply_correlation_rules(enriched_event)
                
                # Nettoyer les anciens événements
                self._cleanup_old_events()
                
                # Mettre à jour les statistiques
                self.stats['events_processed'] += 1
                self.stats['alerts_generated'] += len(alerts)
                
                return enriched_event, alerts
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement: {str(e)}")
            raise CorrelationEngineException(
                reason=str(e),
                message=f"Erreur lors du traitement: {str(e)}"
            )
    
    def process_batch_events(self, events_data: List[Dict[str, Any]]) -> List[Tuple[SecurityEvent, List[SecurityAlert]]]:
        """
        Traite un lot d'événements de sécurité.
        
        Args:
            events_data: Liste des données d'événements
            
        Returns:
            Liste de tuples (événement enrichi, alertes générées)
        """
        results = []
        
        for event_data in events_data:
            try:
                result = self.process_event(event_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'événement en lot: {str(e)}")
                # Continuer avec les autres événements
                continue
        
        # Corrélations inter-événements pour le lot
        batch_alerts = self._correlate_batch_events([result[0] for result in results])
        
        # Ajouter les alertes de corrélation de lot au dernier résultat
        if results and batch_alerts:
            last_event, last_alerts = results[-1]
            results[-1] = (last_event, last_alerts + batch_alerts)
        
        return results
    
    def _create_security_event(self, event_data: Dict[str, Any]) -> SecurityEvent:
        """Crée un objet SecurityEvent à partir des données brutes."""
        return SecurityEvent(
            event_id=event_data.get('event_id'),
            event_type=event_data.get('event_type'),
            source_ip=event_data.get('source_ip'),
            destination_ip=event_data.get('destination_ip'),
            timestamp=self._parse_timestamp(event_data.get('timestamp')),
            severity=event_data.get('severity', 'info'),
            raw_data=event_data
        )
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse un timestamp depuis une chaîne."""
        if not timestamp_str:
            return timezone.now()
        
        try:
            # Essayer plusieurs formats de timestamp
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # Si aucun format ne marche, retourner l'heure actuelle
            logger.warning(f"Format de timestamp non reconnu: {timestamp_str}")
            return timezone.now()
            
        except Exception:
            return timezone.now()
    
    def _apply_middlewares(self, event: SecurityEvent) -> SecurityEvent:
        """Applique tous les middlewares à l'événement."""
        enriched_event = event
        
        for middleware in self.middlewares:
            try:
                enriched_event = middleware.process(enriched_event)
                self.stats['enrichments_applied'] += 1
            except Exception as e:
                logger.warning(f"Erreur dans middleware {type(middleware).__name__}: {str(e)}")
                continue
        
        return enriched_event
    
    def _store_event(self, event: SecurityEvent):
        """Stocke l'événement en mémoire pour corrélation."""
        self.recent_events.append(event)
        
        # Indexer par IP source
        if event.source_ip:
            self.events_by_ip[event.source_ip].append(event)
            # Limiter la taille des listes par IP
            if len(self.events_by_ip[event.source_ip]) > 100:
                self.events_by_ip[event.source_ip] = self.events_by_ip[event.source_ip][-100:]
        
        # Indexer par type d'événement
        if event.event_type:
            self.events_by_type[event.event_type].append(event)
            # Limiter la taille des listes par type
            if len(self.events_by_type[event.event_type]) > 200:
                self.events_by_type[event.event_type] = self.events_by_type[event.event_type][-200:]
    
    def _apply_correlation_rules(self, event: SecurityEvent) -> List[SecurityAlert]:
        """Applique les règles de corrélation à un événement."""
        alerts = []
        
        try:
            active_rules = self.rule_repository.find_active_rules()
            
            for rule in active_rules:
                if self._event_matches_rule(event, rule):
                    # Rechercher les événements corrélés
                    correlated_events = self._find_correlated_events(event, rule)
                    
                    if len(correlated_events) >= rule.min_events:
                        # Créer une alerte
                        alert = self._create_correlation_alert(rule, correlated_events)
                        alerts.append(alert)
                        
                        # Sauvegarder la correspondance
                        match = CorrelationRuleMatch(
                            correlation_rule_id=rule.id,
                            matched_at=timezone.now(),
                            triggering_events=[event.to_dict()]
                        )
                        self.match_repository.save(match)
                        self.rule_repository.increment_trigger_count(rule.id)
                        self.stats['rules_matched'] += 1
            
            # Règles de corrélation prédéfinies
            predefined_alerts = self._apply_predefined_correlations(event)
            alerts.extend(predefined_alerts)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des règles de corrélation: {str(e)}")
        
        return alerts
    
    def _event_matches_rule(self, event: SecurityEvent, rule: CorrelationRule) -> bool:
        """Vérifie si un événement correspond à une règle de corrélation."""
        try:
            for condition in rule.conditions:
                field = condition.get("field")
                operator = condition.get("operator")
                value = condition.get("value")
                
                if not field or not operator or value is None:
                    continue
                
                # Obtenir la valeur de l'événement
                event_value = self._get_event_field_value(event, field)
                
                if event_value is None:
                    return False
                
                # Appliquer l'opérateur
                if not self._apply_condition_operator(event_value, operator, value):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'évaluation de la règle {rule.id}: {str(e)}")
            return False
    
    def _get_event_field_value(self, event: SecurityEvent, field: str) -> Any:
        """Récupère la valeur d'un champ d'événement."""
        # Champs directs
        if hasattr(event, field):
            return getattr(event, field)
        
        # Champs dans raw_data
        if field in event.raw_data:
            return event.raw_data[field]
        
        # Champs dans metadata
        if field in event.metadata:
            return event.metadata[field]
        
        # Champs imbriqués (ex: "ip_reputation.confidence")
        if '.' in field:
            parts = field.split('.')
            value = event
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        
        return None
    
    def _apply_condition_operator(self, event_value: Any, operator: str, condition_value: Any) -> bool:
        """Applique un opérateur de condition."""
        try:
            if operator == "equals":
                return event_value == condition_value
            elif operator == "not_equals":
                return event_value != condition_value
            elif operator == "contains":
                return str(condition_value).lower() in str(event_value).lower()
            elif operator == "not_contains":
                return str(condition_value).lower() not in str(event_value).lower()
            elif operator == "greater_than":
                return float(event_value) > float(condition_value)
            elif operator == "less_than":
                return float(event_value) < float(condition_value)
            elif operator == "regex":
                return bool(re.search(str(condition_value), str(event_value)))
            elif operator == "in":
                return event_value in condition_value
            elif operator == "not_in":
                return event_value not in condition_value
            else:
                logger.warning(f"Opérateur de condition non reconnu: {operator}")
                return False
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'application de l'opérateur {operator}: {str(e)}")
            return False
    
    def _find_correlated_events(self, event: SecurityEvent, rule: CorrelationRule) -> List[SecurityEvent]:
        """Trouve les événements corrélés selon une règle."""
        correlated_events = [event]
        time_threshold = timezone.now() - timedelta(minutes=rule.time_window_minutes)
        
        # Chercher dans les événements récents
        for stored_event in self.recent_events:
            if stored_event == event:
                continue
            
            if stored_event.timestamp < time_threshold:
                continue
            
            if self._events_are_correlated(event, stored_event, rule):
                correlated_events.append(stored_event)
        
        return correlated_events
    
    def _events_are_correlated(self, event1: SecurityEvent, event2: SecurityEvent, rule: CorrelationRule) -> bool:
        """Vérifie si deux événements sont corrélés selon une règle."""
        # Vérifier la corrélation temporelle
        time_diff = abs((event1.timestamp - event2.timestamp).total_seconds() / 60)
        if time_diff > rule.time_window_minutes:
            return False
        
        # Vérifier la corrélation par IP
        if rule.correlation_fields and "source_ip" in rule.correlation_fields:
            if event1.source_ip and event2.source_ip and event1.source_ip == event2.source_ip:
                return True
        
        # Vérifier la corrélation par type d'événement
        if rule.correlation_fields and "event_type" in rule.correlation_fields:
            if event1.event_type and event2.event_type and event1.event_type == event2.event_type:
                return True
        
        # Autres critères de corrélation personnalisés peuvent être ajoutés
        
        return False
    
    def _create_correlation_alert(self, rule: CorrelationRule, events: List[SecurityEvent]) -> SecurityAlert:
        """Crée une alerte de corrélation."""
        alert = SecurityAlert(
            alert_type='correlation',
            severity=rule.severity,
            title=f"Corrélation détectée: {rule.name}",
            description=f"Règle de corrélation '{rule.name}' déclenchée par {len(events)} événements",
            source_events=events
        )
        
        # Calculer le score de corrélation
        alert.calculate_correlation_score()
        
        # Ajouter des métadonnées
        alert.metadata.update({
            'correlation_rule_id': rule.id,
            'correlation_rule_name': rule.name,
            'events_count': len(events),
            'time_window_minutes': rule.time_window_minutes
        })
        
        # Générer des suggestions de remédiation
        alert.remediation_suggestions = self._generate_remediation_suggestions(rule, events)
        
        return alert
    
    def _generate_remediation_suggestions(self, rule: CorrelationRule, events: List[SecurityEvent]) -> List[str]:
        """Génère des suggestions de remédiation pour une alerte."""
        suggestions = []
        
        # Suggestions basées sur le type de règle
        if 'brute_force' in rule.name.lower():
            suggestions.extend([
                "Vérifier les tentatives de connexion multiples",
                "Considérer le bannissement temporaire de l'IP source",
                "Renforcer la politique de mots de passe"
            ])
        
        if 'malware' in rule.name.lower():
            suggestions.extend([
                "Isoler les systèmes affectés",
                "Effectuer une analyse antivirus complète",
                "Vérifier les connexions réseau suspectes"
            ])
        
        if 'anomaly' in rule.name.lower():
            suggestions.extend([
                "Analyser les modèles de trafic",
                "Vérifier les performances système",
                "Examiner les logs détaillés"
            ])
        
        # Suggestions basées sur les IPs impliquées
        source_ips = {event.source_ip for event in events if event.source_ip}
        if source_ips:
            suggestions.append(f"Examiner l'activité des IPs: {', '.join(list(source_ips)[:5])}")
        
        return suggestions
    
    def _apply_predefined_correlations(self, event: SecurityEvent) -> List[SecurityAlert]:
        """Applique des règles de corrélation prédéfinies."""
        alerts = []
        
        try:
            # Détection de brute force
            if event.event_type in ['failed_login', 'authentication_failure']:
                brute_force_alert = self._detect_brute_force(event)
                if brute_force_alert:
                    alerts.append(brute_force_alert)
            
            # Détection d'escalade de privilèges
            if event.event_type in ['privilege_escalation', 'admin_access']:
                escalation_alert = self._detect_privilege_escalation(event)
                if escalation_alert:
                    alerts.append(escalation_alert)
            
            # Détection d'anomalies de trafic
            if event.event_type in ['network_connection', 'data_transfer']:
                traffic_alert = self._detect_traffic_anomaly(event)
                if traffic_alert:
                    alerts.append(traffic_alert)
            
        except Exception as e:
            logger.warning(f"Erreur dans les corrélations prédéfinies: {str(e)}")
        
        return alerts
    
    def _detect_brute_force(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Détecte les attaques par force brute."""
        if not event.source_ip:
            return None
        
        # Compter les tentatives récentes depuis cette IP
        recent_failures = []
        threshold_time = timezone.now() - timedelta(minutes=15)
        
        for stored_event in self.events_by_ip.get(event.source_ip, []):
            if (stored_event.timestamp > threshold_time and 
                stored_event.event_type in ['failed_login', 'authentication_failure']):
                recent_failures.append(stored_event)
        
        # Seuil pour détection de brute force
        if len(recent_failures) >= 10:
            alert = SecurityAlert(
                alert_type='brute_force',
                severity='high',
                title=f"Attaque par force brute détectée depuis {event.source_ip}",
                description=f"{len(recent_failures)} tentatives de connexion échouées en 15 minutes",
                source_events=recent_failures
            )
            
            alert.metadata.update({
                'attack_type': 'brute_force',
                'source_ip': event.source_ip,
                'failure_count': len(recent_failures),
                'time_window_minutes': 15
            })
            
            alert.remediation_suggestions = [
                f"Bannir temporairement l'IP {event.source_ip}",
                "Vérifier les logs d'authentification",
                "Renforcer les politiques de sécurité"
            ]
            
            return alert
        
        return None
    
    def _detect_privilege_escalation(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Détecte les tentatives d'escalade de privilèges."""
        if not event.source_ip:
            return None
        
        # Chercher des patterns d'escalade récents
        recent_events = []
        threshold_time = timezone.now() - timedelta(minutes=30)
        
        for stored_event in self.events_by_ip.get(event.source_ip, []):
            if (stored_event.timestamp > threshold_time and 
                stored_event.event_type in ['privilege_escalation', 'admin_access', 'sudo_command']):
                recent_events.append(stored_event)
        
        # Détecter des patterns suspects
        if len(recent_events) >= 3:
            alert = SecurityAlert(
                alert_type='privilege_escalation',
                severity='critical',
                title=f"Tentative d'escalade de privilèges depuis {event.source_ip}",
                description=f"Multiples tentatives d'accès privilégié détectées",
                source_events=recent_events
            )
            
            alert.metadata.update({
                'attack_type': 'privilege_escalation',
                'source_ip': event.source_ip,
                'escalation_attempts': len(recent_events)
            })
            
            alert.remediation_suggestions = [
                "Examiner immédiatement les logs d'audit",
                "Vérifier les permissions utilisateur",
                "Considérer la suspension du compte"
            ]
            
            return alert
        
        return None
    
    def _detect_traffic_anomaly(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Détecte les anomalies de trafic réseau."""
        # Analyser le volume de trafic récent
        recent_connections = []
        threshold_time = timezone.now() - timedelta(minutes=10)
        
        connection_events = self.events_by_type.get('network_connection', [])
        for stored_event in connection_events:
            if stored_event.timestamp > threshold_time:
                recent_connections.append(stored_event)
        
        # Détection d'anomalies de volume
        if len(recent_connections) > 1000:  # Seuil configurable
            alert = SecurityAlert(
                alert_type='traffic_anomaly',
                severity='warning',
                title="Anomalie de trafic réseau détectée",
                description=f"Volume de connexions anormalement élevé: {len(recent_connections)} en 10 minutes",
                source_events=recent_connections[-20:]  # Garder seulement les 20 derniers
            )
            
            alert.metadata.update({
                'anomaly_type': 'high_volume',
                'connection_count': len(recent_connections),
                'time_window_minutes': 10
            })
            
            alert.remediation_suggestions = [
                "Analyser les patterns de trafic",
                "Vérifier la santé des services",
                "Examiner les logs de pare-feu"
            ]
            
            return alert
        
        return None
    
    def _correlate_batch_events(self, events: List[SecurityEvent]) -> List[SecurityAlert]:
        """Effectue des corrélations entre événements d'un même lot."""
        alerts = []
        
        try:
            # Grouper par IP source
            events_by_ip = defaultdict(list)
            for event in events:
                if event.source_ip:
                    events_by_ip[event.source_ip].append(event)
            
            # Détecter des patterns dans chaque groupe d'IP
            for ip, ip_events in events_by_ip.items():
                if len(ip_events) >= 5:  # Seuil pour corrélation de lot
                    alert = SecurityAlert(
                        alert_type='batch_correlation',
                        severity='medium',
                        title=f"Activité corrélée détectée pour {ip}",
                        description=f"Multiples événements corrélés dans le lot pour l'IP {ip}",
                        source_events=ip_events
                    )
                    
                    alert.metadata.update({
                        'correlation_type': 'batch_ip_correlation',
                        'source_ip': ip,
                        'events_count': len(ip_events)
                    })
                    
                    alerts.append(alert)
            
        except Exception as e:
            logger.warning(f"Erreur dans la corrélation de lot: {str(e)}")
        
        return alerts
    
    def _cleanup_old_events(self):
        """Nettoie les anciens événements de la mémoire."""
        cutoff_time = timezone.now() - timedelta(hours=2)
        
        # Nettoyer les événements par IP
        for ip, events in list(self.events_by_ip.items()):
            self.events_by_ip[ip] = [e for e in events if e.timestamp > cutoff_time]
            if not self.events_by_ip[ip]:
                del self.events_by_ip[ip]
        
        # Nettoyer les événements par type
        for event_type, events in list(self.events_by_type.items()):
            self.events_by_type[event_type] = [e for e in events if e.timestamp > cutoff_time]
            if not self.events_by_type[event_type]:
                del self.events_by_type[event_type]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur de corrélation."""
        return {
            **self.stats,
            'events_in_memory': len(self.recent_events),
            'ips_tracked': len(self.events_by_ip),
            'event_types_tracked': len(self.events_by_type),
            'middlewares_count': len(self.middlewares)
        }
    
    def reset_statistics(self):
        """Remet à zéro les statistiques."""
        self.stats = {
            'events_processed': 0,
            'alerts_generated': 0,
            'rules_matched': 0,
            'enrichments_applied': 0
        }


class AnomalyDetectionService:
    """
    Service avancé de détection d'anomalies avec analyse statistique et intégration Docker.
    """
    
    def __init__(self):
        """Initialise le service de détection d'anomalies."""
        self.baseline_window_hours = 24
        self.anomaly_threshold_std = 2.0  # Écarts-types pour détecter une anomalie
        self.min_samples = 30  # Minimum d'échantillons pour calculer des statistiques
        
        # Cache pour les baselines calculées
        self.baseline_cache = {}
        self.cache_timeout = timedelta(hours=1)
        
        # Configuration Docker
        self.elasticsearch_url = getattr(settings, 'ELASTICSEARCH_API_URL', 'http://nms-elasticsearch:9200')
        self._session = requests.Session()
        self._session.timeout = 30
        
        logger.info("AnomalyDetectionService initialisé")
    
    def detect_anomalies(self, baseline: TrafficBaseline, current_metrics: Dict[str, Any]) -> List[TrafficAnomaly]:
        """
        Détecte des anomalies en comparant les métriques actuelles à une ligne de base.
        
        Args:
            baseline: Ligne de base du trafic
            current_metrics: Métriques actuelles à analyser
            
        Returns:
            Liste des anomalies détectées
        """
        anomalies = []
        
        if baseline.is_learning:
            return anomalies
        
        try:
            # Détecter les anomalies pour chaque métrique
            for metric_name, current_value in current_metrics.items():
                anomaly = self._detect_metric_anomaly(baseline, metric_name, current_value)
                if anomaly:
                    anomalies.append(anomaly)
            
            # Détecter les anomalies composites
            composite_anomalies = self._detect_composite_anomalies(baseline, current_metrics)
            anomalies.extend(composite_anomalies)
            
            # Enrichir avec des données Docker si disponible
            enriched_anomalies = self._enrich_anomalies_with_docker(anomalies)
            
            return enriched_anomalies
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {str(e)}")
            return anomalies
    
    def _detect_metric_anomaly(self, baseline: TrafficBaseline, metric_name: str, current_value: float) -> Optional[TrafficAnomaly]:
        """Détecte une anomalie pour une métrique spécifique."""
        try:
            # Récupérer les statistiques de la baseline
            baseline_stats = self._get_baseline_statistics(baseline, metric_name)
            if not baseline_stats:
                return None
            
            mean = baseline_stats['mean']
            std_dev = baseline_stats['std_dev']
            
            # Calculer la déviation en écarts-types
            if std_dev == 0:
                deviation_std = 0
            else:
                deviation_std = abs(current_value - mean) / std_dev
            
            # Vérifier si c'est une anomalie
            if deviation_std > self.anomaly_threshold_std:
                deviation_percent = ((current_value - mean) / mean) * 100 if mean != 0 else 0
                
                anomaly = TrafficAnomaly(
                    baseline_id=baseline.id,
                    anomaly_type=self._classify_anomaly_type(metric_name, current_value, mean),
                    severity=self._determine_anomaly_severity(deviation_std),
                    current_value=current_value,
                    baseline_value=mean,
                    deviation_percent=abs(deviation_percent),
                    timestamp=timezone.now()
                )
                
                # Ajouter des métadonnées
                anomaly.metadata = {
                    'metric_name': metric_name,
                    'std_deviation': deviation_std,
                    'baseline_std_dev': std_dev,
                    'classification': self._classify_anomaly_type(metric_name, current_value, mean)
                }
                
                return anomaly
            
        except Exception as e:
            logger.warning(f"Erreur lors de la détection d'anomalie pour {metric_name}: {str(e)}")
        
        return None
    
    def _get_baseline_statistics(self, baseline: TrafficBaseline, metric_name: str) -> Optional[Dict[str, float]]:
        """Récupère les statistiques d'une baseline pour une métrique."""
        try:
            # Vérifier le cache
            cache_key = f"{baseline.id}_{metric_name}"
            if cache_key in self.baseline_cache:
                cached_stats, cached_time = self.baseline_cache[cache_key]
                if timezone.now() - cached_time < self.cache_timeout:
                    return cached_stats
            
            # Calculer les statistiques depuis les données historiques
            historical_data = self._fetch_historical_data(baseline, metric_name)
            if len(historical_data) < self.min_samples:
                return None
            
            stats = {
                'mean': statistics.mean(historical_data),
                'std_dev': statistics.stdev(historical_data) if len(historical_data) > 1 else 0,
                'median': statistics.median(historical_data),
                'min': min(historical_data),
                'max': max(historical_data),
                'count': len(historical_data)
            }
            
            # Mettre en cache
            self.baseline_cache[cache_key] = (stats, timezone.now())
            
            return stats
            
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des statistiques de baseline: {str(e)}")
            return None
    
    def _fetch_historical_data(self, baseline: TrafficBaseline, metric_name: str) -> List[float]:
        """Récupère les données historiques depuis Elasticsearch."""
        try:
            # Construire la requête Elasticsearch
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": f"now-{self.baseline_window_hours}h"
                                    }
                                }
                            },
                            {
                                "exists": {
                                    "field": metric_name
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "metric_values": {
                        "terms": {
                            "field": metric_name,
                            "size": 1000
                        }
                    }
                },
                "size": 0
            }
            
            response = self._session.post(
                f"{self.elasticsearch_url}/_search",
                json=query
            )
            
            if response.status_code == 200:
                data = response.json()
                buckets = data.get('aggregations', {}).get('metric_values', {}).get('buckets', [])
                
                # Extraire les valeurs
                values = []
                for bucket in buckets:
                    try:
                        value = float(bucket['key'])
                        count = bucket['doc_count']
                        # Ajouter la valeur autant de fois qu'elle apparaît
                        values.extend([value] * count)
                    except (ValueError, KeyError):
                        continue
                
                return values
            
        except Exception as e:
            logger.debug(f"Erreur lors de la récupération des données historiques: {str(e)}")
        
        # Fallback: utiliser des données simulées basées sur la baseline
        return self._generate_fallback_data(baseline, metric_name)
    
    def _generate_fallback_data(self, baseline: TrafficBaseline, metric_name: str) -> List[float]:
        """Génère des données de fallback basées sur la baseline."""
        import random
        
        base_value = 0
        if metric_name == 'requests_per_minute' and baseline.avg_requests_per_minute:
            base_value = baseline.avg_requests_per_minute
        elif metric_name == 'bytes_per_second' and baseline.avg_bytes_per_second:
            base_value = baseline.avg_bytes_per_second
        elif metric_name == 'connections_per_minute' and hasattr(baseline, 'avg_connections_per_minute'):
            base_value = getattr(baseline, 'avg_connections_per_minute', 0)
        
        if base_value == 0:
            base_value = 100  # Valeur par défaut
        
        # Générer des données avec variabilité normale
        data = []
        for _ in range(self.min_samples * 2):
            variation = random.normalvariate(0, base_value * 0.1)  # 10% de variabilité
            value = max(0, base_value + variation)
            data.append(value)
        
        return data
    
    def _classify_anomaly_type(self, metric_name: str, current_value: float, baseline_value: float) -> str:
        """Classifie le type d'anomalie selon la métrique et les valeurs."""
        if current_value > baseline_value:
            if 'requests' in metric_name or 'connections' in metric_name:
                return 'high_volume'
            elif 'bytes' in metric_name or 'bandwidth' in metric_name:
                return 'high_bandwidth'
            elif 'latency' in metric_name or 'response_time' in metric_name:
                return 'high_latency'
            else:
                return 'spike'
        else:
            if 'requests' in metric_name or 'connections' in metric_name:
                return 'low_volume'
            elif 'bytes' in metric_name or 'bandwidth' in metric_name:
                return 'low_bandwidth'
            else:
                return 'drop'
    
    def _determine_anomaly_severity(self, deviation_std: float) -> SeverityLevel:
        """Détermine la sévérité d'une anomalie selon la déviation."""
        if deviation_std > 5.0:
            return SeverityLevel.CRITICAL
        elif deviation_std > 4.0:
            return SeverityLevel.HIGH
        elif deviation_std > 3.0:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _detect_composite_anomalies(self, baseline: TrafficBaseline, current_metrics: Dict[str, Any]) -> List[TrafficAnomaly]:
        """Détecte des anomalies composites impliquant plusieurs métriques."""
        anomalies = []
        
        try:
            # Détecter l'anomalie "pic de trafic avec haute latence"
            requests_current = current_metrics.get('requests_per_minute', 0)
            latency_current = current_metrics.get('avg_response_time', 0)
            
            if (requests_current > (baseline.avg_requests_per_minute or 0) * 1.5 and
                latency_current > 1000):  # Plus de 1 seconde de latence
                
                anomaly = TrafficAnomaly(
                    baseline_id=baseline.id,
                    anomaly_type='composite_performance_degradation',
                    severity=SeverityLevel.HIGH,
                    current_value=requests_current,
                    baseline_value=baseline.avg_requests_per_minute or 0,
                    deviation_percent=((requests_current - (baseline.avg_requests_per_minute or 0)) / max(baseline.avg_requests_per_minute or 1, 1)) * 100,
                    timestamp=timezone.now()
                )
                
                anomaly.metadata = {
                    'composite_type': 'high_traffic_high_latency',
                    'latency_ms': latency_current,
                    'requests_per_minute': requests_current
                }
                
                anomalies.append(anomaly)
            
            # Détecter l'anomalie "faible trafic avec haute consommation"
            bytes_current = current_metrics.get('bytes_per_second', 0)
            if (requests_current < (baseline.avg_requests_per_minute or 0) * 0.5 and
                bytes_current > (baseline.avg_bytes_per_second or 0) * 2):
                
                anomaly = TrafficAnomaly(
                    baseline_id=baseline.id,
                    anomaly_type='composite_inefficient_usage',
                    severity=SeverityLevel.MEDIUM,
                    current_value=bytes_current,
                    baseline_value=baseline.avg_bytes_per_second or 0,
                    deviation_percent=((bytes_current - (baseline.avg_bytes_per_second or 0)) / max(baseline.avg_bytes_per_second or 1, 1)) * 100,
                    timestamp=timezone.now()
                )
                
                anomaly.metadata = {
                    'composite_type': 'low_requests_high_bandwidth',
                    'requests_per_minute': requests_current,
                    'bytes_per_second': bytes_current
                }
                
                anomalies.append(anomaly)
            
        except Exception as e:
            logger.warning(f"Erreur lors de la détection d'anomalies composites: {str(e)}")
        
        return anomalies
    
    def _enrich_anomalies_with_docker(self, anomalies: List[TrafficAnomaly]) -> List[TrafficAnomaly]:
        """Enrichit les anomalies avec des informations des services Docker."""
        try:
            for anomaly in anomalies:
                # Obtenir des métriques supplémentaires d'Elasticsearch
                additional_context = self._get_anomaly_context_from_elasticsearch(anomaly)
                if additional_context:
                    if not hasattr(anomaly, 'docker_context'):
                        anomaly.docker_context = {}
                    anomaly.docker_context.update(additional_context)
                
                # Ajouter des recommandations spécifiques selon le type d'anomalie
                anomaly.recommendations = self._generate_anomaly_recommendations(anomaly)
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'enrichissement des anomalies: {str(e)}")
        
        return anomalies
    
    def _get_anomaly_context_from_elasticsearch(self, anomaly: TrafficAnomaly) -> Optional[Dict[str, Any]]:
        """Récupère le contexte d'une anomalie depuis Elasticsearch."""
        try:
            # Rechercher des événements corrélés dans une fenêtre de temps
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": (anomaly.timestamp - timedelta(minutes=10)).isoformat(),
                            "lte": (anomaly.timestamp + timedelta(minutes=10)).isoformat()
                        }
                    }
                },
                "aggs": {
                    "event_types": {
                        "terms": {
                            "field": "event_type.keyword",
                            "size": 10
                        }
                    },
                    "source_ips": {
                        "terms": {
                            "field": "source_ip.keyword",
                            "size": 10
                        }
                    }
                },
                "size": 20
            }
            
            response = self._session.post(
                f"{self.elasticsearch_url}/_search",
                json=query
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'correlated_events_count': data['hits']['total']['value'],
                    'top_event_types': [bucket['key'] for bucket in data.get('aggregations', {}).get('event_types', {}).get('buckets', [])],
                    'top_source_ips': [bucket['key'] for bucket in data.get('aggregations', {}).get('source_ips', {}).get('buckets', [])],
                    'sample_events': [hit['_source'] for hit in data['hits']['hits']]
                }
                
        except Exception as e:
            logger.debug(f"Erreur lors de la récupération du contexte d'anomalie: {str(e)}")
        
        return None
    
    def _generate_anomaly_recommendations(self, anomaly: TrafficAnomaly) -> List[str]:
        """Génère des recommandations pour une anomalie."""
        recommendations = []
        
        anomaly_type = anomaly.anomaly_type
        severity = anomaly.severity
        
        # Recommandations par type d'anomalie
        if anomaly_type == 'high_volume':
            recommendations.extend([
                "Vérifier la capacité des serveurs",
                "Analyser les sources du trafic supplémentaire",
                "Considérer l'activation de la limitation de débit"
            ])
            
        elif anomaly_type == 'high_bandwidth':
            recommendations.extend([
                "Examiner les transferts de données volumineux",
                "Vérifier les connexions de streaming",
                "Analyser l'utilisation de la bande passante par service"
            ])
            
        elif anomaly_type == 'high_latency':
            recommendations.extend([
                "Vérifier les performances des services backend",
                "Analyser les requêtes lentes",
                "Examiner la charge des bases de données"
            ])
            
        elif anomaly_type == 'low_volume':
            recommendations.extend([
                "Vérifier la disponibilité des services",
                "Examiner les logs d'erreurs",
                "Confirmer que les clients peuvent accéder aux services"
            ])
            
        elif 'composite' in anomaly_type:
            recommendations.extend([
                "Effectuer une analyse de corrélation complète",
                "Examiner les relations entre les métriques",
                "Considérer une optimisation globale des performances"
            ])
        
        # Recommandations par sévérité
        if severity == SeverityLevel.CRITICAL:
            recommendations.insert(0, "ACTION IMMÉDIATE REQUISE")
            recommendations.append("Notifier l'équipe d'astreinte")
            
        elif severity == SeverityLevel.HIGH:
            recommendations.insert(0, "Intervention rapide recommandée")
            
        return recommendations
    
    def calculate_anomaly_score(self, anomalies: List[TrafficAnomaly]) -> float:
        """Calcule un score global d'anomalie."""
        if not anomalies:
            return 0.0
        
        severity_weights = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4
        }
        
        total_score = 0.0
        for anomaly in anomalies:
            weight = severity_weights.get(anomaly.severity, 0.4)
            deviation_factor = min(anomaly.deviation_percent / 100, 2.0)  # Cap à 200%
            total_score += weight * deviation_factor
        
        # Normaliser le score entre 0 et 1
        return min(total_score / len(anomalies), 1.0)


class RuleConflictDetector:
    """
    Détecteur de conflits entre règles de sécurité.
    
    Cette classe analyse les règles de sécurité pour détecter des conflits
    potentiels qui pourraient causer des problèmes de performance ou de sécurité.
    """
    
    def __init__(self):
        """Initialise le détecteur de conflits."""
        self.conflict_types = {
            'shadow': 'Règle masquée par une autre règle',
            'redundant': 'Règle redondante',
            'contradiction': 'Règles contradictoires',
            'performance': 'Impact sur les performances'
        }
    
    def detect_conflicts(self, rule, existing_rules):
        """
        Détecte les conflits entre une règle et des règles existantes.
        
        Args:
            rule: Règle à vérifier
            existing_rules: Liste des règles existantes
            
        Returns:
            Liste des conflits détectés
        """
        conflicts = []
        
        for existing_rule in existing_rules:
            if existing_rule.id == rule.id:
                continue
            
            # Détecter les conflits de shadow
            if self._is_shadow_conflict(rule, existing_rule):
                conflicts.append({
                    'type': 'shadow',
                    'rule_id': existing_rule.id,
                    'description': f"La règle '{rule.name}' est masquée par '{existing_rule.name}'"
                })
            
            # Détecter les règles redondantes
            if self._is_redundant(rule, existing_rule):
                conflicts.append({
                    'type': 'redundant',
                    'rule_id': existing_rule.id,
                    'description': f"La règle '{rule.name}' est redondante avec '{existing_rule.name}'"
                })
            
            # Détecter les contradictions
            if self._is_contradiction(rule, existing_rule):
                conflicts.append({
                    'type': 'contradiction',
                    'rule_id': existing_rule.id,
                    'description': f"La règle '{rule.name}' contredit '{existing_rule.name}'"
                })
        
        return conflicts
    
    def _is_shadow_conflict(self, rule1, rule2):
        """Vérifie si une règle en masque une autre."""
        # Logique simplifiée de détection de shadow
        if (rule1.source_ip == rule2.source_ip and 
            rule1.destination_ip == rule2.destination_ip and
            rule1.priority < rule2.priority):
            return True
        return False
    
    def _is_redundant(self, rule1, rule2):
        """Vérifie si les règles sont redondantes."""
        return (rule1.source_ip == rule2.source_ip and
                rule1.destination_ip == rule2.destination_ip and
                rule1.action == rule2.action)
    
    def _is_contradiction(self, rule1, rule2):
        """Vérifie si les règles sont contradictoires."""
        return (rule1.source_ip == rule2.source_ip and
                rule1.destination_ip == rule2.destination_ip and
                rule1.action != rule2.action)


# Fonctions utilitaires pour maintenir la compatibilité

def rule_validator_factory(rule_type: RuleType):
    """Fonction utilitaire pour obtenir une stratégie de validation (compatibilité)."""
    from .strategies import rule_validator
    return rule_validator