"""
Interface Simplifiée GNS3 pour les Modules.

Cette interface fournit une API simple et unifiée pour que tous les modules
puissent interagir avec GNS3 sans connaître les détails d'implémentation.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum

from django.core.cache import cache
from django.utils import timezone

from ..infrastructure.gns3_central_service import gns3_central_service, GNS3Event, GNS3EventType
from ..infrastructure.inter_module_service import inter_module_service, MessageType

logger = logging.getLogger(__name__)


class GNS3SubscriptionType(Enum):
    """Types d'abonnements aux événements GNS3."""
    NODE_STATUS = "node_status"
    TOPOLOGY_CHANGES = "topology_changes"
    PROJECT_EVENTS = "project_events"
    ALL_EVENTS = "all_events"


@dataclass
class ModuleSubscription:
    """Abonnement d'un module aux événements GNS3."""
    module_name: str
    subscription_types: Set[GNS3SubscriptionType]
    callback: Optional[Callable] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = timezone.now().isoformat()


class GNS3ModuleInterface:
    """
    Interface simplifiée pour l'interaction des modules avec GNS3.
    
    Cette classe fournit :
    - API simple pour les actions GNS3
    - Système d'abonnement aux événements
    - Cache transparent
    - Gestion d'erreurs automatique
    """
    
    def __init__(self, module_name: str):
        """
        Initialise l'interface pour un module spécifique.
        
        Args:
            module_name: Nom du module utilisant cette interface
        """
        self.module_name = module_name
        self.subscriptions: Set[GNS3SubscriptionType] = set()
        self.event_callback: Optional[Callable] = None
        self.is_initialized = False
        
        logger.info(f"Interface GNS3 initialisée pour le module '{module_name}'")

    # ==================== INITIALISATION ====================
    
    async def initialize(self) -> bool:
        """
        Initialise l'interface module.
        
        Returns:
            True si l'initialisation réussit
        """
        try:
            # Vérifier que le service central est disponible
            status = gns3_central_service.get_service_status()
            if not status.get('status') == 'connected':
                logger.warning(f"Service central GNS3 non connecté pour le module {self.module_name}")
                return False
            
            # Enregistrer ce module
            self._register_with_central_service()
            
            self.is_initialized = True
            logger.info(f"Interface GNS3 initialisée avec succès pour {self.module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'interface GNS3 pour {self.module_name}: {e}")
            return False

    def _register_with_central_service(self):
        """Enregistre ce module auprès du service central."""
        # Enregistrer le callback d'événements
        if self.event_callback:
            gns3_central_service.register_event_callback(self._handle_gns3_event)

    # ==================== LECTURE D'ÉTAT ====================
    
    def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut d'un nœud depuis le cache.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Statut du nœud ou None si non trouvé
        """
        try:
            return gns3_central_service.get_cached_node_status(node_id)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut du nœud {node_id}: {e}")
            return None

    def get_project_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Informations du projet ou None
        """
        try:
            return cache.get(f"{gns3_central_service.cache_prefix}:project:{project_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du projet {project_id}: {e}")
            return None

    def get_complete_topology(self) -> Optional[Dict[str, Any]]:
        """
        Récupère la topologie complète du réseau.
        
        Returns:
            Topologie complète ou None
        """
        try:
            return gns3_central_service.get_cached_topology()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la topologie: {e}")
            return None

    def get_nodes_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les nœuds ayant un statut spécifique.
        
        Args:
            status: Statut recherché ('started', 'stopped', etc.)
            
        Returns:
            Liste des nœuds correspondants
        """
        try:
            topology = self.get_complete_topology()
            if not topology:
                return []
            
            matching_nodes = []
            for node_data in topology.get('nodes', {}).values():
                if node_data.get('status') == status:
                    matching_nodes.append(node_data)
            
            return matching_nodes
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de nœuds par statut {status}: {e}")
            return []

    def get_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les nœuds d'un type spécifique.
        
        Args:
            node_type: Type de nœud ('qemu', 'docker', etc.)
            
        Returns:
            Liste des nœuds correspondants
        """
        try:
            topology = self.get_complete_topology()
            if not topology:
                return []
            
            matching_nodes = []
            for node_data in topology.get('nodes', {}).values():
                if node_data.get('node_type') == node_type:
                    matching_nodes.append(node_data)
            
            return matching_nodes
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de nœuds par type {node_type}: {e}")
            return []

    def get_project_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les nœuds d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des nœuds du projet
        """
        try:
            project = self.get_project_info(project_id)
            if not project:
                return []
            
            return list(project.get('nodes', {}).values())
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des nœuds du projet {project_id}: {e}")
            return []

    # ==================== ACTIONS GNS3 ====================
    
    async def start_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Démarre un nœud.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'opération
        """
        try:
            logger.info(f"Module {self.module_name} demande le démarrage du nœud {node_id}")
            return await gns3_central_service.start_node(project_id, node_id)
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du nœud {node_id} par {self.module_name}: {e}")
            return {"success": False, "error": str(e)}

    async def stop_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Arrête un nœud.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'opération
        """
        try:
            logger.info(f"Module {self.module_name} demande l'arrêt du nœud {node_id}")
            return await gns3_central_service.stop_node(project_id, node_id)
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du nœud {node_id} par {self.module_name}: {e}")
            return {"success": False, "error": str(e)}

    async def restart_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Redémarre un nœud.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'opération
        """
        try:
            logger.info(f"Module {self.module_name} demande le redémarrage du nœud {node_id}")
            return await gns3_central_service.restart_node(project_id, node_id)
        except Exception as e:
            logger.error(f"Erreur lors du redémarrage du nœud {node_id} par {self.module_name}: {e}")
            return {"success": False, "error": str(e)}

    async def start_project(self, project_id: str) -> Dict[str, Any]:
        """
        Démarre tous les nœuds d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Résultat de l'opération
        """
        try:
            logger.info(f"Module {self.module_name} demande le démarrage du projet {project_id}")
            return await gns3_central_service.start_project_nodes(project_id)
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du projet {project_id} par {self.module_name}: {e}")
            return {"success": False, "error": str(e)}

    async def refresh_topology(self) -> Dict[str, Any]:
        """
        Force un rafraîchissement de la topologie.
        
        Returns:
            Nouvelle topologie
        """
        try:
            logger.info(f"Module {self.module_name} demande un rafraîchissement de topologie")
            return await gns3_central_service.refresh_topology()
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement par {self.module_name}: {e}")
            return {"success": False, "error": str(e)}

    # ==================== ABONNEMENTS AUX ÉVÉNEMENTS ====================
    
    def subscribe_to_events(self, 
                          subscription_types: List[GNS3SubscriptionType], 
                          callback: Callable):
        """
        S'abonne aux événements GNS3.
        
        Args:
            subscription_types: Types d'événements à écouter
            callback: Fonction appelée pour chaque événement
        """
        try:
            # Vérifier que subscription_types est une liste
            if not isinstance(subscription_types, (list, tuple)):
                subscription_types = [subscription_types]
            
            self.subscriptions.update(subscription_types)
            self.event_callback = callback
            
            # Réenregistrer avec le service central
            self._register_with_central_service()
            
            logger.info(f"Module {self.module_name} abonné aux événements: {[s.value if hasattr(s, 'value') else str(s) for s in subscription_types]}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'abonnement aux événements pour {self.module_name}: {e}")

    def unsubscribe_from_events(self):
        """Désabonne le module de tous les événements."""
        self.subscriptions.clear()
        self.event_callback = None
        
        # Désenregistrer du service central
        if hasattr(gns3_central_service, 'unregister_event_callback'):
            gns3_central_service.unregister_event_callback(self._handle_gns3_event)
        
        logger.info(f"Module {self.module_name} désabonné de tous les événements")

    async def _handle_gns3_event(self, event: GNS3Event):
        """
        Traite un événement GNS3 et l'envoie au module si pertinent.
        
        Args:
            event: Événement GNS3 reçu
        """
        try:
            # Vérifier si le module est intéressé par cet événement
            if not self._should_handle_event(event):
                return
            
            # Appeler le callback du module
            if self.event_callback:
                await self.event_callback(event)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement d'événement pour {self.module_name}: {e}")

    def _should_handle_event(self, event: GNS3Event) -> bool:
        """
        Détermine si le module doit traiter cet événement.
        
        Args:
            event: Événement à analyser
            
        Returns:
            True si l'événement doit être traité
        """
        if GNS3SubscriptionType.ALL_EVENTS in self.subscriptions:
            return True
        
        # Mapper les types d'événements
        event_mapping = {
            GNS3EventType.NODE_STARTED: GNS3SubscriptionType.NODE_STATUS,
            GNS3EventType.NODE_STOPPED: GNS3SubscriptionType.NODE_STATUS,
            GNS3EventType.NODE_SUSPENDED: GNS3SubscriptionType.NODE_STATUS,
            GNS3EventType.NODE_CREATED: GNS3SubscriptionType.TOPOLOGY_CHANGES,
            GNS3EventType.NODE_DELETED: GNS3SubscriptionType.TOPOLOGY_CHANGES,
            GNS3EventType.PROJECT_OPENED: GNS3SubscriptionType.PROJECT_EVENTS,
            GNS3EventType.PROJECT_CLOSED: GNS3SubscriptionType.PROJECT_EVENTS,
            GNS3EventType.PROJECT_CREATED: GNS3SubscriptionType.PROJECT_EVENTS,
            GNS3EventType.PROJECT_DELETED: GNS3SubscriptionType.PROJECT_EVENTS,
            GNS3EventType.TOPOLOGY_CHANGED: GNS3SubscriptionType.TOPOLOGY_CHANGES,
        }
        
        required_subscription = event_mapping.get(event.event_type)
        return required_subscription in self.subscriptions

    # ==================== UTILITAIRES ====================
    
    def get_interface_status(self) -> Dict[str, Any]:
        """
        Récupère le statut de l'interface.
        
        Returns:
            Statut détaillé de l'interface
        """
        central_status = gns3_central_service.get_service_status()
        
        return {
            'module_name': self.module_name,
            'initialized': self.is_initialized,
            'subscriptions': [s.value for s in self.subscriptions],
            'has_callback': self.event_callback is not None,
            'central_service_status': central_status['status'],
            'central_service_connected': central_status.get('gns3_server', {}).get('connected', False),
            'last_check': timezone.now().isoformat()
        }

    def get_network_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé du réseau pour le module.
        
        Returns:
            Résumé du réseau
        """
        try:
            topology = self.get_complete_topology()
            if not topology:
                return {'error': 'Topologie non disponible'}
            
            # Compter par statut
            status_counts = {}
            type_counts = {}
            
            for node in topology.get('nodes', {}).values():
                status = node.get('status', 'unknown')
                node_type = node.get('node_type', 'unknown')
                
                status_counts[status] = status_counts.get(status, 0) + 1
                type_counts[node_type] = type_counts.get(node_type, 0) + 1
            
            return {
                'projects_count': len(topology.get('projects', {})),
                'nodes_count': len(topology.get('nodes', {})),
                'links_count': len(topology.get('links', {})),
                'status_distribution': status_counts,
                'type_distribution': type_counts,
                'last_update': topology.get('last_update'),
                'requested_by': self.module_name
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé réseau pour {self.module_name}: {e}")
            return {'error': str(e)}


# Factory pour créer des interfaces module
def create_gns3_interface(module_name: str) -> GNS3ModuleInterface:
    """
    Crée une interface GNS3 pour un module.
    
    Args:
        module_name: Nom du module
        
    Returns:
        Interface GNS3 configurée
    """
    interface = GNS3ModuleInterface(module_name)
    logger.info(f"Interface GNS3 créée pour le module {module_name}")
    return interface