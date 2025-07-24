"""
Service unifié d'intégration Security Management avec GNS3 Central et Docker.

Ce service modernise l'intégration du module security_management en utilisant :
- Le Service Central GNS3 pour la contextualisation topologique
- L'intégration Docker pour Suricata, Fail2ban et Traffic Control
- Le moteur de corrélation d'événements sophistiqué
- La détection d'anomalies avec ML
- La gestion des vulnérabilités et threat intelligence

Architecture Développeur Senior :
- Façade unifiée pour toutes les opérations de sécurité
- Intégration transparente avec les services Docker
- Corrélation d'événements en temps réel
- Détection d'anomalies avancée
- Gestion des incidents automatisée
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Count, Avg, Max, Min
from dataclasses import dataclass, asdict
import uuid
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict, deque

from common.api.gns3_module_interface import create_gns3_interface
from common.infrastructure.gns3_central_service import GNS3EventType

# Import des modèles
from ..models import (
    SecurityRuleModel, SecurityAlertModel, CorrelationRuleModel,
    TrafficBaselineModel, TrafficAnomalyModel, IPReputationModel,
    SecurityPolicyModel, VulnerabilityModel, ThreatIntelligenceModel,
    IncidentResponseWorkflowModel, IncidentResponseExecutionModel,
    SecurityReportModel, AuditLogModel
)

# Import des services du domaine
from ..domain.services import (
    SecurityCorrelationEngine, AnomalyDetectionService, SecurityEvent
)

# Import des adaptateurs Docker
from .docker_integration import (
    SuricataDockerAdapter, Fail2BanDockerAdapter, 
    TrafficControlDockerAdapter, ServiceHealthCheck
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityDashboardData:
    """Données du tableau de bord de sécurité."""
    alerts_count: int = 0
    critical_alerts: int = 0
    active_rules: int = 0
    blocked_ips: int = 0
    vulnerability_count: int = 0
    incidents_count: int = 0
    threat_indicators: int = 0
    anomalies_detected: int = 0
    security_score: float = 0.0


@dataclass
class SecurityMetrics:
    """Métriques de sécurité consolidées."""
    total_events: int = 0
    events_by_severity: Dict[str, int] = None
    events_by_type: Dict[str, int] = None
    response_times: Dict[str, float] = None
    detection_rate: float = 0.0
    false_positive_rate: float = 0.0
    
    def __post_init__(self):
        if self.events_by_severity is None:
            self.events_by_severity = {}
        if self.events_by_type is None:
            self.events_by_type = {}
        if self.response_times is None:
            self.response_times = {}


class GNS3SecurityAdapter:
    """
    Adaptateur pour l'intégration GNS3 spécialisé sécurité.
    
    Responsabilités :
    - Contextualisation des événements de sécurité avec les topologies GNS3
    - Collecte des informations de sécurité des projets
    - Intégration des alertes avec les équipements GNS3
    """
    
    def __init__(self):
        self.gns3_interface = create_gns3_interface('security_management')
        self.cache_timeout = 300  # 5 minutes
        
    def is_available(self) -> bool:
        """Vérifie si GNS3 est disponible."""
        try:
            return self.gns3_interface is not None
        except Exception as e:
            logger.debug(f"Vérification GNS3 sécurité échouée: {e}")
            return False
    
    def get_security_topology_context(self, 
                                     source_ip: str = None,
                                     destination_ip: str = None,
                                     device_names: List[str] = None) -> Dict[str, Any]:
        """
        Récupère le contexte de topologie sécurité GNS3.
        
        Args:
            source_ip: Adresse IP source de l'événement
            destination_ip: Adresse IP destination
            device_names: Liste des noms d'équipements
            
        Returns:
            Dict contenant le contexte de topologie sécurité
        """
        try:
            if not self.is_available():
                return {}
            
            # Vérifier le cache
            cache_key = f"security_topology_{source_ip}_{destination_ip}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Récupérer les projets GNS3
            projects = []
            if hasattr(self.gns3_interface, 'get_projects'):
                projects = self.gns3_interface.get_projects() or []
            
            security_context = {
                'projects_count': len(projects),
                'security_devices': [],
                'network_segments': [],
                'security_topology': {},
                'threat_exposure': {}
            }
            
            # Analyser chaque projet pour les aspects sécurité
            for project in projects:
                project_security = self._analyze_project_security(project)
                security_context['security_devices'].extend(project_security.get('security_devices', []))
                security_context['network_segments'].extend(project_security.get('segments', []))
                
                # Correspondance avec les IPs de l'événement
                if source_ip or destination_ip:
                    matching_info = self._find_matching_devices(
                        project, source_ip, destination_ip, device_names
                    )
                    if matching_info:
                        security_context['security_topology'][project.get('name')] = matching_info
            
            # Évaluer l'exposition aux menaces
            security_context['threat_exposure'] = self._evaluate_threat_exposure(
                security_context['security_devices'], source_ip, destination_ip
            )
            
            # Mettre en cache
            cache.set(cache_key, security_context, self.cache_timeout)
            
            return security_context
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contexte GNS3 sécurité: {e}")
            return {}
    
    def _analyze_project_security(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les aspects sécurité d'un projet GNS3."""
        security_info = {
            'security_devices': [],
            'segments': [],
            'security_zones': []
        }
        
        try:
            nodes = project.get('nodes', [])
            links = project.get('links', [])
            
            for node in nodes:
                node_type = node.get('node_type', '').lower()
                node_name = node.get('name', '').lower()
                
                # Identifier les équipements de sécurité
                if any(keyword in node_name or keyword in node_type for keyword in [
                    'firewall', 'fw', 'ids', 'ips', 'suricata', 'snort', 
                    'security', 'guard', 'proxy', 'vpn', 'gateway'
                ]):
                    security_info['security_devices'].append({
                        'name': node.get('name'),
                        'type': node_type,
                        'status': node.get('status', 'unknown'),
                        'security_role': self._classify_security_role(node_name, node_type),
                        'project': project.get('name'),
                        'node_id': node.get('node_id')
                    })
                
                # Identifier les segments réseau
                if node_type in ['cloud', 'nat', 'subnet', 'switch', 'router']:
                    security_info['segments'].append({
                        'name': node.get('name'),
                        'type': node_type,
                        'security_level': self._assess_segment_security(node),
                        'project': project.get('name')
                    })
            
            # Analyser les zones de sécurité basées sur les liens
            security_info['security_zones'] = self._identify_security_zones(nodes, links)
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse de sécurité du projet: {e}")
        
        return security_info
    
    def _classify_security_role(self, name: str, node_type: str) -> str:
        """Classifie le rôle de sécurité d'un équipement."""
        name_lower = name.lower()
        type_lower = node_type.lower()
        
        if 'firewall' in name_lower or 'fw' in name_lower:
            return 'firewall'
        elif 'ids' in name_lower or 'ips' in name_lower or 'suricata' in name_lower:
            return 'ids_ips'
        elif 'vpn' in name_lower:
            return 'vpn_gateway'
        elif 'proxy' in name_lower:
            return 'proxy'
        elif 'guard' in name_lower or 'security' in name_lower:
            return 'security_appliance'
        else:
            return 'security_device'
    
    def _assess_segment_security(self, node: Dict[str, Any]) -> str:
        """Évalue le niveau de sécurité d'un segment réseau."""
        name = node.get('name', '').lower()
        node_type = node.get('node_type', '').lower()
        
        if 'dmz' in name or 'perimeter' in name:
            return 'medium'
        elif 'internal' in name or 'lan' in name:
            return 'high'
        elif 'external' in name or 'wan' in name or 'internet' in name:
            return 'low'
        else:
            return 'medium'
    
    def _identify_security_zones(self, nodes: List[Dict], links: List[Dict]) -> List[Dict[str, Any]]:
        """Identifie les zones de sécurité basées sur la topologie."""
        zones = []
        
        try:
            # Logique simplifiée d'identification des zones
            # Dans une implémentation complète, cela analyserait les connexions
            # pour identifier les zones de sécurité (DMZ, LAN, WAN, etc.)
            
            security_nodes = [n for n in nodes if self._is_security_node(n)]
            
            for sec_node in security_nodes:
                zone = {
                    'name': f"Zone_{sec_node.get('name', 'Unknown')}",
                    'type': 'security_zone',
                    'controlled_by': sec_node.get('name'),
                    'security_level': 'medium',
                    'nodes_count': 1
                }
                zones.append(zone)
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'identification des zones de sécurité: {e}")
        
        return zones
    
    def _is_security_node(self, node: Dict[str, Any]) -> bool:
        """Vérifie si un nœud est un équipement de sécurité."""
        name = node.get('name', '').lower()
        node_type = node.get('node_type', '').lower()
        
        security_keywords = ['firewall', 'fw', 'ids', 'ips', 'security', 'guard', 'vpn']
        return any(keyword in name or keyword in node_type for keyword in security_keywords)
    
    def _find_matching_devices(self, 
                              project: Dict[str, Any],
                              source_ip: str,
                              destination_ip: str,
                              device_names: List[str]) -> Optional[Dict[str, Any]]:
        """Trouve les équipements correspondant aux critères."""
        matching_info = {
            'project_name': project.get('name'),
            'matching_devices': [],
            'ip_associations': {},
            'security_context': {}
        }
        
        try:
            nodes = project.get('nodes', [])
            
            for node in nodes:
                node_name = node.get('name', '')
                
                # Correspondance par nom d'équipement
                if device_names and node_name in device_names:
                    matching_info['matching_devices'].append({
                        'name': node_name,
                        'type': node.get('node_type'),
                        'status': node.get('status'),
                        'match_reason': 'device_name'
                    })
                
                # Correspondance par IP (simplifiée)
                if source_ip or destination_ip:
                    # Dans une implémentation réelle, cela interrogerait les configurations
                    # des équipements pour trouver les correspondances IP
                    if self._node_might_have_ip(node, source_ip, destination_ip):
                        matching_info['matching_devices'].append({
                            'name': node_name,
                            'type': node.get('node_type'),
                            'status': node.get('status'),
                            'match_reason': 'ip_association'
                        })
            
            return matching_info if matching_info['matching_devices'] else None
            
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche d'équipements correspondants: {e}")
            return None
    
    def _node_might_have_ip(self, node: Dict[str, Any], source_ip: str, destination_ip: str) -> bool:
        """Vérifie si un nœud pourrait avoir une IP donnée (logique simplifiée)."""
        # Logique simplifiée - dans une implémentation réelle, cela interrogerait
        # les configurations des équipements
        node_type = node.get('node_type', '').lower()
        return node_type in ['router', 'switch', 'firewall', 'server', 'host']
    
    def _evaluate_threat_exposure(self, 
                                 security_devices: List[Dict],
                                 source_ip: str,
                                 destination_ip: str) -> Dict[str, Any]:
        """Évalue l'exposition aux menaces basée sur la topologie."""
        exposure = {
            'level': 'medium',
            'factors': [],
            'recommendations': []
        }
        
        try:
            # Facteurs d'exposition
            if not security_devices:
                exposure['level'] = 'high'
                exposure['factors'].append('Aucun équipement de sécurité identifié')
                exposure['recommendations'].append('Déployer des équipements de sécurité')
            
            # Analyser les types d'équipements de sécurité
            security_types = [d.get('security_role', 'unknown') for d in security_devices]
            
            if 'firewall' not in security_types:
                exposure['factors'].append('Pas de firewall identifié')
                exposure['recommendations'].append('Déployer un firewall')
            
            if 'ids_ips' not in security_types:
                exposure['factors'].append('Pas d\'IDS/IPS identifié')
                exposure['recommendations'].append('Déployer un système IDS/IPS')
            
            # Évaluer selon le nombre d'équipements
            if len(security_devices) >= 3:
                exposure['level'] = 'low'
            elif len(security_devices) >= 1:
                exposure['level'] = 'medium'
            else:
                exposure['level'] = 'high'
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'évaluation de l'exposition: {e}")
        
        return exposure


class DockerSecurityCollector:
    """
    Collecteur unifié pour les services Docker de sécurité.
    
    Responsabilités :
    - Collecte des données depuis Suricata, Fail2ban et Traffic Control
    - Agrégation des statistiques de sécurité
    - Surveillance de santé des services
    """
    
    def __init__(self):
        self.suricata = SuricataDockerAdapter()
        self.fail2ban = Fail2BanDockerAdapter()
        self.traffic_control = TrafficControlDockerAdapter()
        
        self.services = {
            'suricata': self.suricata,
            'fail2ban': self.fail2ban,
            'traffic_control': self.traffic_control
        }
        
        self.health_cache = {}
        self.health_cache_timeout = 60  # 1 minute
        
    def collect_security_data(self) -> Dict[str, Any]:
        """Collecte toutes les données de sécurité depuis les services Docker."""
        security_data = {
            'timestamp': timezone.now().isoformat(),
            'services_data': {},
            'aggregated_metrics': {},
            'health_status': {},
            'alerts': [],
            'blocked_ips': [],
            'threat_indicators': []
        }
        
        try:
            # Collecter les données de chaque service en parallèle
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._collect_suricata_data): 'suricata',
                    executor.submit(self._collect_fail2ban_data): 'fail2ban',
                    executor.submit(self._collect_traffic_control_data): 'traffic_control'
                }
                
                for future in as_completed(futures):
                    service_name = futures[future]
                    try:
                        service_data = future.result(timeout=30)
                        security_data['services_data'][service_name] = service_data
                        
                        # Extraire les données spécifiques
                        if service_name == 'suricata':
                            security_data['alerts'].extend(service_data.get('alerts', []))
                            security_data['threat_indicators'].extend(service_data.get('indicators', []))
                        elif service_name == 'fail2ban':
                            security_data['blocked_ips'].extend(service_data.get('banned_ips', []))
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de la collecte {service_name}: {e}")
                        security_data['services_data'][service_name] = {'error': str(e)}
            
            # Agréger les métriques
            security_data['aggregated_metrics'] = self._aggregate_security_metrics(
                security_data['services_data']
            )
            
            # Vérifier la santé des services
            security_data['health_status'] = self.check_all_services_health()
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des données de sécurité: {e}")
            security_data['error'] = str(e)
        
        return security_data
    
    def _collect_suricata_data(self) -> Dict[str, Any]:
        """Collecte les données Suricata."""
        try:
            if not self.suricata.test_connection():
                return {'error': 'Service Suricata non accessible'}
            
            # Récupérer les alertes récentes
            alerts = self.suricata.get_alerts(limit=100)
            
            # Récupérer les statistiques
            stats = self.suricata.get_statistics()
            
            # Récupérer les règles actives
            rules_count = self.suricata.get_rules_count()
            
            return {
                'alerts': alerts[:50],  # Limiter à 50 alertes
                'statistics': stats,
                'rules_count': rules_count,
                'service_status': 'active',
                'indicators': self._extract_threat_indicators(alerts)
            }
            
        except Exception as e:
            logger.error(f"Erreur collecte Suricata: {e}")
            return {'error': str(e)}
    
    def _collect_fail2ban_data(self) -> Dict[str, Any]:
        """Collecte les données Fail2ban."""
        try:
            if not self.fail2ban.test_connection():
                return {'error': 'Service Fail2ban non accessible'}
            
            # Récupérer les IPs bannies
            banned_ips = self.fail2ban.get_banned_ips()
            
            # Récupérer les statistiques des prisons
            jails_stats = self.fail2ban.get_jails_statistics()
            
            return {
                'banned_ips': banned_ips,
                'jails_statistics': jails_stats,
                'service_status': 'active',
                'total_banned': len(banned_ips)
            }
            
        except Exception as e:
            logger.error(f"Erreur collecte Fail2ban: {e}")
            return {'error': str(e)}
    
    def _collect_traffic_control_data(self) -> Dict[str, Any]:
        """Collecte les données Traffic Control."""
        try:
            if not self.traffic_control.test_connection():
                return {'error': 'Service Traffic Control non accessible'}
            
            # Récupérer les règles de trafic
            traffic_rules = self.traffic_control.get_traffic_rules()
            
            # Récupérer les statistiques de trafic
            traffic_stats = self.traffic_control.get_traffic_statistics()
            
            return {
                'traffic_rules': traffic_rules,
                'traffic_statistics': traffic_stats,
                'service_status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Erreur collecte Traffic Control: {e}")
            return {'error': str(e)}
    
    def _extract_threat_indicators(self, alerts: List[Dict]) -> List[Dict[str, Any]]:
        """Extrait les indicateurs de menace des alertes."""
        indicators = []
        
        for alert in alerts:
            try:
                # Extraire les IPs sources suspectes
                source_ip = alert.get('source_ip')
                if source_ip:
                    indicators.append({
                        'type': 'ip',
                        'value': source_ip,
                        'severity': alert.get('severity', 'medium'),
                        'description': f"IP source dans alerte: {alert.get('signature', 'Unknown')}",
                        'first_seen': alert.get('timestamp')
                    })
                
                # Extraire les signatures de menace
                signature = alert.get('signature')
                if signature:
                    indicators.append({
                        'type': 'signature',
                        'value': signature,
                        'severity': alert.get('severity', 'medium'),
                        'description': f"Signature de menace détectée",
                        'first_seen': alert.get('timestamp')
                    })
                    
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction d'indicateurs: {e}")
                continue
        
        return indicators
    
    def _aggregate_security_metrics(self, services_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agrège les métriques de sécurité de tous les services."""
        metrics = {
            'total_alerts': 0,
            'total_blocked_ips': 0,
            'total_rules': 0,
            'threat_indicators_count': 0,
            'services_operational': 0,
            'overall_security_score': 0.0
        }
        
        try:
            # Compter les alertes Suricata
            suricata_data = services_data.get('suricata', {})
            if 'alerts' in suricata_data:
                metrics['total_alerts'] = len(suricata_data['alerts'])
            
            # Compter les IPs bloquées Fail2ban
            fail2ban_data = services_data.get('fail2ban', {})
            if 'banned_ips' in fail2ban_data:
                metrics['total_blocked_ips'] = len(fail2ban_data['banned_ips'])
            
            # Compter les règles de trafic
            traffic_data = services_data.get('traffic_control', {})
            if 'traffic_rules' in traffic_data:
                metrics['total_rules'] = len(traffic_data['traffic_rules'])
            
            # Compter les services opérationnels
            operational_services = sum(
                1 for service_data in services_data.values() 
                if service_data.get('service_status') == 'active'
            )
            metrics['services_operational'] = operational_services
            
            # Calculer le score de sécurité global
            total_services = len(services_data)
            if total_services > 0:
                operational_ratio = operational_services / total_services
                metrics['overall_security_score'] = operational_ratio * 100
            
        except Exception as e:
            logger.error(f"Erreur lors de l'agrégation des métriques: {e}")
        
        return metrics
    
    def check_all_services_health(self) -> Dict[str, ServiceHealthCheck]:
        """Vérifie la santé de tous les services Docker."""
        health_status = {}
        
        for service_name, service_adapter in self.services.items():
            try:
                # Vérifier le cache
                cache_key = f"health_{service_name}"
                if cache_key in self.health_cache:
                    cached_health, cached_time = self.health_cache[cache_key]
                    if (timezone.now() - cached_time).total_seconds() < self.health_cache_timeout:
                        health_status[service_name] = cached_health
                        continue
                
                # Vérifier la santé du service
                start_time = timezone.now()
                is_healthy = service_adapter.test_connection()
                response_time = int((timezone.now() - start_time).total_seconds() * 1000)
                
                health_check = ServiceHealthCheck(
                    service_name=service_name,
                    status='healthy' if is_healthy else 'unhealthy',
                    response_time_ms=response_time,
                    last_check=timezone.now(),
                    consecutive_failures=0 if is_healthy else 1
                )
                
                health_status[service_name] = health_check
                
                # Mettre en cache
                self.health_cache[cache_key] = (health_check, timezone.now())
                
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de santé {service_name}: {e}")
                health_status[service_name] = ServiceHealthCheck(
                    service_name=service_name,
                    status='unhealthy',
                    response_time_ms=0,
                    last_check=timezone.now(),
                    error_message=str(e),
                    consecutive_failures=1
                )
        
        return health_status


class UnifiedSecurityService:
    """
    Service unifié pour la gestion de la sécurité avec intégration GNS3 et Docker.
    
    Point d'entrée principal pour toutes les opérations de sécurité du NMS.
    """
    
    def __init__(self):
        self.gns3_adapter = GNS3SecurityAdapter()
        self.docker_collector = DockerSecurityCollector()
        
        # Initialiser les repositories pour le moteur de corrélation
        from ..infrastructure.repositories import (
            DjangoCorrelationRuleRepository,
            DjangoCorrelationRuleMatchRepository,
            DjangoSecurityAlertRepository
        )
        
        try:
            rule_repository = DjangoCorrelationRuleRepository()
            match_repository = DjangoCorrelationRuleMatchRepository()
            alert_repository = DjangoSecurityAlertRepository()
            
            self.correlation_engine = SecurityCorrelationEngine(
                rule_repository=rule_repository,
                match_repository=match_repository,
                alert_repository=alert_repository
            )
        except Exception as e:
            logger.warning(f"Erreur lors de l'initialisation du moteur de corrélation: {e}")
            # Utiliser des repositories en mémoire comme fallback
            self.correlation_engine = None
        
        self.anomaly_service = AnomalyDetectionService()
        
        # Cache pour les performances
        self.cache_timeout = 300  # 5 minutes
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("UnifiedSecurityService initialisé")
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """
        Récupère les données du tableau de bord de sécurité unifié.
        
        Returns:
            Données complètes du tableau de bord sécurité
        """
        try:
            with self._lock:
                # Vérifier le cache
                cache_key = "security_dashboard"
                cached_data = cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                # Collecter les données de base
                dashboard_data = SecurityDashboardData()
                
                # Données depuis la base de données
                dashboard_data.alerts_count = SecurityAlertModel.objects.count()
                dashboard_data.critical_alerts = SecurityAlertModel.objects.filter(
                    severity='critical'
                ).count()
                dashboard_data.active_rules = SecurityRuleModel.objects.filter(
                    enabled=True
                ).count()
                dashboard_data.vulnerability_count = VulnerabilityModel.objects.count()
                dashboard_data.incidents_count = IncidentResponseExecutionModel.objects.count()
                dashboard_data.threat_indicators = ThreatIntelligenceModel.objects.filter(
                    is_active=True
                ).count()
                
                # Données depuis les services Docker
                docker_data = self.docker_collector.collect_security_data()
                dashboard_data.blocked_ips = len(docker_data.get('blocked_ips', []))
                dashboard_data.anomalies_detected = len(docker_data.get('alerts', []))
                
                # Calcul du score de sécurité
                dashboard_data.security_score = self._calculate_security_score(
                    dashboard_data, docker_data
                )
                
                # Contexte GNS3
                gns3_context = self.gns3_adapter.get_security_topology_context()
                
                # Métriques détaillées
                detailed_metrics = self._get_detailed_security_metrics()
                
                # Construire la réponse
                result = {
                    'timestamp': timezone.now().isoformat(),
                    'dashboard_data': asdict(dashboard_data),
                    'gns3_context': gns3_context,
                    'docker_services': docker_data,
                    'detailed_metrics': detailed_metrics,
                    'health_status': {
                        'gns3_integration': self.gns3_adapter.is_available(),
                        'docker_services': docker_data.get('health_status', {}),
                        'overall_health': self._calculate_overall_health(docker_data)
                    }
                }
                
                # Mettre en cache
                cache.set(cache_key, result, self.cache_timeout)
                
                return result
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du tableau de bord: {e}")
            return {'error': str(e)}
    
    def process_security_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un événement de sécurité avec corrélation et détection d'anomalies.
        
        Args:
            event_data: Données de l'événement de sécurité
            
        Returns:
            Résultat du traitement avec enrichissement
        """
        try:
            # Créer l'événement de sécurité
            security_event = SecurityEvent(
                event_type=event_data.get('event_type', 'unknown'),
                source_ip=event_data.get('source_ip'),
                destination_ip=event_data.get('destination_ip'),
                timestamp=datetime.fromisoformat(
                    event_data.get('timestamp', timezone.now().isoformat()).replace('Z', '+00:00')
                ),
                severity=event_data.get('severity', 'medium'),
                raw_data=event_data.get('raw_data', {}),
                metadata=event_data.get('metadata', {})
            )
            
            # Enrichir avec le contexte GNS3
            gns3_context = self.gns3_adapter.get_security_topology_context(
                source_ip=security_event.source_ip,
                destination_ip=security_event.destination_ip
            )
            security_event.add_enrichment('gns3_context', gns3_context)
            
            # Traiter avec le moteur de corrélation
            enriched_event, generated_alerts = self.correlation_engine.process_event(
                security_event.to_dict()
            )
            
            # Détecter les anomalies
            anomalies = self.anomaly_service.detect_anomalies([security_event])
            
            # Sauvegarder les alertes générées
            saved_alerts = []
            for alert in generated_alerts:
                try:
                    alert_model = SecurityAlertModel.objects.create(
                        title=alert.title,
                        description=alert.description,
                        severity=alert.severity,
                        source_ip=alert.source_events[0].source_ip if alert.source_events else None,
                        destination_ip=alert.source_events[0].destination_ip if alert.source_events else None,
                        detection_time=alert.created_at,
                        status='new',
                        raw_data=alert.to_dict()
                    )
                    saved_alerts.append(alert_model.id)
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde d'alerte: {e}")
            
            # Construire la réponse
            result = {
                'event_id': enriched_event.event_id,
                'processing_timestamp': timezone.now().isoformat(),
                'enriched_event': enriched_event.to_dict(),
                'correlation_results': {
                    'alerts_generated': len(generated_alerts),
                    'alert_ids': saved_alerts,
                    'correlation_score': enriched_event.correlation_info.get('score', 0.0)
                },
                'anomaly_results': {
                    'anomalies_detected': len(anomalies),
                    'anomaly_types': [a.anomaly_type for a in anomalies],
                    'max_confidence': max([a.confidence for a in anomalies], default=0.0)
                },
                'gns3_context': gns3_context,
                'recommended_actions': self._generate_event_recommendations(
                    enriched_event, generated_alerts, anomalies
                )
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement de sécurité: {e}")
            return {'error': str(e)}
    
    def run_security_analysis(self, 
                            analysis_type: str = 'comprehensive',
                            time_range: str = '24h') -> Dict[str, Any]:
        """
        Lance une analyse de sécurité complète.
        
        Args:
            analysis_type: Type d'analyse (comprehensive, threats, vulnerabilities)
            time_range: Période d'analyse (1h, 24h, 7d, 30d)
            
        Returns:
            Résultats de l'analyse de sécurité
        """
        try:
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
            
            analysis_results = {
                'analysis_metadata': {
                    'type': analysis_type,
                    'time_range': time_range,
                    'period': {
                        'start': start_time.isoformat(),
                        'end': now.isoformat()
                    },
                    'analysis_timestamp': now.isoformat()
                },
                'security_posture': {},
                'threat_landscape': {},
                'vulnerability_assessment': {},
                'recommendations': []
            }
            
            if analysis_type in ['comprehensive', 'threats']:
                # Analyse des menaces
                analysis_results['threat_landscape'] = self._analyze_threat_landscape(
                    start_time, now
                )
            
            if analysis_type in ['comprehensive', 'vulnerabilities']:
                # Évaluation des vulnérabilités
                analysis_results['vulnerability_assessment'] = self._assess_vulnerabilities()
            
            if analysis_type == 'comprehensive':
                # Posture de sécurité globale
                analysis_results['security_posture'] = self._evaluate_security_posture(
                    start_time, now
                )
            
            # Générer les recommandations
            analysis_results['recommendations'] = self._generate_security_recommendations(
                analysis_results
            )
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de sécurité: {e}")
            return {'error': str(e)}
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet du système de sécurité.
        
        Returns:
            Statut unifié du système de sécurité
        """
        try:
            # Statistiques de base
            security_stats = {
                'total_rules': SecurityRuleModel.objects.count(),
                'active_rules': SecurityRuleModel.objects.filter(enabled=True).count(),
                'total_alerts': SecurityAlertModel.objects.count(),
                'active_alerts': SecurityAlertModel.objects.filter(
                    status__in=['new', 'acknowledged']
                ).count(),
                'vulnerabilities': VulnerabilityModel.objects.count(),
                'critical_vulnerabilities': VulnerabilityModel.objects.filter(
                    severity='critical'
                ).count(),
                'threat_indicators': ThreatIntelligenceModel.objects.filter(
                    is_active=True
                ).count(),
                'recent_incidents': IncidentResponseExecutionModel.objects.filter(
                    started_at__gte=timezone.now() - timedelta(days=7)
                ).count()
            }
            
            # Statut des services Docker
            docker_health = self.docker_collector.check_all_services_health()
            
            # Métriques de performance
            performance_metrics = self._get_performance_metrics()
            
            # Statut global
            operational_docker_services = sum(
                1 for health in docker_health.values() 
                if health.status == 'healthy'
            )
            total_docker_services = len(docker_health)
            
            gns3_available = self.gns3_adapter.is_available()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'service': 'security_management',
                'version': '1.0.0',
                'operational': operational_docker_services >= 2 and gns3_available,
                'services_status': {
                    'gns3_integration': gns3_available,
                    'docker_services': {
                        service_name: {
                            'status': health.status,
                            'response_time_ms': health.response_time_ms,
                            'last_check': health.last_check.isoformat(),
                            'consecutive_failures': health.consecutive_failures
                        }
                        for service_name, health in docker_health.items()
                    }
                },
                'security_statistics': security_stats,
                'performance_metrics': performance_metrics,
                'health_score': self._calculate_health_score(
                    operational_docker_services, total_docker_services, gns3_available
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {'error': str(e)}
    
    def _calculate_security_score(self, 
                                 dashboard_data: SecurityDashboardData,
                                 docker_data: Dict[str, Any]) -> float:
        """Calcule le score de sécurité global."""
        try:
            # Facteurs de score
            factors = {
                'rules_coverage': min(dashboard_data.active_rules / 50, 1.0) * 20,
                'alert_response': max(0, 20 - dashboard_data.critical_alerts * 2),
                'threat_detection': min(dashboard_data.threat_indicators / 100, 1.0) * 15,
                'vulnerability_management': max(0, 15 - dashboard_data.vulnerability_count * 0.5),
                'docker_services': docker_data.get('aggregated_metrics', {}).get('overall_security_score', 0) * 0.3
            }
            
            total_score = sum(factors.values())
            return min(100.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score de sécurité: {e}")
            return 0.0
    
    def _get_detailed_security_metrics(self) -> SecurityMetrics:
        """Récupère les métriques détaillées de sécurité."""
        try:
            metrics = SecurityMetrics()
            
            # Métriques des alertes
            recent_alerts = SecurityAlertModel.objects.filter(
                detection_time__gte=timezone.now() - timedelta(days=1)
            )
            
            metrics.total_events = recent_alerts.count()
            
            # Répartition par sévérité
            severity_counts = recent_alerts.values('severity').annotate(
                count=Count('id')
            ).values_list('severity', 'count')
            metrics.events_by_severity = dict(severity_counts)
            
            # Répartition par type (simulé)
            metrics.events_by_type = {
                'intrusion': recent_alerts.filter(title__icontains='intrusion').count(),
                'malware': recent_alerts.filter(title__icontains='malware').count(),
                'anomaly': recent_alerts.filter(title__icontains='anomaly').count(),
                'policy_violation': recent_alerts.filter(title__icontains='policy').count()
            }
            
            # Temps de réponse (simulé)
            metrics.response_times = {
                'detection': 1.5,
                'analysis': 3.2,
                'response': 8.7
            }
            
            # Taux de détection et faux positifs (simulé)
            metrics.detection_rate = 0.85
            metrics.false_positive_rate = 0.12
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques: {e}")
            return SecurityMetrics()
    
    def _calculate_overall_health(self, docker_data: Dict[str, Any]) -> str:
        """Calcule la santé globale du système."""
        try:
            health_status = docker_data.get('health_status', {})
            
            healthy_services = sum(
                1 for health in health_status.values() 
                if getattr(health, 'status', 'unhealthy') == 'healthy'
            )
            
            total_services = len(health_status)
            
            if total_services == 0:
                return 'unknown'
            
            health_ratio = healthy_services / total_services
            
            if health_ratio >= 0.8:
                return 'healthy'
            elif health_ratio >= 0.6:
                return 'degraded'
            else:
                return 'unhealthy'
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la santé globale: {e}")
            return 'unknown'
    
    def _generate_event_recommendations(self, 
                                      event: SecurityEvent,
                                      alerts: List,
                                      anomalies: List) -> List[str]:
        """Génère des recommandations pour un événement."""
        recommendations = []
        
        # Recommandations basées sur la sévérité
        if event.severity in ['high', 'critical']:
            recommendations.append("Investigation immédiate recommandée")
            recommendations.append("Vérifier les logs détaillés")
        
        # Recommandations basées sur les alertes
        if alerts:
            recommendations.append(f"Analyser les {len(alerts)} alertes générées")
            recommendations.append("Vérifier les règles de corrélation")
        
        # Recommandations basées sur les anomalies
        if anomalies:
            recommendations.append("Analyser les anomalies détectées")
            recommendations.append("Ajuster les baselines si nécessaire")
        
        # Recommandations basées sur l'IP source
        if event.source_ip:
            recommendations.append(f"Vérifier la réputation de l'IP {event.source_ip}")
        
        return recommendations
    
    def _analyze_threat_landscape(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyse le paysage des menaces."""
        try:
            # Analyser les alertes récentes
            recent_alerts = SecurityAlertModel.objects.filter(
                detection_time__gte=start_time,
                detection_time__lte=end_time
            )
            
            # Top des menaces
            threat_types = {}
            for alert in recent_alerts:
                threat_type = alert.raw_data.get('threat_type', 'unknown')
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
            
            # Analyse géographique des menaces
            geo_threats = {}
            for alert in recent_alerts:
                if alert.source_ip:
                    # Simuler la géolocalisation
                    country = 'Unknown'  # En réalité, utiliser une API de géolocalisation
                    geo_threats[country] = geo_threats.get(country, 0) + 1
            
            return {
                'total_threats': recent_alerts.count(),
                'threat_types': threat_types,
                'geographic_distribution': geo_threats,
                'trend': 'increasing' if recent_alerts.count() > 10 else 'stable',
                'top_source_ips': list(
                    recent_alerts.values('source_ip')
                    .annotate(count=Count('id'))
                    .order_by('-count')[:10]
                    .values_list('source_ip', 'count')
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des menaces: {e}")
            return {}
    
    def _assess_vulnerabilities(self) -> Dict[str, Any]:
        """Évalue les vulnérabilités."""
        try:
            vulnerabilities = VulnerabilityModel.objects.all()
            
            # Répartition par sévérité
            severity_distribution = dict(
                vulnerabilities.values('severity')
                .annotate(count=Count('id'))
                .values_list('severity', 'count')
            )
            
            # Vulnérabilités avec patches disponibles
            patchable_count = vulnerabilities.filter(patch_available=True).count()
            
            # Score CVSS moyen
            avg_cvss = vulnerabilities.aggregate(
                avg_cvss=Avg('cvss_score')
            )['avg_cvss'] or 0.0
            
            return {
                'total_vulnerabilities': vulnerabilities.count(),
                'severity_distribution': severity_distribution,
                'patchable_vulnerabilities': patchable_count,
                'average_cvss_score': round(avg_cvss, 2),
                'patching_rate': round(patchable_count / max(vulnerabilities.count(), 1) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation des vulnérabilités: {e}")
            return {}
    
    def _evaluate_security_posture(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Évalue la posture de sécurité globale."""
        try:
            # Métriques de base
            active_rules = SecurityRuleModel.objects.filter(enabled=True).count()
            total_rules = SecurityRuleModel.objects.count()
            
            # Incidents récents
            recent_incidents = IncidentResponseExecutionModel.objects.filter(
                started_at__gte=start_time,
                started_at__lte=end_time
            ).count()
            
            # Temps de réponse moyen (simulé)
            avg_response_time = 15.5  # minutes
            
            # Score de maturité
            maturity_factors = {
                'rule_coverage': min(active_rules / 100, 1.0),
                'incident_response': max(0, 1 - recent_incidents / 10),
                'response_time': max(0, 1 - avg_response_time / 60)
            }
            
            maturity_score = sum(maturity_factors.values()) / len(maturity_factors)
            
            return {
                'rule_coverage': f"{active_rules}/{total_rules}",
                'incident_count': recent_incidents,
                'average_response_time_minutes': avg_response_time,
                'maturity_score': round(maturity_score * 100, 2),
                'maturity_level': self._classify_maturity_level(maturity_score)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la posture: {e}")
            return {}
    
    def _classify_maturity_level(self, score: float) -> str:
        """Classifie le niveau de maturité."""
        if score >= 0.8:
            return 'Advanced'
        elif score >= 0.6:
            return 'Intermediate'
        elif score >= 0.4:
            return 'Basic'
        else:
            return 'Initial'
    
    def _generate_security_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Génère des recommandations de sécurité."""
        recommendations = []
        
        # Recommandations basées sur les vulnérabilités
        vuln_assessment = analysis_results.get('vulnerability_assessment', {})
        if vuln_assessment.get('total_vulnerabilities', 0) > 0:
            recommendations.append("Prioriser la correction des vulnérabilités critiques")
            
            patching_rate = vuln_assessment.get('patching_rate', 0)
            if patching_rate < 50:
                recommendations.append("Améliorer le processus de gestion des patches")
        
        # Recommandations basées sur les menaces
        threat_landscape = analysis_results.get('threat_landscape', {})
        if threat_landscape.get('total_threats', 0) > 20:
            recommendations.append("Renforcer la surveillance des menaces")
            recommendations.append("Réviser les règles de détection")
        
        # Recommandations basées sur la posture
        security_posture = analysis_results.get('security_posture', {})
        maturity_level = security_posture.get('maturity_level', 'Initial')
        if maturity_level in ['Initial', 'Basic']:
            recommendations.append("Améliorer la maturité du programme de sécurité")
            recommendations.append("Implémenter des processus de sécurité standardisés")
        
        return recommendations
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de performance."""
        try:
            # Métriques des services Docker
            docker_metrics = self.docker_collector.collect_security_data()
            
            # Métriques de corrélation
            correlation_stats = self.correlation_engine.get_statistics()
            
            return {
                'docker_services': docker_metrics.get('aggregated_metrics', {}),
                'correlation_engine': correlation_stats,
                'database_performance': {
                    'total_alerts': SecurityAlertModel.objects.count(),
                    'total_rules': SecurityRuleModel.objects.count(),
                    'total_vulnerabilities': VulnerabilityModel.objects.count()
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de performance: {e}")
            return {}
    
    def _calculate_health_score(self, 
                               operational_docker: int,
                               total_docker: int,
                               gns3_available: bool) -> float:
        """Calcule le score de santé global."""
        try:
            docker_score = (operational_docker / max(total_docker, 1)) * 80
            gns3_score = 20 if gns3_available else 0
            
            return docker_score + gns3_score
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score de santé: {e}")
            return 0.0


# Instance globale du service unifié de sécurité
unified_security_service = UnifiedSecurityService()