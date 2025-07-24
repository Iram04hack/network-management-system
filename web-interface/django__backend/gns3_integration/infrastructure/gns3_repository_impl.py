"""
Implémentation du GNS3Repository.

Ce module contient l'implémentation concrète de l'interface GNS3Repository,
utilisant les modèles Django pour persister les données GNS3.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, F, Max
from django.core.cache import cache

from gns3_integration.domain.interfaces import GNS3Repository
from gns3_integration.domain.models import Project as ProjectEntity
from gns3_integration.domain.models import Node as NodeEntity
from gns3_integration.domain.models import Link as LinkEntity
from gns3_integration.domain.models import Server as ServerEntity
from gns3_integration.models import Project, Node, Link, Snapshot, GNS3Config, Server
from gns3_integration.domain.exceptions import GNS3RepositoryError

logger = logging.getLogger(__name__)

class DjangoGNS3Repository(GNS3Repository):
    """
    Implémentation Django du repository GNS3.
    
    Cette classe fournit les méthodes pour interagir avec les données
    persistantes de l'intégration GNS3, stockées dans une base de données Django.
    Elle assure la conversion entre les entités de domaine et les modèles ORM.
    """
    
    # Durée de cache par défaut
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialise le repository GNS3.
        
        Args:
            cache_enabled: Activation du cache pour les requêtes fréquentes
        """
        self.cache_enabled = cache_enabled
    
    def _cache_key(self, prefix: str, *args) -> str:
        """
        Génère une clé de cache.
        
        Args:
            prefix: Préfixe de la clé
            args: Arguments pour la clé
            
        Returns:
            Clé de cache
        """
        return f"gns3_repo:{prefix}:{':'.join([str(arg) for arg in args])}"
    
    def _to_project_entity(self, project_model: Project) -> ProjectEntity:
        """
        Convertit un modèle Project en entité de domaine.
        
        Args:
            project_model: Modèle Project Django
            
        Returns:
            Entité Project
        """
        if not project_model:
            return None
        
        return ProjectEntity(
            id=project_model.project_id,
            name=project_model.name,
            status=project_model.status,
            path=project_model.path,
            created_at=project_model.created_at,
            updated_at=project_model.updated_at,
            auto_start=project_model.auto_start,
            auto_close=project_model.auto_close,
            filename=project_model.filename,
            description=project_model.description
        )
    
    def _to_node_entity(self, node_model: Node) -> NodeEntity:
        """
        Convertit un modèle Node en entité de domaine.
        
        Args:
            node_model: Modèle Node Django
            
        Returns:
            Entité Node
        """
        if not node_model:
            return None
        
        return NodeEntity(
            id=node_model.node_id,
            name=node_model.name,
            project_id=node_model.project.project_id if node_model.project else None,
            node_type=node_model.node_type,
            status=node_model.status,
            console_type=node_model.console_type,
            console_port=node_model.console_port,
            x=node_model.x,
            y=node_model.y,
            symbol=node_model.symbol,
            properties=node_model.properties,
            compute_id=node_model.compute_id,
            created_at=node_model.created_at,
            updated_at=node_model.updated_at
        )
    
    def _to_link_entity(self, link_model: Link) -> LinkEntity:
        """
        Convertit un modèle Link en entité de domaine.
        
        Args:
            link_model: Modèle Link Django
            
        Returns:
            Entité Link
        """
        if not link_model:
            return None
        
        source_node = None
        if link_model.source_node:
            source_node = self._to_node_entity(link_model.source_node)
        
        destination_node = None
        if link_model.destination_node:
            destination_node = self._to_node_entity(link_model.destination_node)
        
        return LinkEntity(
            id=link_model.link_id,
            project_id=link_model.project.project_id if link_model.project else None,
            link_type=link_model.link_type,
            source_node=source_node,
            source_port=link_model.source_port,
            destination_node=destination_node,
            destination_port=link_model.destination_port,
            status=link_model.status,
            created_at=link_model.created_at,
            updated_at=link_model.updated_at
        )
    
    @transaction.atomic
    def save_project(self, project: ProjectEntity) -> ProjectEntity:
        """
        Sauvegarde un projet.
        
        Args:
            project: Entité Project à sauvegarder
            
        Returns:
            Entité Project mise à jour
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la sauvegarde
        """
        try:
            # Récupérer le serveur par défaut
            from ..models import Server
            from django.conf import settings
            
            server = Server.objects.filter(
                host=settings.GNS3_HOST,
                port=settings.GNS3_PORT
            ).first()
            
            if not server:
                # Créer le serveur par défaut s'il n'existe pas
                server = Server.objects.create(
                    name='Serveur GNS3 Principal',
                    host=settings.GNS3_HOST,
                    port=settings.GNS3_PORT,
                    protocol=settings.GNS3_PROTOCOL,
                    username=getattr(settings, 'GNS3_USERNAME', ''),
                    password=getattr(settings, 'GNS3_PASSWORD', ''),
                    verify_ssl=settings.GNS3_VERIFY_SSL,
                    is_active=True,
                    timeout=getattr(settings, 'GNS3_TIMEOUT', 30),
                )
                logger.info(f"✅ Serveur GNS3 par défaut créé: {server.name}")
            
            # Vérification si le projet existe déjà
            project_model, created = Project.objects.update_or_create(
                project_id=project.id,
                defaults={
                    'server': server,
                    'name': project.name,
                    'status': project.status,
                    'path': project.path,
                    'filename': project.filename,
                    'auto_start': project.auto_start,
                    'auto_close': project.auto_close,
                    'description': project.description,
                    'updated_at': timezone.now()
                }
            )
            
            # Invalider le cache
            if self.cache_enabled:
                cache.delete(self._cache_key('project', project.id))
                cache.delete(self._cache_key('projects'))
            
            return self._to_project_entity(project_model)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du projet {project.id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la sauvegarde du projet: {e}")
    
    def get_project(self, project_id: str) -> Optional[ProjectEntity]:
        """
        Récupère un projet par son ID.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Entité Project ou None si non trouvée
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('project', project_id)
            cached_project = cache.get(cache_key)
            if cached_project:
                return cached_project
        
        try:
            project_model = Project.objects.get(project_id=project_id)
            project_entity = self._to_project_entity(project_model)
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, project_entity, self.CACHE_TIMEOUT)
                
            return project_entity
        except Project.DoesNotExist:
            logger.warning(f"Projet GNS3 {project_id} non trouvé")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du projet {project_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération du projet: {e}")
    
    def list_projects(self) -> List[ProjectEntity]:
        """
        Liste tous les projets.
        
        Returns:
            Liste d'entités Project
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('projects')
            cached_projects = cache.get(cache_key)
            if cached_projects:
                return cached_projects
        
        try:
            projects = []
            
            # Optimisation: précharger le compte de nœuds pour éviter des requêtes N+1
            project_models = Project.objects.annotate(
                nodes_count=Count('nodes'),
                links_count=Count('links')
            ).order_by('-updated_at')
            
            for project_model in project_models:
                project = self._to_project_entity(project_model)
                project.nodes_count = project_model.nodes_count
                project.links_count = project_model.links_count
                projects.append(project)
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, projects, self.CACHE_TIMEOUT)
                
            return projects
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération des projets: {e}")
    
    @transaction.atomic
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la suppression
        """
        try:
            # Supprimer d'abord les liens et nœuds (assuré par on_delete=CASCADE)
            result = Project.objects.filter(project_id=project_id).delete()
            
            # Invalider le cache
            if self.cache_enabled:
                cache.delete(self._cache_key('project', project_id))
                cache.delete(self._cache_key('projects'))
                cache.delete_many([
                    self._cache_key('nodes', project_id),
                    self._cache_key('links', project_id)
                ])
                
            return result[0] > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du projet {project_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la suppression du projet: {e}")
    
    @transaction.atomic
    def save_node(self, node: NodeEntity) -> NodeEntity:
        """
        Sauvegarde un nœud.
        
        Args:
            node: Entité Node à sauvegarder
            
        Returns:
            Entité Node mise à jour
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la sauvegarde
        """
        try:
            # Récupérer le projet
            try:
                project = Project.objects.get(project_id=node.project_id)
            except Project.DoesNotExist:
                raise GNS3RepositoryError(f"Le projet {node.project_id} n'existe pas")
            
            # Sauvegarder le nœud
            node_model, created = Node.objects.update_or_create(
                node_id=node.id,
                project=project,
                defaults={
                    'name': node.name,
                    'node_type': node.node_type,
                    'status': node.status,
                    'console_type': node.console_type,
                    'console_port': node.console_port,
                    'x': node.x,
                    'y': node.y,
                    'symbol': node.symbol,
                    'properties': node.properties,
                    'compute_id': node.compute_id,
                    'updated_at': timezone.now()
                }
            )
            
            # Invalider le cache
            if self.cache_enabled:
                cache.delete(self._cache_key('node', node.id))
                cache.delete(self._cache_key('nodes', node.project_id))
            
            return self._to_node_entity(node_model)
        except GNS3RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du nœud {node.id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la sauvegarde du nœud: {e}")
    
    def get_node(self, node_id: str) -> Optional[NodeEntity]:
        """
        Récupère un nœud par son ID.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Entité Node ou None si non trouvée
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('node', node_id)
            cached_node = cache.get(cache_key)
            if cached_node:
                return cached_node
                
        try:
            node_model = Node.objects.select_related('project').get(node_id=node_id)
            node_entity = self._to_node_entity(node_model)
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, node_entity, self.CACHE_TIMEOUT)
                
            return node_entity
        except Node.DoesNotExist:
            logger.warning(f"Nœud {node_id} non trouvé")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du nœud {node_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération du nœud: {e}")
    
    def list_nodes(self, project_id: str) -> List[NodeEntity]:
        """
        Liste tous les nœuds d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste d'entités Node
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('nodes', project_id)
            cached_nodes = cache.get(cache_key)
            if cached_nodes:
                return cached_nodes
        
        try:
            node_models = Node.objects.filter(project__project_id=project_id).select_related('project').order_by('name')
            nodes = [self._to_node_entity(node_model) for node_model in node_models]
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, nodes, self.CACHE_TIMEOUT)
                
            return nodes
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des nœuds du projet {project_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération des nœuds: {e}")
    
    @transaction.atomic
    def save_link(self, link: LinkEntity) -> LinkEntity:
        """
        Sauvegarde un lien.
        
        Args:
            link: Entité Link à sauvegarder
            
        Returns:
            Entité Link mise à jour
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la sauvegarde
        """
        try:
            # Récupérer le projet
            try:
                project = Project.objects.get(project_id=link.project_id)
            except Project.DoesNotExist:
                raise GNS3RepositoryError(f"Le projet {link.project_id} n'existe pas")
            
            # Récupérer les nœuds
            try:
                source_node = Node.objects.get(node_id=link.source_node.id, project=project)
                destination_node = Node.objects.get(node_id=link.destination_node.id, project=project)
            except Node.DoesNotExist as e:
                raise GNS3RepositoryError(f"Un des nœuds n'existe pas: {e}")
            
            # Sauvegarder le lien
            link_model, created = Link.objects.update_or_create(
                link_id=link.id,
                project=project,
                defaults={
                    'link_type': link.link_type,
                    'source_node': source_node,
                    'source_port': link.source_port,
                    'destination_node': destination_node,
                    'destination_port': link.destination_port,
                    'status': link.status,
                    'updated_at': timezone.now()
                }
            )
            
            # Invalider le cache
            if self.cache_enabled:
                cache.delete(self._cache_key('link', link.id))
                cache.delete(self._cache_key('links', link.project_id))
            
            return self._to_link_entity(link_model)
        except GNS3RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du lien {link.id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la sauvegarde du lien: {e}")
    
    def get_link(self, link_id: str) -> Optional[LinkEntity]:
        """
        Récupère un lien par son ID.
        
        Args:
            link_id: ID du lien
            
        Returns:
            Entité Link ou None si non trouvée
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('link', link_id)
            cached_link = cache.get(cache_key)
            if cached_link:
                return cached_link
        
        try:
            link_model = Link.objects.select_related('project', 'source_node', 'destination_node').get(link_id=link_id)
            link_entity = self._to_link_entity(link_model)
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, link_entity, self.CACHE_TIMEOUT)
                
            return link_entity
        except Link.DoesNotExist:
            logger.warning(f"Lien {link_id} non trouvé")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du lien {link_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération du lien: {e}")
    
    def list_links(self, project_id: str) -> List[LinkEntity]:
        """
        Liste tous les liens d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste d'entités Link
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('links', project_id)
            cached_links = cache.get(cache_key)
            if cached_links:
                return cached_links
        
        try:
            link_models = Link.objects.filter(project__project_id=project_id).select_related(
                'project', 'source_node', 'destination_node'
            ).order_by('created_at')
            
            links = [self._to_link_entity(link_model) for link_model in link_models]
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, links, self.CACHE_TIMEOUT)
                
            return links
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des liens du projet {project_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération des liens: {e}")
    
    @transaction.atomic
    def delete_link(self, link_id: str) -> bool:
        """
        Supprime un lien.
        
        Args:
            link_id: ID du lien
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la suppression
        """
        try:
            # Récupérer d'abord le lien pour connaître son projet (pour invalider le cache)
            try:
                link = Link.objects.select_related('project').get(link_id=link_id)
                project_id = link.project.project_id
                
                # Supprimer le lien
                link.delete()
                
                # Invalider le cache
                if self.cache_enabled:
                    cache.delete(self._cache_key('link', link_id))
                    cache.delete(self._cache_key('links', project_id))
                    
                return True
            except Link.DoesNotExist:
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du lien {link_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la suppression du lien: {e}")
    
    @transaction.atomic
    def delete_node(self, node_id: str) -> bool:
        """
        Supprime un nœud.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la suppression
        """
        try:
            # Récupérer d'abord le nœud pour connaître son projet (pour invalider le cache)
            try:
                node = Node.objects.select_related('project').get(node_id=node_id)
                project_id = node.project.project_id
                
                # Supprimer le nœud (et les liens associés par CASCADE)
                node.delete()
                
                # Invalider le cache
                if self.cache_enabled:
                    cache.delete(self._cache_key('node', node_id))
                    cache.delete(self._cache_key('nodes', project_id))
                    cache.delete(self._cache_key('links', project_id))
                    
                return True
            except Node.DoesNotExist:
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du nœud {node_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la suppression du nœud: {e}")
    
    @transaction.atomic
    def save_snapshot(self, project_id: str, snapshot_id: str, snapshot_name: str) -> bool:
        """
        Sauvegarde un snapshot.
        
        Args:
            project_id: ID du projet
            snapshot_id: ID du snapshot
            snapshot_name: Nom du snapshot
            
        Returns:
            True si la sauvegarde a réussi, False sinon
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la sauvegarde
        """
        try:
            # Récupérer le projet
            try:
                project = Project.objects.get(project_id=project_id)
            except Project.DoesNotExist:
                raise GNS3RepositoryError(f"Le projet {project_id} n'existe pas")
            
            # Sauvegarder le snapshot
            Snapshot.objects.update_or_create(
                snapshot_id=snapshot_id,
                project=project,
                defaults={
                    'name': snapshot_name,
                    'created_at': timezone.now()
                }
            )
            
            return True
        except GNS3RepositoryError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du snapshot {snapshot_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la sauvegarde du snapshot: {e}")
    
    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les snapshots d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste de snapshots
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        try:
            snapshots = Snapshot.objects.filter(project__project_id=project_id).order_by('-created_at')
            return [
                {
                    "id": snapshot.snapshot_id,
                    "name": snapshot.name,
                    "created_at": snapshot.created_at
                }
                for snapshot in snapshots
            ]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des snapshots du projet {project_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération des snapshots: {e}")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Récupère la configuration globale de GNS3.
        
        Returns:
            Configuration de GNS3
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        try:
            config = {}
            for item in GNS3Config.objects.all():
                config[item.key] = item.value
            return config
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la configuration GNS3: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération de la configuration: {e}")
    
    @transaction.atomic
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Sauvegarde la configuration globale de GNS3.
        
        Args:
            config: Configuration de GNS3
            
        Returns:
            True si la sauvegarde a réussi, False sinon
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la sauvegarde
        """
        try:
            for key, value in config.items():
                GNS3Config.objects.update_or_create(
                    key=key,
                    defaults={'value': value}
                )
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration GNS3: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def invalidate_cache(self) -> None:
        """
        Invalide tout le cache du repository.
        
        Cette méthode est utile lors de grandes synchronisations pour s'assurer
        que les données en cache sont rafraîchies.
        """
        if not self.cache_enabled:
            return
            
        # Supprimer toutes les clés qui commencent par "gns3_repo:"
        keys_pattern = "gns3_repo:*"
        cache.delete_pattern(keys_pattern) if hasattr(cache, 'delete_pattern') else None
    
    def _to_server_entity(self, server_model: Server) -> ServerEntity:
        """
        Convertit un modèle Server en entité de domaine.
        
        Args:
            server_model: Modèle Server Django
            
        Returns:
            Entité Server
        """
        if not server_model:
            return None
        
        return ServerEntity(
            id=server_model.id,
            name=server_model.name,
            host=server_model.host,
            port=server_model.port,
            protocol=server_model.protocol,
            username=server_model.username,
            password=server_model.password,  # Note: password est déjà hashé dans le modèle
            verify_ssl=server_model.verify_ssl,
            is_active=server_model.is_active,
            timeout=server_model.timeout,
            created_at=server_model.created_at,
            updated_at=server_model.updated_at,
            projects_count=server_model.projects.count() if hasattr(server_model, 'projects') else 0
        )
    
    def list_servers(self) -> List[ServerEntity]:
        """
        Liste tous les serveurs GNS3.
        
        Returns:
            Liste d'entités Server
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('servers')
            cached_servers = cache.get(cache_key)
            if cached_servers:
                return cached_servers
        
        try:
            server_models = Server.objects.annotate(
                projects_count=Count('projects')
            ).order_by('-updated_at')
            
            servers = []
            for server_model in server_models:
                server = self._to_server_entity(server_model)
                servers.append(server)
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, servers, self.CACHE_TIMEOUT)
                
            return servers
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des serveurs: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération des serveurs: {e}")
    
    def get_server(self, server_id: str) -> Optional[ServerEntity]:
        """
        Récupère un serveur par son ID.
        
        Args:
            server_id: ID du serveur
            
        Returns:
            Entité Server ou None si non trouvé
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la récupération
        """
        # Vérifier le cache
        if self.cache_enabled:
            cache_key = self._cache_key('server', server_id)
            cached_server = cache.get(cache_key)
            if cached_server:
                return cached_server
        
        try:
            server_model = Server.objects.annotate(
                projects_count=Count('projects')
            ).get(id=server_id)
            
            server_entity = self._to_server_entity(server_model)
            
            # Mettre en cache
            if self.cache_enabled:
                cache.set(cache_key, server_entity, self.CACHE_TIMEOUT)
                
            return server_entity
        except Server.DoesNotExist:
            logger.warning(f"Serveur {server_id} non trouvé")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du serveur {server_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la récupération du serveur: {e}")
    
    @transaction.atomic
    def save_server(self, server: ServerEntity) -> ServerEntity:
        """
        Sauvegarde un serveur.
        
        Args:
            server: Entité Server à sauvegarder
            
        Returns:
            Entité Server mise à jour
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la sauvegarde
        """
        try:
            if server.id:
                # Mise à jour d'un serveur existant
                server_model = Server.objects.get(id=server.id)
                server_model.name = server.name
                server_model.host = server.host
                server_model.port = server.port
                server_model.protocol = server.protocol
                server_model.username = server.username
                if server.password:  # Seulement si un nouveau mot de passe est fourni
                    server_model.password = server.password
                server_model.verify_ssl = server.verify_ssl
                server_model.is_active = server.is_active
                server_model.timeout = server.timeout
                server_model.save()
            else:
                # Création d'un nouveau serveur
                server_model = Server.objects.create(
                    name=server.name,
                    host=server.host,
                    port=server.port,
                    protocol=server.protocol,
                    username=server.username,
                    password=server.password,
                    verify_ssl=server.verify_ssl,
                    is_active=server.is_active,
                    timeout=server.timeout
                )
            
            # Invalider le cache
            if self.cache_enabled:
                cache.delete(self._cache_key('server', server_model.id))
                cache.delete(self._cache_key('servers'))
            
            return self._to_server_entity(server_model)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du serveur: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la sauvegarde du serveur: {e}")
    
    @transaction.atomic
    def delete_server(self, server_id: str) -> bool:
        """
        Supprime un serveur.
        
        Args:
            server_id: ID du serveur
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            GNS3RepositoryError: Si une erreur survient lors de la suppression
        """
        try:
            result = Server.objects.filter(id=server_id).delete()
            
            # Invalider le cache
            if self.cache_enabled:
                cache.delete(self._cache_key('server', server_id))
                cache.delete(self._cache_key('servers'))
                
            return result[0] > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du serveur {server_id}: {e}")
            raise GNS3RepositoryError(f"Erreur lors de la suppression du serveur: {e}")


# Alias pour la compatibilité avec l'ancien code
GNS3RepositoryImpl = DjangoGNS3Repository
