"""
Service d'application pour la gestion des liens GNS3.

Ce module contient les services d'application qui orchestrent les opérations
liées aux liens entre nœuds GNS3 entre les interfaces de domaine et l'extérieur.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from django.db import transaction
from django.contrib.auth.models import User

from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.domain.models import Link, Node
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class LinkService:
    """
    Service pour la gestion des liens GNS3.
    
    Ce service orchestre les opérations entre le client GNS3,
    le repository et les entités du domaine pour la gestion des liens entre nœuds.
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
    
    def list_links(self, project_id: str) -> List[Link]:
        """
        Liste tous les liens d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des liens
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour lister les liens")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupération des liens depuis le repository
            return self.repository.list_links(project_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération des liens du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des liens du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des liens: {e}")
    
    def get_link(self, project_id: str, link_id: str) -> Optional[Link]:
        """
        Récupère les détails d'un lien GNS3.
        
        Args:
            project_id: ID du projet
            link_id: ID du lien
            
        Returns:
            Lien ou None si non trouvé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou lien non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour récupérer le lien")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupération du lien depuis le repository
            link = self.repository.get_link(project_id, link_id)
            
            if not link:
                logger.warning(f"Lien {link_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Lien {link_id} non trouvé")
                
            return link
        except GNS3ResourceNotFoundError:
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération du lien {link_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération du lien {link_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération du lien: {e}")
    
    @transaction.atomic
    def create_link(self, project_id: str, node1_id: str, port1_id: str, 
                   node2_id: str, port2_id: str,
                   created_by: Optional[User] = None) -> Link:
        """
        Crée un nouveau lien entre deux nœuds d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            node1_id: ID du premier nœud
            port1_id: ID du port du premier nœud
            node2_id: ID du deuxième nœud
            port2_id: ID du port du deuxième nœud
            created_by: Utilisateur créateur (optionnel)
            
        Returns:
            Lien créé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou nœuds non trouvés
            GNS3OperationError: Erreur lors de la création
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour créer un lien")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Vérification de l'existence des nœuds
            node1 = self.repository.get_node(project_id, node1_id)
            if not node1:
                logger.warning(f"Nœud {node1_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node1_id} non trouvé")
                
            node2 = self.repository.get_node(project_id, node2_id)
            if not node2:
                logger.warning(f"Nœud {node2_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Nœud {node2_id} non trouvé")
            
            # Vérification que le projet est ouvert
            if project.status != "open":
                logger.warning(f"Tentative de création d'un lien dans un projet fermé: {project_id}")
                # Ouverture automatique du projet
                self.client.open_project(project_id)
                project.status = "open"
                project.updated_at = datetime.now()
                self.repository.save_project(project)
                
            # Création du lien sur le serveur GNS3
            gns3_link = self.client.create_link(
                project_id=project_id,
                node1_id=node1_id,
                port1_id=port1_id,
                node2_id=node2_id,
                port2_id=port2_id
            )
            
            # Création de l'entité Link
            link = Link(
                id=gns3_link["link_id"],
                project_id=project_id,
                node1_id=node1_id,
                port1_id=port1_id,
                node2_id=node2_id,
                port2_id=port2_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by_id=created_by.id if created_by else None
            )
            
            # Sauvegarde dans le repository
            return self.repository.save_link(link)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la création du lien dans le projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la création du lien dans le projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la sauvegarde du lien dans le projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création du lien dans le projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la création du lien: {e}")
    
    @transaction.atomic
    def delete_link(self, project_id: str, link_id: str) -> bool:
        """
        Supprime un lien d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            link_id: ID du lien
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou lien non trouvé
            GNS3OperationError: Erreur lors de la suppression
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour supprimer le lien")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
                
            # Vérification de l'existence du lien
            link = self.repository.get_link(project_id, link_id)
            if not link:
                logger.warning(f"Lien {link_id} non trouvé dans le projet {project_id}")
                raise GNS3ResourceNotFoundError(f"Lien {link_id} non trouvé")
            
            # Suppression sur le serveur GNS3
            if not self.client.delete_link(project_id, link_id):
                logger.error(f"Échec de la suppression du lien {link_id} sur le serveur GNS3")
                raise GNS3OperationError(f"Échec de la suppression du lien {link_id}")
            
            # Suppression dans le repository
            return self.repository.delete_link(project_id, link_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la suppression du lien {link_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la suppression du lien {link_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la suppression du lien {link_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la suppression du lien {link_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la suppression du lien: {e}")
    
    @transaction.atomic
    def sync_link(self, project_id: str, link_id: str) -> Link:
        """
        Synchronise un lien entre GNS3 et le repository.
        
        Cette méthode récupère les informations à jour du lien sur le serveur GNS3
        et les synchronise avec le repository.
        
        Args:
            project_id: ID du projet
            link_id: ID du lien
            
        Returns:
            Lien synchronisé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou lien non trouvé
            GNS3OperationError: Erreur lors de la synchronisation
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération des informations à jour sur le serveur GNS3
            gns3_link = self.client.get_link(project_id, link_id)
            
            # Récupération du lien depuis le repository
            link = self.repository.get_link(project_id, link_id)
            
            if not link:
                # Extraction des informations des nœuds et ports depuis la réponse GNS3
                node1_id = gns3_link["nodes"][0]["node_id"]
                port1_id = gns3_link["nodes"][0]["adapter_number"]
                node2_id = gns3_link["nodes"][1]["node_id"]
                port2_id = gns3_link["nodes"][1]["adapter_number"]
                
                # Création d'une nouvelle entité Link si elle n'existe pas
                link = Link(
                    id=gns3_link["link_id"],
                    project_id=project_id,
                    node1_id=node1_id,
                    port1_id=port1_id,
                    node2_id=node2_id,
                    port2_id=port2_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                # Mise à jour de l'entité Link existante si nécessaire
                # Dans ce cas, les liens n'ont pas beaucoup de propriétés modifiables
                # Mais on pourrait ajouter des informations supplémentaires comme le statut
                link.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_link(link)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la synchronisation du lien {link_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la synchronisation du lien {link_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du lien {link_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la synchronisation du lien {link_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la synchronisation du lien: {e}") 