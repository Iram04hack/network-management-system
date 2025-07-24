"""
Mixin pour faciliter l'intégration des modules avec le Service Central de Topologie.
"""
import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)

class ModuleIntegrationMixin:
    """
    Mixin pour faciliter l'intégration des modules avec GNS3 et le système de topologie.
    
    Les modules peuvent hériter de cette classe pour bénéficier automatiquement
    des fonctionnalités d'intégration.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = getattr(self, 'module_name', self.__class__.__module__.split('.')[0])
        self.gns3_data = {}
        self.docker_integrations = {}
        self.last_topology_update = None
        
    def integrate_gns3_topology(self, topology_data: Dict[str, Any]):
        """
        Intègre les données de topologie GNS3.
        
        Args:
            topology_data: Données de topologie depuis GNS3
        """
        try:
            self.gns3_data = topology_data
            self.last_topology_update = timezone.now()
            
            # Traitement spécifique selon le module
            self._process_gns3_topology(topology_data)
            
            logger.info(f"Module {self.module_name}: Topologie GNS3 intégrée - {len(topology_data)} projets")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration GNS3 dans {self.module_name}: {e}")
            
    def _process_gns3_topology(self, topology_data: Dict[str, Any]):
        """
        Traite les données de topologie GNS3 (à surcharger par les modules).
        
        Args:
            topology_data: Données de topologie
        """
        # Implémentation par défaut - les modules peuvent surcharger cette méthode
        pass
        
    def handle_node_status_change(self, node_data: Dict[str, Any]):
        """
        Traite un changement de statut de nœud GNS3.
        
        Args:
            node_data: Données du nœud
        """
        try:
            node_id = node_data.get('node_id')
            new_status = node_data.get('status')
            project_id = node_data.get('project_id')
            
            logger.debug(f"Module {self.module_name}: Nœud {node_id} -> {new_status}")
            
            # Traitement spécifique selon le module
            self._process_node_status_change(node_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du changement de nœud dans {self.module_name}: {e}")
            
    def _process_node_status_change(self, node_data: Dict[str, Any]):
        """
        Traite un changement de statut de nœud (à surcharger par les modules).
        
        Args:
            node_data: Données du nœud
        """
        # Implémentation par défaut
        pass
        
    def handle_network_event(self, event_data: Dict[str, Any]):
        """
        Traite un événement réseau.
        
        Args:
            event_data: Données de l'événement
        """
        try:
            event_type = event_data.get('event_type', 'unknown')
            
            logger.debug(f"Module {self.module_name}: Événement réseau {event_type}")
            
            # Traitement spécifique selon le module
            self._process_network_event(event_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement réseau dans {self.module_name}: {e}")
            
    def _process_network_event(self, event_data: Dict[str, Any]):
        """
        Traite un événement réseau (à surcharger par les modules).
        
        Args:
            event_data: Données de l'événement
        """
        # Implémentation par défaut
        pass
        
    def handle_configuration_change(self, config_data: Dict[str, Any]):
        """
        Traite un changement de configuration.
        
        Args:
            config_data: Données de configuration
        """
        try:
            config_type = config_data.get('config_type', 'unknown')
            
            logger.debug(f"Module {self.module_name}: Changement de configuration {config_type}")
            
            # Traitement spécifique selon le module
            self._process_configuration_change(config_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du changement de configuration dans {self.module_name}: {e}")
            
    def _process_configuration_change(self, config_data: Dict[str, Any]):
        """
        Traite un changement de configuration (à surcharger par les modules).
        
        Args:
            config_data: Données de configuration
        """
        # Implémentation par défaut
        pass
        
    def get_topology_data(self) -> Dict[str, Any]:
        """
        Récupère les données de topologie du module.
        
        Returns:
            Données de topologie spécifiques au module
        """
        return {
            'module_name': self.module_name,
            'gns3_integrated': bool(self.gns3_data),
            'gns3_projects_count': len(self.gns3_data) if self.gns3_data else 0,
            'docker_integrations': list(self.docker_integrations.keys()),
            'last_topology_update': self.last_topology_update.isoformat() if self.last_topology_update else None,
            'specific_data': self._get_module_specific_topology_data()
        }
        
    def _get_module_specific_topology_data(self) -> Dict[str, Any]:
        """
        Récupère les données de topologie spécifiques au module (à surcharger).
        
        Returns:
            Données spécifiques au module
        """
        return {}
        
    def health_check(self) -> Dict[str, Any]:
        """
        Effectue un health check du module.
        
        Returns:
            Statut de santé du module
        """
        try:
            # Health check de base
            status = {
                'status': 'ok',
                'message': f'Module {self.module_name} opérationnel',
                'gns3_integrated': bool(self.gns3_data),
                'last_update': self.last_topology_update.isoformat() if self.last_topology_update else None
            }
            
            # Health check spécifique au module
            module_health = self._module_specific_health_check()
            status.update(module_health)
            
            return status
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur health check module {self.module_name}: {str(e)}',
                'error': str(e)
            }
            
    def _module_specific_health_check(self) -> Dict[str, Any]:
        """
        Health check spécifique au module (à surcharger par les modules).
        
        Returns:
            Données de health check spécifiques
        """
        return {}
        
    def integrate_docker_service(self, service_name: str, service_config: Dict[str, Any]):
        """
        Intègre un service Docker avec le module.
        
        Args:
            service_name: Nom du service Docker
            service_config: Configuration du service
        """
        try:
            self.docker_integrations[service_name] = {
                'config': service_config,
                'integrated_at': timezone.now(),
                'status': 'integrated'
            }
            
            # Traitement spécifique selon le module
            self._process_docker_integration(service_name, service_config)
            
            logger.info(f"Module {self.module_name}: Service Docker {service_name} intégré")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration Docker {service_name} dans {self.module_name}: {e}")
            self.docker_integrations[service_name] = {
                'config': service_config,
                'integrated_at': timezone.now(),
                'status': 'error',
                'error': str(e)
            }
            
    def _process_docker_integration(self, service_name: str, service_config: Dict[str, Any]):
        """
        Traite l'intégration d'un service Docker (à surcharger par les modules).
        
        Args:
            service_name: Nom du service
            service_config: Configuration du service
        """
        # Implémentation par défaut
        pass
        
    def get_gns3_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """
        Récupère les nœuds GNS3 d'un type spécifique.
        
        Args:
            node_type: Type de nœud recherché
            
        Returns:
            Liste des nœuds du type spécifié
        """
        nodes = []
        
        for project in self.gns3_data:
            project_nodes = project.get('nodes', [])
            for node in project_nodes:
                if node.get('node_type') == node_type:
                    nodes.append({
                        **node,
                        'project_id': project.get('project_id'),
                        'project_name': project.get('name')
                    })
                    
        return nodes
        
    def get_gns3_nodes_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Récupère les nœuds GNS3 d'un statut spécifique.
        
        Args:
            status: Statut recherché (started, stopped, etc.)
            
        Returns:
            Liste des nœuds du statut spécifié
        """
        nodes = []
        
        for project in self.gns3_data:
            project_nodes = project.get('nodes', [])
            for node in project_nodes:
                if node.get('status') == status:
                    nodes.append({
                        **node,
                        'project_id': project.get('project_id'),
                        'project_name': project.get('name')
                    })
                    
        return nodes
        
    def send_inter_module_message(self, message_type: str, data: Dict[str, Any], target: Optional[str] = None):
        """
        Envoie un message à d'autres modules.
        
        Args:
            message_type: Type du message
            data: Données du message
            target: Module cible (None pour diffusion)
        """
        try:
            from .inter_module_service import inter_module_service, MessageType
            
            # Convertir le type de message string en enum
            msg_type = MessageType(message_type)
            
            inter_module_service.send_message(
                msg_type,
                data,
                sender=self.module_name,
                target=target
            )
            
            logger.debug(f"Module {self.module_name}: Message {message_type} envoyé")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message depuis {self.module_name}: {e}")
            
    def get_integration_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé de l'intégration du module.
        
        Returns:
            Résumé de l'intégration
        """
        return {
            'module_name': self.module_name,
            'gns3_integration': {
                'enabled': bool(self.gns3_data),
                'projects_count': len(self.gns3_data) if self.gns3_data else 0,
                'last_update': self.last_topology_update.isoformat() if self.last_topology_update else None
            },
            'docker_integration': {
                'services_count': len(self.docker_integrations),
                'services': list(self.docker_integrations.keys())
            },
            'health': self.health_check()
        }