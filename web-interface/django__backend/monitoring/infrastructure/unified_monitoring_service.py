"""
Service unifié d'intégration Monitoring avec GNS3 Central et Docker.

Ce service modernise l'intégration du module monitoring en utilisant :
- Le nouveau Service Central GNS3 
- L'intégration Docker pour le monitoring des conteneurs
- Une architecture événementielle unifiée
- La gestion des métriques temps réel

Architecture Développeur Senior :
- Séparation claire des responsabilités (GNS3/Docker/Alerting)
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

from common.api.gns3_module_interface import create_gns3_interface
from common.infrastructure.gns3_central_service import GNS3EventType
from ..models import Alert, DeviceMetric, MetricValue, ServiceCheck, DeviceServiceCheck

logger = logging.getLogger(__name__)


class DockerMetricsCollector:
    """
    Collecteur de métriques Docker spécialisé pour l'infrastructure NMS.
    
    Responsabilités :
    - Connexion au daemon Docker
    - Collecte de métriques des conteneurs NMS spécialisés
    - Intégration avec Prometheus, Netdata, ntopng, etc.
    - Transformation en format standardisé
    """
    
    def __init__(self):
        self.client = None
        # Services Docker NMS à surveiller (basé sur docker-compose)
        self.nms_services = {
            # Services de monitoring
            'nms-prometheus': {'port': 9090, 'health_endpoint': '/-/healthy', 'type': 'monitoring'},
            'nms-grafana': {'port': 3001, 'health_endpoint': '/api/health', 'type': 'monitoring'},
            'nms-netdata': {'port': 19999, 'health_endpoint': '/api/v1/info', 'type': 'monitoring'},
            'nms-ntopng': {'port': 3000, 'health_endpoint': '/', 'type': 'network_monitoring'},
            'nms-haproxy': {'port': 1936, 'health_endpoint': '/stats', 'type': 'load_balancer'},
            
            # Services de base
            'nms-postgres': {'port': 5432, 'health_endpoint': None, 'type': 'database'},
            'nms-redis': {'port': 6379, 'health_endpoint': None, 'type': 'cache'},
            'nms-elasticsearch': {'port': 9200, 'health_endpoint': '/_cluster/health', 'type': 'search'},
            
            # Services applicatifs
            'nms-django': {'port': 8000, 'health_endpoint': '/api/common/api/v1/integration/health/', 'type': 'application'},
            'nms-celery': {'port': None, 'health_endpoint': None, 'type': 'task_queue'},
            
            # Services de sécurité
            'nms-suricata': {'port': 8068, 'health_endpoint': None, 'type': 'security'},
            'nms-fail2ban': {'port': 5001, 'health_endpoint': None, 'type': 'security'},
            'nms-kibana': {'port': 5601, 'health_endpoint': '/api/status', 'type': 'visualization'},
            
            # Services réseau
            'nms-snmp-agent': {'port': 161, 'health_endpoint': None, 'type': 'network_protocol'},
            'nms-netflow-collector': {'port': 9995, 'health_endpoint': '/health', 'type': 'network_collector'}
        }
        self._initialize_docker_client()
        
    def _initialize_docker_client(self):
        """Initialise le client Docker avec gestion d'erreurs."""
        try:
            self.client = docker.from_env()
            # Test de connectivité
            self.client.ping()
            logger.info("✅ Connexion Docker établie avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion Docker: {e}")
            self.client = None
            
    def is_available(self) -> bool:
        """Vérifie si Docker est disponible."""
        return self.client is not None
        
    def collect_nms_services_metrics(self) -> List[Dict[str, Any]]:
        """
        Collecte les métriques des services NMS Docker.
        
        Returns:
            Liste des métriques des services NMS
        """
        if not self.is_available():
            logger.warning("Docker non disponible pour la collecte de métriques NMS")
            return []
            
        metrics = []
        
        try:
            for service_name, service_config in self.nms_services.items():
                container_metrics = self._collect_service_metrics(service_name, service_config)
                if container_metrics:
                    metrics.append(container_metrics)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques NMS: {e}")
            
        logger.info(f"📊 Collecté les métriques de {len(metrics)} services NMS")
        return metrics
        
    def collect_container_metrics(self, container_name_pattern: str = None) -> List[Dict[str, Any]]:
        """
        Collecte les métriques des conteneurs Docker (méthode générique).
        
        Args:
            container_name_pattern: Pattern de filtrage des conteneurs
            
        Returns:
            Liste des métriques collectées
        """
        if not self.is_available():
            logger.warning("Docker non disponible pour la collecte de métriques")
            return []
            
        metrics = []
        
        try:
            containers = self.client.containers.list(all=True)
            
            for container in containers:
                # Filtrage par pattern si spécifié
                if container_name_pattern and container_name_pattern not in container.name:
                    continue
                    
                container_metrics = self._extract_container_metrics(container)
                if container_metrics:
                    metrics.append(container_metrics)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques Docker: {e}")
            
        logger.info(f"📊 Collecté les métriques de {len(metrics)} conteneurs Docker")
        return metrics
        
    def _extract_container_metrics(self, container) -> Optional[Dict[str, Any]]:
        """
        Extrait les métriques d'un conteneur spécifique.
        
        Args:
            container: Objet conteneur Docker
            
        Returns:
            Métriques du conteneur ou None si erreur
        """
        try:
            # Informations de base
            container_info = {
                'name': container.name,
                'id': container.short_id,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created_at': container.attrs['Created'],
                'timestamp': timezone.now().isoformat()
            }
            
            # Métriques de performance si le conteneur est en cours d'exécution
            if container.status == 'running':
                try:
                    stats = container.stats(stream=False)
                    container_info.update(self._parse_container_stats(stats))
                except Exception as e:
                    logger.warning(f"Impossible de récupérer les stats du conteneur {container.name}: {e}")
                    container_info.update({
                        'cpu_percent': 0,
                        'memory_usage_mb': 0,
                        'memory_limit_mb': 0,
                        'memory_percent': 0,
                        'network_rx_bytes': 0,
                        'network_tx_bytes': 0
                    })
            else:
                # Conteneur arrêté
                container_info.update({
                    'cpu_percent': 0,
                    'memory_usage_mb': 0,
                    'memory_limit_mb': 0,
                    'memory_percent': 0,
                    'network_rx_bytes': 0,
                    'network_tx_bytes': 0
                })
                
            return container_info
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des métriques pour {container.name}: {e}")
            return None
            
    def _parse_container_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse les statistiques Docker en métriques standardisées.
        
        Args:
            stats: Statistiques brutes du conteneur
            
        Returns:
            Métriques parsées
        """
        parsed_metrics = {}
        
        try:
            # CPU
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          precpu_stats.get('system_cpu_usage', 0)
            
            num_cpus = len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', []))
            if num_cpus == 0:
                num_cpus = 1
                
            cpu_percent = 0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100
                
            parsed_metrics['cpu_percent'] = round(cpu_percent, 2)
            
            # Mémoire
            memory_stats = stats.get('memory_stats', {})
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            
            parsed_metrics['memory_usage_mb'] = round(memory_usage / (1024 * 1024), 2)
            parsed_metrics['memory_limit_mb'] = round(memory_limit / (1024 * 1024), 2)
            
            memory_percent = 0
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100
            parsed_metrics['memory_percent'] = round(memory_percent, 2)
            
            # Réseau
            networks = stats.get('networks', {})
            total_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
            total_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
            
            parsed_metrics['network_rx_bytes'] = total_rx
            parsed_metrics['network_tx_bytes'] = total_tx
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing des stats: {e}")
            
        return parsed_metrics
        
    def _collect_service_metrics(self, service_name: str, service_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Collecte les métriques d'un service NMS spécifique.
        
        Args:
            service_name: Nom du service NMS
            service_config: Configuration du service
            
        Returns:
            Métriques du service ou None
        """
        try:
            # Recherche du conteneur par nom exact
            containers = self.client.containers.list(all=True, filters={'name': service_name})
            
            if not containers:
                logger.warning(f"Service {service_name} non trouvé")
                return None
                
            container = containers[0]
            
            # Métriques de base
            service_metrics = {
                'service_name': service_name,
                'service_type': service_config.get('type'),
                'container_id': container.short_id,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'port': service_config.get('port'),
                'health_endpoint': service_config.get('health_endpoint'),
                'timestamp': timezone.now().isoformat()
            }
            
            # Métriques de performance si en cours d'exécution
            if container.status == 'running':
                try:
                    stats = container.stats(stream=False)
                    service_metrics.update(self._parse_container_stats(stats))
                    
                    # Vérification de santé spécialisée
                    if service_config.get('health_endpoint'):
                        service_metrics['health_status'] = self._check_service_health(
                            service_name, service_config
                        )
                        
                except Exception as e:
                    logger.warning(f"Impossible de récupérer les stats du service {service_name}: {e}")
                    service_metrics.update(self._get_default_metrics())
            else:
                service_metrics.update(self._get_default_metrics())
                service_metrics['health_status'] = 'container_stopped'
                
            return service_metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques pour {service_name}: {e}")
            return None
            
    def _check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> str:
        """
        Vérifie la santé d'un service via son endpoint.
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
            
        Returns:
            Statut de santé du service
        """
        try:
            import requests
            
            port = service_config.get('port')
            health_endpoint = service_config.get('health_endpoint')
            
            if not port or not health_endpoint:
                return 'health_check_unavailable'
                
            # Construction de l'URL de santé
            health_url = f"http://localhost:{port}{health_endpoint}"
            
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                return 'healthy'
            else:
                return f'unhealthy_http_{response.status_code}'
                
        except requests.exceptions.RequestException as e:
            logger.debug(f"Health check échoué pour {service_name}: {e}")
            return 'health_check_failed'
        except Exception as e:
            logger.error(f"Erreur lors du health check de {service_name}: {e}")
            return 'health_check_error'
            
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Retourne des métriques par défaut pour les services arrêtés."""
        return {
            'cpu_percent': 0,
            'memory_usage_mb': 0,
            'memory_limit_mb': 0,
            'memory_percent': 0,
            'network_rx_bytes': 0,
            'network_tx_bytes': 0
        }
        
    def get_nms_services_health(self) -> Dict[str, Any]:
        """
        Vérifie la santé de tous les services NMS.
        
        Returns:
            Statut de santé détaillé des services NMS
        """
        if not self.is_available():
            return {'status': 'docker_unavailable', 'reason': 'Docker daemon non accessible'}
            
        health_status = {
            'status': 'healthy',
            'services': {},
            'summary': {
                'total_services': 0,
                'running_services': 0,
                'stopped_services': 0,
                'critical_services_down': 0
            },
            'timestamp': timezone.now().isoformat()
        }
        
        try:
            for service_name, service_config in self.nms_services.items():
                service_health = self._get_service_health_detail(service_name, service_config)
                health_status['services'][service_name] = service_health
                
                health_status['summary']['total_services'] += 1
                
                if service_health['container_status'] == 'running':
                    health_status['summary']['running_services'] += 1
                else:
                    health_status['summary']['stopped_services'] += 1
                    
                    # Vérifier si c'est un service critique
                    if service_name in getattr(self, 'critical_services', []):
                        health_status['summary']['critical_services_down'] += 1
                        
            # Déterminer le statut global
            if health_status['summary']['critical_services_down'] > 0:
                health_status['status'] = 'critical'
            elif health_status['summary']['stopped_services'] > health_status['summary']['running_services']:
                health_status['status'] = 'degraded'
            elif health_status['summary']['stopped_services'] > 0:
                health_status['status'] = 'warning'
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé des services NMS: {e}")
            health_status['status'] = 'error'
            health_status['error'] = str(e)
            
        return health_status
        
    def _get_service_health_detail(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les détails de santé d'un service.
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
            
        Returns:
            Détails de santé du service
        """
        service_detail = {
            'service_type': service_config.get('type'),
            'container_status': 'not_found',
            'health_status': 'unknown',
            'port': service_config.get('port'),
            'critical': service_name in getattr(self, 'critical_services', [])
        }
        
        try:
            containers = self.client.containers.list(all=True, filters={'name': service_name})
            
            if containers:
                container = containers[0]
                service_detail['container_status'] = container.status
                service_detail['image'] = container.image.tags[0] if container.image.tags else 'unknown'
                
                if container.status == 'running' and service_config.get('health_endpoint'):
                    service_detail['health_status'] = self._check_service_health(service_name, service_config)
                elif container.status == 'running':
                    service_detail['health_status'] = 'running_no_health_check'
                else:
                    service_detail['health_status'] = 'container_not_running'
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de {service_name}: {e}")
            service_detail['health_status'] = 'check_error'
            service_detail['error'] = str(e)
            
        return service_detail
    
    def get_service_health(self, service_patterns: List[str]) -> Dict[str, Any]:
        """
        Vérifie la santé des services Docker.
        
        Args:
            service_patterns: Liste des patterns de services à vérifier
            
        Returns:
            Statut de santé des services
        """
        if not self.is_available():
            return {'status': 'unavailable', 'reason': 'Docker non disponible'}
            
        health_status = {
            'status': 'healthy',
            'services': {},
            'total_services': 0,
            'healthy_services': 0,
            'unhealthy_services': 0,
            'timestamp': timezone.now().isoformat()
        }
        
        try:
            for pattern in service_patterns:
                containers = self.client.containers.list(all=True, filters={'name': pattern})
                
                for container in containers:
                    service_name = container.name
                    is_healthy = container.status == 'running'
                    
                    health_status['services'][service_name] = {
                        'status': container.status,
                        'healthy': is_healthy,
                        'image': container.image.tags[0] if container.image.tags else 'unknown'
                    }
                    
                    health_status['total_services'] += 1
                    if is_healthy:
                        health_status['healthy_services'] += 1
                    else:
                        health_status['unhealthy_services'] += 1
                        
            # Déterminer le statut global
            if health_status['total_services'] == 0:
                health_status['status'] = 'no_services'
            elif health_status['unhealthy_services'] > 0:
                unhealthy_ratio = health_status['unhealthy_services'] / health_status['total_services']
                if unhealthy_ratio > 0.5:
                    health_status['status'] = 'critical'
                else:
                    health_status['status'] = 'warning'
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé des services: {e}")
            health_status['status'] = 'error'
            health_status['error'] = str(e)
            
        return health_status


class GNS3MonitoringAdapter:
    """
    Adaptateur pour l'intégration avec le Service Central GNS3.
    
    Responsabilités :
    - Interface avec le nouveau Service Central GNS3
    - Gestion des événements GNS3
    - Transformation des données topologiques
    """
    
    def __init__(self):
        self.gns3_interface = None
        self.monitored_nodes = {}
        self.event_handlers = {}
        self._initialize_gns3_interface()
        
    def _initialize_gns3_interface(self):
        """Initialise l'interface GNS3 via le Service Central."""
        try:
            self.gns3_interface = create_gns3_interface("monitoring")
            
            # S'abonner aux événements GNS3 pertinents pour le monitoring
            gns3_events = [
                'node_started',
                'node_stopped', 
                'node_suspended',
                'topology_changed',
                'node_created',
                'node_deleted'
            ]
            
            self.gns3_interface.subscribe_to_events(gns3_events, self._handle_gns3_event)
            logger.info("✅ Interface GNS3 Central initialisée pour le monitoring")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de l'interface GNS3: {e}")
            self.gns3_interface = None
            
    def is_available(self) -> bool:
        """Vérifie si l'interface GNS3 est disponible."""
        return self.gns3_interface is not None
        
    def _handle_gns3_event(self, event: Dict[str, Any]):
        """
        Gestionnaire unifié des événements GNS3.
        
        Args:
            event: Données de l'événement GNS3
        """
        event_type = event.get('type')
        node_data = event.get('data', {})
        
        logger.info(f"📡 Événement GNS3 reçu: {event_type}")
        
        try:
            if event_type == 'node_started':
                self._handle_node_started(node_data)
            elif event_type == 'node_stopped':
                self._handle_node_stopped(node_data)
            elif event_type == 'node_suspended':
                self._handle_node_suspended(node_data)
            elif event_type == 'topology_changed':
                self._handle_topology_changed(node_data)
            elif event_type in ['node_created', 'node_deleted']:
                self._handle_node_lifecycle(event_type, node_data)
                
            # Déclencher les handlers personnalisés
            for handler in self.event_handlers.get(event_type, []):
                handler(event)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement {event_type}: {e}")
            
    def _handle_node_started(self, node_data: Dict[str, Any]):
        """Traite le démarrage d'un nœud."""
        node_id = node_data.get('node_id')
        if node_id:
            self._update_node_monitoring_status(node_id, 'running')
            
    def _handle_node_stopped(self, node_data: Dict[str, Any]):
        """Traite l'arrêt d'un nœud."""
        node_id = node_data.get('node_id')
        if node_id:
            self._update_node_monitoring_status(node_id, 'stopped')
            
    def _handle_node_suspended(self, node_data: Dict[str, Any]):
        """Traite la suspension d'un nœud."""
        node_id = node_data.get('node_id')
        if node_id:
            self._update_node_monitoring_status(node_id, 'suspended')
            
    def _handle_topology_changed(self, topology_data: Dict[str, Any]):
        """Traite un changement de topologie."""
        logger.info("🗺️  Topologie GNS3 modifiée - Mise à jour du monitoring")
        self._refresh_monitored_nodes()
        
    def _handle_node_lifecycle(self, event_type: str, node_data: Dict[str, Any]):
        """Traite les événements de cycle de vie des nœuds."""
        node_id = node_data.get('node_id')
        if event_type == 'node_created':
            self._add_node_to_monitoring(node_data)
        elif event_type == 'node_deleted':
            self._remove_node_from_monitoring(node_id)
            
    def _add_node_to_monitoring(self, node_data: Dict[str, Any]):
        """Ajoute un nœud à la surveillance."""
        node_id = node_data.get('node_id')
        if node_id:
            logger.info(f"➕ Nœud {node_id} ajouté à la surveillance")
            
    def _remove_node_from_monitoring(self, node_id: str):
        """Retire un nœud de la surveillance."""
        if node_id and node_id in self.monitored_nodes:
            del self.monitored_nodes[node_id]
            logger.info(f"➖ Nœud {node_id} retiré de la surveillance")
            
    def _update_node_monitoring_status(self, node_id: str, status: str):
        """Met à jour le statut de monitoring d'un nœud."""
        if node_id in self.monitored_nodes:
            old_status = self.monitored_nodes[node_id].get('status')
            self.monitored_nodes[node_id]['status'] = status
            self.monitored_nodes[node_id]['last_update'] = timezone.now()
            
            logger.info(f"🔄 Nœud {node_id}: {old_status} → {status}")
            
    def _refresh_monitored_nodes(self):
        """Rafraîchit la liste des nœuds surveillés."""
        if not self.is_available():
            return
            
        try:
            topology = self.gns3_interface.get_complete_topology()
            if topology:
                self._update_monitored_nodes_from_topology(topology)
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement des nœuds surveillés: {e}")
            
    def _update_monitored_nodes_from_topology(self, topology: Dict[str, Any]):
        """Met à jour les nœuds surveillés depuis la topologie."""
        new_monitored_nodes = {}
        
        for project_id, project_data in topology.get('projects', {}).items():
            for node_id, node_data in project_data.get('nodes', {}).items():
                monitoring_config = self._get_monitoring_config_for_node_type(
                    node_data.get('node_type')
                )
                
                if monitoring_config:
                    new_monitored_nodes[node_id] = {
                        'node_id': node_id,
                        'name': node_data.get('name'),
                        'type': node_data.get('node_type'),
                        'project_id': project_id,
                        'status': node_data.get('status'),
                        'monitoring_config': monitoring_config,
                        'last_update': timezone.now()
                    }
                    
        self.monitored_nodes = new_monitored_nodes
        logger.info(f"📊 Surveillance mise à jour: {len(self.monitored_nodes)} nœuds")
        
    def _get_monitoring_config_for_node_type(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Récupère la configuration de monitoring pour un type de nœud."""
        monitoring_configs = {
            'qemu': {
                'metrics': ['cpu_usage', 'memory_usage', 'disk_io', 'network_io'],
                'check_interval': 30,
                'thresholds': {'cpu_usage': 80, 'memory_usage': 85}
            },
            'docker': {
                'metrics': ['cpu_usage', 'memory_usage', 'network_io', 'container_status'],
                'check_interval': 20,
                'thresholds': {'cpu_usage': 75, 'memory_usage': 80}
            },
            'dynamips': {
                'metrics': ['interface_status', 'cpu_usage', 'routing_table'],
                'check_interval': 60,
                'thresholds': {'cpu_usage': 70}
            }
        }
        
        return monitoring_configs.get(node_type)
        
    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Enregistre un gestionnaire d'événements personnalisé."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def get_monitored_nodes_summary(self) -> Dict[str, Any]:
        """Récupère un résumé des nœuds surveillés."""
        if not self.monitored_nodes:
            return {'total': 0, 'by_status': {}, 'by_type': {}}
            
        summary = {
            'total': len(self.monitored_nodes),
            'by_status': {},
            'by_type': {},
            'last_update': timezone.now().isoformat()
        }
        
        for node in self.monitored_nodes.values():
            status = node.get('status', 'unknown')
            node_type = node.get('type', 'unknown')
            
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            summary['by_type'][node_type] = summary['by_type'].get(node_type, 0) + 1
            
        return summary


class UnifiedMonitoringService:
    """
    Service unifié de monitoring intégrant GNS3 Central et Docker.
    
    Architecture Développeur Senior :
    - Façade unifiée pour toutes les opérations de monitoring
    - Intégration transparente GNS3 + Docker
    - Gestion d'événements asynchrone
    - Interface simplifiée pour les use cases
    """
    
    def __init__(self):
        self.gns3_adapter = GNS3MonitoringAdapter()
        self.docker_collector = DockerMetricsCollector()
        self.alert_handlers = []
        self.metric_processors = []
        
        # Initialisation sécurisée
        self.monitored_docker_services = []
        try:
            # Configuration des services Docker NMS à surveiller
            self.monitored_docker_services = list(self.docker_collector.nms_services.keys())
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des services Docker: {e}")
            self.monitored_docker_services = []
        
        # Services critiques pour le monitoring
        self.critical_services = [
            'nms-prometheus', 'nms-grafana', 'nms-netdata', 'nms-django', 
            'nms-postgres', 'nms-redis', 'nms-elasticsearch'
        ]
        
        # Endpoints spécialisés pour intégration
        self.service_endpoints = {
            'prometheus': 'http://nms-prometheus:9090',
            'grafana': 'http://nms-grafana:3000', 
            'netdata': 'http://nms-netdata:19999',
            'ntopng': 'http://nms-ntopng:3000',
            'elasticsearch': 'http://nms-elasticsearch:9200',
            'kibana': 'http://nms-kibana:5601'
        }
        
        logger.info("🚀 Service Unifié de Monitoring initialisé")
        
    def is_fully_operational(self) -> bool:
        """Vérifie si tous les composants sont opérationnels."""
        return self.gns3_adapter.is_available() and self.docker_collector.is_available()
        
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Récupère un statut complet du monitoring.
        
        Returns:
            Statut détaillé de tous les composants
        """
        status = {
            'service_name': 'Unified Monitoring Service',
            'operational': self.is_fully_operational(),
            'timestamp': timezone.now().isoformat(),
            'components': {
                'gns3_integration': {
                    'available': self.gns3_adapter.is_available(),
                    'monitored_nodes': len(self.gns3_adapter.monitored_nodes)
                },
                'docker_integration': {
                    'available': self.docker_collector.is_available(),
                    'monitored_services': len(self.monitored_docker_services)
                }
            }
        }
        
        # Ajouter les statistiques GNS3
        if self.gns3_adapter.is_available():
            status['gns3_summary'] = self.gns3_adapter.get_monitored_nodes_summary()
            
        # Ajouter le statut Docker
        if self.docker_collector.is_available():
            status['docker_health'] = self.docker_collector.get_service_health(
                self.monitored_docker_services
            )
            
        return status
        
    def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collecte toutes les métriques (GNS3 + Docker).
        
        Returns:
            Métriques consolidées
        """
        metrics = {
            'collection_time': timezone.now().isoformat(),
            'gns3_metrics': {},
            'docker_metrics': [],
            'summary': {
                'total_sources': 0,
                'successful_collections': 0,
                'failed_collections': 0
            }
        }
        
        # Métriques GNS3
        if self.gns3_adapter.is_available():
            try:
                gns3_summary = self.gns3_adapter.get_monitored_nodes_summary()
                metrics['gns3_metrics'] = gns3_summary
                metrics['summary']['total_sources'] += gns3_summary.get('total', 0)
                metrics['summary']['successful_collections'] += 1
            except Exception as e:
                logger.error(f"Erreur collecte métriques GNS3: {e}")
                metrics['summary']['failed_collections'] += 1
                
        # Métriques Docker NMS
        if self.docker_collector.is_available():
            try:
                # Collecte spécialisée des services NMS
                nms_metrics = self.docker_collector.collect_nms_services_metrics()
                metrics['nms_services_metrics'] = nms_metrics
                metrics['summary']['total_sources'] += len(nms_metrics)
                metrics['summary']['successful_collections'] += 1
                
                # Santé des services NMS
                nms_health = self.docker_collector.get_nms_services_health()
                metrics['nms_services_health'] = nms_health
                
            except Exception as e:
                logger.error(f"Erreur collecte métriques services NMS: {e}")
                metrics['summary']['failed_collections'] += 1
                
        logger.info(f"📊 Collecte terminée: {metrics['summary']['successful_collections']} sources réussies")
        return metrics
        
    def register_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Enregistre un gestionnaire d'alertes."""
        self.alert_handlers.append(handler)
        
    def register_metric_processor(self, processor: Callable[[Dict[str, Any]], None]):
        """Enregistre un processeur de métriques."""
        self.metric_processors.append(processor)
        
    def trigger_alert(self, alert_data: Dict[str, Any]):
        """Déclenche une alerte via tous les handlers enregistrés."""
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Erreur dans le handler d'alerte: {e}")
                
    def process_metrics(self, metrics_data: Dict[str, Any]):
        """Traite les métriques via tous les processeurs enregistrés."""
        for processor in self.metric_processors:
            try:
                processor(metrics_data)
            except Exception as e:
                logger.error(f"Erreur dans le processeur de métriques: {e}")
                
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """
        Récupère les données pour le dashboard de monitoring unifié.
        
        Returns:
            Données complètes du dashboard
        """
        dashboard_data = {
            'overview': self.get_comprehensive_status(),
            'metrics': self.collect_all_metrics(),
            'infrastructure_health': {},
            'alerts_summary': {},
            'performance_indicators': {}
        }
        
        # Ajouter les indicateurs de performance NMS
        if self.docker_collector.is_available():
            dashboard_data['nms_infrastructure_health'] = self.docker_collector.get_nms_services_health()
            
            # Métriques spécialisées par type de service
            dashboard_data['service_metrics_by_type'] = self._organize_metrics_by_service_type(
                dashboard_data['metrics'].get('nms_services_metrics', [])
            )
            
    def _organize_metrics_by_service_type(self, nms_metrics: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organise les métriques par type de service.
        
        Args:
            nms_metrics: Liste des métriques des services NMS
            
        Returns:
            Métriques organisées par type de service
        """
        metrics_by_type = {
            'monitoring': [],
            'database': [],
            'security': [],
            'network': [],
            'application': []
        }
        
        for metric in nms_metrics:
            service_type = metric.get('service_type', 'unknown')
            
            if service_type in ['monitoring', 'network_monitoring', 'visualization']:
                metrics_by_type['monitoring'].append(metric)
            elif service_type in ['database', 'cache', 'search']:
                metrics_by_type['database'].append(metric)
            elif service_type == 'security':
                metrics_by_type['security'].append(metric)
            elif service_type in ['network_protocol', 'network_collector', 'load_balancer']:
                metrics_by_type['network'].append(metric)
            elif service_type in ['application', 'task_queue']:
                metrics_by_type['application'].append(metric)
                
        return metrics_by_type
        
    def get_specialized_service_data(self, service_type: str) -> Dict[str, Any]:
        """
        Récupère des données spécialisées pour un type de service.
        
        Args:
            service_type: Type de service ('monitoring', 'security', etc.)
            
        Returns:
            Données spécialisées du service
        """
        specialized_data = {
            'service_type': service_type,
            'timestamp': timezone.now().isoformat(),
            'services': [],
            'endpoints': {},
            'status': 'unknown'
        }
        
        if not self.docker_collector.is_available():
            specialized_data['status'] = 'docker_unavailable'
            return specialized_data
            
        # Filtrer les services par type
        relevant_services = {
            name: config for name, config in self.docker_collector.nms_services.items()
            if self._service_matches_type(config.get('type'), service_type)
        }
        
        if not relevant_services:
            specialized_data['status'] = 'no_services_found'
            return specialized_data
            
        # Collecter les données spécialisées
        for service_name, service_config in relevant_services.items():
            service_data = self.docker_collector._collect_service_metrics(service_name, service_config)
            if service_data:
                specialized_data['services'].append(service_data)
                
                # Ajouter les endpoints d'accès
                if service_config.get('port'):
                    specialized_data['endpoints'][service_name] = f"http://localhost:{service_config['port']}"
                    
        # Déterminer le statut global
        running_services = sum(1 for s in specialized_data['services'] if s.get('status') == 'running')
        total_services = len(specialized_data['services'])
        
        if total_services == 0:
            specialized_data['status'] = 'no_services'
        elif running_services == total_services:
            specialized_data['status'] = 'all_healthy'
        elif running_services > 0:
            specialized_data['status'] = 'partially_healthy'
        else:
            specialized_data['status'] = 'all_down'
            
        return specialized_data
        
    def _service_matches_type(self, service_type: str, requested_type: str) -> bool:
        """
        Vérifie si un type de service correspond au type demandé.
        
        Args:
            service_type: Type du service
            requested_type: Type demandé
            
        Returns:
            True si correspondance
        """
        type_mappings = {
            'monitoring': ['monitoring', 'network_monitoring', 'visualization'],
            'security': ['security'],
            'database': ['database', 'cache', 'search'],
            'network': ['network_protocol', 'network_collector', 'load_balancer'],
            'application': ['application', 'task_queue']
        }
        
        return service_type in type_mappings.get(requested_type, [])
            
        return dashboard_data


# Instance singleton du service unifié
unified_monitoring_service = UnifiedMonitoringService()


def get_monitoring_service_endpoints() -> Dict[str, str]:
    """
    Récupère les endpoints des services de monitoring NMS.
    
    Returns:
        Dictionnaire des endpoints accessibles
    """
    return {
        'prometheus': 'http://localhost:9090',
        'grafana': 'http://localhost:3001', 
        'netdata': 'http://localhost:19999',
        'ntopng': 'http://localhost:3000',
        'elasticsearch': 'http://localhost:9200',
        'kibana': 'http://localhost:5601',
        'haproxy_stats': 'http://localhost:1936/stats',
        'django_api': 'http://localhost:8000/api/',
        'swagger_docs': 'http://localhost:8000/swagger/'
    }


def get_service_integration_status() -> Dict[str, Any]:
    """
    Vérifie le statut d'intégration de tous les services.
    
    Returns:
        Statut d'intégration détaillé
    """
    integration_status = {
        'gns3_central': unified_monitoring_service.gns3_adapter.is_available(),
        'docker_services': unified_monitoring_service.docker_collector.is_available(),
        'unified_service': unified_monitoring_service.is_fully_operational(),
        'endpoints': get_monitoring_service_endpoints(),
        'timestamp': timezone.now().isoformat()
    }
    
    if unified_monitoring_service.docker_collector.is_available():
        integration_status['nms_services_health'] = unified_monitoring_service.docker_collector.get_nms_services_health()
        
    return integration_status