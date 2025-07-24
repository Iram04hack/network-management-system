"""
Module de gestion des configurations temporaire pour corriger les dépendances.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigurationVersionRepository:
    """Référentiel temporaire pour la gestion des versions de configurations."""
    
    def __init__(self):
        """Initialise le référentiel."""
        self.configurations = {}
        
    def get_configuration(self, configuration_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une configuration par son ID.
        
        Args:
            configuration_id: ID de la configuration
            
        Returns:
            Configuration ou None si non trouvée
        """
        return self.configurations.get(configuration_id)
    
    def save_configuration(self, configuration: Dict[str, Any]) -> int:
        """
        Sauvegarde une configuration.
        
        Args:
            configuration: Données de configuration
            
        Returns:
            ID de la configuration sauvegardée
        """
        config_id = len(self.configurations) + 1
        self.configurations[config_id] = {
            **configuration,
            'id': config_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        return config_id
    
    def get_configurations_by_node(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les configurations d'un nœud.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Liste des configurations du nœud
        """
        return [
            config for config in self.configurations.values()
            if config.get('node_id') == node_id
        ]
    
    def delete_configuration(self, configuration_id: int) -> bool:
        """
        Supprime une configuration.
        
        Args:
            configuration_id: ID de la configuration
            
        Returns:
            True si supprimée, False sinon
        """
        if configuration_id in self.configurations:
            del self.configurations[configuration_id]
            return True
        return False