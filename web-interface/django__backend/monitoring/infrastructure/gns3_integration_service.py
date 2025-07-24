"""
Service d'intégration GNS3 pour le module Monitoring.
"""
import logging
from typing import Dict, List, Any
from django.utils import timezone
# DEPRECATED: Ancien système d'intégration GNS3
# Cette classe est conservée pour compatibilité mais remplacée par unified_monitoring_service
# Utiliser monitoring.infrastructure.unified_monitoring_service à la place

from common.api.gns3_module_interface import create_gns3_interface
from common.infrastructure.gns3_central_service import GNS3EventType

logger = logging.getLogger(__name__)

class MonitoringGNS3Service:
    """
    DEPRECATED: Service d'intégration GNS3 pour le module Monitoring.
    
    ⚠️  ATTENTION: Cette classe est dépréciée.
    Utiliser unified_monitoring_service à la place pour bénéficier de :
    - Intégration avec le nouveau Service Central GNS3
    - Support Docker NMS complet
    - Architecture moderne et performante
    
    Cette classe est conservée uniquement pour compatibilité ascendante.
    """
    """
    Service d'intégration GNS3 spécifique au module Monitoring.
    """
    
    def __init__(self):
        # Initialisation basique pour compatibilité
        self.module_name = 'monitoring'
        self.monitored_nodes = {}
        self.network_metrics = {}
        self.alerts = []
        
        # Intégration avec le nouveau Service Central GNS3
        try:
            self.gns3_interface = create_gns3_interface('monitoring_legacy')
            logger.warning(
                "⚠️  Utilisation du service GNS3 legacy. "
                "Migrer vers unified_monitoring_service pour de meilleures performances."
            )
        except Exception as e:
            logger.error(f"Erreur d'initialisation de l'interface GNS3 legacy: {e}")
            self.gns3_interface = None
        
    def _process_gns3_topology(self, topology_data: Dict[str, Any]):
        """
        Traite les données de topologie GNS3 pour le monitoring.
        
        Args:
            topology_data: Données de topologie depuis GNS3
        """
        logger.info("Traitement de la topologie GNS3 pour le monitoring")
        
        # Identifier les nœuds à surveiller
        self._identify_nodes_to_monitor(topology_data)
        
        # Configurer les métriques réseau
        self._setup_network_metrics(topology_data)
        
        # Migration vers le service unifié recommandée
        logger.info(
            f"Topologie traitée par le service legacy: {len(self.monitored_nodes)} nœuds surveillés. "
            "Recommandation: Migrer vers unified_monitoring_service."
        )
        
    def _identify_nodes_to_monitor(self, topology_data: Dict[str, Any]):
        """
        Identifie les nœuds GNS3 à surveiller.
        
        Args:
            topology_data: Données de topologie
        """
        for project in topology_data:
            project_id = project.get('project_id')
            project_name = project.get('name', 'Unknown')
            nodes = project.get('nodes', [])
            
            for node in nodes:
                node_id = node.get('node_id')
                node_name = node.get('name', 'Unknown')
                node_type = node.get('node_type')
                
                # Configurer la surveillance selon le type de nœud
                monitoring_config = self._get_monitoring_config_for_node(node_type)
                
                if monitoring_config:
                    self.monitored_nodes[node_id] = {
                        'node_id': node_id,
                        'name': node_name,
                        'type': node_type,
                        'project_id': project_id,
                        'project_name': project_name,
                        'monitoring_config': monitoring_config,
                        'status': node.get('status', 'unknown'),
                        'last_check': None,
                        'metrics': {}
                    }
                    
        logger.info(f"Nœuds identifiés pour surveillance: {len(self.monitored_nodes)}")
        
    def _get_monitoring_config_for_node(self, node_type: str) -> Dict[str, Any]:
        """
        Récupère la configuration de monitoring pour un type de nœud.
        
        Args:
            node_type: Type du nœud
            
        Returns:
            Configuration de monitoring ou None
        """
        monitoring_configs = {
            'qemu': {
                'metrics': ['cpu_usage', 'memory_usage', 'network_io'],
                'check_interval': 30,
                'alert_thresholds': {
                    'cpu_usage': 80,
                    'memory_usage': 85
                }
            },
            'docker': {
                'metrics': ['cpu_usage', 'memory_usage', 'network_io', 'container_status'],
                'check_interval': 20,
                'alert_thresholds': {
                    'cpu_usage': 75,
                    'memory_usage': 80
                }
            },
            'dynamips': {
                'metrics': ['interface_status', 'cpu_usage', 'routing_table'],
                'check_interval': 60,
                'alert_thresholds': {
                    'cpu_usage': 70
                }
            },
            'vpcs': {
                'metrics': ['connectivity', 'ping_response'],
                'check_interval': 45,
                'alert_thresholds': {}
            },
            'ethernet_switch': {
                'metrics': ['port_status', 'traffic_stats', 'error_counters'],
                'check_interval': 30,
                'alert_thresholds': {
                    'error_rate': 5
                }
            }
        }
        
        return monitoring_configs.get(node_type)
        
    def _setup_network_metrics(self, topology_data: Dict[str, Any]):
        """
        Configure les métriques réseau globales.
        
        Args:
            topology_data: Données de topologie
        """
        self.network_metrics = {
            'total_projects': len(topology_data),
            'total_nodes': sum(len(project.get('nodes', [])) for project in topology_data),
            'node_types': {},
            'status_distribution': {},
            'monitoring_coverage': 0
        }
        
        # Analyser la distribution des types et statuts
        for project in topology_data:
            for node in project.get('nodes', []):
                node_type = node.get('node_type', 'unknown')
                status = node.get('status', 'unknown')
                
                self.network_metrics['node_types'][node_type] = \
                    self.network_metrics['node_types'].get(node_type, 0) + 1
                    
                self.network_metrics['status_distribution'][status] = \
                    self.network_metrics['status_distribution'].get(status, 0) + 1
                    
        # Calculer la couverture de monitoring
        if self.network_metrics['total_nodes'] > 0:
            self.network_metrics['monitoring_coverage'] = \
                (len(self.monitored_nodes) / self.network_metrics['total_nodes']) * 100
                
        logger.info(f"Métriques réseau configurées: {self.network_metrics['monitoring_coverage']:.1f}% de couverture")
        
    def _process_node_status_change(self, node_data: Dict[str, Any]):
        """
        Traite un changement de statut de nœud pour le monitoring.
        
        Args:
            node_data: Données du nœud
        """
        node_id = node_data.get('node_id')
        new_status = node_data.get('status')
        
        if node_id in self.monitored_nodes:
            old_status = self.monitored_nodes[node_id]['status']
            self.monitored_nodes[node_id]['status'] = new_status
            self.monitored_nodes[node_id]['last_check'] = timezone.now()
            
            # Générer une alerte si nécessaire
            if old_status != new_status:
                self._generate_status_change_alert(node_id, old_status, new_status)
                
            logger.info(f"Nœud {node_id}: {old_status} -> {new_status}")
            
    def _generate_status_change_alert(self, node_id: str, old_status: str, new_status: str):
        """
        Génère une alerte pour un changement de statut.
        
        Args:
            node_id: ID du nœud
            old_status: Ancien statut
            new_status: Nouveau statut
        """
        node_info = self.monitored_nodes.get(node_id, {})
        
        alert = {
            'type': 'node_status_change',
            'severity': self._get_alert_severity(old_status, new_status),
            'node_id': node_id,
            'node_name': node_info.get('name', 'Unknown'),
            'project_name': node_info.get('project_name', 'Unknown'),
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': timezone.now(),
            'message': f"Nœud {node_info.get('name', node_id)} est passé de {old_status} à {new_status}"
        }
        
        self.alerts.append(alert)
        
        # TODO: Intégration avec le système d'alertes unifié
        logger.info(f"Alerte générée par le service legacy: {alert['message']}")
        
        logger.warning(f"Alerte générée: {alert['message']}")
        
    def _get_alert_severity(self, old_status: str, new_status: str) -> str:
        """
        Détermine la sévérité d'une alerte selon le changement de statut.
        
        Args:
            old_status: Ancien statut
            new_status: Nouveau statut
            
        Returns:
            Niveau de sévérité
        """
        # Transitions critiques
        if old_status == 'started' and new_status in ['stopped', 'suspended']:
            return 'critical'
        elif old_status in ['stopped', 'suspended'] and new_status == 'started':
            return 'info'
        elif new_status == 'unknown':
            return 'warning'
        else:
            return 'low'
            
    def _process_docker_integration(self, service_name: str, service_config: Dict[str, Any]):
        """
        Traite l'intégration d'un service Docker pour le monitoring.
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
        """
        logger.info(f"Intégration Docker pour monitoring: {service_name}")
        
        # Configurer les métriques selon le type de service
        if service_config.get('type') == 'monitoring':
            # Service de monitoring (Netdata, Prometheus, etc.)
            self._integrate_monitoring_service(service_name, service_config)
        elif service_config.get('type') == 'database':
            # Base de données à surveiller
            self._setup_database_monitoring(service_name, service_config)
        elif service_config.get('type') == 'search':
            # Service de recherche (Elasticsearch)
            self._setup_search_monitoring(service_name, service_config)
            
    def _integrate_monitoring_service(self, service_name: str, service_config: Dict[str, Any]):
        """
        Intègre un service de monitoring.
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
        """
        monitoring_integration = {
            'service_name': service_name,
            'type': 'monitoring_service',
            'endpoint': f"http://{service_config.get('host')}:{service_config.get('port')}",
            'health_endpoint': service_config.get('health_endpoint'),
            'integrated_at': timezone.now()
        }
        
        # Ajouter aux intégrations Docker
        self.docker_integrations[service_name] = monitoring_integration
        
    def _setup_database_monitoring(self, service_name: str, service_config: Dict[str, Any]):
        """
        Configure le monitoring d'une base de données.
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
        """
        db_monitoring = {
            'service_name': service_name,
            'type': 'database_monitoring',
            'metrics': ['connection_count', 'query_performance', 'disk_usage'],
            'check_interval': 60,
            'integrated_at': timezone.now()
        }
        
        self.docker_integrations[service_name] = db_monitoring
        
    def _setup_search_monitoring(self, service_name: str, service_config: Dict[str, Any]):
        """
        Configure le monitoring d'un service de recherche.
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
        """
        search_monitoring = {
            'service_name': service_name,
            'type': 'search_monitoring',
            'metrics': ['cluster_health', 'index_count', 'search_performance'],
            'check_interval': 45,
            'integrated_at': timezone.now()
        }
        
        self.docker_integrations[service_name] = search_monitoring
        
    def _get_module_specific_topology_data(self) -> Dict[str, Any]:
        """
        Récupère les données de topologie spécifiques au monitoring.
        
        Returns:
            Données spécifiques au monitoring
        """
        return {
            'monitored_nodes': len(self.monitored_nodes),
            'network_metrics': self.network_metrics,
            'alerts_count': len(self.alerts),
            'recent_alerts': self.alerts[-5:] if self.alerts else [],
            'monitoring_coverage': self.network_metrics.get('monitoring_coverage', 0)
        }
        
    def _module_specific_health_check(self) -> Dict[str, Any]:
        """
        Health check spécifique au monitoring.
        
        Returns:
            Données de health check du monitoring
        """
        # Vérifier si tous les nœuds surveillés sont accessibles
        healthy_nodes = sum(1 for node in self.monitored_nodes.values() 
                          if node.get('status') == 'started')
        total_nodes = len(self.monitored_nodes)
        
        health_percentage = (healthy_nodes / total_nodes * 100) if total_nodes > 0 else 100
        
        # Compter les alertes critiques récentes (dernière heure)
        recent_critical_alerts = sum(1 for alert in self.alerts 
                                   if alert.get('severity') == 'critical' and 
                                   (timezone.now() - alert.get('timestamp')).seconds < 3600)
        
        status = 'ok'
        if health_percentage < 80:
            status = 'warning'
        if health_percentage < 60 or recent_critical_alerts > 5:
            status = 'critical'
            
        return {
            'monitoring_health_percentage': health_percentage,
            'healthy_nodes': healthy_nodes,
            'total_monitored_nodes': total_nodes,
            'recent_critical_alerts': recent_critical_alerts,
            'status': status
        }
        
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """
        Récupère les données pour le dashboard de monitoring.
        
        Returns:
            Données du dashboard
        """
        return {
            'network_overview': self.network_metrics,
            'monitored_nodes': list(self.monitored_nodes.values()),
            'docker_services': list(self.docker_integrations.values()),
            'recent_alerts': self.alerts[-10:] if self.alerts else [],
            'last_update': timezone.now().isoformat()
        }

# DEPRECATED: Instance du service de monitoring GNS3 legacy
# ⚠️  Utiliser unified_monitoring_service à la place
monitoring_gns3_service = MonitoringGNS3Service()

# Import recommandé pour le nouveau système
# from .unified_monitoring_service import unified_monitoring_service