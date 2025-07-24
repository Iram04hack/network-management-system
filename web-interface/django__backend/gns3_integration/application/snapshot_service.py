"""
Service d'application pour la gestion des snapshots GNS3.

Ce module contient les services d'application qui orchestrent les opérations
liées aux snapshots GNS3 entre les interfaces de domaine et l'extérieur.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.models import Snapshot, Project
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class SnapshotService:
    """
    Service pour la gestion des snapshots GNS3.
    
    Ce service orchestre les opérations entre le client GNS3,
    le repository et les entités du domaine pour la gestion des snapshots.
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
    
    def list_snapshots(self, project_id: str) -> List[Snapshot]:
        """
        Liste tous les snapshots d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des snapshots
            
        Raises:
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérifier que le projet existe
            project = Project.objects.get(project_id=project_id)
            
            # Récupération des snapshots depuis la base de données
            return Snapshot.objects.filter(project=project).order_by('-created_at')
        except Project.DoesNotExist:
            logger.warning(f"Projet {project_id} non trouvé")
            raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des snapshots: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des snapshots: {e}")
    
    def get_snapshot(self, project_id: str, snapshot_id: str) -> Optional[Snapshot]:
        """
        Récupère les détails d'un snapshot GNS3.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            
        Returns:
            Snapshot ou None si non trouvé
            
        Raises:
            GNS3ResourceNotFoundError: Snapshot non trouvé
        """
        try:
            project = Project.objects.get(project_id=project_id)
            return Snapshot.objects.get(project=project, snapshot_id=snapshot_id)
        except (Project.DoesNotExist, Snapshot.DoesNotExist):
            logger.warning(f"Snapshot {snapshot_id} non trouvé dans le projet {project_id}")
            raise GNS3ResourceNotFoundError(f"Snapshot {snapshot_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du snapshot: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération du snapshot: {e}")
    
    @transaction.atomic
    def create_snapshot(self, project_id: str, name: str, description: str = "", created_by: Optional[User] = None) -> Snapshot:
        """
        Crée un nouveau snapshot GNS3.
        
        Args:
            project_id: ID du projet
            name: Nom du snapshot
            description: Description du snapshot
            created_by: Utilisateur créateur
            
        Returns:
            Snapshot créé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3OperationError: Erreur lors de la création
        """
        try:
            # Vérifier que le projet existe
            project = Project.objects.get(project_id=project_id)
            
            # Créer le snapshot sur le serveur GNS3
            gns3_snapshot = self.client.create_snapshot(project_id, name)
            
            # Créer l'entité Snapshot
            snapshot = Snapshot.objects.create(
                project=project,
                name=name,
                snapshot_id=gns3_snapshot.get("snapshot_id", f"snapshot-{datetime.now().timestamp()}"),
                description=description,
                created_by=created_by
            )
            
            return snapshot
        except Project.DoesNotExist:
            logger.warning(f"Projet {project_id} non trouvé pour création de snapshot")
            raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la création du snapshot: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création du snapshot: {e}")
            raise GNS3Exception(f"Erreur lors de la création du snapshot: {e}")
    
    @transaction.atomic
    def delete_snapshot(self, project_id: str, snapshot_id: str) -> bool:
        """
        Supprime un snapshot GNS3.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            GNS3ResourceNotFoundError: Snapshot non trouvé
            GNS3OperationError: Erreur lors de la suppression
        """
        try:
            # Récupérer le snapshot
            project = Project.objects.get(project_id=project_id)
            snapshot = Snapshot.objects.get(project=project, snapshot_id=snapshot_id)
            
            # Supprimer sur le serveur GNS3
            if not self.client.delete_snapshot(project_id, snapshot_id):
                logger.error(f"Échec de la suppression du snapshot {snapshot_id}")
                raise GNS3OperationError(f"Échec de la suppression du snapshot {snapshot_id}")
            
            # Supprimer de la base de données
            snapshot.delete()
            return True
        except (Project.DoesNotExist, Snapshot.DoesNotExist):
            logger.warning(f"Snapshot {snapshot_id} non trouvé pour suppression")
            raise GNS3ResourceNotFoundError(f"Snapshot {snapshot_id} non trouvé")
        except GNS3OperationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du snapshot: {e}")
            raise GNS3Exception(f"Erreur lors de la suppression du snapshot: {e}")
    
    @transaction.atomic
    def restore_snapshot(self, project_id: str, snapshot_id: str) -> bool:
        """
        Restaure un snapshot GNS3.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            
        Returns:
            True si restauré avec succès
            
        Raises:
            GNS3ResourceNotFoundError: Snapshot non trouvé
            GNS3OperationError: Erreur lors de la restauration
        """
        try:
            # Vérifier que le snapshot existe
            project = Project.objects.get(project_id=project_id)
            snapshot = Snapshot.objects.get(project=project, snapshot_id=snapshot_id)
            
            # Restaurer sur le serveur GNS3
            if not self.client.restore_snapshot(project_id, snapshot_id):
                logger.error(f"Échec de la restauration du snapshot {snapshot_id}")
                raise GNS3OperationError(f"Échec de la restauration du snapshot {snapshot_id}")
            
            logger.info(f"Snapshot {snapshot_id} restauré avec succès")
            return True
        except (Project.DoesNotExist, Snapshot.DoesNotExist):
            logger.warning(f"Snapshot {snapshot_id} non trouvé pour restauration")
            raise GNS3ResourceNotFoundError(f"Snapshot {snapshot_id} non trouvé")
        except GNS3OperationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la restauration du snapshot: {e}")
            raise GNS3Exception(f"Erreur lors de la restauration du snapshot: {e}") 