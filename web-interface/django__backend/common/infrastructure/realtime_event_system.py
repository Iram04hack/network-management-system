"""
Système d'Événements Temps Réel pour GNS3 Central Service.

Ce module implémente un système complet d'événements temps réel utilisant :
- WebSocket pour la communication bidirectionnelle
- Redis Pub/Sub pour la distribution d'événements
- Channels Django pour la gestion WebSocket
- Queue système pour la gestion des événements asynchrones
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from redis import Redis
import redis.asyncio as aioredis

from .gns3_central_service import GNS3Event, GNS3EventType
from .ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priorités des événements pour la gestion de la queue."""
    CRITICAL = "critical"
    HIGH = "high" 
    NORMAL = "normal"
    LOW = "low"


class EventDeliveryStatus(Enum):
    """Statuts de livraison des événements."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class RealtimeEvent:
    """Événement temps réel enrichi."""
    event_id: str
    event_type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: EventPriority = EventPriority.NORMAL
    delivery_status: EventDeliveryStatus = EventDeliveryStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    target_modules: Optional[List[str]] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'événement en dictionnaire."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'delivery_status': self.delivery_status.value,
            'retry_count': self.retry_count,
            'correlation_id': self.correlation_id,
            'target_modules': self.target_modules or []
        }


class GNS3WebSocketConsumer(AsyncWebsocketConsumer):
    """
    Consommateur WebSocket pour les événements GNS3 temps réel.
    
    Gère les connexions WebSocket des clients et distribue les événements
    en fonction des abonnements de chaque connexion.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = "gns3_events"
        self.user_subscriptions: Set[str] = set()
        self.connection_id = str(uuid.uuid4())
        self.last_heartbeat = timezone.now()
        
    async def connect(self):
        """Accepte la connexion WebSocket."""
        try:
            # Rejoindre le groupe d'événements GNS3
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Enregistrer la connexion
            await self._register_connection()
            
            # Envoyer un message de bienvenue
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'connection_id': self.connection_id,
                'message': 'Connexion WebSocket GNS3 établie',
                'available_subscriptions': [
                    'node_status', 'topology_changes', 'project_events', 'all_events'
                ],
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"Connexion WebSocket GNS3 établie: {self.connection_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion WebSocket: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Ferme la connexion WebSocket."""
        try:
            # Quitter le groupe d'événements
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Désenregistrer la connexion
            await self._unregister_connection()
            
            logger.info(f"Connexion WebSocket GNS3 fermée: {self.connection_id} (code: {close_code})")
            
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture WebSocket: {e}")
    
    async def receive(self, text_data):
        """Reçoit et traite les messages du client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self._handle_subscription(data)
            elif message_type == 'unsubscribe':
                await self._handle_unsubscription(data)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(data)
            elif message_type == 'request_topology':
                await self._handle_topology_request()
            elif message_type == 'node_action':
                await self._handle_node_action(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Type de message non reconnu: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erreur interne: {str(e)}'
            }))
    
    async def _handle_subscription(self, data):
        """Gère les demandes d'abonnement."""
        subscriptions = data.get('subscriptions', [])
        
        for subscription in subscriptions:
            if subscription in ['node_status', 'topology_changes', 'project_events', 'all_events']:
                self.user_subscriptions.add(subscription)
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscriptions': list(self.user_subscriptions),
            'message': f'Abonné à {len(self.user_subscriptions)} types d\'événements'
        }))
        
        # Mettre à jour le cache des abonnements
        await self._update_subscription_cache()
    
    async def _handle_unsubscription(self, data):
        """Gère les demandes de désabonnement."""
        subscriptions = data.get('subscriptions', [])
        
        for subscription in subscriptions:
            self.user_subscriptions.discard(subscription)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'remaining_subscriptions': list(self.user_subscriptions)
        }))
        
        await self._update_subscription_cache()
    
    async def _handle_heartbeat(self, data):
        """Gère les messages de heartbeat."""
        self.last_heartbeat = timezone.now()
        
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_ack',
            'server_time': self.last_heartbeat.isoformat()
        }))
    
    async def _handle_topology_request(self):
        """Gère les demandes de topologie."""
        from .gns3_central_service import gns3_central_service
        
        try:
            topology = gns3_central_service.get_cached_topology()
            
            await self.send(text_data=json.dumps({
                'type': 'topology_response',
                'data': topology or {},
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erreur lors de la récupération de la topologie: {str(e)}'
            }))
    
    async def _handle_node_action(self, data):
        """Gère les actions sur les nœuds."""
        from .gns3_central_service import gns3_central_service
        
        try:
            action = data.get('action')
            project_id = data.get('project_id')
            node_id = data.get('node_id')
            
            if not all([action, project_id, node_id]):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'action, project_id et node_id sont requis'
                }))
                return
            
            if action == 'start':
                result = await gns3_central_service.start_node(project_id, node_id)
            elif action == 'stop':
                result = await gns3_central_service.stop_node(project_id, node_id)
            elif action == 'restart':
                result = await gns3_central_service.restart_node(project_id, node_id)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Action non supportée: {action}'
                }))
                return
            
            await self.send(text_data=json.dumps({
                'type': 'node_action_result',
                'action': action,
                'project_id': project_id,
                'node_id': node_id,
                'result': result
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erreur lors de l\'action sur le nœud: {str(e)}'
            }))
    
    async def _register_connection(self):
        """Enregistre la connexion dans le cache."""
        connection_data = {
            'connection_id': self.connection_id,
            'channel_name': self.channel_name,
            'connected_at': timezone.now().isoformat(),
            'subscriptions': list(self.user_subscriptions),
            'last_heartbeat': self.last_heartbeat.isoformat()
        }
        
        cache.set(f"gns3_websocket_connection:{self.connection_id}", connection_data, timeout=3600)
    
    async def _unregister_connection(self):
        """Désenregistre la connexion du cache."""
        cache.delete(f"gns3_websocket_connection:{self.connection_id}")
    
    async def _update_subscription_cache(self):
        """Met à jour le cache des abonnements."""
        connection_data = cache.get(f"gns3_websocket_connection:{self.connection_id}")
        if connection_data:
            connection_data['subscriptions'] = list(self.user_subscriptions)
            cache.set(f"gns3_websocket_connection:{self.connection_id}", connection_data, timeout=3600)
    
    # Gestionnaires d'événements du group
    async def gns3_event(self, event):
        """Reçoit et filtre les événements GNS3."""
        event_data = event['event_data']
        event_type = event_data.get('event_type', '')
        
        # Filtrer selon les abonnements
        if self._should_send_event(event_type):
            await self.send(text_data=json.dumps({
                'type': 'gns3_event',
                'event_data': event_data,
                'timestamp': timezone.now().isoformat()
            }))
    
    def _should_send_event(self, event_type: str) -> bool:
        """Détermine si l'événement doit être envoyé au client."""
        if 'all_events' in self.user_subscriptions:
            return True
        
        # Mapping des types d'événements aux abonnements
        event_mapping = {
            'node.started': 'node_status',
            'node.stopped': 'node_status',
            'node.suspended': 'node_status',
            'node.created': 'topology_changes',
            'node.deleted': 'topology_changes',
            'node.updated': 'topology_changes',
            'project.opened': 'project_events',
            'project.closed': 'project_events',
            'project.created': 'project_events',
            'project.deleted': 'project_events',
            'topology.changed': 'topology_changes',
            'link.created': 'topology_changes',
            'link.deleted': 'topology_changes',
        }
        
        required_subscription = event_mapping.get(event_type)
        return required_subscription in self.user_subscriptions


class RealtimeEventManager:
    """
    Gestionnaire d'événements temps réel pour le service central GNS3.
    
    Responsabilités :
    - Distribution d'événements via WebSocket et Redis
    - Gestion des queues d'événements par priorité
    - Retry logic pour les événements échoués
    - Métriques et monitoring des événements
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'événements."""
        self.redis_config = {
            'host': getattr(settings, 'REDIS_HOST', 'localhost'),
            'port': getattr(settings, 'REDIS_PORT', 6379),
            'db': getattr(settings, 'REDIS_DB', 0),
            'decode_responses': True
        }
        
        self.redis_client = Redis(**self.redis_config)
        self.event_queues = {
            EventPriority.CRITICAL: f"gns3_events:critical",
            EventPriority.HIGH: f"gns3_events:high",
            EventPriority.NORMAL: f"gns3_events:normal",
            EventPriority.LOW: f"gns3_events:low"
        }
        
        self.channel_name = "gns3_events_realtime"
        self.statistics = {
            'events_published': 0,
            'events_delivered': 0,
            'events_failed': 0,
            'events_retried': 0,
            'connections_active': 0,
            'last_event_time': None
        }
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_running = False
        
        logger.info("Gestionnaire d'événements temps réel GNS3 initialisé")
    
    async def start(self):
        """Démarre le gestionnaire d'événements."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Démarrer les workers de traitement des événements
        asyncio.create_task(self._process_event_queues())
        asyncio.create_task(self._cleanup_expired_events())
        asyncio.create_task(self._monitor_connections())
        
        logger.info("Gestionnaire d'événements temps réel démarré")
    
    async def stop(self):
        """Arrête le gestionnaire d'événements."""
        self.is_running = False
        self.executor.shutdown(wait=True)
        logger.info("Gestionnaire d'événements temps réel arrêté")
    
    async def publish_event(self, event: RealtimeEvent):
        """
        Publie un événement vers tous les canaux de distribution.
        
        Args:
            event: Événement à publier
        """
        try:
            # Générer un ID unique si pas fourni
            if not event.event_id:
                event.event_id = str(uuid.uuid4())
            
            # Ajouter à la queue Redis selon la priorité
            queue_name = self.event_queues[event.priority]
            event_data = json.dumps(event.to_dict())
            
            await self._async_redis_lpush(queue_name, event_data)
            
            # Publier immédiatement via Redis Pub/Sub pour les événements critiques
            if event.priority in [EventPriority.CRITICAL, EventPriority.HIGH]:
                await self._publish_to_pubsub(event)
            
            # Publier via Channels pour WebSocket
            await self._publish_to_websocket(event)
            
            # Mettre à jour les statistiques
            self.statistics['events_published'] += 1
            self.statistics['last_event_time'] = timezone.now()
            
            # Cache pour la traçabilité
            cache.set(f"gns3_event:{event.event_id}", event.to_dict(), timeout=3600)
            
            logger.debug(f"Événement publié: {event.event_type} (ID: {event.event_id})")
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication d'événement: {e}")
            raise
    
    async def publish_gns3_event(self, gns3_event: GNS3Event):
        """
        Publie un événement GNS3 en le convertissant en événement temps réel.
        
        Args:
            gns3_event: Événement GNS3 à publier
        """
        # Déterminer la priorité selon le type d'événement
        priority_mapping = {
            GNS3EventType.NODE_STARTED: EventPriority.HIGH,
            GNS3EventType.NODE_STOPPED: EventPriority.HIGH,
            GNS3EventType.NODE_SUSPENDED: EventPriority.NORMAL,
            GNS3EventType.NODE_CREATED: EventPriority.NORMAL,
            GNS3EventType.NODE_DELETED: EventPriority.HIGH,
            GNS3EventType.PROJECT_OPENED: EventPriority.NORMAL,
            GNS3EventType.PROJECT_CLOSED: EventPriority.NORMAL,
            GNS3EventType.TOPOLOGY_CHANGED: EventPriority.HIGH,
        }
        
        priority = priority_mapping.get(gns3_event.event_type, EventPriority.NORMAL)
        
        realtime_event = RealtimeEvent(
            event_id=str(uuid.uuid4()),
            event_type=gns3_event.event_type.value,
            source=gns3_event.source,
            data=gns3_event.data,
            timestamp=gns3_event.timestamp,
            priority=priority,
            correlation_id=gns3_event.data.get('correlation_id')
        )
        
        await self.publish_event(realtime_event)
    
    async def _publish_to_pubsub(self, event: RealtimeEvent):
        """Publie l'événement via Redis Pub/Sub."""
        try:
            redis_async = aioredis.from_url(f"redis://{self.redis_config['host']}:{self.redis_config['port']}")
            
            channel = f"gns3_events:{event.event_type}"
            await redis_async.publish(channel, json.dumps(event.to_dict()))
            
            await redis_async.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication Redis Pub/Sub: {e}")
    
    async def _publish_to_websocket(self, event: RealtimeEvent):
        """Publie l'événement via WebSocket Channels."""
        try:
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            
            await channel_layer.group_send(
                "gns3_events",
                {
                    "type": "gns3_event",
                    "event_data": event.to_dict()
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication WebSocket: {e}")
    
    async def _async_redis_lpush(self, queue_name: str, data: str):
        """Version async de Redis LPUSH."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.redis_client.lpush, queue_name, data)
    
    async def _process_event_queues(self):
        """Traite les queues d'événements par ordre de priorité."""
        priorities = [EventPriority.CRITICAL, EventPriority.HIGH, EventPriority.NORMAL, EventPriority.LOW]
        
        while self.is_running:
            try:
                for priority in priorities:
                    queue_name = self.event_queues[priority]
                    
                    # Traiter jusqu'à 10 événements par cycle
                    for _ in range(10):
                        event_data = self.redis_client.rpop(queue_name)
                        if not event_data:
                            break
                        
                        await self._process_single_event(json.loads(event_data))
                
                # Pause entre les cycles
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Erreur dans le traitement des queues d'événements: {e}")
                await asyncio.sleep(1)
    
    async def _process_single_event(self, event_data: Dict[str, Any]):
        """Traite un événement individuel."""
        try:
            event = RealtimeEvent(**event_data)
            
            # Logique de traitement spécifique
            success = await self._deliver_event(event)
            
            if success:
                event.delivery_status = EventDeliveryStatus.DELIVERED
                self.statistics['events_delivered'] += 1
            else:
                if event.retry_count < event.max_retries:
                    event.retry_count += 1
                    event.delivery_status = EventDeliveryStatus.RETRY
                    self.statistics['events_retried'] += 1
                    
                    # Remettre en queue avec délai
                    await asyncio.sleep(2 ** event.retry_count)  # Backoff exponentiel
                    await self._async_redis_lpush(
                        self.event_queues[event.priority], 
                        json.dumps(event.to_dict())
                    )
                else:
                    event.delivery_status = EventDeliveryStatus.FAILED
                    self.statistics['events_failed'] += 1
                    logger.error(f"Événement échoué définitivement: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement d'événement: {e}")
    
    async def _deliver_event(self, event: RealtimeEvent) -> bool:
        """Livre un événement vers ses destinations."""
        try:
            # Notifier les modules intéressés
            await self._notify_modules(event)
            
            # Notification système pour événements critiques
            if event.priority == EventPriority.CRITICAL:
                ubuntu_notification_service.send_notification(
                    title=f"🚨 Événement GNS3 Critique",
                    message=f"{event.event_type}: {event.data.get('message', 'Événement système')}",
                    urgency='critical',
                    category='network.gns3'
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la livraison d'événement: {e}")
            return False
    
    async def _notify_modules(self, event: RealtimeEvent):
        """Notifie les modules intéressés par l'événement."""
        # Si des modules cibles sont spécifiés
        if event.target_modules:
            for module in event.target_modules:
                await self._send_to_module(module, event)
        else:
            # Sinon, diffuser à tous les modules abonnés
            await self._broadcast_to_all_modules(event)
    
    async def _send_to_module(self, module_name: str, event: RealtimeEvent):
        """Envoie un événement à un module spécifique."""
        try:
            # Utiliser le système inter-modules existant
            from .inter_module_service import inter_module_service, MessageType
            
            inter_module_service.send_message(
                message_type=MessageType.NETWORK_EVENT,
                data={
                    'gns3_event': event.to_dict(),
                    'source': 'realtime_event_system'
                },
                sender='gns3_realtime_events',
                target_module=module_name
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi à {module_name}: {e}")
    
    async def _broadcast_to_all_modules(self, event: RealtimeEvent):
        """Diffuse un événement à tous les modules."""
        from .inter_module_service import inter_module_service, MessageType
        
        inter_module_service.send_message(
            message_type=MessageType.NETWORK_EVENT,
            data={
                'gns3_event': event.to_dict(),
                'source': 'realtime_event_system'
            },
            sender='gns3_realtime_events'
        )
    
    async def _cleanup_expired_events(self):
        """Nettoie les événements expirés du cache."""
        while self.is_running:
            try:
                # Nettoyer toutes les heures
                await asyncio.sleep(3600)
                
                # Les événements sont automatiquement expirés par Redis TTL
                logger.debug("Nettoyage des événements expirés effectué")
                
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage: {e}")
    
    async def _monitor_connections(self):
        """Monitore les connexions WebSocket actives."""
        while self.is_running:
            try:
                # Compter les connexions actives
                pattern = "gns3_websocket_connection:*"
                try:
                    connections = cache.keys(pattern)
                    self.statistics['connections_active'] = len(connections)
                except AttributeError:
                    # LocMemCache n'a pas de méthode keys(), utiliser une estimation
                    self.statistics['connections_active'] = getattr(self, '_estimated_connections', 0)
                
                # Nettoyer les connexions expirées (seulement si on a accès aux clés)
                if 'connections' in locals():
                    current_time = timezone.now()
                    for conn_key in connections:
                        conn_data = cache.get(conn_key)
                        if conn_data:
                            last_heartbeat = datetime.fromisoformat(conn_data['last_heartbeat'])
                            if current_time - last_heartbeat > timedelta(minutes=5):
                                cache.delete(conn_key)
                
                await asyncio.sleep(30)  # Vérifier toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"Erreur lors du monitoring des connexions: {e}")
                await asyncio.sleep(60)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques du gestionnaire d'événements."""
        return {
            **self.statistics,
            'queue_sizes': {
                priority.value: self.redis_client.llen(queue_name)
                for priority, queue_name in self.event_queues.items()
            },
            'is_running': self.is_running,
            'last_check': timezone.now().isoformat()
        }


# Instance globale du gestionnaire d'événements
realtime_event_manager = RealtimeEventManager()


# Fonctions utilitaires pour l'intégration
async def publish_gns3_event_realtime(gns3_event: GNS3Event):
    """
    Fonction utilitaire pour publier un événement GNS3 en temps réel.
    
    Args:
        gns3_event: Événement GNS3 à publier
    """
    await realtime_event_manager.publish_gns3_event(gns3_event)


def create_realtime_event(event_type: str, data: Dict[str, Any], 
                         priority: EventPriority = EventPriority.NORMAL,
                         target_modules: Optional[List[str]] = None) -> RealtimeEvent:
    """
    Crée un événement temps réel.
    
    Args:
        event_type: Type de l'événement
        data: Données de l'événement
        priority: Priorité de l'événement
        target_modules: Modules cibles (optionnel)
        
    Returns:
        Événement temps réel créé
    """
    return RealtimeEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        source="gns3_central_service",
        data=data,
        timestamp=timezone.now(),
        priority=priority,
        target_modules=target_modules
    )