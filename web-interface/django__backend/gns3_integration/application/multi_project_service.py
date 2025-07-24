"""
Service pour la gestion de projets GNS3 multiples avec basculement automatique.

Ce module permet de gérer plusieurs projets GNS3 simultanément, de basculer entre eux,
et de démarrer automatiquement le travail quand il y a du trafic réseau.
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from django.db import transaction
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings

from .project_service import ProjectService
from ..domain.interfaces import GNS3ClientPort, GNS3Repository
from ..domain.models import Project
from ..domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

@dataclass
class ProjectSelection:
    """Représente une sélection de projet avec ses métadonnées."""
    project_id: str
    project_name: str
    selected_at: datetime
    is_active: bool = False
    traffic_detected: bool = False
    last_traffic: Optional[datetime] = None
    priority: int = 1  # 1 = haute priorité, 5 = basse priorité
    auto_start_on_traffic: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrafficStatus:
    """État du trafic réseau pour un projet."""
    project_id: str
    has_traffic: bool
    traffic_level: str  # 'low', 'medium', 'high'
    detected_at: datetime
    interface_stats: Dict[str, Any] = field(default_factory=dict)

class MultiProjectService:
    """
    Service pour la gestion de projets GNS3 multiples avec basculement automatique.
    
    Ce service permet de :
    - Sélectionner plusieurs projets GNS3 pour surveillance
    - Basculer automatiquement entre projets
    - Démarrer le travail automatiquement quand il y a du trafic
    - Gérer les priorités et configurations de chaque projet
    """
    
    CACHE_KEY_SELECTED_PROJECTS = "gns3_selected_projects"
    CACHE_KEY_ACTIVE_PROJECT = "gns3_active_project"
    CACHE_KEY_TRAFFIC_STATUS = "gns3_traffic_status_{}"
    CACHE_TIMEOUT = 3600  # 1 heure
    
    def __init__(self, project_service: ProjectService, gns3_client: GNS3ClientPort, gns3_repository: GNS3Repository):
        """
        Initialise le service.
        
        Args:
            project_service: Service de gestion des projets
            gns3_client: Client GNS3
            gns3_repository: Repository GNS3
        """
        self.project_service = project_service
        self.client = gns3_client
        self.repository = gns3_repository
        self._monitoring_enabled = True
        self._monitoring_interval = getattr(settings, 'GNS3_MONITOR_INTERVAL', 30)
        self._auto_monitor = getattr(settings, 'GNS3_AUTO_MONITOR', True)
        
    def get_selected_projects(self) -> List[ProjectSelection]:
        """
        Récupère la liste des projets sélectionnés.
        
        Returns:
            Liste des projets sélectionnés avec leurs métadonnées
        """
        try:
            cached_data = cache.get(self.CACHE_KEY_SELECTED_PROJECTS, [])
            return [ProjectSelection(**data) for data in cached_data]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets sélectionnés: {e}")
            return []
    
    def add_project_selection(self, project_id: str, priority: int = 1, 
                            auto_start_on_traffic: bool = True,
                            metadata: Optional[Dict[str, Any]] = None) -> ProjectSelection:
        """
        Ajoute un projet à la sélection.
        
        Args:
            project_id: ID du projet à ajouter
            priority: Priorité du projet (1 = haute, 5 = basse)
            auto_start_on_traffic: Si le projet doit démarrer automatiquement sur trafic
            metadata: Métadonnées supplémentaires
            
        Returns:
            Sélection créée
            
        Raises:
            GNS3ResourceNotFoundError: Projet non trouvé
            GNS3Exception: Erreur lors de l'ajout
        """
        try:
            # Vérifier que le projet existe
            project = self.project_service.get_project(project_id)
            if not project:
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Récupérer les sélections existantes
            selected_projects = self.get_selected_projects()
            
            # Vérifier si le projet n'est pas déjà sélectionné
            existing_selection = next(
                (sel for sel in selected_projects if sel.project_id == project_id), 
                None
            )
            
            if existing_selection:
                # Mettre à jour la sélection existante
                existing_selection.priority = priority
                existing_selection.auto_start_on_traffic = auto_start_on_traffic
                existing_selection.metadata.update(metadata or {})
                existing_selection.selected_at = datetime.now()
                selection = existing_selection
            else:
                # Créer une nouvelle sélection
                selection = ProjectSelection(
                    project_id=project_id,
                    project_name=project.name,
                    selected_at=datetime.now(),
                    priority=priority,
                    auto_start_on_traffic=auto_start_on_traffic,
                    metadata=metadata or {}
                )
                selected_projects.append(selection)
            
            # Sauvegarder dans le cache
            self._save_selected_projects(selected_projects)
            
            logger.info(f"Projet {project_id} ajouté à la sélection avec priorité {priority}")
            return selection
            
        except GNS3ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du projet {project_id} à la sélection: {e}")
            raise GNS3Exception(f"Erreur lors de l'ajout du projet à la sélection: {e}")
    
    def remove_project_selection(self, project_id: str) -> bool:
        """
        Retire un projet de la sélection.
        
        Args:
            project_id: ID du projet à retirer
            
        Returns:
            True si retiré avec succès
        """
        try:
            selected_projects = self.get_selected_projects()
            initial_count = len(selected_projects)
            
            # Filtrer le projet à retirer
            selected_projects = [sel for sel in selected_projects if sel.project_id != project_id]
            
            if len(selected_projects) < initial_count:
                self._save_selected_projects(selected_projects)
                
                # Si c'était le projet actif, désactiver
                active_project = self.get_active_project()
                if active_project and active_project.project_id == project_id:
                    self.set_active_project(None)
                
                logger.info(f"Projet {project_id} retiré de la sélection")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du projet {project_id} de la sélection: {e}")
            return False
    
    def get_active_project(self) -> Optional[ProjectSelection]:
        """
        Récupère le projet actuellement actif.
        
        Returns:
            Projet actif ou None si aucun
        """
        try:
            cached_data = cache.get(self.CACHE_KEY_ACTIVE_PROJECT)
            if cached_data:
                return ProjectSelection(**cached_data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du projet actif: {e}")
            return None
    
    def set_active_project(self, project_id: Optional[str]) -> bool:
        """
        Définit le projet actif.
        
        Args:
            project_id: ID du projet à activer ou None pour désactiver
            
        Returns:
            True si changement effectué avec succès
        """
        try:
            selected_projects = self.get_selected_projects()
            
            # Désactiver tous les projets
            for selection in selected_projects:
                selection.is_active = False
            
            active_selection = None
            
            if project_id:
                # Activer le projet spécifié
                target_selection = next(
                    (sel for sel in selected_projects if sel.project_id == project_id), 
                    None
                )
                
                if not target_selection:
                    raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé dans la sélection")
                
                target_selection.is_active = True
                active_selection = target_selection
                
                # Ouvrir le projet s'il n'est pas ouvert
                try:
                    self.project_service.open_project(project_id)
                    logger.info(f"Projet {project_id} ouvert automatiquement")
                except Exception as e:
                    logger.warning(f"Impossible d'ouvrir automatiquement le projet {project_id}: {e}")
            
            # Sauvegarder les changements
            self._save_selected_projects(selected_projects)
            
            if active_selection:
                cache.set(self.CACHE_KEY_ACTIVE_PROJECT, active_selection.__dict__, self.CACHE_TIMEOUT)
                logger.info(f"Projet {project_id} défini comme actif")
            else:
                cache.delete(self.CACHE_KEY_ACTIVE_PROJECT)
                logger.info("Aucun projet actif")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la définition du projet actif {project_id}: {e}")
            return False
    
    def switch_to_next_priority_project(self) -> Optional[ProjectSelection]:
        """
        Bascule vers le projet suivant selon la priorité.
        
        Returns:
            Nouveau projet actif ou None si aucun
        """
        try:
            selected_projects = self.get_selected_projects()
            if not selected_projects:
                return None
            
            # Trier par priorité (1 = plus haute priorité)
            sorted_projects = sorted(selected_projects, key=lambda x: x.priority)
            
            current_active = self.get_active_project()
            current_index = -1
            
            if current_active:
                try:
                    current_index = next(
                        i for i, proj in enumerate(sorted_projects) 
                        if proj.project_id == current_active.project_id
                    )
                except StopIteration:
                    current_index = -1
            
            # Passer au projet suivant
            next_index = (current_index + 1) % len(sorted_projects)
            next_project = sorted_projects[next_index]
            
            if self.set_active_project(next_project.project_id):
                logger.info(f"Basculement vers le projet {next_project.project_id} ({next_project.project_name})")
                return next_project
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du basculement vers le projet suivant: {e}")
            return None
    
    def detect_traffic_on_project(self, project_id: str) -> TrafficStatus:
        """
        Détecte le trafic réseau sur un projet.
        
        Args:
            project_id: ID du projet à surveiller
            
        Returns:
            État du trafic détecté
        """
        try:
            # Récupérer les nœuds du projet
            project = self.project_service.get_project(project_id)
            if not project:
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            
            # Simuler la détection de trafic en interrogeant les statistiques des nœuds
            # En réalité, ceci devrait interroger l'API GNS3 pour les statistiques de trafic
            has_traffic = False
            traffic_level = 'low'
            interface_stats = {}
            
            try:
                # Récupérer les nœuds du projet depuis GNS3
                nodes = self.client.list_nodes(project_id)
                
                for node in nodes:
                    if node.get('status') == 'started':
                        # Vérifier les statistiques des interfaces
                        node_stats = self.client.get_node_statistics(project_id, node['node_id'])
                        if node_stats:
                            # Analyser les statistiques pour détecter le trafic
                            for port in node_stats.get('ports', []):
                                rx_bytes = port.get('bytes_received', 0)
                                tx_bytes = port.get('bytes_sent', 0)
                                
                                if rx_bytes > 0 or tx_bytes > 0:
                                    has_traffic = True
                                    
                                    # Déterminer le niveau de trafic
                                    total_bytes = rx_bytes + tx_bytes
                                    if total_bytes > 1000000:  # > 1MB
                                        traffic_level = 'high'
                                    elif total_bytes > 100000:  # > 100KB
                                        traffic_level = 'medium'
                                    
                                    interface_stats[f"{node['name']}_{port.get('name', 'unknown')}"] = {
                                        'rx_bytes': rx_bytes,
                                        'tx_bytes': tx_bytes,
                                        'total_bytes': total_bytes
                                    }
                            
                            if has_traffic:
                                break
                
            except Exception as e:
                logger.warning(f"Impossible de récupérer les statistiques pour le projet {project_id}: {e}")
                # Fallback : considérer qu'il y a du trafic si le projet est ouvert
                project_status = self.client.get_project(project_id)
                has_traffic = project_status.get('status') == 'opened'
            
            traffic_status = TrafficStatus(
                project_id=project_id,
                has_traffic=has_traffic,
                traffic_level=traffic_level,
                detected_at=datetime.now(),
                interface_stats=interface_stats
            )
            
            # Mettre en cache le statut du trafic
            cache.set(
                self.CACHE_KEY_TRAFFIC_STATUS.format(project_id),
                traffic_status.__dict__,
                300  # 5 minutes
            )
            
            return traffic_status
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection de trafic pour le projet {project_id}: {e}")
            return TrafficStatus(
                project_id=project_id,
                has_traffic=False,
                traffic_level='low',
                detected_at=datetime.now()
            )
    
    def start_automatic_monitoring(self) -> bool:
        """
        Démarre la surveillance automatique des projets sélectionnés.
        
        Returns:
            True si démarré avec succès
        """
        try:
            if not self._auto_monitor:
                logger.info("Surveillance automatique désactivée par configuration")
                return False
            
            self._monitoring_enabled = True
            
            # Démarrer la tâche de surveillance en arrière-plan
            asyncio.create_task(self._monitoring_loop())
            
            logger.info("Surveillance automatique des projets GNS3 démarrée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la surveillance automatique: {e}")
            return False
    
    def stop_automatic_monitoring(self) -> bool:
        """
        Arrête la surveillance automatique.
        
        Returns:
            True si arrêté avec succès
        """
        try:
            self._monitoring_enabled = False
            logger.info("Surveillance automatique des projets GNS3 arrêtée")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de la surveillance automatique: {e}")
            return False
    
    async def _monitoring_loop(self):
        """
        Boucle principale de surveillance des projets.
        """
        logger.info("Démarrage de la boucle de surveillance des projets GNS3")
        
        while self._monitoring_enabled:
            try:
                await self._check_projects_traffic()
                await asyncio.sleep(self._monitoring_interval)
            except Exception as e:
                logger.error(f"Erreur dans la boucle de surveillance: {e}")
                await asyncio.sleep(5)  # Attendre avant de réessayer
    
    async def _check_projects_traffic(self):
        """
        Vérifie le trafic sur tous les projets sélectionnés.
        """
        try:
            selected_projects = self.get_selected_projects()
            if not selected_projects:
                return
            
            current_active = self.get_active_project()
            traffic_detected_projects = []
            
            # Vérifier le trafic pour chaque projet
            for selection in selected_projects:
                if not selection.auto_start_on_traffic:
                    continue
                
                traffic_status = self.detect_traffic_on_project(selection.project_id)
                
                if traffic_status.has_traffic:
                    selection.traffic_detected = True
                    selection.last_traffic = traffic_status.detected_at
                    traffic_detected_projects.append((selection, traffic_status))
                else:
                    selection.traffic_detected = False
            
            # Sauvegarder les mises à jour
            self._save_selected_projects(selected_projects)
            
            # Si du trafic est détecté et aucun projet n'est actif, 
            # ou si le projet actif n'a pas de trafic mais d'autres en ont
            if traffic_detected_projects:
                should_switch = False
                
                if not current_active:
                    should_switch = True
                    logger.info("Aucun projet actif, basculement nécessaire")
                elif not current_active.traffic_detected:
                    # Le projet actuel n'a pas de trafic, vérifier si un autre en a
                    higher_priority_with_traffic = any(
                        sel.priority < current_active.priority and sel.traffic_detected
                        for sel, _ in traffic_detected_projects
                    )
                    if higher_priority_with_traffic:
                        should_switch = True
                        logger.info("Projet avec priorité plus élevée et trafic détecté")
                
                if should_switch:
                    # Trier par priorité et sélectionner le premier avec du trafic
                    best_project = min(
                        traffic_detected_projects,
                        key=lambda x: x[0].priority
                    )[0]
                    
                    if self.set_active_project(best_project.project_id):
                        logger.info(f"Basculement automatique vers le projet {best_project.project_id} détecté avec trafic")
                        
                        # Démarrer tous les nœuds du projet
                        try:
                            await self._start_project_work(best_project.project_id)
                        except Exception as e:
                            logger.error(f"Erreur lors du démarrage du travail pour le projet {best_project.project_id}: {e}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du trafic des projets: {e}")
    
    async def _start_project_work(self, project_id: str):
        """
        Démarre le travail automatique pour un projet.
        
        Args:
            project_id: ID du projet
        """
        try:
            logger.info(f"Démarrage du travail automatique pour le projet {project_id}")
            
            # Ouvrir le projet s'il n'est pas ouvert
            self.project_service.open_project(project_id)
            
            # Démarrer tous les nœuds du projet
            result = self.project_service.start_all_nodes(project_id)
            
            if result:
                logger.info(f"Travail automatique démarré avec succès pour le projet {project_id}")
                logger.info(f"Nœuds démarrés: {result.get('started_nodes', [])}")
                if result.get('failed_nodes'):
                    logger.warning(f"Nœuds en échec: {result.get('failed_nodes', [])}")
            else:
                logger.warning(f"Aucun nœud démarré pour le projet {project_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du travail pour le projet {project_id}: {e}")
            raise
    
    def get_traffic_status_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé du statut de trafic pour tous les projets sélectionnés.
        
        Returns:
            Résumé du statut de trafic
        """
        try:
            selected_projects = self.get_selected_projects()
            active_project = self.get_active_project()
            
            summary = {
                'total_projects': len(selected_projects),
                'active_project': active_project.project_id if active_project else None,
                'projects_with_traffic': 0,
                'monitoring_enabled': self._monitoring_enabled,
                'last_check': datetime.now().isoformat(),
                'projects': []
            }
            
            for selection in selected_projects:
                traffic_status = cache.get(
                    self.CACHE_KEY_TRAFFIC_STATUS.format(selection.project_id)
                )
                
                project_info = {
                    'project_id': selection.project_id,
                    'project_name': selection.project_name,
                    'is_active': selection.is_active,
                    'priority': selection.priority,
                    'auto_start_on_traffic': selection.auto_start_on_traffic,
                    'traffic_detected': selection.traffic_detected,
                    'last_traffic': selection.last_traffic.isoformat() if selection.last_traffic else None,
                    'traffic_status': traffic_status
                }
                
                if selection.traffic_detected:
                    summary['projects_with_traffic'] += 1
                
                summary['projects'].append(project_info)
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé de trafic: {e}")
            return {
                'error': str(e),
                'total_projects': 0,
                'projects_with_traffic': 0,
                'monitoring_enabled': False,
                'last_check': datetime.now().isoformat()
            }
    
    def select_project_for_monitoring(self, project_id: str, priority: int = 1, 
                                     auto_start_on_traffic: bool = True,
                                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sélectionne un projet pour la surveillance automatique.
        
        Args:
            project_id: ID du projet à sélectionner
            priority: Priorité du projet (1 = haute, 5 = basse)
            auto_start_on_traffic: Si le projet doit démarrer automatiquement sur trafic
            metadata: Métadonnées supplémentaires
            
        Returns:
            True si sélectionné avec succès
        """
        try:
            selection = self.add_project_selection(
                project_id=project_id,
                priority=priority,
                auto_start_on_traffic=auto_start_on_traffic,
                metadata=metadata
            )
            
            logger.info(f"Projet {project_id} sélectionné pour surveillance automatique")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du projet {project_id} pour surveillance: {e}")
            return False
    
    def _save_selected_projects(self, projects: List[ProjectSelection]):
        """
        Sauvegarde la liste des projets sélectionnés dans le cache.
        
        Args:
            projects: Liste des projets à sauvegarder
        """
        try:
            projects_data = [proj.__dict__ for proj in projects]
            cache.set(self.CACHE_KEY_SELECTED_PROJECTS, projects_data, self.CACHE_TIMEOUT)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des projets sélectionnés: {e}")