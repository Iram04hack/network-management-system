"""
Module d'analyse d'impact sophistiqué pour les règles de sécurité.

Ce module contient les implémentations pour analyser l'impact des règles de sécurité
sur les performances, la sécurité, et les opérations, avec intégration Docker pour
obtenir des métriques en temps réel et des analyses prédictives.
"""

import logging
import statistics
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import requests

from django.conf import settings
from django.utils import timezone

from .interfaces import (
    ImpactAnalyzer, RuleMetricsCalculator, RecommendationGenerator,
    ImpactMetric, ImpactAnalysisResult
)
from .entities import SecurityRule, RuleType, SeverityLevel

logger = logging.getLogger(__name__)


class ImpactCategory(Enum):
    """Catégories d'impact pour l'analyse."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    COST = "cost"


class ImpactSeverity(Enum):
    """Niveaux de sévérité d'impact."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Métriques de performance pour l'analyse d'impact."""
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    network_latency_ms: float = 0.0
    throughput_mbps: float = 0.0
    packet_loss_percent: float = 0.0
    connection_count: int = 0
    rule_processing_time_us: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convertit les métriques en dictionnaire."""
        return {
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_mb': self.memory_usage_mb,
            'network_latency_ms': self.network_latency_ms,
            'throughput_mbps': self.throughput_mbps,
            'packet_loss_percent': self.packet_loss_percent,
            'connection_count': float(self.connection_count),
            'rule_processing_time_us': self.rule_processing_time_us
        }


@dataclass
class SecurityMetrics:
    """Métriques de sécurité pour l'analyse d'impact."""
    blocked_attacks: int = 0
    false_positives: int = 0
    detection_accuracy: float = 0.0
    coverage_score: float = 0.0
    threat_level_reduction: float = 0.0
    compliance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convertit les métriques en dictionnaire."""
        return {
            'blocked_attacks': float(self.blocked_attacks),
            'false_positives': float(self.false_positives),
            'detection_accuracy': self.detection_accuracy,
            'coverage_score': self.coverage_score,
            'threat_level_reduction': self.threat_level_reduction,
            'compliance_score': self.compliance_score
        }


@dataclass
class OperationalMetrics:
    """Métriques opérationnelles pour l'analyse d'impact."""
    maintenance_overhead: float = 0.0
    alert_volume: int = 0
    investigation_time_hours: float = 0.0
    automation_level: float = 0.0
    skill_requirement: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convertit les métriques en dictionnaire."""
        return {
            'maintenance_overhead': self.maintenance_overhead,
            'alert_volume': float(self.alert_volume),
            'investigation_time_hours': self.investigation_time_hours,
            'automation_level': self.automation_level,
            'skill_requirement': self.skill_requirement
        }


class DockerMetricsCollector:
    """
    Collecteur de métriques depuis les services Docker pour l'analyse d'impact.
    """
    
    def __init__(self):
        """Initialise le collecteur avec les services Docker."""
        self.services = {
            'suricata': getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068'),
            'fail2ban': getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001'),
            'traffic_control': getattr(settings, 'TRAFFIC_CONTROL_API_URL', 'http://nms-traffic-control:8003'),
            'elasticsearch': getattr(settings, 'ELASTICSEARCH_API_URL', 'http://nms-elasticsearch:9200'),
            'prometheus': getattr(settings, 'PROMETHEUS_API_URL', 'http://nms-prometheus:9090'),
        }
        
        self._session = requests.Session()
        self._session.timeout = 10
        
        # Cache pour éviter les appels répétés
        self._metrics_cache = {}
        self._cache_timeout = timedelta(minutes=2)
        
        logger.info("DockerMetricsCollector initialisé")
    
    def collect_performance_metrics(self, rule_type: str) -> PerformanceMetrics:
        """
        Collecte les métriques de performance depuis les services Docker.
        
        Args:
            rule_type: Type de règle pour cibler le bon service
            
        Returns:
            Métriques de performance collectées
        """
        try:
            cache_key = f"performance_{rule_type}"
            if self._is_cached(cache_key):
                return self._metrics_cache[cache_key][0]
            
            metrics = PerformanceMetrics()
            
            # Collecter depuis Prometheus si disponible
            prometheus_metrics = self._collect_from_prometheus(rule_type)
            if prometheus_metrics:
                metrics.cpu_usage_percent = prometheus_metrics.get('cpu_usage', 0.0)
                metrics.memory_usage_mb = prometheus_metrics.get('memory_usage_mb', 0.0)
                metrics.network_latency_ms = prometheus_metrics.get('network_latency_ms', 0.0)
                metrics.throughput_mbps = prometheus_metrics.get('throughput_mbps', 0.0)
            
            # Collecter depuis le service spécifique
            if rule_type.lower() == 'ids' or rule_type.lower() == 'suricata':
                suricata_metrics = self._collect_from_suricata()
                if suricata_metrics:
                    metrics.packet_loss_percent = suricata_metrics.get('packet_loss', 0.0)
                    metrics.rule_processing_time_us = suricata_metrics.get('processing_time_us', 0.0)
                    metrics.connection_count = suricata_metrics.get('active_connections', 0)
            
            elif rule_type.lower() == 'firewall':
                traffic_metrics = self._collect_from_traffic_control()
                if traffic_metrics:
                    metrics.connection_count = traffic_metrics.get('active_connections', 0)
                    metrics.rule_processing_time_us = traffic_metrics.get('rule_processing_time', 0.0)
            
            # Mettre en cache
            self._cache_metrics(cache_key, metrics)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Erreur lors de la collecte des métriques de performance: {str(e)}")
            return PerformanceMetrics()
    
    def collect_security_metrics(self, rule_type: str) -> SecurityMetrics:
        """
        Collecte les métriques de sécurité depuis les services Docker.
        
        Args:
            rule_type: Type de règle pour cibler le bon service
            
        Returns:
            Métriques de sécurité collectées
        """
        try:
            cache_key = f"security_{rule_type}"
            if self._is_cached(cache_key):
                return self._metrics_cache[cache_key][0]
            
            metrics = SecurityMetrics()
            
            # Collecter depuis Elasticsearch pour les alertes
            es_metrics = self._collect_from_elasticsearch(rule_type)
            if es_metrics:
                metrics.blocked_attacks = es_metrics.get('blocked_attacks', 0)
                metrics.false_positives = es_metrics.get('false_positives', 0)
                metrics.detection_accuracy = es_metrics.get('detection_accuracy', 0.0)
            
            # Collecter depuis le service spécifique
            if rule_type.lower() == 'ids' or rule_type.lower() == 'suricata':
                suricata_metrics = self._collect_from_suricata()
                if suricata_metrics:
                    metrics.coverage_score = suricata_metrics.get('coverage_score', 0.0)
                    metrics.threat_level_reduction = suricata_metrics.get('threat_reduction', 0.0)
            
            elif rule_type.lower() == 'fail2ban':
                fail2ban_metrics = self._collect_from_fail2ban()
                if fail2ban_metrics:
                    metrics.blocked_attacks = fail2ban_metrics.get('blocked_ips', 0)
                    metrics.detection_accuracy = fail2ban_metrics.get('accuracy', 0.0)
            
            # Calculer le score de compliance (simulé)
            metrics.compliance_score = self._calculate_compliance_score(rule_type, metrics)
            
            # Mettre en cache
            self._cache_metrics(cache_key, metrics)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Erreur lors de la collecte des métriques de sécurité: {str(e)}")
            return SecurityMetrics()
    
    def collect_operational_metrics(self, rule_type: str) -> OperationalMetrics:
        """
        Collecte les métriques opérationnelles depuis les services Docker.
        
        Args:
            rule_type: Type de règle pour cibler le bon service
            
        Returns:
            Métriques opérationnelles collectées
        """
        try:
            cache_key = f"operational_{rule_type}"
            if self._is_cached(cache_key):
                return self._metrics_cache[cache_key][0]
            
            metrics = OperationalMetrics()
            
            # Collecter depuis Elasticsearch pour les alertes
            es_metrics = self._collect_from_elasticsearch(rule_type)
            if es_metrics:
                metrics.alert_volume = es_metrics.get('alert_count_24h', 0)
                metrics.investigation_time_hours = es_metrics.get('avg_investigation_time', 0.0)
            
            # Calculer des métriques basées sur le type de règle
            metrics.maintenance_overhead = self._calculate_maintenance_overhead(rule_type)
            metrics.automation_level = self._calculate_automation_level(rule_type)
            metrics.skill_requirement = self._calculate_skill_requirement(rule_type)
            
            # Mettre en cache
            self._cache_metrics(cache_key, metrics)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Erreur lors de la collecte des métriques opérationnelles: {str(e)}")
            return OperationalMetrics()
    
    def _collect_from_prometheus(self, rule_type: str) -> Optional[Dict[str, Any]]:
        """Collecte les métriques depuis Prometheus."""
        try:
            # Requêtes Prometheus pour différentes métriques
            queries = {
                'cpu_usage': f'rate(container_cpu_usage_seconds_total{{name=~".*{rule_type}.*"}}[5m]) * 100',
                'memory_usage_mb': f'container_memory_usage_bytes{{name=~".*{rule_type}.*"}} / 1024 / 1024',
                'network_latency_ms': f'rate(container_network_receive_packets_total{{name=~".*{rule_type}.*"}}[5m])',
                'throughput_mbps': f'rate(container_network_transmit_bytes_total{{name=~".*{rule_type}.*"}}[5m]) * 8 / 1000000'
            }
            
            metrics = {}
            
            for metric_name, query in queries.items():
                response = self._session.get(
                    f"{self.services['prometheus']}/api/v1/query",
                    params={'query': query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success' and data.get('data', {}).get('result'):
                        # Prendre la première valeur disponible
                        result = data['data']['result'][0]
                        value = float(result['value'][1])
                        metrics[metric_name] = value
            
            return metrics if metrics else None
            
        except Exception as e:
            logger.debug(f"Erreur lors de la collecte Prometheus: {str(e)}")
            return None
    
    def _collect_from_suricata(self) -> Optional[Dict[str, Any]]:
        """Collecte les métriques depuis Suricata."""
        try:
            response = self._session.get(f"{self.services['suricata']}/stats")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'packet_loss': data.get('capture', {}).get('kernel_drops', 0) / max(data.get('capture', {}).get('kernel_packets', 1), 1) * 100,
                    'processing_time_us': data.get('decode', {}).get('avg_pkt_size', 0),
                    'active_connections': data.get('flow', {}).get('tcp', 0),
                    'coverage_score': min(data.get('rules', {}).get('loaded', 0) / 1000 * 100, 100),
                    'threat_reduction': data.get('detect', {}).get('alert', 0) / max(data.get('decoder', {}).get('pkts', 1), 1) * 100
                }
                
        except Exception as e:
            logger.debug(f"Erreur lors de la collecte Suricata: {str(e)}")
            return None
    
    def _collect_from_fail2ban(self) -> Optional[Dict[str, Any]]:
        """Collecte les métriques depuis Fail2Ban."""
        try:
            response = self._session.get(f"{self.services['fail2ban']}/stats")
            
            if response.status_code == 200:
                data = response.json()
                total_banned = sum(jail.get('currently_banned', 0) for jail in data.get('jails', []))
                total_failed = sum(jail.get('total_failed', 0) for jail in data.get('jails', []))
                
                return {
                    'blocked_ips': total_banned,
                    'accuracy': max(0, (total_failed - total_banned) / max(total_failed, 1)) * 100 if total_failed > 0 else 0
                }
                
        except Exception as e:
            logger.debug(f"Erreur lors de la collecte Fail2Ban: {str(e)}")
            return None
    
    def _collect_from_traffic_control(self) -> Optional[Dict[str, Any]]:
        """Collecte les métriques depuis Traffic Control."""
        try:
            response = self._session.get(f"{self.services['traffic_control']}/stats")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active_connections': data.get('connections', {}).get('active', 0),
                    'rule_processing_time': data.get('firewall', {}).get('avg_processing_time_us', 0)
                }
                
        except Exception as e:
            logger.debug(f"Erreur lors de la collecte Traffic Control: {str(e)}")
            return None
    
    def _collect_from_elasticsearch(self, rule_type: str) -> Optional[Dict[str, Any]]:
        """Collecte les métriques depuis Elasticsearch."""
        try:
            # Requête pour les alertes des dernières 24h
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now-24h"
                                    }
                                }
                            },
                            {
                                "term": {
                                    "rule_type.keyword": rule_type
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "alert_types": {
                        "terms": {
                            "field": "alert_type.keyword",
                            "size": 10
                        }
                    },
                    "severity_levels": {
                        "terms": {
                            "field": "severity.keyword",
                            "size": 5
                        }
                    }
                },
                "size": 0
            }
            
            response = self._session.post(
                f"{self.services['elasticsearch']}/_search",
                json=query
            )
            
            if response.status_code == 200:
                data = response.json()
                total_alerts = data['hits']['total']['value']
                
                # Estimer les faux positifs (simplifié)
                false_positives = 0
                for bucket in data.get('aggregations', {}).get('alert_types', {}).get('buckets', []):
                    if 'false' in bucket['key'].lower() or 'noise' in bucket['key'].lower():
                        false_positives += bucket['doc_count']
                
                return {
                    'alert_count_24h': total_alerts,
                    'blocked_attacks': total_alerts - false_positives,
                    'false_positives': false_positives,
                    'detection_accuracy': (total_alerts - false_positives) / max(total_alerts, 1) * 100,
                    'avg_investigation_time': 0.5  # Temps moyen simulé en heures
                }
                
        except Exception as e:
            logger.debug(f"Erreur lors de la collecte Elasticsearch: {str(e)}")
            return None
    
    def _calculate_compliance_score(self, rule_type: str, security_metrics: SecurityMetrics) -> float:
        """Calcule un score de compliance basé sur les métriques."""
        base_score = 70.0  # Score de base
        
        # Bonus pour la détection
        if security_metrics.detection_accuracy > 90:
            base_score += 20
        elif security_metrics.detection_accuracy > 80:
            base_score += 10
        
        # Bonus pour la couverture
        if security_metrics.coverage_score > 80:
            base_score += 10
        
        return min(base_score, 100.0)
    
    def _calculate_maintenance_overhead(self, rule_type: str) -> float:
        """Calcule l'overhead de maintenance pour un type de règle."""
        # Basé sur la complexité historique des types de règles
        overhead_map = {
            'firewall': 2.0,  # Heures par semaine
            'ids': 4.0,
            'suricata': 4.0,
            'fail2ban': 1.5,
            'access_control': 3.0
        }
        
        return overhead_map.get(rule_type.lower(), 3.0)
    
    def _calculate_automation_level(self, rule_type: str) -> float:
        """Calcule le niveau d'automatisation pour un type de règle."""
        # Pourcentage d'automatisation
        automation_map = {
            'firewall': 85.0,
            'ids': 70.0,
            'suricata': 70.0,
            'fail2ban': 90.0,
            'access_control': 60.0
        }
        
        return automation_map.get(rule_type.lower(), 75.0)
    
    def _calculate_skill_requirement(self, rule_type: str) -> float:
        """Calcule le niveau de compétence requis (1-10)."""
        skill_map = {
            'firewall': 6.0,
            'ids': 8.0,
            'suricata': 8.0,
            'fail2ban': 5.0,
            'access_control': 7.0
        }
        
        return skill_map.get(rule_type.lower(), 6.5)
    
    def _is_cached(self, cache_key: str) -> bool:
        """Vérifie si une métrique est en cache et encore valide."""
        if cache_key not in self._metrics_cache:
            return False
        
        _, timestamp = self._metrics_cache[cache_key]
        return timezone.now() - timestamp < self._cache_timeout
    
    def _cache_metrics(self, cache_key: str, metrics: Any):
        """Met en cache une métrique."""
        self._metrics_cache[cache_key] = (metrics, timezone.now())


class AdvancedRuleMetricsCalculator(RuleMetricsCalculator):
    """
    Calculateur avancé de métriques pour les règles de sécurité.
    """
    
    def __init__(self):
        """Initialise le calculateur avec le collecteur de métriques Docker."""
        self.metrics_collector = DockerMetricsCollector()
        self._calculation_cache = {}
        self._cache_timeout = timedelta(minutes=5)
    
    def calculate_metrics(self, rule_data: Dict[str, Any]) -> List[ImpactMetric]:
        """
        Calcule les métriques d'impact pour une règle.
        
        Args:
            rule_data: Données de la règle
            
        Returns:
            Liste des métriques calculées
        """
        try:
            rule_type = rule_data.get('rule_type', 'unknown')
            rule_content = rule_data.get('content', '')
            rule_id = rule_data.get('id', 'unknown')
            
            # Vérifier le cache
            cache_key = f"metrics_{rule_type}_{hash(rule_content)}"
            if self._is_calculation_cached(cache_key):
                return self._calculation_cache[cache_key][0]
            
            metrics = []
            
            # Collecter les métriques depuis Docker
            performance_metrics = self.metrics_collector.collect_performance_metrics(rule_type)
            security_metrics = self.metrics_collector.collect_security_metrics(rule_type)
            operational_metrics = self.metrics_collector.collect_operational_metrics(rule_type)
            
            # Calculer les métriques de performance
            perf_metrics = self._calculate_performance_metrics(rule_data, performance_metrics)
            metrics.extend(perf_metrics)
            
            # Calculer les métriques de sécurité
            sec_metrics = self._calculate_security_metrics(rule_data, security_metrics)
            metrics.extend(sec_metrics)
            
            # Calculer les métriques opérationnelles
            ops_metrics = self._calculate_operational_metrics(rule_data, operational_metrics)
            metrics.extend(ops_metrics)
            
            # Calculer les métriques de coût
            cost_metrics = self._calculate_cost_metrics(rule_data, performance_metrics, operational_metrics)
            metrics.extend(cost_metrics)
            
            # Calculer les métriques de compliance
            compliance_metrics = self._calculate_compliance_metrics(rule_data, security_metrics)
            metrics.extend(compliance_metrics)
            
            # Mettre en cache
            self._cache_calculation(cache_key, metrics)
            
            logger.info(f"Calculé {len(metrics)} métriques pour la règle {rule_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques: {str(e)}")
            return []
    
    def _calculate_performance_metrics(self, rule_data: Dict[str, Any], 
                                     performance_metrics: PerformanceMetrics) -> List[ImpactMetric]:
        """Calcule les métriques de performance."""
        metrics = []
        
        # Impact CPU
        cpu_impact = min(performance_metrics.cpu_usage_percent / 100, 1.0)
        metrics.append(ImpactMetric(
            name="cpu_impact",
            value=cpu_impact,
            description=f"Impact sur l'utilisation CPU: {performance_metrics.cpu_usage_percent:.1f}%",
            category=ImpactCategory.PERFORMANCE.value
        ))
        
        # Impact mémoire
        memory_impact = min(performance_metrics.memory_usage_mb / 1000, 1.0)  # Normalize to GB
        metrics.append(ImpactMetric(
            name="memory_impact",
            value=memory_impact,
            description=f"Impact sur la mémoire: {performance_metrics.memory_usage_mb:.1f} MB",
            category=ImpactCategory.PERFORMANCE.value
        ))
        
        # Impact latence réseau
        latency_impact = min(performance_metrics.network_latency_ms / 100, 1.0)  # Normalize to 100ms
        metrics.append(ImpactMetric(
            name="latency_impact",
            value=latency_impact,
            description=f"Impact sur la latence réseau: {performance_metrics.network_latency_ms:.1f} ms",
            category=ImpactCategory.PERFORMANCE.value
        ))
        
        # Impact throughput
        throughput_impact = 1.0 - min(performance_metrics.throughput_mbps / 1000, 1.0)  # Invert: lower = worse
        metrics.append(ImpactMetric(
            name="throughput_impact",
            value=throughput_impact,
            description=f"Impact sur le débit: {performance_metrics.throughput_mbps:.1f} Mbps",
            category=ImpactCategory.PERFORMANCE.value
        ))
        
        # Complexité de la règle (basée sur le contenu)
        rule_complexity = self._calculate_rule_complexity(rule_data.get('content', ''))
        metrics.append(ImpactMetric(
            name="rule_complexity",
            value=rule_complexity,
            description=f"Complexité de la règle: {rule_complexity:.2f}",
            category=ImpactCategory.PERFORMANCE.value
        ))
        
        return metrics
    
    def _calculate_security_metrics(self, rule_data: Dict[str, Any], 
                                   security_metrics: SecurityMetrics) -> List[ImpactMetric]:
        """Calcule les métriques de sécurité."""
        metrics = []
        
        # Efficacité de détection
        detection_effectiveness = security_metrics.detection_accuracy / 100
        metrics.append(ImpactMetric(
            name="detection_effectiveness",
            value=1.0 - detection_effectiveness,  # Invert: higher accuracy = lower impact
            description=f"Efficacité de détection: {security_metrics.detection_accuracy:.1f}%",
            category=ImpactCategory.SECURITY.value
        ))
        
        # Taux de faux positifs
        false_positive_rate = security_metrics.false_positives / max(security_metrics.blocked_attacks + security_metrics.false_positives, 1)
        metrics.append(ImpactMetric(
            name="false_positive_rate",
            value=false_positive_rate,
            description=f"Taux de faux positifs: {false_positive_rate:.2%}",
            category=ImpactCategory.SECURITY.value
        ))
        
        # Couverture de sécurité
        security_coverage = security_metrics.coverage_score / 100
        metrics.append(ImpactMetric(
            name="security_coverage",
            value=1.0 - security_coverage,  # Invert: higher coverage = lower impact
            description=f"Couverture de sécurité: {security_metrics.coverage_score:.1f}%",
            category=ImpactCategory.SECURITY.value
        ))
        
        # Réduction du niveau de menace
        threat_reduction = security_metrics.threat_level_reduction / 100
        metrics.append(ImpactMetric(
            name="threat_reduction",
            value=1.0 - threat_reduction,  # Invert: higher reduction = lower impact
            description=f"Réduction des menaces: {security_metrics.threat_level_reduction:.1f}%",
            category=ImpactCategory.SECURITY.value
        ))
        
        return metrics
    
    def _calculate_operational_metrics(self, rule_data: Dict[str, Any], 
                                     operational_metrics: OperationalMetrics) -> List[ImpactMetric]:
        """Calcule les métriques opérationnelles."""
        metrics = []
        
        # Overhead de maintenance
        maintenance_impact = min(operational_metrics.maintenance_overhead / 10, 1.0)  # Normalize to 10h/week
        metrics.append(ImpactMetric(
            name="maintenance_overhead",
            value=maintenance_impact,
            description=f"Overhead de maintenance: {operational_metrics.maintenance_overhead:.1f}h/semaine",
            category=ImpactCategory.OPERATIONAL.value
        ))
        
        # Volume d'alertes
        alert_volume_impact = min(operational_metrics.alert_volume / 1000, 1.0)  # Normalize to 1000 alerts/day
        metrics.append(ImpactMetric(
            name="alert_volume",
            value=alert_volume_impact,
            description=f"Volume d'alertes: {operational_metrics.alert_volume}/jour",
            category=ImpactCategory.OPERATIONAL.value
        ))
        
        # Temps d'investigation
        investigation_impact = min(operational_metrics.investigation_time_hours / 8, 1.0)  # Normalize to 8h
        metrics.append(ImpactMetric(
            name="investigation_time",
            value=investigation_impact,
            description=f"Temps d'investigation: {operational_metrics.investigation_time_hours:.1f}h",
            category=ImpactCategory.OPERATIONAL.value
        ))
        
        # Niveau d'automatisation
        automation_impact = 1.0 - (operational_metrics.automation_level / 100)  # Invert: higher automation = lower impact
        metrics.append(ImpactMetric(
            name="automation_level",
            value=automation_impact,
            description=f"Niveau d'automatisation: {operational_metrics.automation_level:.1f}%",
            category=ImpactCategory.OPERATIONAL.value
        ))
        
        # Exigence de compétences
        skill_impact = operational_metrics.skill_requirement / 10  # Normalize to 1-10 scale
        metrics.append(ImpactMetric(
            name="skill_requirement",
            value=skill_impact,
            description=f"Niveau de compétence requis: {operational_metrics.skill_requirement:.1f}/10",
            category=ImpactCategory.OPERATIONAL.value
        ))
        
        return metrics
    
    def _calculate_cost_metrics(self, rule_data: Dict[str, Any], 
                               performance_metrics: PerformanceMetrics,
                               operational_metrics: OperationalMetrics) -> List[ImpactMetric]:
        """Calcule les métriques de coût."""
        metrics = []
        
        # Coût en ressources (CPU + mémoire)
        resource_cost = (performance_metrics.cpu_usage_percent / 100 + 
                        performance_metrics.memory_usage_mb / 1000) / 2
        metrics.append(ImpactMetric(
            name="resource_cost",
            value=min(resource_cost, 1.0),
            description=f"Coût en ressources: {resource_cost:.3f}",
            category=ImpactCategory.COST.value
        ))
        
        # Coût opérationnel (maintenance + investigation)
        operational_cost = (operational_metrics.maintenance_overhead + 
                          operational_metrics.investigation_time_hours) / 20  # Normalize to 20h total
        metrics.append(ImpactMetric(
            name="operational_cost",
            value=min(operational_cost, 1.0),
            description=f"Coût opérationnel: {operational_cost:.3f}",
            category=ImpactCategory.COST.value
        ))
        
        # Coût de formation (basé sur l'exigence de compétences)
        training_cost = operational_metrics.skill_requirement / 10
        metrics.append(ImpactMetric(
            name="training_cost",
            value=training_cost,
            description=f"Coût de formation: {training_cost:.2f}",
            category=ImpactCategory.COST.value
        ))
        
        return metrics
    
    def _calculate_compliance_metrics(self, rule_data: Dict[str, Any], 
                                    security_metrics: SecurityMetrics) -> List[ImpactMetric]:
        """Calcule les métriques de compliance."""
        metrics = []
        
        # Score de compliance
        compliance_impact = 1.0 - (security_metrics.compliance_score / 100)  # Invert: higher compliance = lower impact
        metrics.append(ImpactMetric(
            name="compliance_score",
            value=compliance_impact,
            description=f"Score de compliance: {security_metrics.compliance_score:.1f}%",
            category=ImpactCategory.COMPLIANCE.value
        ))
        
        # Conformité réglementaire (simulée basée sur le type de règle)
        regulatory_compliance = self._calculate_regulatory_compliance(rule_data)
        metrics.append(ImpactMetric(
            name="regulatory_compliance",
            value=1.0 - regulatory_compliance,  # Invert: higher compliance = lower impact
            description=f"Conformité réglementaire: {regulatory_compliance:.2f}",
            category=ImpactCategory.COMPLIANCE.value
        ))
        
        return metrics
    
    def _calculate_rule_complexity(self, rule_content: str) -> float:
        """Calcule la complexité d'une règle basée sur son contenu."""
        if not rule_content:
            return 0.0
        
        complexity_factors = [
            len(rule_content) / 1000,  # Longueur de la règle
            rule_content.count('(') * 0.1,  # Nombre de groupes/conditions
            rule_content.count('|') * 0.05,  # Nombre d'alternatives
            rule_content.count('*') * 0.02,  # Wildcards
            rule_content.count('+') * 0.02,  # Répétitions
        ]
        
        return min(sum(complexity_factors), 1.0)
    
    def _calculate_regulatory_compliance(self, rule_data: Dict[str, Any]) -> float:
        """Calcule la conformité réglementaire simulée."""
        rule_type = rule_data.get('rule_type', '').lower()
        
        # Scores basés sur des standards comme NIST, ISO 27001, etc.
        compliance_scores = {
            'firewall': 0.85,
            'ids': 0.90,
            'suricata': 0.90,
            'fail2ban': 0.75,
            'access_control': 0.80
        }
        
        return compliance_scores.get(rule_type, 0.70)
    
    def _is_calculation_cached(self, cache_key: str) -> bool:
        """Vérifie si un calcul est en cache et encore valide."""
        if cache_key not in self._calculation_cache:
            return False
        
        _, timestamp = self._calculation_cache[cache_key]
        return timezone.now() - timestamp < self._cache_timeout
    
    def _cache_calculation(self, cache_key: str, metrics: List[ImpactMetric]):
        """Met en cache un calcul de métriques."""
        self._calculation_cache[cache_key] = (metrics, timezone.now())


class IntelligentRecommendationGenerator(RecommendationGenerator):
    """
    Générateur intelligent de recommandations basé sur l'analyse d'impact.
    """
    
    def __init__(self):
        """Initialise le générateur de recommandations."""
        self.recommendation_templates = self._load_recommendation_templates()
    
    def generate_recommendation(self, metrics: List[ImpactMetric], is_acceptable: bool, 
                              rule_data: Dict[str, Any]) -> str:
        """
        Génère une recommandation basée sur les métriques d'impact.
        
        Args:
            metrics: Liste des métriques d'impact
            is_acceptable: Indique si l'impact global est acceptable
            rule_data: Données de la règle
            
        Returns:
            Recommandation sous forme de texte
        """
        try:
            # Analyser les métriques par catégorie
            metrics_by_category = self._group_metrics_by_category(metrics)
            
            # Identifier les domaines problématiques
            problem_areas = self._identify_problem_areas(metrics_by_category)
            
            # Générer la recommandation principale
            if is_acceptable:
                recommendation = self._generate_positive_recommendation(metrics_by_category, rule_data)
            else:
                recommendation = self._generate_improvement_recommendation(problem_areas, rule_data)
            
            # Ajouter des recommandations spécifiques
            specific_recommendations = self._generate_specific_recommendations(metrics_by_category, rule_data)
            
            if specific_recommendations:
                recommendation += "\n\nRecommandations spécifiques:\n" + "\n".join(f"• {rec}" for rec in specific_recommendations)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de recommandations: {str(e)}")
            return "Impossible de générer des recommandations à ce moment. Veuillez réessayer."
    
    def _group_metrics_by_category(self, metrics: List[ImpactMetric]) -> Dict[str, List[ImpactMetric]]:
        """Groupe les métriques par catégorie."""
        grouped = defaultdict(list)
        for metric in metrics:
            grouped[metric.category].append(metric)
        return dict(grouped)
    
    def _identify_problem_areas(self, metrics_by_category: Dict[str, List[ImpactMetric]]) -> List[str]:
        """Identifie les domaines problématiques."""
        problem_areas = []
        
        for category, category_metrics in metrics_by_category.items():
            avg_impact = sum(metric.value for metric in category_metrics) / len(category_metrics)
            
            if avg_impact > 0.7:
                problem_areas.append(category)
        
        return problem_areas
    
    def _generate_positive_recommendation(self, metrics_by_category: Dict[str, List[ImpactMetric]], 
                                        rule_data: Dict[str, Any]) -> str:
        """Génère une recommandation positive."""
        rule_name = rule_data.get('name', 'la règle')
        
        recommendations = [
            f"✅ {rule_name} présente un impact acceptable sur le système.",
            "La règle peut être déployée en production avec confiance."
        ]
        
        # Identifier les points forts
        strong_points = []
        for category, category_metrics in metrics_by_category.items():
            avg_impact = sum(metric.value for metric in category_metrics) / len(category_metrics)
            
            if avg_impact < 0.3:
                strong_points.append(f"Excellent impact {category.lower()}")
        
        if strong_points:
            recommendations.append(f"Points forts: {', '.join(strong_points)}.")
        
        return " ".join(recommendations)
    
    def _generate_improvement_recommendation(self, problem_areas: List[str], 
                                           rule_data: Dict[str, Any]) -> str:
        """Génère une recommandation d'amélioration."""
        rule_name = rule_data.get('name', 'la règle')
        
        if not problem_areas:
            return f"⚠️ {rule_name} nécessite des optimisations mineures avant le déploiement."
        
        recommendations = [
            f"⚠️ {rule_name} présente un impact élevé dans les domaines suivants: {', '.join(problem_areas)}.",
            "Des optimisations sont recommandées avant le déploiement en production."
        ]
        
        return " ".join(recommendations)
    
    def _generate_specific_recommendations(self, metrics_by_category: Dict[str, List[ImpactMetric]], 
                                         rule_data: Dict[str, Any]) -> List[str]:
        """Génère des recommandations spécifiques par domaine."""
        recommendations = []
        
        # Recommandations de performance
        if ImpactCategory.PERFORMANCE.value in metrics_by_category:
            perf_recommendations = self._generate_performance_recommendations(
                metrics_by_category[ImpactCategory.PERFORMANCE.value], rule_data
            )
            recommendations.extend(perf_recommendations)
        
        # Recommandations de sécurité
        if ImpactCategory.SECURITY.value in metrics_by_category:
            sec_recommendations = self._generate_security_recommendations(
                metrics_by_category[ImpactCategory.SECURITY.value], rule_data
            )
            recommendations.extend(sec_recommendations)
        
        # Recommandations opérationnelles
        if ImpactCategory.OPERATIONAL.value in metrics_by_category:
            ops_recommendations = self._generate_operational_recommendations(
                metrics_by_category[ImpactCategory.OPERATIONAL.value], rule_data
            )
            recommendations.extend(ops_recommendations)
        
        # Recommandations de coût
        if ImpactCategory.COST.value in metrics_by_category:
            cost_recommendations = self._generate_cost_recommendations(
                metrics_by_category[ImpactCategory.COST.value], rule_data
            )
            recommendations.extend(cost_recommendations)
        
        return recommendations
    
    def _generate_performance_recommendations(self, metrics: List[ImpactMetric], 
                                            rule_data: Dict[str, Any]) -> List[str]:
        """Génère des recommandations de performance."""
        recommendations = []
        
        for metric in metrics:
            if metric.value > 0.7:
                if metric.name == "cpu_impact":
                    recommendations.append("Optimiser la règle pour réduire l'utilisation CPU")
                elif metric.name == "memory_impact":
                    recommendations.append("Réduire l'empreinte mémoire de la règle")
                elif metric.name == "latency_impact":
                    recommendations.append("Simplifier la règle pour améliorer la latence")
                elif metric.name == "rule_complexity":
                    recommendations.append("Diviser la règle complexe en plusieurs règles plus simples")
        
        return recommendations
    
    def _generate_security_recommendations(self, metrics: List[ImpactMetric], 
                                         rule_data: Dict[str, Any]) -> List[str]:
        """Génère des recommandations de sécurité."""
        recommendations = []
        
        for metric in metrics:
            if metric.value > 0.5:
                if metric.name == "false_positive_rate":
                    recommendations.append("Affiner la règle pour réduire les faux positifs")
                elif metric.name == "detection_effectiveness":
                    recommendations.append("Améliorer la précision de détection de la règle")
                elif metric.name == "security_coverage":
                    recommendations.append("Étendre la couverture de sécurité de la règle")
        
        return recommendations
    
    def _generate_operational_recommendations(self, metrics: List[ImpactMetric], 
                                            rule_data: Dict[str, Any]) -> List[str]:
        """Génère des recommandations opérationnelles."""
        recommendations = []
        
        for metric in metrics:
            if metric.value > 0.6:
                if metric.name == "maintenance_overhead":
                    recommendations.append("Automatiser la maintenance de cette règle")
                elif metric.name == "alert_volume":
                    recommendations.append("Ajuster les seuils pour réduire le volume d'alertes")
                elif metric.name == "investigation_time":
                    recommendations.append("Créer des playbooks pour accélérer les investigations")
                elif metric.name == "skill_requirement":
                    recommendations.append("Prévoir une formation pour l'équipe sur cette règle")
        
        return recommendations
    
    def _generate_cost_recommendations(self, metrics: List[ImpactMetric], 
                                     rule_data: Dict[str, Any]) -> List[str]:
        """Génère des recommandations de coût."""
        recommendations = []
        
        for metric in metrics:
            if metric.value > 0.6:
                if metric.name == "resource_cost":
                    recommendations.append("Optimiser l'utilisation des ressources")
                elif metric.name == "operational_cost":
                    recommendations.append("Réduire les coûts opérationnels par l'automatisation")
                elif metric.name == "training_cost":
                    recommendations.append("Simplifier la règle pour réduire les besoins de formation")
        
        return recommendations
    
    def _load_recommendation_templates(self) -> Dict[str, str]:
        """Charge les templates de recommandations."""
        return {
            "high_performance_impact": "Cette règle a un impact élevé sur les performances. Considérez l'optimisation.",
            "high_security_risk": "Cette règle présente des risques de sécurité. Révision recommandée.",
            "high_operational_overhead": "Cette règle nécessite un overhead opérationnel important.",
            "acceptable_impact": "Cette règle présente un impact acceptable et peut être déployée.",
            "optimization_needed": "Des optimisations sont nécessaires avant le déploiement."
        }


class ComprehensiveImpactAnalyzer(ImpactAnalyzer):
    """
    Analyseur d'impact complet intégrant tous les composants.
    """
    
    def __init__(self):
        """Initialise l'analyseur d'impact complet."""
        self.metrics_calculator = AdvancedRuleMetricsCalculator()
        self.recommendation_generator = IntelligentRecommendationGenerator()
        
        # Configuration des seuils d'acceptabilité
        self.acceptability_thresholds = {
            ImpactCategory.PERFORMANCE.value: 0.7,
            ImpactCategory.SECURITY.value: 0.5,
            ImpactCategory.OPERATIONAL.value: 0.8,
            ImpactCategory.COST.value: 0.6,
            ImpactCategory.COMPLIANCE.value: 0.3
        }
        
        # Poids par catégorie pour le calcul global
        self.category_weights = {
            ImpactCategory.PERFORMANCE.value: 0.25,
            ImpactCategory.SECURITY.value: 0.35,
            ImpactCategory.OPERATIONAL.value: 0.20,
            ImpactCategory.COST.value: 0.15,
            ImpactCategory.COMPLIANCE.value: 0.05
        }
        
        logger.info("ComprehensiveImpactAnalyzer initialisé")
    
    def analyze_impact(self, rule_data: Dict[str, Any]) -> ImpactAnalysisResult:
        """
        Analyse l'impact complet d'une règle de sécurité.
        
        Args:
            rule_data: Données de la règle à analyser
            
        Returns:
            Résultat de l'analyse d'impact
        """
        try:
            rule_id = rule_data.get('id', 'unknown')
            rule_type = rule_data.get('rule_type', 'unknown')
            
            logger.info(f"Début de l'analyse d'impact pour la règle {rule_id}")
            
            # Calculer toutes les métriques
            metrics = self.metrics_calculator.calculate_metrics(rule_data)
            
            # Analyser l'acceptabilité
            is_acceptable = self._evaluate_acceptability(metrics)
            
            # Générer les recommandations
            recommendation = self.recommendation_generator.generate_recommendation(
                metrics, is_acceptable, rule_data
            )
            
            # Créer le résultat
            result = ImpactAnalysisResult(
                rule_id=rule_id,
                rule_type=rule_type,
                metrics=metrics,
                is_acceptable=is_acceptable,
                recommendation=recommendation
            )
            
            logger.info(f"Analyse d'impact terminée pour la règle {rule_id}: {len(metrics)} métriques, acceptable={is_acceptable}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'impact: {str(e)}")
            
            # Retourner un résultat d'erreur
            return ImpactAnalysisResult(
                rule_id=rule_data.get('id', 'unknown'),
                rule_type=rule_data.get('rule_type', 'unknown'),
                metrics=[],
                is_acceptable=False,
                recommendation=f"Erreur lors de l'analyse d'impact: {str(e)}"
            )
    
    def _evaluate_acceptability(self, metrics: List[ImpactMetric]) -> bool:
        """Évalue si l'impact global est acceptable."""
        if not metrics:
            return False
        
        # Grouper par catégorie
        metrics_by_category = defaultdict(list)
        for metric in metrics:
            metrics_by_category[metric.category].append(metric)
        
        # Calculer le score pondéré par catégorie
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for category, category_metrics in metrics_by_category.items():
            if not category_metrics:
                continue
            
            # Moyenne des métriques dans cette catégorie
            avg_impact = sum(metric.value for metric in category_metrics) / len(category_metrics)
            
            # Appliquer le poids de la catégorie
            weight = self.category_weights.get(category, 0.1)
            total_weighted_score += avg_impact * weight
            total_weight += weight
        
        if total_weight == 0:
            return False
        
        # Score global
        global_impact_score = total_weighted_score / total_weight
        
        # Acceptable si le score global est en dessous de 0.6
        return global_impact_score < 0.6


# Instance globale de l'analyseur d'impact
impact_analyzer = ComprehensiveImpactAnalyzer()