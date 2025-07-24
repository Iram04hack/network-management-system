"""
Interfaces du domaine pour l'intégration GNS3.

Ce module définit les interfaces du domaine pour l'intégration GNS3
selon les principes de l'architecture hexagonale (ports and adapters).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from .models.project import Project
from .models.node import Node
from .models.link import Link
from .models.server import Server
from .models.template import Template
from .models.snapshot import Snapshot

class GNS3Repository(ABC):
    """
    Interface pour le repository GNS3.
    
    Cette interface définit le contrat que doit respecter
    tout repository permettant de persister les données GNS3.
    """
    
    @abstractmethod
    def save_project(self, project: Project) -> Project:
        """
        Sauvegarde un projet.
        
        Args:
            project: Projet à sauvegarder
            
        Returns:
            Projet sauvegardé
        """
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Récupère un projet par son ID.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def list_projects(self) -> List[Project]:
        """
        Liste tous les projets.
        
        Returns:
            Liste des projets
        """
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            True si supprimé avec succès
        """
        pass
    
    @abstractmethod
    def save_node(self, node: Node) -> Node:
        """
        Sauvegarde un nœud.
        
        Args:
            node: Nœud à sauvegarder
            
        Returns:
            Nœud sauvegardé
        """
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Récupère un nœud par son ID.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Nœud ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def list_nodes(self, project_id: str) -> List[Node]:
        """
        Liste tous les nœuds d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des nœuds
        """
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """
        Supprime un nœud.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            True si supprimé avec succès
        """
        pass
    
    @abstractmethod
    def save_link(self, link: Link) -> Link:
        """
        Sauvegarde un lien.
        
        Args:
            link: Lien à sauvegarder
            
        Returns:
            Lien sauvegardé
        """
        pass
    
    @abstractmethod
    def get_link(self, link_id: str) -> Optional[Link]:
        """
        Récupère un lien par son ID.
        
        Args:
            link_id: ID du lien
            
        Returns:
            Lien ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def list_links(self, project_id: str) -> List[Link]:
        """
        Liste tous les liens d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des liens
        """
        pass
    
    @abstractmethod
    def delete_link(self, link_id: str) -> bool:
        """
        Supprime un lien.
        
        Args:
            link_id: ID du lien
            
        Returns:
            True si supprimé avec succès
        """
        pass
    
    @abstractmethod
    def save_snapshot(self, project_id: str, snapshot_id: str, snapshot_name: str) -> bool:
        """
        Sauvegarde un snapshot.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            snapshot_name: Nom du snapshot
            
        Returns:
            True si sauvegardé avec succès
        """
        pass
    
    @abstractmethod
    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les snapshots d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des snapshots
        """
        pass
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """
        Récupère la configuration globale de GNS3.
        
        Returns:
            Configuration
        """
        pass
    
    @abstractmethod
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Sauvegarde la configuration globale de GNS3.
        
        Args:
            config: Configuration à sauvegarder
            
        Returns:
            True si sauvegardé avec succès
        """
        pass
    
    @abstractmethod
    def list_servers(self) -> List[Server]:
        """
        Liste tous les serveurs GNS3.
        
        Returns:
            Liste des serveurs
        """
        pass
    
    @abstractmethod
    def get_server(self, server_id: str) -> Optional[Server]:
        """
        Récupère un serveur par son ID.
        
        Args:
            server_id: ID du serveur
            
        Returns:
            Serveur ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def save_server(self, server: Server) -> Server:
        """
        Sauvegarde un serveur.
        
        Args:
            server: Serveur à sauvegarder
            
        Returns:
            Serveur sauvegardé
        """
        pass
    
    @abstractmethod
    def delete_server(self, server_id: str) -> bool:
        """
        Supprime un serveur.
        
        Args:
            server_id: ID du serveur
            
        Returns:
            True si supprimé avec succès
        """
        pass


class GNS3ClientPort(ABC):
    """
    Interface pour le client GNS3.
    
    Cette interface définit le contrat que doit respecter
    tout client permettant d'interagir avec l'API GNS3.
    """
    
    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du serveur GNS3.
        
        Returns:
            Informations du serveur
        """
        pass
    
    @abstractmethod
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Liste tous les projets GNS3.
        
        Returns:
            Liste des projets
        """
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Informations du projet
        """
        pass
    
    @abstractmethod
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Crée un projet GNS3.
        
        Args:
            name: Nom du projet
            description: Description du projet
            
        Returns:
            Projet créé
        """
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            True si supprimé avec succès
        """
        pass
    
    @abstractmethod
    def open_project(self, project_id: str) -> Dict[str, Any]:
        """
        Ouvre un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet ouvert
        """
        pass
    
    @abstractmethod
    def close_project(self, project_id: str) -> Dict[str, Any]:
        """
        Ferme un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet fermé
        """
        pass
    
    @abstractmethod
    def list_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les nœuds d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des nœuds
        """
        pass
    
    @abstractmethod
    def get_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Informations du nœud
        """
        pass
    
    @abstractmethod
    def create_node(
        self, 
        project_id: str, 
        node_type: str, 
        name: str, 
        x: int = 0, 
        y: int = 0,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crée un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_type: Type de nœud
            name: Nom du nœud
            x: Position X
            y: Position Y
            properties: Propriétés du nœud
            
        Returns:
            Nœud créé
        """
        pass
    
    @abstractmethod
    def delete_node(self, project_id: str, node_id: str) -> bool:
        """
        Supprime un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            True si supprimé avec succès
        """
        pass
    
    @abstractmethod
    def start_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Démarre un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat du démarrage
        """
        pass
    
    @abstractmethod
    def stop_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Arrête un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'arrêt
        """
        pass
    
    @abstractmethod
    def restart_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Redémarre un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat du redémarrage
        """
        pass
    
    @abstractmethod
    def get_node_console(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les informations de console d'un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Informations de console
        """
        pass
    
    @abstractmethod
    def create_link(
        self,
        project_id: str,
        source_node_id: str,
        source_port: int,
        target_node_id: str,
        target_port: int
    ) -> Dict[str, Any]:
        """
        Crée un lien GNS3.
        
        Args:
            project_id: ID du projet
            source_node_id: ID du nœud source
            source_port: Port du nœud source
            target_node_id: ID du nœud cible
            target_port: Port du nœud cible
            
        Returns:
            Lien créé
        """
        pass
    
    @abstractmethod
    def delete_link(self, project_id: str, link_id: str) -> bool:
        """
        Supprime un lien GNS3.
        
        Args:
            project_id: ID du projet
            link_id: ID du lien
            
        Returns:
            True si supprimé avec succès
        """
        pass
    
    @abstractmethod
    def get_link(self, project_id: str, link_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un lien GNS3.
        
        Args:
            project_id: ID du projet
            link_id: ID du lien
            
        Returns:
            Informations du lien
        """
        pass
    
    @abstractmethod
    def list_links(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les liens d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des liens
        """
        pass
    
    @abstractmethod
    def create_snapshot(self, project_id: str, name: str = None) -> Dict[str, Any]:
        """
        Crée un snapshot d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            name: Nom du snapshot
            
        Returns:
            Snapshot créé
        """
        pass
    
    @abstractmethod
    def restore_snapshot(self, project_id: str, snapshot_id: str) -> Dict[str, Any]:
        """
        Restaure un snapshot d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            
        Returns:
            Résultat de la restauration
        """
        pass
    
    @abstractmethod
    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les snapshots d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des snapshots
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques d'utilisation du client.
        
        Returns:
            Métriques d'utilisation
        """
        pass
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """
        Réinitialise les métriques du client.
        """
        pass


class GNS3AutomationService(ABC):
    """
    Interface pour le service d'automatisation GNS3.
    
    Cette interface définit le contrat que doit respecter
    tout service permettant d'automatiser des tâches sur GNS3.
    """
    
    @abstractmethod
    def execute_script(
        self,
        project_id: str,
        node_id: str,
        script_id: int,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Exécute un script sur un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            script_id: ID du script à exécuter
            parameters: Paramètres du script
            
        Returns:
            Résultat de l'exécution
        """
        pass
    
    @abstractmethod
    def execute_command(
        self,
        project_id: str,
        node_id: str,
        command: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Exécute une commande sur un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            command: Commande à exécuter
            timeout: Timeout en secondes
            
        Returns:
            Résultat de l'exécution
        """
        pass
    
    @abstractmethod
    def deploy_configuration(
        self,
        project_id: str,
        node_id: str,
        configuration: str,
        config_type: str = "startup-config"
    ) -> Dict[str, Any]:
        """
        Déploie une configuration sur un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            configuration: Configuration à déployer
            config_type: Type de configuration (startup-config, running-config...)
            
        Returns:
            Résultat du déploiement
        """
        pass
    
    @abstractmethod
    def run_workflow(
        self,
        project_id: str,
        workflow_id: int,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Exécute un workflow sur un projet GNS3.
        
        Args:
            project_id: ID du projet
            workflow_id: ID du workflow à exécuter
            parameters: Paramètres du workflow
            
        Returns:
            Résultat de l'exécution
        """
        pass
    
    @abstractmethod
    def check_workflow_status(self, execution_id: int) -> Dict[str, Any]:
        """
        Vérifie le statut d'exécution d'un workflow.
        
        Args:
            execution_id: ID de l'exécution
            
        Returns:
            Statut de l'exécution
        """
        pass
    
    @abstractmethod
    def cancel_workflow(self, execution_id: int) -> bool:
        """
        Annule l'exécution d'un workflow.
        
        Args:
            execution_id: ID de l'exécution
            
        Returns:
            True si annulé avec succès
        """
        pass 