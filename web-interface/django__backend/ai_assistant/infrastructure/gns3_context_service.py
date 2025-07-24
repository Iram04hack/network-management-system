"""
Service de contextualisation GNS3 pour l'assistant IA.

Ce service enrichit les réponses de l'assistant IA avec des informations
de topologie réseau provenant de GNS3, permettant des réponses contextualisées
basées sur l'infrastructure réseau réelle.
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GNS3ConnectionStatus(Enum):
    """États de connexion GNS3."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class GNS3ServerInfo:
    """Informations du serveur GNS3."""
    host: str
    port: int
    version: str = ""
    status: GNS3ConnectionStatus = GNS3ConnectionStatus.UNKNOWN
    last_check: Optional[datetime] = None


@dataclass
class NetworkTopologyContext:
    """Contexte de topologie réseau pour l'IA."""
    projects: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    topology_stats: Dict[str, Any]
    server_info: GNS3ServerInfo
    last_updated: datetime


class GNS3ContextService:
    """
    Service de contextualisation GNS3 pour l'assistant IA.
    
    Fournit des informations de topologie réseau pour enrichir
    les réponses de l'assistant IA avec le contexte infrastructure.
    """
    
    def __init__(self, gns3_host: str = "localhost", gns3_port: int = 3080):
        """
        Initialise le service de contextualisation GNS3.
        
        Args:
            gns3_host: Hôte du serveur GNS3
            gns3_port: Port du serveur GNS3
        """
        self.server_info = GNS3ServerInfo(host=gns3_host, port=gns3_port)
        self.base_url = f"http://{gns3_host}:{gns3_port}/v2"
        self._topology_cache: Optional[NetworkTopologyContext] = None
        self._cache_timeout = timedelta(minutes=5)
    
    async def get_topology_context(self, force_refresh: bool = False) -> NetworkTopologyContext:
        """
        Récupère le contexte de topologie réseau.
        
        Args:
            force_refresh: Force la mise à jour du cache
            
        Returns:
            Contexte de topologie réseau
        """
        # Vérifier le cache
        if (not force_refresh and 
            self._topology_cache and 
            datetime.now() - self._topology_cache.last_updated < self._cache_timeout):
            return self._topology_cache
        
        try:
            # Récupérer les données de GNS3
            projects = await self._get_projects()
            nodes = await self._get_all_nodes()
            links = await self._get_all_links()
            topology_stats = self._calculate_topology_stats(projects, nodes, links)
            
            # Mettre à jour les informations du serveur
            await self._check_server_status()
            
            # Créer le contexte
            context = NetworkTopologyContext(
                projects=projects,
                nodes=nodes,
                links=links,
                topology_stats=topology_stats,
                server_info=self.server_info,
                last_updated=datetime.now()
            )
            
            # Mettre en cache
            self._topology_cache = context
            
            return context
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contexte topologie: {e}")
            
            # Retourner un contexte vide en cas d'erreur
            return NetworkTopologyContext(
                projects=[],
                nodes=[],
                links=[],
                topology_stats={},
                server_info=GNS3ServerInfo(
                    host=self.server_info.host,
                    port=self.server_info.port,
                    status=GNS3ConnectionStatus.ERROR
                ),
                last_updated=datetime.now()
            )
    
    async def _get_projects(self) -> List[Dict[str, Any]]:
        """Récupère la liste des projets GNS3."""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(f"{self.base_url}/projects") as response:
                    if response.status == 200:
                        projects = await response.json()
                        logger.info(f"Récupération de {len(projects)} projets GNS3")
                        return projects
                    else:
                        logger.warning(f"Erreur HTTP {response.status} lors de la récupération des projets")
                        return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets: {e}")
            return []
    
    async def _get_all_nodes(self) -> List[Dict[str, Any]]:
        """Récupère tous les nœuds de tous les projets."""
        all_nodes = []
        projects = await self._get_projects()
        
        for project in projects:
            project_id = project.get('project_id')
            if not project_id:
                continue
            
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(f"{self.base_url}/projects/{project_id}/nodes") as response:
                        if response.status == 200:
                            nodes = await response.json()
                            # Enrichir avec les informations du projet
                            for node in nodes:
                                node['project_name'] = project.get('name', 'Unknown')
                                node['project_id'] = project_id
                            all_nodes.extend(nodes)
                        else:
                            logger.warning(f"Erreur HTTP {response.status} pour les nœuds du projet {project_id}")
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des nœuds du projet {project_id}: {e}")
        
        logger.info(f"Récupération de {len(all_nodes)} nœuds au total")
        return all_nodes
    
    async def _get_all_links(self) -> List[Dict[str, Any]]:
        """Récupère tous les liens de tous les projets."""
        all_links = []
        projects = await self._get_projects()
        
        for project in projects:
            project_id = project.get('project_id')
            if not project_id:
                continue
            
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(f"{self.base_url}/projects/{project_id}/links") as response:
                        if response.status == 200:
                            links = await response.json()
                            # Enrichir avec les informations du projet
                            for link in links:
                                link['project_name'] = project.get('name', 'Unknown')
                                link['project_id'] = project_id
                            all_links.extend(links)
                        else:
                            logger.warning(f"Erreur HTTP {response.status} pour les liens du projet {project_id}")
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des liens du projet {project_id}: {e}")
        
        logger.info(f"Récupération de {len(all_links)} liens au total")
        return all_links
    
    async def _check_server_status(self):
        """Vérifie le statut du serveur GNS3."""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(f"{self.base_url}/version") as response:
                    if response.status == 200:
                        version_info = await response.json()
                        self.server_info.version = version_info.get('version', 'Unknown')
                        self.server_info.status = GNS3ConnectionStatus.CONNECTED
                        self.server_info.last_check = datetime.now()
                        logger.info(f"Serveur GNS3 connecté - Version: {self.server_info.version}")
                    else:
                        self.server_info.status = GNS3ConnectionStatus.ERROR
                        logger.warning(f"Erreur HTTP {response.status} lors de la vérification du serveur")
        except Exception as e:
            self.server_info.status = GNS3ConnectionStatus.DISCONNECTED
            logger.error(f"Impossible de se connecter au serveur GNS3: {e}")
    
    def _calculate_topology_stats(self, projects: List[Dict], nodes: List[Dict], links: List[Dict]) -> Dict[str, Any]:
        """Calcule les statistiques de topologie."""
        stats = {
            'total_projects': len(projects),
            'total_nodes': len(nodes),
            'total_links': len(links),
            'projects_by_status': {},
            'nodes_by_type': {},
            'nodes_by_status': {},
            'average_nodes_per_project': 0,
            'network_complexity_score': 0
        }
        
        # Statistiques des projets
        for project in projects:
            status = project.get('status', 'unknown')
            stats['projects_by_status'][status] = stats['projects_by_status'].get(status, 0) + 1
        
        # Statistiques des nœuds
        for node in nodes:
            node_type = node.get('node_type', 'unknown')
            status = node.get('status', 'unknown')
            
            stats['nodes_by_type'][node_type] = stats['nodes_by_type'].get(node_type, 0) + 1
            stats['nodes_by_status'][status] = stats['nodes_by_status'].get(status, 0) + 1
        
        # Calculs dérivés
        if stats['total_projects'] > 0:
            stats['average_nodes_per_project'] = round(stats['total_nodes'] / stats['total_projects'], 2)
        
        # Score de complexité (simple métrique basée sur les nœuds et liens)
        if stats['total_nodes'] > 0:
            stats['network_complexity_score'] = min(100, int(
                (stats['total_links'] / stats['total_nodes']) * 10 +
                (stats['total_nodes'] / 10) * 5
            ))
        
        return stats
    
    def generate_ai_context_summary(self, context: NetworkTopologyContext) -> str:
        """
        Génère un résumé textuel du contexte pour l'IA.
        
        Args:
            context: Contexte de topologie réseau
            
        Returns:
            Résumé textuel pour l'IA
        """
        if not context.projects and not context.nodes:
            return "Aucune infrastructure réseau GNS3 détectée ou serveur GNS3 non disponible."
        
        summary_parts = []
        
        # Informations générales
        summary_parts.append(f"Infrastructure réseau GNS3 :")
        summary_parts.append(f"- {context.topology_stats.get('total_projects', 0)} projet(s) GNS3")
        summary_parts.append(f"- {context.topology_stats.get('total_nodes', 0)} dispositif(s) réseau")
        summary_parts.append(f"- {context.topology_stats.get('total_links', 0)} connexion(s) réseau")
        
        # Projets actifs
        active_projects = [p for p in context.projects if p.get('status') == 'opened']
        if active_projects:
            summary_parts.append(f"\nProjets actifs :")
            for project in active_projects[:3]:  # Limiter à 3 projets
                summary_parts.append(f"- {project.get('name', 'Projet sans nom')}")
        
        # Types de dispositifs
        nodes_by_type = context.topology_stats.get('nodes_by_type', {})
        if nodes_by_type:
            summary_parts.append(f"\nTypes de dispositifs :")
            for device_type, count in list(nodes_by_type.items())[:5]:  # Top 5
                summary_parts.append(f"- {device_type}: {count}")
        
        # Dispositifs en cours d'exécution
        running_nodes = [n for n in context.nodes if n.get('status') == 'started']
        if running_nodes:
            summary_parts.append(f"\nDispositifs actifs : {len(running_nodes)}")
            if len(running_nodes) <= 5:
                for node in running_nodes:
                    summary_parts.append(f"- {node.get('name', 'Dispositif sans nom')} ({node.get('node_type', 'type inconnu')})")
        
        # Score de complexité
        complexity = context.topology_stats.get('network_complexity_score', 0)
        if complexity > 0:
            complexity_level = "faible" if complexity < 30 else "moyenne" if complexity < 70 else "élevée"
            summary_parts.append(f"\nComplexité réseau : {complexity_level} (score: {complexity}/100)")
        
        return "\n".join(summary_parts)
    
    def is_available(self) -> bool:
        """Vérifie si le service GNS3 est disponible."""
        return (self.server_info.status == GNS3ConnectionStatus.CONNECTED and
                self.server_info.last_check and
                datetime.now() - self.server_info.last_check < timedelta(minutes=10))
    
    async def get_device_details(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un dispositif spécifique.
        
        Args:
            device_name: Nom du dispositif
            
        Returns:
            Détails du dispositif ou None si non trouvé
        """
        context = await self.get_topology_context()
        
        for node in context.nodes:
            if node.get('name', '').lower() == device_name.lower():
                return {
                    'name': node.get('name'),
                    'type': node.get('node_type'),
                    'status': node.get('status'),
                    'project': node.get('project_name'),
                    'console_host': node.get('console_host'),
                    'console_port': node.get('console_port'),
                    'properties': node.get('properties', {}),
                    'coordinates': {
                        'x': node.get('x', 0),
                        'y': node.get('y', 0)
                    }
                }
        
        return None
    
    async def get_project_topology(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère la topologie d'un projet spécifique.
        
        Args:
            project_name: Nom du projet
            
        Returns:
            Topologie du projet ou None si non trouvé
        """
        context = await self.get_topology_context()
        
        # Trouver le projet
        project = None
        for p in context.projects:
            if p.get('name', '').lower() == project_name.lower():
                project = p
                break
        
        if not project:
            return None
        
        project_id = project.get('project_id')
        
        # Filtrer les nœuds et liens du projet
        project_nodes = [n for n in context.nodes if n.get('project_id') == project_id]
        project_links = [l for l in context.links if l.get('project_id') == project_id]
        
        return {
            'project': project,
            'nodes': project_nodes,
            'links': project_links,
            'stats': {
                'total_nodes': len(project_nodes),
                'total_links': len(project_links),
                'running_nodes': len([n for n in project_nodes if n.get('status') == 'started']),
                'node_types': list(set(n.get('node_type') for n in project_nodes if n.get('node_type')))
            }
        }


# Instance globale du service GNS3
gns3_context_service = GNS3ContextService()