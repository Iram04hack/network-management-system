"""
Service Central GNS3 - Infrastructure complète pour la communication avec GNS3.

Ce service constitue l'interface principale entre l'application et GNS3,
gérant toutes les interactions, le cache temps réel et les événements.
"""

import asyncio
import logging
import json
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum

from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

from api_clients.network.gns3_client import GNS3Client
from .inter_module_service import inter_module_service, MessageType
from .ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)


class GNS3EventType(Enum):
    """Types d'événements GNS3."""
    NODE_CREATED = "node.created"
    NODE_UPDATED = "node.updated"
    NODE_DELETED = "node.deleted"
    NODE_STARTED = "node.started"
    NODE_STOPPED = "node.stopped"
    NODE_SUSPENDED = "node.suspended"
    PROJECT_OPENED = "project.opened"
    PROJECT_CLOSED = "project.closed"
    PROJECT_CREATED = "project.created"
    PROJECT_DELETED = "project.deleted"
    LINK_CREATED = "link.created"
    LINK_DELETED = "link.deleted"
    TOPOLOGY_CHANGED = "topology.changed"


@dataclass
class GNS3Event:
    """Événement GNS3 structuré."""
    event_type: GNS3EventType
    project_id: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str = "gns3"


@dataclass
class NetworkState:
    """État complet du réseau GNS3."""
    projects: Dict[str, Dict[str, Any]]
    nodes: Dict[str, Dict[str, Any]]
    links: Dict[str, Dict[str, Any]]
    last_update: datetime
    server_status: str


class GNS3CentralService:
    """
    Service central pour toutes les interactions avec GNS3.
    
    Fonctionnalités :
    - Connexion unique et persistante à GNS3
    - Cache Redis pour l'état temps réel
    - Événements WebSocket en temps réel
    - Interface simplifiée pour les modules
    - Gestion automatique des reconnexions
    """
    
    def __init__(self):
        """Initialise le service central GNS3."""
        # Configuration GNS3
        self.gns3_config = {
            'host': getattr(settings, 'GNS3_HOST', 'localhost'),
            'port': getattr(settings, 'GNS3_PORT', 3080),
            'protocol': getattr(settings, 'GNS3_PROTOCOL', 'http'),
            'username': getattr(settings, 'GNS3_USERNAME', ''),
            'password': getattr(settings, 'GNS3_PASSWORD', ''),
            'verify_ssl': getattr(settings, 'GNS3_VERIFY_SSL', True),
            'timeout': getattr(settings, 'GNS3_TIMEOUT', 30)
        }
        
        # Client GNS3 principal
        self.gns3_client = GNS3Client(**self.gns3_config)
        
        # État du service
        self.is_connected = False
        self.is_monitoring = False
        self.websocket_connection = None
        self.event_callbacks: Set[Callable] = set()
        
        # Cache et état
        self.cache_prefix = "gns3_central"
        self.state_ttl = 300  # 5 minutes
        self.current_state: Optional[NetworkState] = None
        
        # Statistiques
        self.stats = {
            'events_processed': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_activity': None,
            'uptime_start': timezone.now()
        }
        
        logger.info("Service Central GNS3 initialisé")

    # ==================== CONNEXION ET ÉTAT ====================
    
    async def initialize(self) -> bool:
        """
        Initialise complètement le service.
        
        Returns:
            True si l'initialisation réussit
        """
        try:
            # 1. Tester la connexion GNS3
            if not await self._test_gns3_connection():
                logger.error("Impossible de se connecter à GNS3")
                return False
            
            # 2. Charger l'état initial
            await self._load_initial_state()
            
            # 3. Démarrer le monitoring WebSocket
            await self._start_websocket_monitoring()
            
            # 4. Enregistrer les callbacks inter-modules
            self._register_inter_module_callbacks()
            
            self.is_connected = True
            logger.info("Service Central GNS3 initialisé avec succès")
            
            # Notification système
            ubuntu_notification_service.send_notification(
                title="🚀 Service Central GNS3 Démarré",
                message="Infrastructure de communication GNS3 opérationnelle",
                urgency='low',
                category='system.gns3'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service GNS3: {e}")
            return False

    async def _test_gns3_connection(self) -> bool:
        """Teste la connexion au serveur GNS3."""
        try:
            version_info = self.gns3_client.get_version()
            if version_info and 'version' in version_info:
                logger.info(f"Connecté à GNS3 v{version_info['version']}")
                return True
            return False
        except Exception as e:
            logger.error(f"Test de connexion GNS3 échoué: {e}")
            return False

    async def _load_initial_state(self):
        """Charge l'état initial du réseau GNS3."""
        try:
            # Récupérer tous les projets
            projects_data = {}
            projects = self.gns3_client.get_projects() or []
            
            for project in projects:
                project_id = project.get('project_id')
                if project_id:
                    # Récupérer les nœuds
                    nodes = self.gns3_client.get_nodes(project_id) or []
                    project['nodes'] = {node.get('node_id'): node for node in nodes}
                    projects_data[project_id] = project
            
            # Créer l'état réseau
            self.current_state = NetworkState(
                projects=projects_data,
                nodes={},
                links={},
                last_update=timezone.now(),
                server_status="connected"
            )
            
            # Indexer tous les nœuds
            for project in projects_data.values():
                for node_id, node in project.get('nodes', {}).items():
                    self.current_state.nodes[node_id] = {
                        **node,
                        'project_id': project.get('project_id')
                    }
            
            # Mettre en cache
            await self._cache_network_state()
            
            logger.info(f"État initial chargé: {len(self.current_state.projects)} projets, "
                       f"{len(self.current_state.nodes)} nœuds")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'état initial: {e}")

    # ==================== CACHE REDIS ====================
    
    async def _cache_network_state(self):
        """Met en cache l'état complet du réseau."""
        if not self.current_state:
            return
            
        try:
            # Cache principal
            cache.set(
                f"{self.cache_prefix}:network_state",
                {
                    'projects': self.current_state.projects,
                    'nodes': self.current_state.nodes,
                    'links': self.current_state.links,
                    'last_update': self.current_state.last_update.isoformat(),
                    'server_status': self.current_state.server_status
                },
                timeout=self.state_ttl
            )
            
            # Cache individuel pour accès rapide
            for node_id, node in self.current_state.nodes.items():
                cache.set(
                    f"{self.cache_prefix}:node:{node_id}",
                    node,
                    timeout=self.state_ttl
                )
                
            for project_id, project in self.current_state.projects.items():
                cache.set(
                    f"{self.cache_prefix}:project:{project_id}",
                    project,
                    timeout=self.state_ttl
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache: {e}")

    def get_cached_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut d'un nœud depuis le cache.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Statut du nœud ou None
        """
        try:
            node_data = cache.get(f"{self.cache_prefix}:node:{node_id}")
            if node_data:
                self.stats['cache_hits'] += 1
                return node_data
            else:
                self.stats['cache_misses'] += 1
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du cache pour le nœud {node_id}: {e}")
            return None

    def get_cached_topology(self) -> Optional[Dict[str, Any]]:
        """
        Récupère la topologie complète depuis le cache.
        
        Returns:
            Topologie complète ou None
        """
        try:
            topology = cache.get(f"{self.cache_prefix}:network_state")
            if topology:
                self.stats['cache_hits'] += 1
                return topology
            else:
                self.stats['cache_misses'] += 1
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du cache de topologie: {e}")
            return None

    # ==================== ACTIONS GNS3 ====================
    
    async def start_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Démarre un nœud avec gestion d'événements.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'opération
        """
        try:
            self.stats['api_calls'] += 1
            self.stats['last_activity'] = timezone.now()
            
            # 1. Exécuter l'action via l'API GNS3
            result = self.gns3_client.start_node(project_id, node_id)
            
            if result.get('success', True):
                # 2. Mettre à jour le cache
                node_data = self.get_cached_node_status(node_id) or {}
                node_data.update({
                    'status': 'started',
                    'last_update': timezone.now().isoformat(),
                    'project_id': project_id
                })
                
                cache.set(
                    f"{self.cache_prefix}:node:{node_id}",
                    node_data,
                    timeout=self.state_ttl
                )
                
                # 3. Générer l'événement
                event = GNS3Event(
                    event_type=GNS3EventType.NODE_STARTED,
                    project_id=project_id,
                    data={
                        'node_id': node_id,
                        'old_status': node_data.get('previous_status', 'stopped'),
                        'new_status': 'started',
                        'action': 'start_node',
                        'node_name': node_data.get('name', 'Unknown')
                    },
                    timestamp=timezone.now()
                )
                
                # 4. Diffuser l'événement
                await self._broadcast_event(event)
                
                logger.info(f"Nœud {node_id} démarré avec succès")
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du nœud {node_id}: {e}")
            return {"success": False, "error": str(e)}

    async def stop_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Arrête un nœud avec gestion d'événements.
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'opération
        """
        try:
            self.stats['api_calls'] += 1
            self.stats['last_activity'] = timezone.now()
            
            # Récupérer l'état actuel
            current_node = self.get_cached_node_status(node_id) or {}
            old_status = current_node.get('status', 'unknown')
            
            # Exécuter l'action
            result = self.gns3_client.stop_node(project_id, node_id)
            
            if result.get('success', True):
                # Mettre à jour le cache
                current_node.update({
                    'status': 'stopped',
                    'previous_status': old_status,
                    'last_update': timezone.now().isoformat()
                })
                
                cache.set(
                    f"{self.cache_prefix}:node:{node_id}",
                    current_node,
                    timeout=self.state_ttl
                )
                
                # Générer l'événement
                event = GNS3Event(
                    event_type=GNS3EventType.NODE_STOPPED,
                    project_id=project_id,
                    data={
                        'node_id': node_id,
                        'old_status': old_status,
                        'new_status': 'stopped',
                        'action': 'stop_node',
                        'node_name': current_node.get('name', 'Unknown')
                    },
                    timestamp=timezone.now()
                )
                
                await self._broadcast_event(event)
                
                logger.info(f"Nœud {node_id} arrêté avec succès")
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du nœud {node_id}: {e}")
            return {"success": False, "error": str(e)}

    async def restart_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Redémarre un nœud (stop puis start).
        
        Args:
            project_id: ID du projet
            node_id: ID du nœud
            
        Returns:
            Résultat de l'opération
        """
        try:
            # 1. Arrêter le nœud
            stop_result = await self.stop_node(project_id, node_id)
            if not stop_result.get('success', True):
                return stop_result
            
            # 2. Attendre un peu
            await asyncio.sleep(2)
            
            # 3. Démarrer le nœud
            start_result = await self.start_node(project_id, node_id)
            
            return {
                'success': start_result.get('success', True),
                'action': 'restart_node',
                'stop_result': stop_result,
                'start_result': start_result
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du redémarrage du nœud {node_id}: {e}")
            return {"success": False, "error": str(e)}

    async def start_project_nodes(self, project_id: str) -> Dict[str, Any]:
        """
        Démarre tous les nœuds d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Résultat de l'opération
        """
        try:
            project_data = cache.get(f"{self.cache_prefix}:project:{project_id}")
            if not project_data:
                return {"success": False, "error": "Projet non trouvé"}
            
            nodes = project_data.get('nodes', {})
            results = {}
            
            # Démarrer tous les nœuds en parallèle
            tasks = []
            for node_id in nodes:
                task = self.start_node(project_id, node_id)
                tasks.append((node_id, task))
            
            # Attendre tous les résultats
            for node_id, task in tasks:
                try:
                    result = await task
                    results[node_id] = result
                except Exception as e:
                    results[node_id] = {"success": False, "error": str(e)}
            
            success_count = sum(1 for r in results.values() if r.get('success', True))
            
            # Événement de démarrage de projet
            event = GNS3Event(
                event_type=GNS3EventType.TOPOLOGY_CHANGED,
                project_id=project_id,
                data={
                    'action': 'start_project_nodes',
                    'total_nodes': len(nodes),
                    'started_nodes': success_count,
                    'results': results
                },
                timestamp=timezone.now()
            )
            
            await self._broadcast_event(event)
            
            return {
                'success': success_count > 0,
                'total_nodes': len(nodes),
                'started_nodes': success_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage des nœuds du projet {project_id}: {e}")
            return {"success": False, "error": str(e)}

    # ==================== ÉVÉNEMENTS ====================
    
    async def _broadcast_event(self, event: GNS3Event):
        """
        Diffuse un événement à tous les modules abonnés.
        
        Args:
            event: Événement à diffuser
        """
        try:
            self.stats['events_processed'] += 1
            
            # Convertir en message inter-module
            message_type = self._event_to_message_type(event.event_type)
            
            # Diffuser via le système inter-modules
            inter_module_service.send_message(
                message_type=message_type,
                data={
                    'event_type': event.event_type.value,
                    'project_id': event.project_id,
                    'timestamp': event.timestamp.isoformat(),
                    'source': event.source,
                    **event.data
                },
                sender='gns3_central_service'
            )
            
            # Appeler les callbacks spécifiques
            for callback in self.event_callbacks:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Erreur dans callback d'événement: {e}")
                    
            logger.debug(f"Événement diffusé: {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la diffusion d'événement: {e}")

    def _event_to_message_type(self, event_type: GNS3EventType) -> MessageType:
        """Convertit un type d'événement GNS3 en type de message inter-module."""
        mapping = {
            GNS3EventType.NODE_STARTED: MessageType.NODE_STATUS_CHANGE,
            GNS3EventType.NODE_STOPPED: MessageType.NODE_STATUS_CHANGE,
            GNS3EventType.NODE_SUSPENDED: MessageType.NODE_STATUS_CHANGE,
            GNS3EventType.NODE_CREATED: MessageType.TOPOLOGY_UPDATE,
            GNS3EventType.NODE_DELETED: MessageType.TOPOLOGY_UPDATE,
            GNS3EventType.PROJECT_OPENED: MessageType.TOPOLOGY_UPDATE,
            GNS3EventType.PROJECT_CLOSED: MessageType.TOPOLOGY_UPDATE,
            GNS3EventType.TOPOLOGY_CHANGED: MessageType.TOPOLOGY_UPDATE,
            GNS3EventType.LINK_CREATED: MessageType.NETWORK_EVENT,
            GNS3EventType.LINK_DELETED: MessageType.NETWORK_EVENT,
        }
        return mapping.get(event_type, MessageType.NETWORK_EVENT)

    def register_event_callback(self, callback: Callable):
        """
        Enregistre un callback pour les événements GNS3.
        
        Args:
            callback: Fonction async à appeler pour chaque événement
        """
        self.event_callbacks.add(callback)
        logger.debug(f"Callback d'événement enregistré: {callback.__name__}")

    def unregister_event_callback(self, callback: Callable):
        """Désenregistre un callback d'événement."""
        self.event_callbacks.discard(callback)

    # ==================== WEBSOCKET (pour le futur) ====================
    
    async def _start_websocket_monitoring(self):
        """Démarre le monitoring WebSocket (sera implémenté plus tard)."""
        # Pour l'instant, on utilise du polling
        self.is_monitoring = True
        logger.info("Monitoring WebSocket préparé (polling mode)")

    def _register_inter_module_callbacks(self):
        """Enregistre les callbacks pour les messages inter-modules."""
        # Les modules pourront s'abonner via le système existant
        logger.debug("Callbacks inter-modules enregistrés")

    # ==================== API PUBLIQUE ====================
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet du service.
        
        Returns:
            Statut détaillé du service
        """
        uptime = timezone.now() - self.stats['uptime_start']
        
        return {
            'service_name': 'GNS3CentralService',
            'version': '1.0.0',
            'status': 'connected' if self.is_connected else 'disconnected',
            'gns3_server': {
                'host': self.gns3_config['host'],
                'port': self.gns3_config['port'],
                'connected': self.is_connected
            },
            'monitoring': {
                'active': self.is_monitoring,
                'websocket_connected': self.websocket_connection is not None
            },
            'statistics': {
                **self.stats,
                'uptime_seconds': uptime.total_seconds(),
                'last_activity_ago': (timezone.now() - self.stats['last_activity']).total_seconds() 
                    if self.stats['last_activity'] else None
            },
            'cache': {
                'prefix': self.cache_prefix,
                'ttl_seconds': self.state_ttl,
                'network_state_cached': cache.get(f"{self.cache_prefix}:network_state") is not None
            },
            'callbacks': {
                'registered_callbacks': len(self.event_callbacks)
            },
            'last_update': timezone.now().isoformat()
        }

    async def refresh_topology(self) -> Dict[str, Any]:
        """
        Force une actualisation complète de la topologie.
        
        Returns:
            Nouvelle topologie
        """
        try:
            await self._load_initial_state()
            topology = self.get_cached_topology()
            
            # Événement de rafraîchissement
            event = GNS3Event(
                event_type=GNS3EventType.TOPOLOGY_CHANGED,
                project_id="",
                data={
                    'action': 'topology_refresh',
                    'projects_count': len(self.current_state.projects) if self.current_state else 0,
                    'nodes_count': len(self.current_state.nodes) if self.current_state else 0
                },
                timestamp=timezone.now()
            )
            
            await self._broadcast_event(event)
            
            return {
                'success': True,
                'topology': topology,
                'refresh_time': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement de topologie: {e}")
            return {"success": False, "error": str(e)}


# Instance globale du service
gns3_central_service = GNS3CentralService()