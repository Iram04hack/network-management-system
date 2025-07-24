"""
Service d'application pour la gestion des nœuds GNS3.

Ce module contient les services d'application qui orchestrent les opérations
liées aux nœuds (appareils) GNS3 entre les interfaces de domaine et l'extérieur.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from django.db import transaction
from django.contrib.auth.models import User

from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.domain.models import Node, Project
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class NodeService:
    """
    Service pour la gestion des nœuds GNS3.
    
    Ce service orchestre les opérations entre le client GNS3,
    le repository et les entités du domaine pour la gestion des nœuds (appareils).
    """
    
    def __init__(self, gns3_client: GNS3ClientPort, gns3_repository: GNS3Repository):
        """
        Initialise le service.
        
        Args:
            gns3_client: Client GNS3
            gns3_repository: Repository GNS3
        """
        self.client = gns3_client
        self.repository = gns3_repository
    
    def list_nodes(self, project_id: str) -> List[Node]:
        """
        Liste tous les nœuds d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des nœuds
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour lister les nœuds")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupération des nœuds depuis le repository
            return self.repository.list_nodes(project_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération des nœuds du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des nœuds du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des nœuds: {e}")
    
    def get_node(self, project_id: str, node_id: str) -> Optional[Node]:
        """
        Récupère les détails d'un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Nœud ou None si non trouvé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour récupérer le nœud")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupération du nœud depuis le repository
            node = self.repository.get_node(project_id, node_id)
            
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
                
            return node
        except GNS3ResourceNotFoundError:
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération du nœud: {e}")
    
    @transaction.atomic
    def create_node(self, project_id: str, template_id: str, name: str = None,
                   compute_id: str = "local", x: int = 0, y: int = 0,
                   created_by: Optional[User] = None) -> Node:
        """
        Crée un nouveau nœud dans un projet GNS3.
        
        Args:
            project_id: ID du projet
            template_id: ID du template à utiliser
            name: Nom du nœud (optionnel)
            compute_id: ID du serveur de calcul (défaut: "local")
            x: Position X du nœud (défaut: 0)
            y: Position Y du nœud (défaut: 0)
            created_by: Utilisateur créateur (optionnel)
            
        Returns:
            Nœud créé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou template non trouvé
            GNS3OperationError: Erreur lors de la création
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour créer un nœud")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Vérification que le projet est ouvert
            if project.status != "open":
                logger.warning(f"Tentative de création d'un nœud dans un projet fermé: {project_id}")
                # Ouverture automatique du projet
                self.client.open_project(project_id)
                project.status = "open"
                project.updated_at = datetime.now()
                self.repository.save_project(project)
                
            # Création du nœud sur le serveur GNS3
            gns3_node = self.client.create_node(
                project_id=project_id,
                template_id=template_id,
                name=name,
                compute_id=compute_id,
                x=x,
                y=y
            )
            
            # Création de l'entité Node
            node = Node(
                id=gns3_node["node_id"],
                name=gns3_node["name"],
                project_id=project_id,
                node_type=gns3_node.get("node_type", ""),
                compute_id=gns3_node.get("compute_id", "local"),
                console=gns3_node.get("console", None),
                console_type=gns3_node.get("console_type", ""),
                x=gns3_node.get("x", 0),
                y=gns3_node.get("y", 0),
                z=gns3_node.get("z", 0),
                status=gns3_node.get("status", "stopped"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by_id=created_by.id if created_by else None
            )
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la création du nœud dans le projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la création du nœud dans le projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la sauvegarde du nœud dans le projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création du nœud dans le projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la création du nœud: {e}")
    
    @transaction.atomic
    def delete_node(self, project_id: str, node_id: str) -> bool:
        """
        Supprime un nœud d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors de la suppression
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour supprimer le nœud")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
                
            # Vérification de l'existence du nœud
            node = self.repository.get_node(project_id, node_id)
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Suppression sur le serveur GNS3
            if not self.client.delete_node(project_id, node_id):
                logger.error(f"Échec de la suppression du nœud {node_id} sur le serveur GNS3")
                raise GNS3OperationError(f"Échec de la suppression du nœud {node_id}")
            
            # Suppression dans le repository
            return self.repository.delete_node(project_id, node_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la suppression du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la suppression du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la suppression du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la suppression du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la suppression du nœud: {e}")
    
    @transaction.atomic
    def start_node(self, project_id: str, node_id: str) -> Node:
        """
        Démarre un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Nœud démarré
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors du démarrage
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du nœud
            node = self.repository.get_node(project_id, node_id)
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Démarrage sur le serveur GNS3
            gns3_node = self.client.start_node(project_id, node_id)
            
            # Mise à jour de l'entité Node
            node.status = "started"
            node.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors du démarrage du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors du démarrage du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du démarrage du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors du démarrage du nœud: {e}")
    
    @transaction.atomic
    def stop_node(self, project_id: str, node_id: str) -> Node:
        """
        Arrête un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Nœud arrêté
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors de l'arrêt
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du nœud
            node = self.repository.get_node(project_id, node_id)
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Arrêt sur le serveur GNS3
            gns3_node = self.client.stop_node(project_id, node_id)
            
            # Mise à jour de l'entité Node
            node.status = "stopped"
            node.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de l'arrêt du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de l'arrêt du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'arrêt du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de l'arrêt du nœud: {e}")
    
    @transaction.atomic
    def reload_node(self, project_id: str, node_id: str) -> Node:
        """
        Redémarre un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Nœud redémarré
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors du redémarrage
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du nœud
            node = self.repository.get_node(project_id, node_id)
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Redémarrage sur le serveur GNS3
            gns3_node = self.client.reload_node(project_id, node_id)
            
            # Mise à jour de l'entité Node
            node.status = "started"
            node.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors du redémarrage du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors du redémarrage du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du redémarrage du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors du redémarrage du nœud: {e}")
    
    @transaction.atomic
    def update_node_position(self, project_id: str, node_id: str, x: int, y: int, z: int = 0) -> Node:
        """
        Met à jour la position d'un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            x: Position X du nœud
            y: Position Y du nœud
            z: Position Z du nœud (défaut: 0)
            
        Returns:
            Nœud mis à jour
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors de la mise à jour
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du nœud
            node = self.repository.get_node(project_id, node_id)
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Mise à jour sur le serveur GNS3
            gns3_node = self.client.update_node(
                project_id=project_id,
                node_id=node_id,
                x=x,
                y=y,
                z=z
            )
            
            # Mise à jour de l'entité Node
            node.x = x
            node.y = y
            node.z = z
            node.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la mise à jour du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la mise à jour du nœud: {e}")
    
    @transaction.atomic
    def update_node_name(self, project_id: str, node_id: str, name: str) -> Node:
        """
        Met à jour le nom d'un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            name: Nouveau nom du nœud
            
        Returns:
            Nœud mis à jour
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors de la mise à jour
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du nœud
            node = self.repository.get_node(project_id, node_id)
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Mise à jour sur le serveur GNS3
            gns3_node = self.client.update_node(
                project_id=project_id,
                node_id=node_id,
                name=name
            )
            
            # Mise à jour de l'entité Node
            node.name = name
            node.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la mise à jour du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la mise à jour du nœud: {e}")
    
    @transaction.atomic
    def sync_node(self, project_id: str, node_id: str) -> Node:
        """
        Synchronise un nœud entre GNS3 et le repository.
        
        Cette méthode récupère les informations à jour du nœud sur le serveur GNS3
        et les synchronise avec le repository.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Nœud synchronisé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
            GNS3OperationError: Erreur lors de la synchronisation
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération des informations à jour sur le serveur GNS3
            gns3_node = self.client.get_node(project_id, node_id)
            
            # Récupération du nœud depuis le repository
            node = self.repository.get_node(project_id, node_id)
            
            if not node:
                # Création d'une nouvelle entité Node si elle n'existe pas
                node = Node(
                    id=gns3_node["node_id"],
                    name=gns3_node["name"],
                    project_id=project_id,
                    node_type=gns3_node.get("node_type", ""),
                    compute_id=gns3_node.get("compute_id", "local"),
                    console=gns3_node.get("console", None),
                    console_type=gns3_node.get("console_type", ""),
                    x=gns3_node.get("x", 0),
                    y=gns3_node.get("y", 0),
                    z=gns3_node.get("z", 0),
                    status=gns3_node.get("status", "stopped"),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                # Mise à jour de l'entité Node existante
                node.name = gns3_node["name"]
                node.node_type = gns3_node.get("node_type", node.node_type)
                node.compute_id = gns3_node.get("compute_id", node.compute_id)
                node.console = gns3_node.get("console", node.console)
                node.console_type = gns3_node.get("console_type", node.console_type)
                node.x = gns3_node.get("x", node.x)
                node.y = gns3_node.get("y", node.y)
                node.z = gns3_node.get("z", node.z)
                node.status = gns3_node.get("status", node.status)
                node.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_node(node)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la synchronisation du nœud {node_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la synchronisation du nœud {node_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la synchronisation du nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la synchronisation du nœud: {e}")
    
    def get_console_url(self, project_id: str, node_id: str) -> str:
        """
        Récupère l'URL de console d'un nœud GNS3.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            URL de console
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœud non trouvé
        """
        try:
            # Récupération du nœud depuis le repository
            node = self.repository.get_node(project_id, node_id)
            
            if not node:
                logger.warning(f"Nœud {node_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node_id} non trouvé")
            
            # Récupération de l'URL de console sur le serveur GNS3
            return self.client.get_console_url(project_id, node_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la récupération de l'URL de console pour le nœud {node_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération de l'URL de console pour le nœud {node_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération de l'URL de console: {e}") 