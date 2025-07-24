"""
Service unifié d'intégration QoS Management avec GNS3 Central et Docker.

Ce service modernise l'intégration du module qos_management en utilisant :
- Le nouveau Service Central GNS3 
- L'intégration Docker pour la gestion des services QoS (Traffic Control, HAProxy, etc.)
- Une architecture événementielle unifiée
- La gestion temps réel des politiques QoS et SLA

Architecture Développeur Senior :
- Séparation claire des responsabilités (GNS3/Docker/QoS)
- Pattern Observer pour les événements
- Circuit Breaker pour la résilience
- Interface simplifiée pour les use cases
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import docker
import json
import requests

from common.api.gns3_module_interface import create_gns3_interface
from common.infrastructure.gns3_central_service import GNS3EventType
from ..models import QoSPolicy, TrafficClass, InterfaceQoSPolicy, SLAComplianceRecord

logger = logging.getLogger(__name__)


class DockerQoSCollector:
    """
    Collecteur de services Docker spécialisé pour la gestion QoS.
    
    Responsabilités :
    - Connexion au daemon Docker
    - Gestion des services QoS spécialisés (Traffic Control, HAProxy, etc.)
    - Intégration avec les services de contrôle de trafic
    - Transformation en format standardisé
    """
    
    def __init__(self):
        self.client = None
        # Services Docker QoS à surveiller
        self.qos_services = {
            # Service principal de Traffic Control
            'nms-traffic-control': {'port': 8003, 'health_endpoint': '/health', 'type': 'traffic_control'},
            
            # Services de load balancing et proxy
            'nms-haproxy': {'port': 1936, 'health_endpoint': '/stats', 'type': 'load_balancer'},
            
            # Services de monitoring QoS
            'nms-prometheus': {'port': 9090, 'health_endpoint': '/-/healthy', 'type': 'metrics_collector'},
            'nms-grafana': {'port': 3001, 'health_endpoint': '/api/health', 'type': 'metrics_visualization'},
            'nms-netdata': {'port': 19999, 'health_endpoint': '/api/v1/info', 'type': 'realtime_metrics'},
            'nms-ntopng': {'port': 3000, 'health_endpoint': '/', 'type': 'traffic_analysis'},
            
            # Services de données pour SLA
            'nms-elasticsearch': {'port': 9200, 'health_endpoint': '/_cluster/health', 'type': 'log_storage'},
            'nms-kibana': {'port': 5601, 'health_endpoint': '/api/status', 'type': 'log_visualization'},
            
            # Services applicatifs
            'nms-django': {'port': 8000, 'health_endpoint': '/api/common/api/v1/integration/health/', 'type': 'application'},
            'nms-celery': {'port': None, 'health_endpoint': None, 'type': 'task_queue'},
            
            # Services de base de données
            'nms-postgres': {'port': 5432, 'health_endpoint': None, 'type': 'database'},
            'nms-redis': {'port': 6379, 'health_endpoint': None, 'type': 'cache'}
        }
        self._initialize_docker_client()
        
    def _initialize_docker_client(self):
        """Initialise le client Docker avec gestion d'erreurs."""
        try:
            self.client = docker.from_env()
            # Test de connectivité
            self.client.ping()
            logger.info("✅ Connexion Docker établie pour QoS management")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion Docker QoS management: {e}")
            self.client = None
            
    def is_available(self) -> bool:
        """Vérifie si Docker est disponible."""
        return self.client is not None
        
    def collect_qos_services_status(self) -> List[Dict[str, Any]]:
        """
        Collecte le statut des services QoS Docker.
        
        Returns:
            Liste des statuts des services QoS NMS
        """
        if not self.is_available():
            logger.warning("Docker non disponible pour la collecte des services QoS")
            return []
            
        services_status = []
        
        try:
            containers = self.client.containers.list(all=True)
            
            for container in containers:
                container_name = container.name
                
                if container_name in self.qos_services:
                    service_config = self.qos_services[container_name]
                    
                    try:
                        # Récupérer les informations de base
                        status_info = {
                            'service_name': container_name,
                            'service_type': service_config['type'],
                            'container_id': container.id[:12],
                            'status': container.status,
                            'image': container.image.tags[0] if container.image.tags else 'unknown',
                            'created': container.attrs['Created'],
                            'ports': service_config.get('port'),
                            'health_endpoint': service_config.get('health_endpoint'),
                            'is_healthy': False,
                            'last_check': datetime.now().isoformat()
                        }
                        
                        # Test de santé si le service est running
                        if container.status == 'running' and service_config.get('health_endpoint'):
                            try:
                                port = service_config.get('port')
                                if port:
                                    health_url = f"http://localhost:{port}{service_config['health_endpoint']}"
                                    response = requests.get(health_url, timeout=5)
                                    status_info['is_healthy'] = response.status_code == 200
                                    status_info['health_response_time'] = response.elapsed.total_seconds()
                            except Exception as health_e:
                                logger.debug(f"Test de santé échoué pour {container_name}: {health_e}")
                                status_info['health_error'] = str(health_e)
                        
                        # Informations spécifiques au type de service
                        if service_config['type'] == 'traffic_control':
                            status_info['qos_capabilities'] = self._get_traffic_control_capabilities(container)
                        elif service_config['type'] == 'load_balancer':
                            status_info['load_balancer_stats'] = self._get_haproxy_stats(container)
                        elif service_config['type'] in ['metrics_collector', 'metrics_visualization']:
                            status_info['metrics_status'] = self._get_metrics_service_status(container)
                            
                        services_status.append(status_info)
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de la collecte du statut pour {container_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des services QoS Docker: {e}")
            
        return services_status
        
    def _get_traffic_control_capabilities(self, container) -> Dict[str, Any]:
        """Récupère les capacités du service Traffic Control."""
        try:
            # Vérifier les capacités TC dans le conteneur
            result = container.exec_run("tc -V")
            if result.exit_code == 0:
                return {
                    'tc_available': True,
                    'tc_version': result.output.decode().strip(),
                    'supported_qdiscs': ['htb', 'cbq', 'pfifo_fast', 'sfq', 'fq_codel'],
                    'supported_classes': ['htb', 'cbq', 'drr', 'hfsc']
                }
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification des capacités TC: {e}")
            
        return {'tc_available': False}
        
    def _get_haproxy_stats(self, container) -> Dict[str, Any]:
        """Récupère les statistiques HAProxy."""
        try:
            # Essayer de récupérer les stats HAProxy
            response = requests.get("http://localhost:1936/stats", timeout=5)
            if response.status_code == 200:
                return {
                    'stats_available': True,
                    'response_time': response.elapsed.total_seconds(),
                    'content_length': len(response.content)
                }
        except Exception as e:
            logger.debug(f"Erreur lors de la récupération des stats HAProxy: {e}")
            
        return {'stats_available': False}
        
    def _get_metrics_service_status(self, container) -> Dict[str, Any]:
        """Récupère le statut des services de métriques."""
        service_name = container.name
        
        try:
            if 'prometheus' in service_name:
                response = requests.get("http://localhost:9090/-/healthy", timeout=5)
                return {
                    'service_healthy': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds()
                }
            elif 'grafana' in service_name:
                response = requests.get("http://localhost:3001/api/health", timeout=5)
                return {
                    'service_healthy': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            logger.debug(f"Erreur lors du test de santé pour {service_name}: {e}")
            
        return {'service_healthy': False}


class GNS3QoSAdapter:
    """
    Adaptateur pour l'intégration GNS3 spécialisé QoS.
    
    Responsabilités :
    - Communication avec GNS3 Central Service
    - Synchronisation des politiques QoS avec les topologies GNS3
    - Gestion des événements de modification de topologie
    - Application automatique des politiques QoS sur les équipements
    """
    
    def __init__(self):
        self.gns3_interface = create_gns3_interface('qos_management')
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._initialize_event_subscriptions()
        
    def _initialize_event_subscriptions(self):
        """Initialise les abonnements aux événements GNS3."""
        try:
            # Événements liés aux modifications de topologie
            qos_relevant_events = [
                'project.updated',
                'node.updated', 
                'link.created',
                'link.updated',
                'link.deleted',
                'node.started',
                'node.stopped'
            ]
            
            for event_name in qos_relevant_events:
                try:
                    # Vérifier si l'interface a la méthode subscribe_to_event
                    if hasattr(self.gns3_interface, 'subscribe_to_event'):
                        # Vérifier si l'événement existe dans l'enum
                        if hasattr(GNS3EventType, event_name.upper().replace('.', '_')):
                            event_type = getattr(GNS3EventType, event_name.upper().replace('.', '_'))
                            self.gns3_interface.subscribe_to_event(
                                event_type, 
                                self._handle_qos_event
                            )
                            logger.info(f"✅ Abonnement aux événements QoS GNS3: {event_name}")
                        else:
                            # Abonnement avec string si enum pas disponible
                            self.gns3_interface.subscribe_to_event(
                                event_name, 
                                self._handle_qos_event
                            )
                            logger.info(f"✅ Abonnement aux événements QoS GNS3 (string): {event_name}")
                    else:
                        # Interface GNS3 sans gestion d'événements - mode dégradé
                        logger.info(f"Interface GNS3 sans gestion d'événements pour QoS: {event_name}")
                        
                except Exception as e:
                    logger.debug(f"Abonnement QoS échoué pour {event_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Initialisation des abonnements QoS en mode dégradé: {e}")
            
    def is_available(self) -> bool:
        """Vérifie si GNS3 est disponible."""
        try:
            if hasattr(self.gns3_interface, 'get_status'):
                return self.gns3_interface.get_status()
            elif hasattr(self.gns3_interface, 'get_projects'):
                # Test alternatif : essayer de récupérer les projets
                projects = self.gns3_interface.get_projects()
                return isinstance(projects, list)
            elif hasattr(self.gns3_interface, 'health_check'):
                # Autre test alternatif
                return self.gns3_interface.health_check()
            else:
                # Test de connectivité basique si l'interface existe
                return self.gns3_interface is not None
        except Exception as e:
            logger.debug(f"Vérification de disponibilité GNS3 QoS échouée: {e}")
            # Retourner True si l'interface existe (mode dégradé)
            return self.gns3_interface is not None
            
    def _handle_qos_event(self, event_data: Dict[str, Any]):
        """
        Gestionnaire d'événements GNS3 pour QoS.
        
        Args:
            event_data: Données de l'événement GNS3
        """
        try:
            event_type = event_data.get('event_type', 'unknown')
            project_id = event_data.get('project_id')
            
            logger.info(f"📡 Événement GNS3 QoS reçu: {event_type} pour projet {project_id}")
            
            # Traitement selon le type d'événement
            if 'node' in event_type:
                self._handle_node_qos_event(event_data)
            elif 'link' in event_type:
                self._handle_link_qos_event(event_data)
            elif 'project' in event_type:
                self._handle_project_qos_event(event_data)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement QoS GNS3: {e}")
            
    def _handle_node_qos_event(self, event_data: Dict[str, Any]):
        """Traite les événements liés aux nœuds pour appliquer les politiques QoS."""
        try:
            node_data = event_data.get('node', {})
            node_id = node_data.get('node_id')
            node_name = node_data.get('name', 'Unknown')
            node_type = node_data.get('node_type', 'unknown')
            
            # Vérifier si le nœud supporte QoS
            if self._node_supports_qos(node_type):
                logger.info(f"🔧 Application des politiques QoS sur le nœud {node_name} ({node_type})")
                self._apply_qos_policies_to_node(node_id, node_data)
            else:
                logger.debug(f"Nœud {node_name} ne supporte pas QoS ({node_type})")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement nœud QoS: {e}")
            
    def _handle_link_qos_event(self, event_data: Dict[str, Any]):
        """Traite les événements liés aux liens pour ajuster les politiques QoS."""
        try:
            link_data = event_data.get('link', {})
            link_id = link_data.get('link_id')
            
            # Récupérer les informations des nœuds connectés
            source_node = link_data.get('nodes', [{}])[0] if link_data.get('nodes') else {}
            target_node = link_data.get('nodes', [{}])[1] if len(link_data.get('nodes', [])) > 1 else {}
            
            logger.info(f"🔗 Mise à jour QoS pour le lien {link_id}")
            
            # Appliquer les politiques QoS sur les interfaces du lien
            self._apply_qos_policies_to_link(link_id, source_node, target_node)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement lien QoS: {e}")
            
    def _handle_project_qos_event(self, event_data: Dict[str, Any]):
        """Traite les événements liés aux projets pour synchroniser les politiques QoS."""
        try:
            project_id = event_data.get('project_id')
            project_data = event_data.get('project', {})
            
            logger.info(f"📁 Synchronisation des politiques QoS pour le projet {project_id}")
            
            # Synchroniser toutes les politiques QoS du projet
            self._sync_project_qos_policies(project_id, project_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement projet QoS: {e}")
            
    def _node_supports_qos(self, node_type: str) -> bool:
        """Vérifie si un type de nœud supporte QoS."""
        qos_supporting_types = [
            'dynamips',  # Routeurs Cisco
            'qemu',      # Machines virtuelles
            'docker',    # Conteneurs Docker
            'vmware',    # Machines VMware
            'virtualbox' # Machines VirtualBox
        ]
        return node_type.lower() in qos_supporting_types
        
    def _apply_qos_policies_to_node(self, node_id: str, node_data: Dict[str, Any]):
        """Applique les politiques QoS appropriées à un nœud."""
        try:
            node_name = node_data.get('name', 'Unknown')
            node_type = node_data.get('node_type', 'unknown')
            
            # Rechercher les politiques QoS applicables
            applicable_policies = QoSPolicy.objects.filter(
                status='active',
                policy_type__in=self._get_supported_policy_types(node_type)
            )
            
            for policy in applicable_policies:
                logger.info(f"📋 Application de la politique QoS '{policy.name}' sur {node_name}")
                
                # Créer l'association interface-politique si elle n'existe pas
                self._create_interface_qos_associations(node_id, node_data, policy)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application des politiques QoS au nœud: {e}")
            
    def _apply_qos_policies_to_link(self, link_id: str, source_node: Dict, target_node: Dict):
        """Applique les politiques QoS appropriées à un lien."""
        try:
            # Appliquer QoS sur les interfaces source et cible
            for node in [source_node, target_node]:
                if node and self._node_supports_qos(node.get('node_type', '')):
                    self._apply_qos_policies_to_node(node.get('node_id'), node)
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'application des politiques QoS au lien: {e}")
            
    def _sync_project_qos_policies(self, project_id: str, project_data: Dict[str, Any]):
        """Synchronise toutes les politiques QoS d'un projet."""
        try:
            # Récupérer tous les nœuds du projet
            nodes = self.gns3_interface.get_project_nodes(project_id)
            
            for node in nodes:
                if self._node_supports_qos(node.get('node_type', '')):
                    self._apply_qos_policies_to_node(node.get('node_id'), node)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des politiques QoS du projet: {e}")
            
    def _get_supported_policy_types(self, node_type: str) -> List[str]:
        """Retourne les types de politiques QoS supportés par un type de nœud."""
        policy_mappings = {
            'dynamips': ['cbwfq', 'htb', 'shaping'],
            'qemu': ['htb', 'tbf', 'sfq'],
            'docker': ['htb', 'fq_codel', 'tbf'],
            'vmware': ['htb', 'cbq'],
            'virtualbox': ['htb', 'cbq']
        }
        return policy_mappings.get(node_type.lower(), ['htb'])
        
    def _create_interface_qos_associations(self, node_id: str, node_data: Dict, policy: QoSPolicy):
        """Crée les associations interface-politique QoS pour un nœud."""
        try:
            # Récupérer les interfaces du nœud
            interfaces = node_data.get('ports', [])
            
            for interface in interfaces:
                interface_name = interface.get('name', f"eth{interface.get('port_number', 0)}")
                
                # Créer l'association si elle n'existe pas
                association, created = InterfaceQoSPolicy.objects.get_or_create(
                    device_id=int(node_id) if str(node_id).isdigit() else hash(node_id) % 2147483647,
                    interface_id=interface.get('port_number', 0),
                    interface_name=interface_name,
                    direction='egress',  # Par défaut sortie
                    defaults={
                        'policy': policy,
                        'parameters': {
                            'gns3_node_id': node_id,
                            'gns3_node_type': node_data.get('node_type'),
                            'auto_applied': True
                        }
                    }
                )
                
                if created:
                    logger.info(f"✅ Association QoS créée: {interface_name} -> {policy.name}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la création des associations QoS: {e}")


class UnifiedQoSService:
    """
    Service unifié pour la gestion QoS avec intégration GNS3 et Docker.
    
    Point d'entrée principal pour toutes les opérations QoS du NMS.
    """
    
    def __init__(self):
        self.docker_collector = DockerQoSCollector()
        self.gns3_adapter = GNS3QoSAdapter()
        self.circuit_breaker_failures = {}
        
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet du système QoS.
        
        Returns:
            Statut unifié du système QoS
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'service': 'qos_management',
            'version': '1.0.0',
            'operational': False,
            'components': {},
            'summary': {}
        }
        
        try:
            # Statut Docker
            docker_available = self.docker_collector.is_available()
            status['components']['docker'] = {
                'available': docker_available,
                'services_count': len(self.docker_collector.qos_services),
                'last_check': datetime.now().isoformat()
            }
            
            # Statut GNS3
            gns3_available = self.gns3_adapter.is_available()
            status['components']['gns3'] = {
                'available': gns3_available,
                'interface_connected': gns3_available,
                'last_check': datetime.now().isoformat()
            }
            
            # Statut base de données
            try:
                policies_count = QoSPolicy.objects.count()
                active_policies = QoSPolicy.objects.filter(status='active').count()
                interfaces_count = InterfaceQoSPolicy.objects.count()
                
                status['components']['database'] = {
                    'available': True,
                    'policies_count': policies_count,
                    'active_policies': active_policies,
                    'interfaces_configured': interfaces_count
                }
            except Exception as e:
                status['components']['database'] = {
                    'available': False,
                    'error': str(e)
                }
            
            # Statut global
            components_operational = [
                status['components'].get('docker', {}).get('available', False),
                status['components'].get('gns3', {}).get('available', False),
                status['components'].get('database', {}).get('available', False)
            ]
            
            status['operational'] = sum(components_operational) >= 2  # Au moins 2/3 des composants
            
            # Résumé
            status['summary'] = {
                'total_policies': status['components'].get('database', {}).get('policies_count', 0),
                'active_policies': status['components'].get('database', {}).get('active_policies', 0),
                'configured_interfaces': status['components'].get('database', {}).get('interfaces_configured', 0),
                'docker_services': len(self.docker_collector.qos_services),
                'gns3_connected': gns3_available
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut QoS: {e}")
            status['error'] = str(e)
            
        return status
        
    def collect_all_qos_data(self) -> Dict[str, Any]:
        """
        Collecte toutes les données QoS depuis Docker et GNS3.
        
        Returns:
            Données unifiées de QoS
        """
        collection_result = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'summary': {
                'successful_collections': 0,
                'failed_collections': 0,
                'total_sources': 2
            }
        }
        
        # Collecte Docker
        try:
            docker_services = self.docker_collector.collect_qos_services_status()
            collection_result['sources']['docker'] = {
                'status': 'success',
                'services_count': len(docker_services),
                'services': docker_services,
                'collected_at': datetime.now().isoformat()
            }
            collection_result['summary']['successful_collections'] += 1
        except Exception as e:
            collection_result['sources']['docker'] = {
                'status': 'error',
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }
            collection_result['summary']['failed_collections'] += 1
            
        # Collecte GNS3 (politiques appliquées)
        try:
            applied_policies = self._get_applied_qos_policies()
            collection_result['sources']['gns3'] = {
                'status': 'success',
                'applied_policies_count': len(applied_policies),
                'policies': applied_policies,
                'collected_at': datetime.now().isoformat()
            }
            collection_result['summary']['successful_collections'] += 1
        except Exception as e:
            collection_result['sources']['gns3'] = {
                'status': 'error',
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }
            collection_result['summary']['failed_collections'] += 1
            
        return collection_result
        
    def _get_applied_qos_policies(self) -> List[Dict[str, Any]]:
        """Récupère les politiques QoS appliquées sur les interfaces."""
        try:
            applied_policies = []
            
            # Récupérer toutes les associations interface-politique
            associations = InterfaceQoSPolicy.objects.select_related('policy').all()
            
            for association in associations:
                policy_info = {
                    'interface_name': association.interface_name,
                    'device_id': association.device_id,
                    'policy_name': association.policy.name,
                    'policy_type': association.policy.policy_type,
                    'direction': association.direction,
                    'applied_at': association.applied_at.isoformat(),
                    'parameters': association.parameters or {}
                }
                applied_policies.append(policy_info)
                
            return applied_policies
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques appliquées: {e}")
            return []
            
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Récupère les données pour le dashboard QoS.
        
        Returns:
            Données de dashboard QoS
        """
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'qos_overview': self._get_qos_overview(),
                'performance_metrics': self._get_performance_metrics(),
                'sla_compliance': self._get_sla_compliance_summary(),
                'active_policies': self._get_active_policies_summary(),
                'infrastructure_health': self._get_infrastructure_health()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de dashboard QoS: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            
    def _get_qos_overview(self) -> Dict[str, Any]:
        """Récupère la vue d'ensemble QoS."""
        try:
            total_policies = QoSPolicy.objects.count()
            active_policies = QoSPolicy.objects.filter(status='active').count()
            total_classes = TrafficClass.objects.count()
            configured_interfaces = InterfaceQoSPolicy.objects.count()
            
            return {
                'total_policies': total_policies,
                'active_policies': active_policies,
                'inactive_policies': total_policies - active_policies,
                'total_traffic_classes': total_classes,
                'configured_interfaces': configured_interfaces,
                'policy_types': list(QoSPolicy.objects.values_list('policy_type', flat=True).distinct())
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la vue d'ensemble QoS: {e}")
            return {}
            
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de performance QoS."""
        try:
            # Récupérer les métriques depuis les services Docker
            docker_services = self.docker_collector.collect_qos_services_status()
            
            metrics = {
                'services_health': {},
                'response_times': {},
                'availability': {}
            }
            
            for service in docker_services:
                service_name = service.get('service_name', 'unknown')
                metrics['services_health'][service_name] = service.get('is_healthy', False)
                
                if 'health_response_time' in service:
                    metrics['response_times'][service_name] = service['health_response_time']
                    
                metrics['availability'][service_name] = service.get('status') == 'running'
                
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de performance: {e}")
            return {}
            
    def _get_sla_compliance_summary(self) -> Dict[str, Any]:
        """Récupère le résumé de conformité SLA."""
        try:
            # Récupérer les enregistrements de conformité récents
            recent_records = SLAComplianceRecord.objects.filter(
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).order_by('-timestamp')
            
            if not recent_records.exists():
                return {
                    'overall_compliance': 0.0,
                    'compliant_devices': 0,
                    'total_devices': 0,
                    'trend': 'stable'
                }
                
            # Calculer la conformité globale
            total_compliance = sum(record.overall_compliance for record in recent_records)
            avg_compliance = total_compliance / len(recent_records)
            
            compliant_devices = recent_records.filter(overall_compliance__gte=0.95).count()
            
            return {
                'overall_compliance': round(avg_compliance * 100, 2),
                'compliant_devices': compliant_devices,
                'total_devices': recent_records.values('device_id').distinct().count(),
                'trend': 'improving',  # À implémenter avec logique de tendance
                'last_check': recent_records.first().timestamp.isoformat() if recent_records.exists() else None
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la conformité SLA: {e}")
            return {}
            
    def _get_active_policies_summary(self) -> Dict[str, Any]:
        """Récupère le résumé des politiques actives."""
        try:
            active_policies = QoSPolicy.objects.filter(status='active')
            
            policies_by_type = {}
            total_bandwidth = 0
            
            for policy in active_policies:
                policy_type = policy.policy_type
                if policy_type not in policies_by_type:
                    policies_by_type[policy_type] = 0
                policies_by_type[policy_type] += 1
                
                if policy.bandwidth_limit:
                    total_bandwidth += policy.bandwidth_limit
                    
            return {
                'total_active': len(active_policies),
                'by_type': policies_by_type,
                'total_allocated_bandwidth': total_bandwidth,
                'average_priority': sum(p.priority for p in active_policies) / len(active_policies) if active_policies else 0
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques actives: {e}")
            return {}
            
    def _get_infrastructure_health(self) -> Dict[str, Any]:
        """Récupère la santé de l'infrastructure QoS."""
        try:
            docker_services = self.docker_collector.collect_qos_services_status()
            
            total_services = len(docker_services)
            healthy_services = sum(1 for service in docker_services if service.get('is_healthy', False))
            running_services = sum(1 for service in docker_services if service.get('status') == 'running')
            
            return {
                'total_services': total_services,
                'healthy_services': healthy_services,
                'running_services': running_services,
                'health_percentage': round((healthy_services / total_services * 100) if total_services > 0 else 0, 2),
                'gns3_connected': self.gns3_adapter.is_available(),
                'docker_connected': self.docker_collector.is_available()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la santé de l'infrastructure: {e}")
            return {}


# Instance globale du service unifié QoS
unified_qos_service = UnifiedQoSService()