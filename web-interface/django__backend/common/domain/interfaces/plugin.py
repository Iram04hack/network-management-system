"""
Interface pour le service de gestion des plugins.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PluginInterface(ABC):
    """Interface pour le service de gestion des plugins."""

    @abstractmethod
    def discover_plugins(self) -> Dict[str, int]:
        """
        Découvre et charge tous les plugins disponibles.
        
        Returns:
            Dict avec les types de plugins et le nombre de plugins découverts par type
        """
        pass

    @abstractmethod
    def get_alert_handlers(self) -> List[Any]:
        """
        Récupère tous les handlers d'alertes enregistrés.
        
        Returns:
            Liste des instances de handlers d'alertes
        """
        pass

    @abstractmethod
    def handle_alert(self, alert: Any) -> Dict[str, Any]:
        """
        Traite une alerte avec tous les handlers appropriés.
        
        Args:
            alert: Objet d'alerte (SecurityAlert ou Alert)
            
        Returns:
            Dict avec les résultats par handler
        """
        pass 