"""
Interfaces pour le module plugins.

Ce module définit les contrats d'interface pour les différents
types de plugins et leur gestion.
"""

from typing import Dict, Any, List, Optional, Set, Type, TypeVar, Generic, Protocol
from abc import ABC, abstractmethod


class PluginMetadata(Protocol):
    """Interface pour les métadonnées d'un plugin."""
    
    @property
    def id(self) -> str:
        """Identifiant unique du plugin."""
        ...
    
    @property
    def name(self) -> str:
        """Nom lisible du plugin."""
        ...
    
    @property
    def version(self) -> str:
        """Version du plugin."""
        ...
    
    @property
    def description(self) -> str:
        """Description du plugin."""
        ...
    
    @property
    def author(self) -> str:
        """Auteur du plugin."""
        ...
    
    @property
    def dependencies(self) -> List[str]:
        """Liste des IDs des plugins dont dépend ce plugin."""
        ...
    
    @property
    def provides(self) -> List[str]:
        """Liste des fonctionnalités fournies par ce plugin."""
        ...


class BasePlugin(ABC):
    """Classe de base pour tous les plugins."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialise le plugin.
        
        Returns:
            True si l'initialisation a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """
        Nettoie les ressources utilisées par le plugin.
        
        Returns:
            True si le nettoyage a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Obtient les métadonnées du plugin.
        
        Returns:
            Métadonnées du plugin
        """
        pass


T = TypeVar('T', bound=BasePlugin)


class PluginRegistry(Generic[T]):
    """
    Interface pour le registre de plugins.
    
    Cette interface définit les méthodes pour enregistrer,
    désinscrire et récupérer des plugins.
    """
    
    @abstractmethod
    def register(self, plugin: T) -> bool:
        """
        Enregistre un plugin dans le registre.
        
        Args:
            plugin: Plugin à enregistrer
            
        Returns:
            True si l'enregistrement a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def unregister(self, plugin_id: str) -> bool:
        """
        Désinscrit un plugin du registre.
        
        Args:
            plugin_id: ID du plugin à désinscrire
            
        Returns:
            True si la désinscription a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_id: str) -> Optional[T]:
        """
        Récupère un plugin par son ID.
        
        Args:
            plugin_id: ID du plugin à récupérer
            
        Returns:
            Plugin correspondant à l'ID, ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def get_all_plugins(self) -> List[T]:
        """
        Récupère tous les plugins enregistrés.
        
        Returns:
            Liste de tous les plugins enregistrés
        """
        pass
    
    @abstractmethod
    def get_plugins_by_type(self, plugin_type: Type[T]) -> List[T]:
        """
        Récupère tous les plugins d'un type spécifique.
        
        Args:
            plugin_type: Type de plugin à récupérer
            
        Returns:
            Liste des plugins du type spécifié
        """
        pass


class DependencyResolver(ABC):
    """
    Interface pour le résolveur de dépendances entre plugins.
    """
    
    @abstractmethod
    def resolve_dependencies(self, plugins: List[BasePlugin]) -> List[BasePlugin]:
        """
        Résout les dépendances entre plugins et retourne une liste
        des plugins triés selon l'ordre de dépendance.
        
        Args:
            plugins: Liste des plugins à trier
            
        Returns:
            Liste des plugins triés selon l'ordre de dépendance
            
        Raises:
            CircularDependencyError: Si des dépendances circulaires sont détectées
            MissingDependencyError: Si des dépendances sont manquantes
        """
        pass
    
    @abstractmethod
    def check_dependencies(self, plugin: BasePlugin, available_plugins: List[BasePlugin]) -> List[str]:
        """
        Vérifie que toutes les dépendances d'un plugin sont satisfaites.
        
        Args:
            plugin: Plugin à vérifier
            available_plugins: Liste des plugins disponibles
            
        Returns:
            Liste des dépendances manquantes (vide si toutes les dépendances sont satisfaites)
        """
        pass
    
    @abstractmethod
    def get_dependent_plugins(self, plugin_id: str, all_plugins: List[BasePlugin]) -> List[BasePlugin]:
        """
        Récupère tous les plugins qui dépendent directement d'un plugin donné.
        
        Args:
            plugin_id: ID du plugin dont on veut connaître les dépendants
            all_plugins: Liste de tous les plugins disponibles
            
        Returns:
            Liste des plugins qui dépendent directement du plugin spécifié
        """
        pass


class AlertHandlerPlugin(BasePlugin):
    """Interface pour les plugins gestionnaires d'alertes."""
    
    @abstractmethod
    def handle_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une alerte.
        
        Args:
            alert_data: Données de l'alerte à traiter
            
        Returns:
            Résultat du traitement de l'alerte
        """
        pass


class DashboardWidgetPlugin(BasePlugin):
    """Interface pour les plugins de widgets de tableau de bord."""
    
    @abstractmethod
    def get_widget_data(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Récupère les données à afficher dans le widget.
        
        Args:
            context: Contexte optionnel pour la récupération des données
            
        Returns:
            Données à afficher dans le widget
        """
        pass
    
    @abstractmethod
    def get_widget_configuration(self) -> Dict[str, Any]:
        """
        Récupère la configuration du widget (taille, titre, icône, etc.).
        
        Returns:
            Configuration du widget
        """
        pass


class ReportGeneratorPlugin(BasePlugin):
    """Interface pour les plugins générateurs de rapports."""
    
    @abstractmethod
    def generate_report(self, report_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Génère un rapport.
        
        Args:
            report_type: Type de rapport à générer
            params: Paramètres optionnels pour la génération du rapport
            
        Returns:
            Rapport généré
        """
        pass
    
    @abstractmethod
    def get_supported_report_types(self) -> List[Dict[str, Any]]:
        """
        Récupère les types de rapports pris en charge par ce plugin.
        
        Returns:
            Liste des types de rapports pris en charge, avec leurs métadonnées
        """
        pass


class PluginManager(ABC):
    """
    Interface pour le gestionnaire de plugins.
    """
    
    @abstractmethod
    def load_plugins(self, directory: str = None) -> List[str]:
        """
        Charge les plugins depuis un répertoire.
        
        Args:
            directory: Répertoire contenant les plugins (optionnel)
            
        Returns:
            Liste des IDs des plugins chargés
        """
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Décharge un plugin.
        
        Args:
            plugin_id: ID du plugin à décharger
            
        Returns:
            True si le déchargement a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Active un plugin.
        
        Args:
            plugin_id: ID du plugin à activer
            
        Returns:
            True si l'activation a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Désactive un plugin.
        
        Args:
            plugin_id: ID du plugin à désactiver
            
        Returns:
            True si la désactivation a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def get_loaded_plugins(self) -> List[BasePlugin]:
        """
        Récupère tous les plugins chargés.
        
        Returns:
            Liste des plugins chargés
        """
        pass
    
    @abstractmethod
    def get_enabled_plugins(self) -> List[BasePlugin]:
        """
        Récupère tous les plugins activés.
        
        Returns:
            Liste des plugins activés
        """
        pass 