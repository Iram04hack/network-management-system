"""
Service d'application pour la gestion des projets GNS3.

Ce module contient les services d'application qui orchestrent les opérations
liées aux projets GNS3 entre les interfaces de domaine et l'extérieur.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from django.db import transaction
from django.contrib.auth.models import User

from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.domain.models import Project, Node, Link
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class ProjectService:
    """
    Service pour la gestion des projets GNS3.
    
    Ce service orchestre les opérations entre le client GNS3,
    le repository et les entités du domaine pour la gestion des projets.
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
    
    def list_projects(self) -> List[Project]:
        """
        Liste tous les projets GNS3.
        
        Returns:
            Liste des projets
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération des projets depuis le repository
            return self.repository.list_projects()
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération des projets: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des projets: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des projets: {e}")
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Récupère les détails d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet ou None si non trouvé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération du projet depuis le repository
            project = self.repository.get_project(project_id)
            
            if not project:
                logger.warning(f"Projet {project_id} non trouvé dans le repository")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
                
            return project
        except GNS3ResourceNotFoundError:
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération du projet: {e}")
    
    @transaction.atomic
    def create_project(self, name: str, description: str = "", created_by: Optional[User] = None) -> Project:
        """
        Crée un nouveau projet GNS3.
        
        Args:
            name: Nom du projet
            description: Description du projet
            created_by: Utilisateur créateur
            
        Returns:
            Projet créé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3OperationError: Erreur lors de la création
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Création du projet sur le serveur GNS3
            gns3_project = self.client.create_project(name, description)
            
            # Création de l'entité Project
            project = Project(
                id=gns3_project["project_id"],
                name=gns3_project["name"],
                status=gns3_project.get("status", "closed"),
                path=gns3_project.get("path", ""),
                filename=gns3_project.get("filename", ""),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by_id=created_by.id if created_by else None,
                description=description
            )
            
            # Sauvegarde dans le repository
            return self.repository.save_project(project)
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la création du projet {name}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la création du projet {name}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la sauvegarde du projet {name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création du projet {name}: {e}")
            raise GNS3Exception(f"Erreur lors de la création du projet: {e}")
    
    @transaction.atomic
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de la suppression
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour suppression")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Suppression sur le serveur GNS3
            if not self.client.delete_project(project_id):
                logger.error(f"Échec de la suppression du projet {project_id} sur le serveur GNS3")
                raise GNS3OperationError(f"Échec de la suppression du projet {project_id}")
            
            # Suppression dans le repository
            return self.repository.delete_project(project_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la suppression du projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la suppression du projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la suppression du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la suppression du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la suppression du projet: {e}")
    
    @transaction.atomic
    def open_project(self, project_id: str) -> Project:
        """
        Ouvre un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet ouvert
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de l'ouverture
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour ouverture")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Ouverture sur le serveur GNS3
            gns3_project = self.client.open_project(project_id)
            
            # Mise à jour de l'entité Project
            project.status = "open"
            project.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_project(project)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de l'ouverture du projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de l'ouverture du projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'ouverture du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de l'ouverture du projet: {e}")
    
    @transaction.atomic
    def close_project(self, project_id: str) -> Project:
        """
        Ferme un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet fermé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de la fermeture
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour fermeture")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Fermeture sur le serveur GNS3
            gns3_project = self.client.close_project(project_id)
            
            # Mise à jour de l'entité Project
            project.status = "closed"
            project.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_project(project)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la fermeture du projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la fermeture du projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la fermeture du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la fermeture du projet: {e}")
    
    @transaction.atomic
    def sync_project(self, project_id: str) -> Project:
        """
        Synchronise un projet entre GNS3 et le repository.
        
        Cette méthode récupère les informations à jour du projet sur le serveur GNS3
        et les synchronise avec le repository.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Projet synchronisé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de la synchronisation
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération des informations à jour sur le serveur GNS3
            gns3_project = self.client.get_project(project_id)
            
            # Récupération du projet depuis le repository
            project = self.repository.get_project(project_id)
            
            if not project:
                # Création d'une nouvelle entité Project si elle n'existe pas
                project = Project(
                    id=gns3_project["project_id"],
                    name=gns3_project["name"],
                    status=gns3_project.get("status", "closed"),
                    path=gns3_project.get("path", ""),
                    filename=gns3_project.get("filename", ""),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                # Mise à jour de l'entité Project existante
                project.name = gns3_project["name"]
                project.status = gns3_project.get("status", project.status)
                project.path = gns3_project.get("path", project.path)
                project.filename = gns3_project.get("filename", project.filename)
                project.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_project(project)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la synchronisation du projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la synchronisation du projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la synchronisation du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la synchronisation du projet: {e}")
    
    def create_snapshot(self, project_id: str, name: str = None, created_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Crée un snapshot d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            name: Nom du snapshot (optionnel)
            created_by: Utilisateur créateur (optionnel)
            
        Returns:
            Informations du snapshot créé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de la création du snapshot
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour snapshot")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Génération d'un nom si non fourni
            snapshot_name = name or f"Snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Création du snapshot sur le serveur GNS3
            gns3_snapshot = self.client.create_snapshot(project_id, snapshot_name)
            
            # Sauvegarde dans le repository
            self.repository.save_snapshot(
                project_id=project_id,
                snapshot_id=gns3_snapshot["snapshot_id"],
                snapshot_name=gns3_snapshot["name"]
            )
            
            return gns3_snapshot
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la création du snapshot pour le projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la création du snapshot pour le projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la sauvegarde du snapshot pour le projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création du snapshot pour le projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la création du snapshot: {e}")
    
    def restore_snapshot(self, project_id: str, snapshot_id: str) -> bool:
        """
        Restaure un snapshot d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            
        Returns:
            True si restauré avec succès
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet ou snapshot non trouvé
            GNS3OperationError: Erreur lors de la restauration
        """
        try:
            # Restauration sur le serveur GNS3
            self.client.restore_snapshot(project_id, snapshot_id)
            
            # Synchronisation du projet après restauration
            self.sync_project(project_id)
            
            return True
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la restauration du snapshot {snapshot_id} pour le projet {project_id}: {e}")
            raise
        except GNS3OperationError as e:
            logger.error(f"Erreur d'opération lors de la restauration du snapshot {snapshot_id} pour le projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la restauration du snapshot {snapshot_id} pour le projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la restauration du snapshot: {e}")
    
    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste les snapshots d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des snapshots
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour la liste des snapshots")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupération des snapshots depuis le repository
            return self.repository.list_snapshots(project_id)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la récupération des snapshots pour le projet {project_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération des snapshots pour le projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des snapshots pour le projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des snapshots: {e}")
    
    @transaction.atomic
    def sync_all_projects(self) -> List[Project]:
        """
        Synchronise TOUS les projets depuis le serveur GNS3 vers la base de données Django.
        
        Cette méthode récupère tous les projets directement du serveur GNS3
        et les synchronise avec la base de données Django.
        
        Returns:
            Liste de tous les projets synchronisés
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            logger.info("🔄 Début de la synchronisation de tous les projets GNS3...")
            
            # Récupération des projets directement depuis le serveur GNS3
            gns3_projects = self.client.list_projects()
            logger.info(f"📡 {len(gns3_projects)} projets trouvés sur le serveur GNS3")
            
            synchronized_projects = []
            
            for gns3_project in gns3_projects:
                try:
                    # Récupération du projet depuis le repository
                    project = self.repository.get_project(gns3_project["project_id"])
                    
                    if not project:
                        # Création d'une nouvelle entité Project si elle n'existe pas
                        project = Project(
                            id=gns3_project["project_id"],
                            name=gns3_project["name"],
                            status=gns3_project.get("status", "closed"),
                            path=gns3_project.get("path", ""),
                            filename=gns3_project.get("filename", ""),
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            auto_start=gns3_project.get("auto_start", False),
                            auto_close=gns3_project.get("auto_close", True),
                            description=gns3_project.get("description", "")
                        )
                        logger.info(f"✨ Nouveau projet créé: {project.name}")
                    else:
                        # Mise à jour de l'entité Project existante
                        project.name = gns3_project["name"]
                        project.status = gns3_project.get("status", project.status)
                        project.path = gns3_project.get("path", project.path)
                        project.filename = gns3_project.get("filename", project.filename)
                        project.auto_start = gns3_project.get("auto_start", project.auto_start)
                        project.auto_close = gns3_project.get("auto_close", project.auto_close)
                        project.updated_at = datetime.now()
                        logger.info(f"🔄 Projet mis à jour: {project.name}")
                    
                    # Sauvegarde dans le repository
                    saved_project = self.repository.save_project(project)
                    synchronized_projects.append(saved_project)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la synchronisation du projet {gns3_project.get('name', 'Inconnu')}: {e}")
                    continue
            
            logger.info(f"✅ Synchronisation terminée: {len(synchronized_projects)} projets synchronisés")
            
            # Invalider le cache pour forcer le rafraîchissement
            if hasattr(self.repository, 'invalidate_cache'):
                self.repository.invalidate_cache()
            
            return synchronized_projects
            
        except GNS3ConnectionError as e:
            logger.error(f"❌ Erreur de connexion lors de la synchronisation des projets: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de la synchronisation des projets: {e}")
            raise GNS3Exception(f"Erreur lors de la synchronisation des projets: {e}")

    def get_all_projects(self, force_sync: bool = False) -> List[Project]:
        """
        Récupère tous les projets GNS3.
        
        Args:
            force_sync: Force la synchronisation avec le serveur GNS3
        
        Returns:
            Liste de tous les projets
        """
        if force_sync:
            return self.sync_all_projects()
        else:
            # Essayer d'abord de récupérer depuis la base de données
            projects = self.list_projects()
            
            # Si aucun projet n'est trouvé, synchroniser automatiquement
            if not projects:
                logger.info("🔄 Aucun projet en base de données, synchronisation automatique...")
                projects = self.sync_all_projects()
            
            return projects
    
    def start_all_nodes(self, project_id: str) -> Dict[str, Any]:
        """
        Démarre tous les nœuds d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Résultat de l'opération avec les nœuds démarrés et en échec
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors du démarrage
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour démarrage des nœuds")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupérer la liste des nœuds du projet
            nodes = self.client.list_nodes(project_id)
            
            started_nodes = []
            failed_nodes = []
            
            for node in nodes:
                try:
                    node_id = node.get('node_id')
                    if node.get('status') != 'started':
                        # Démarrer le nœud
                        self.client.start_node(project_id, node_id)
                        started_nodes.append({
                            'node_id': node_id,
                            'name': node.get('name', 'Unknown'),
                            'node_type': node.get('node_type', 'Unknown')
                        })
                        logger.info(f"Nœud {node.get('name')} démarré avec succès")
                    else:
                        started_nodes.append({
                            'node_id': node_id,
                            'name': node.get('name', 'Unknown'),
                            'node_type': node.get('node_type', 'Unknown'),
                            'already_started': True
                        })
                except Exception as e:
                    failed_nodes.append({
                        'node_id': node.get('node_id'),
                        'name': node.get('name', 'Unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Échec du démarrage du nœud {node.get('name')}: {e}")
            
            result = {
                'started_nodes': started_nodes,
                'failed_nodes': failed_nodes,
                'total_nodes': len(nodes),
                'success_count': len(started_nodes),
                'failure_count': len(failed_nodes)
            }
            
            logger.info(f"Démarrage des nœuds du projet {project_id}: {len(started_nodes)} succès, {len(failed_nodes)} échecs")
            return result
            
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors du démarrage des nœuds du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du démarrage des nœuds du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors du démarrage des nœuds: {e}")
    
    def stop_all_nodes(self, project_id: str) -> Dict[str, Any]:
        """
        Arrête tous les nœuds d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Résultat de l'opération avec les nœuds arrêtés et en échec
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de l'arrêt
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour arrêt des nœuds")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupérer la liste des nœuds du projet
            nodes = self.client.list_nodes(project_id)
            
            stopped_nodes = []
            failed_nodes = []
            
            for node in nodes:
                try:
                    node_id = node.get('node_id')
                    if node.get('status') == 'started':
                        # Arrêter le nœud
                        self.client.stop_node(project_id, node_id)
                        stopped_nodes.append({
                            'node_id': node_id,
                            'name': node.get('name', 'Unknown'),
                            'node_type': node.get('node_type', 'Unknown')
                        })
                        logger.info(f"Nœud {node.get('name')} arrêté avec succès")
                    else:
                        stopped_nodes.append({
                            'node_id': node_id,
                            'name': node.get('name', 'Unknown'),
                            'node_type': node.get('node_type', 'Unknown'),
                            'already_stopped': True
                        })
                except Exception as e:
                    failed_nodes.append({
                        'node_id': node.get('node_id'),
                        'name': node.get('name', 'Unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Échec de l'arrêt du nœud {node.get('name')}: {e}")
            
            result = {
                'stopped_nodes': stopped_nodes,
                'failed_nodes': failed_nodes,
                'total_nodes': len(nodes),
                'success_count': len(stopped_nodes),
                'failure_count': len(failed_nodes)
            }
            
            logger.info(f"Arrêt des nœuds du projet {project_id}: {len(stopped_nodes)} succès, {len(failed_nodes)} échecs")
            return result
            
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de l'arrêt des nœuds du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'arrêt des nœuds du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de l'arrêt des nœuds: {e}")
    
    def duplicate_project(self, project_id: str, new_name: str, reset_mac_addresses: bool = True) -> Project:
        """
        Duplique un projet GNS3 existant.
        
        Args:
            project_id: ID du projet à dupliquer
            new_name: Nom du nouveau projet
            reset_mac_addresses: Si les adresses MAC doivent être réinitialisées
            
        Returns:
            Nouveau projet créé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de la duplication
        """
        try:
            # Vérification de l'existence du projet source
            source_project = self.repository.get_project(project_id)
            if not source_project:
                logger.warning(f"Projet source {project_id} non trouvé pour duplication")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Duplication sur le serveur GNS3
            duplicate_data = self.client.duplicate_project(project_id, new_name, reset_mac_addresses)
            
            # Création de l'entité Project pour le duplicata
            new_project = Project(
                id=duplicate_data["project_id"],
                name=duplicate_data["name"],
                status=duplicate_data.get("status", "closed"),
                path=duplicate_data.get("path", ""),
                filename=duplicate_data.get("filename", ""),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                description=f"Copie de {source_project.name}"
            )
            
            # Sauvegarde dans le repository
            return self.repository.save_project(new_project)
            
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la duplication du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la duplication du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la duplication du projet: {e}")
    
    def export_project(self, project_id: str) -> Dict[str, Any]:
        """
        Exporte un projet GNS3 vers un fichier archive.
        
        Args:
            project_id: ID du projet à exporter
            
        Returns:
            Informations sur l'export (chemin, taille, etc.)
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3OperationError: Erreur lors de l'export
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour export")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Export sur le serveur GNS3
            export_data = self.client.export_project(project_id)
            
            result = {
                'export_path': export_data.get('export_path', ''),
                'file_size': export_data.get('file_size', 0),
                'exported_at': datetime.now().isoformat(),
                'project_name': project.name
            }
            
            logger.info(f"Projet {project_id} exporté avec succès")
            return result
            
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de l'export du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'export du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de l'export du projet: {e}")
    
    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques détaillées d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Statistiques du projet
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Projet non trouvé
        """
        try:
            # Vérification de l'existence du projet
            project = self.repository.get_project(project_id)
            if not project:
                logger.warning(f"Projet {project_id} non trouvé pour statistiques")
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupérer les nœuds du projet
            nodes = self.client.list_nodes(project_id)
            
            # Compter les types de nœuds et statuts
            node_types = {}
            node_statuses = {'started': 0, 'stopped': 0, 'suspended': 0}
            total_memory = 0
            total_cpu = 0
            
            for node in nodes:
                # Types de nœuds
                node_type = node.get('node_type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
                
                # Statuts des nœuds
                status = node.get('status', 'stopped')
                if status in node_statuses:
                    node_statuses[status] += 1
                
                # Ressources (approximatives)
                properties = node.get('properties', {})
                if 'ram' in properties:
                    total_memory += properties.get('ram', 0)
                if 'cpus' in properties:
                    total_cpu += properties.get('cpus', 1)
            
            # Récupérer les liens
            links = self.client.get_project_links(project_id)
            
            # Récupérer les snapshots
            snapshots = self.repository.list_snapshots(project_id)
            
            statistics = {
                'project_id': project_id,
                'project_name': project.name,
                'project_status': project.status,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                'nodes': {
                    'total_count': len(nodes),
                    'by_type': node_types,
                    'by_status': node_statuses
                },
                'links': {
                    'total_count': len(links)
                },
                'snapshots': {
                    'total_count': len(snapshots)
                },
                'resources': {
                    'estimated_memory_mb': total_memory,
                    'estimated_cpu_cores': total_cpu
                },
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Statistiques générées pour le projet {project_id}")
            return statistics
            
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la récupération des statistiques du projet {project_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des statistiques du projet {project_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des statistiques: {e}")