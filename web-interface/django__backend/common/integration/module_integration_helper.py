"""
Helper d'intégration pour faciliter l'adoption du service central GNS3 par les modules.

Ce module fournit des outils et des guides pour permettre aux modules existants
d'intégrer facilement le service central GNS3 sans modification majeure de leur code.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..api.gns3_module_interface import create_gns3_interface, GNS3SubscriptionType
from ..infrastructure.gns3_central_service import GNS3Event

logger = logging.getLogger(__name__)


@dataclass
class ModuleIntegrationConfig:
    """Configuration d'intégration pour un module."""
    module_name: str
    auto_subscribe_events: List[GNS3SubscriptionType]
    enable_cache: bool = True
    enable_realtime_events: bool = True
    custom_event_handler: Optional[Callable] = None
    required_node_types: Optional[List[str]] = None
    required_projects: Optional[List[str]] = None


class GNS3ModuleIntegrationMixin:
    """
    Mixin pour faciliter l'intégration GNS3 dans les modules existants.
    
    Usage:
        class MonitoringModule(GNS3ModuleIntegrationMixin):
            def __init__(self):
                self.setup_gns3_integration('monitoring')
    """
    
    def setup_gns3_integration(self, module_name: str, 
                              config: Optional[ModuleIntegrationConfig] = None):
        """
        Configure l'intégration GNS3 pour le module.
        
        Args:
            module_name: Nom du module
            config: Configuration d'intégration personnalisée
        """
        self.module_name = module_name
        self.gns3_interface = create_gns3_interface(module_name)
        self.integration_config = config or ModuleIntegrationConfig(
            module_name=module_name,
            auto_subscribe_events=[GNS3SubscriptionType.ALL_EVENTS]
        )
        
        # Initialiser l'interface de manière asynchrone
        self._initialize_gns3_integration()
        
        logger.info(f"Intégration GNS3 configurée pour le module {module_name}")
    
    def _initialize_gns3_integration(self):
        """Initialise l'intégration GNS3 de manière asynchrone."""
        import asyncio
        
        try:
            # Créer une tâche d'initialisation asynchrone
            loop = asyncio.get_event_loop()
            loop.create_task(self._async_initialize_gns3())
        except RuntimeError:
            # Si pas de boucle d'événements, initialiser de manière synchrone
            logger.warning(f"Initialisation GNS3 différée pour {self.module_name}")
    
    async def _async_initialize_gns3(self):
        """Initialisation asynchrone de l'interface GNS3."""
        try:
            # Initialiser l'interface
            await self.gns3_interface.initialize()
            
            # Configurer les abonnements aux événements
            if self.integration_config.auto_subscribe_events:
                self.gns3_interface.subscribe_to_events(
                    self.integration_config.auto_subscribe_events,
                    self._handle_gns3_event
                )
            
            logger.info(f"Interface GNS3 initialisée pour {self.module_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation GNS3 pour {self.module_name}: {e}")
    
    async def _handle_gns3_event(self, event: GNS3Event):
        """Gestionnaire d'événements GNS3 par défaut."""
        try:
            # Appeler le gestionnaire personnalisé si configuré
            if self.integration_config.custom_event_handler:
                await self.integration_config.custom_event_handler(event)
            else:
                # Gestionnaire par défaut
                await self._default_event_handler(event)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement d'événement GNS3 dans {self.module_name}: {e}")
    
    async def _default_event_handler(self, event: GNS3Event):
        """Gestionnaire d'événements par défaut."""
        logger.debug(f"Événement GNS3 reçu dans {self.module_name}: {event.event_type.value}")
        
        # Logique par défaut selon le type d'événement
        if hasattr(self, 'on_node_status_change') and 'node' in event.event_type.value:
            await self.on_node_status_change(event)
        elif hasattr(self, 'on_topology_change') and 'topology' in event.event_type.value:
            await self.on_topology_change(event)
        elif hasattr(self, 'on_project_change') and 'project' in event.event_type.value:
            await self.on_project_change(event)
    
    # Méthodes utilitaires pour les modules
    def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut d'un nœud."""
        if hasattr(self, 'gns3_interface'):
            return self.gns3_interface.get_node_status(node_id)
        return None
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Récupère un résumé du réseau."""
        if hasattr(self, 'gns3_interface'):
            return self.gns3_interface.get_network_summary()
        return {}
    
    def get_nodes_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Récupère les nœuds par statut."""
        if hasattr(self, 'gns3_interface'):
            return self.gns3_interface.get_nodes_by_status(status)
        return []
    
    async def start_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """Démarre un nœud."""
        if hasattr(self, 'gns3_interface'):
            return await self.gns3_interface.start_node(project_id, node_id)
        return {"success": False, "error": "Interface GNS3 non disponible"}
    
    async def stop_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """Arrête un nœud."""
        if hasattr(self, 'gns3_interface'):
            return await self.gns3_interface.stop_node(project_id, node_id)
        return {"success": False, "error": "Interface GNS3 non disponible"}


class AbstractGNS3Module(ABC):
    """
    Classe abstraite pour les modules utilisant GNS3.
    
    Fournit une structure standardisée pour l'intégration GNS3.
    """
    
    def __init__(self, module_name: str):
        """Initialise le module avec intégration GNS3."""
        self.module_name = module_name
        self.gns3_interface = create_gns3_interface(module_name)
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialise le module. Doit être implémenté par les sous-classes."""
        pass
    
    @abstractmethod
    async def on_node_status_change(self, event: GNS3Event):
        """Gère les changements de statut des nœuds."""
        pass
    
    @abstractmethod
    async def on_topology_change(self, event: GNS3Event):
        """Gère les changements de topologie."""
        pass
    
    async def on_project_change(self, event: GNS3Event):
        """Gère les changements de projets (optionnel)."""
        pass
    
    async def setup_gns3_integration(self):
        """Configure l'intégration GNS3 de base."""
        try:
            # Initialiser l'interface
            await self.gns3_interface.initialize()
            
            # S'abonner aux événements
            self.gns3_interface.subscribe_to_events(
                [GNS3SubscriptionType.NODE_STATUS, GNS3SubscriptionType.TOPOLOGY_CHANGES],
                self._handle_gns3_event
            )
            
            self.is_initialized = True
            logger.info(f"Intégration GNS3 configurée pour {self.module_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration GNS3 pour {self.module_name}: {e}")
            raise
    
    async def _handle_gns3_event(self, event: GNS3Event):
        """Distribue les événements aux gestionnaires appropriés."""
        try:
            if 'node' in event.event_type.value and 'status' in str(event.data):
                await self.on_node_status_change(event)
            elif 'topology' in event.event_type.value:
                await self.on_topology_change(event)
            elif 'project' in event.event_type.value:
                await self.on_project_change(event)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement d'événement dans {self.module_name}: {e}")


class GNS3IntegrationGuide:
    """
    Guide d'intégration pour aider les développeurs à adopter le service central GNS3.
    """
    
    @staticmethod
    def get_integration_examples() -> Dict[str, str]:
        """Retourne des exemples d'intégration pour différents types de modules."""
        return {
            "monitoring_module": """
# Exemple d'intégration pour un module de monitoring
from common.integration.module_integration_helper import GNS3ModuleIntegrationMixin

class MonitoringModule(GNS3ModuleIntegrationMixin):
    def __init__(self):
        super().__init__()
        self.setup_gns3_integration('monitoring')
        
    async def on_node_status_change(self, event):
        node_id = event.data.get('node_id')
        new_status = event.data.get('new_status')
        
        # Mettre à jour les métriques de monitoring
        self.update_node_metrics(node_id, new_status)
        
    def monitor_network(self):
        # Utiliser l'interface GNS3 pour surveiller le réseau
        summary = self.get_network_summary()
        started_nodes = self.get_nodes_by_status('started')
        
        return {
            'network_summary': summary,
            'active_nodes': len(started_nodes)
        }
            """,
            
            "security_module": """
# Exemple d'intégration pour un module de sécurité
from common.integration.module_integration_helper import AbstractGNS3Module

class SecurityModule(AbstractGNS3Module):
    def __init__(self):
        super().__init__('security')
        
    async def initialize(self):
        await self.setup_gns3_integration()
        return True
        
    async def on_node_status_change(self, event):
        if event.data.get('new_status') == 'started':
            # Nouveau nœud démarré, scanner pour les vulnérabilités
            node_id = event.data.get('node_id')
            await self.scan_node_security(node_id)
            
    async def on_topology_change(self, event):
        # Analyser les changements de topologie pour les risques
        await self.analyze_topology_security()
        
    async def scan_node_security(self, node_id):
        node_info = self.gns3_interface.get_node_status(node_id)
        # Logique de scan de sécurité
        pass
            """,
            
            "simple_integration": """
# Intégration simple pour un module existant
from common.api.gns3_module_interface import create_gns3_interface

class ExistingModule:
    def __init__(self):
        # Ajouter ces lignes dans un module existant
        self.gns3 = create_gns3_interface('existing_module')
        
    async def initialize_gns3(self):
        await self.gns3.initialize()
        
    def get_network_status(self):
        # Utiliser l'interface pour obtenir des informations réseau
        return self.gns3.get_network_summary()
        
    async def control_node(self, project_id, node_id, action):
        if action == 'start':
            return await self.gns3.start_node(project_id, node_id)
        elif action == 'stop':
            return await self.gns3.stop_node(project_id, node_id)
            """
        }
    
    @staticmethod
    def get_migration_checklist() -> List[str]:
        """Retourne une checklist pour migrer vers le service central GNS3."""
        return [
            "✅ Identifier les appels directs à l'API GNS3 dans le code existant",
            "✅ Remplacer les clients GNS3 directs par l'interface module",
            "✅ Configurer les abonnements aux événements selon les besoins",
            "✅ Tester l'intégration en mode développement",
            "✅ Migrer les configurations GNS3 vers le service central",
            "✅ Mettre à jour la documentation du module",
            "✅ Configurer les tests avec l'interface GNS3",
            "✅ Déployer et monitorer l'intégration"
        ]
    
    @staticmethod
    def get_best_practices() -> List[str]:
        """Retourne les meilleures pratiques pour l'intégration GNS3."""
        return [
            "Utiliser l'interface module plutôt que d'accéder directement au service central",
            "S'abonner uniquement aux événements nécessaires pour optimiser les performances",
            "Implémenter une gestion d'erreur robuste pour les actions GNS3",
            "Utiliser le cache Redis via l'interface pour les données fréquemment consultées",
            "Tester l'intégration avec et sans connexion GNS3",
            "Documenter les dépendances GNS3 du module",
            "Monitorer les performances et ajuster les abonnements si nécessaire"
        ]


def create_integration_config(module_name: str, 
                            events: Optional[List[str]] = None,
                            node_types: Optional[List[str]] = None) -> ModuleIntegrationConfig:
    """
    Fonction utilitaire pour créer une configuration d'intégration.
    
    Args:
        module_name: Nom du module
        events: Types d'événements à écouter
        node_types: Types de nœuds d'intérêt
        
    Returns:
        Configuration d'intégration
    """
    # Mapper les chaînes en énums
    event_mapping = {
        'node_status': GNS3SubscriptionType.NODE_STATUS,
        'topology_changes': GNS3SubscriptionType.TOPOLOGY_CHANGES,
        'project_events': GNS3SubscriptionType.PROJECT_EVENTS,
        'all_events': GNS3SubscriptionType.ALL_EVENTS
    }
    
    subscription_types = []
    if events:
        for event in events:
            if event in event_mapping:
                subscription_types.append(event_mapping[event])
    else:
        subscription_types = [GNS3SubscriptionType.ALL_EVENTS]
    
    return ModuleIntegrationConfig(
        module_name=module_name,
        auto_subscribe_events=subscription_types,
        required_node_types=node_types
    )


# Fonction d'aide pour les modules legacy
def quick_gns3_setup(module_name: str) -> Any:
    """
    Configuration rapide GNS3 pour les modules existants.
    
    Args:
        module_name: Nom du module
        
    Returns:
        Interface GNS3 configurée
    """
    interface = create_gns3_interface(module_name)
    
    # Configuration automatique en arrière-plan
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(interface.initialize())
    except RuntimeError:
        logger.info(f"Interface GNS3 créée pour {module_name}, initialisation différée")
    
    return interface