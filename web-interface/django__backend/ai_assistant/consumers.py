"""
Consumers WebSocket pour l'assistant IA.

Ce module contient les consumers WebSocket pour permettre une communication
en temps réel avec l'assistant IA, notamment pour le streaming des réponses.
"""

import json
import logging
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from .config import di, settings
from .domain.exceptions import AIClientException, KnowledgeBaseException

logger = logging.getLogger(__name__)


class AIAssistantConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour l'assistant IA."""
    
    async def connect(self):
        """Gère la connexion WebSocket."""
        # Vérifier l'authentification de l'utilisateur
        if self.scope["user"] is None or isinstance(self.scope["user"], AnonymousUser):
            logger.warning("Tentative de connexion WebSocket sans authentification")
            await self.close(code=4001)
            return
            
        # Accepter la connexion
        self.user_id = self.scope["user"].id
        self.conversation_id = None
        self.streaming_task = None
        
        # Générer un identifiant unique pour cette connexion
        self.connection_id = str(uuid.uuid4())
        
        # Rejoindre un groupe spécifique à l'utilisateur
        self.group_name = f"ai_assistant_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()
        logger.info(f"Connexion WebSocket établie pour l'utilisateur {self.user_id}")

    async def disconnect(self, close_code):
        """Gère la déconnexion WebSocket."""
        # Annuler toute tâche de streaming en cours
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                logger.info(f"Tâche de streaming annulée pour l'utilisateur {self.user_id}")
        
        # Quitter le groupe
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            
        logger.info(f"Déconnexion WebSocket pour l'utilisateur {self.user_id} (code: {close_code})")

    async def receive(self, text_data):
        """
        Gère la réception de messages WebSocket.
        
        Args:
            text_data: Données textuelles reçues
        """
        try:
            # Parser les données JSON
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Traiter selon le type de message
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'command':
                await self.handle_command(data)
            elif message_type == 'start_conversation':
                await self.handle_start_conversation(data)
            elif message_type == 'cancel_streaming':
                await self.handle_cancel_streaming()
            else:
                logger.warning(f"Type de message non supporté: {message_type}")
                await self.send_error("Type de message non supporté")
        except json.JSONDecodeError:
            logger.exception("Erreur de décodage JSON")
            await self.send_error("Format de message invalide")
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du message: {e}")
            await self.send_error(f"Erreur: {str(e)}")

    async def handle_message(self, data):
        """
        Gère un message de l'utilisateur.
        
        Args:
            data: Données du message
        """
        content = data.get('content')
        conversation_id = data.get('conversation_id')
        
        if not content:
            await self.send_error("Contenu du message manquant")
            return
            
        if not conversation_id:
            await self.send_error("ID de conversation manquant")
            return
            
        self.conversation_id = conversation_id
        
        # Envoyer un accusé de réception
        await self.send(text_data=json.dumps({
            'type': 'message_received',
            'message_id': data.get('message_id', str(uuid.uuid4())),
            'status': 'processing'
        }))
        
        # Traiter le message de manière asynchrone
        if settings.ENABLE_STREAMING:
            # Démarrer le streaming de la réponse
            self.streaming_task = asyncio.create_task(
                self.stream_response(conversation_id, content)
            )
        else:
            # Traitement synchrone sans streaming
            try:
                response = await self.process_message(conversation_id, content)
                await self.send(text_data=json.dumps({
                    'type': 'message_response',
                    'conversation_id': conversation_id,
                    'content': response.get('content', ''),
                    'actions': response.get('actions', []),
                    'sources': response.get('sources', []),
                    'processing_time': response.get('processing_time', 0)
                }))
            except Exception as e:
                logger.exception(f"Erreur lors du traitement du message: {e}")
                await self.send_error(f"Erreur lors du traitement du message: {str(e)}")

    async def stream_response(self, conversation_id, content):
        """
        Streame la réponse à un message.
        
        Args:
            conversation_id: ID de la conversation
            content: Contenu du message
        """
        try:
            # Obtenir le service IA
            service = di.get_ai_assistant_service()
            
            # Définir la fonction de callback pour le streaming
            async def stream_callback(chunk):
                await self.send(text_data=json.dumps({
                    'type': 'message_chunk',
                    'conversation_id': conversation_id,
                    'content': chunk
                }))
            
            # Traiter le message avec streaming
            full_response = await database_sync_to_async(service.process_message_stream)(
                conversation_id, 
                self.user_id, 
                content,
                stream_callback
            )
            
            # Envoyer la fin du streaming avec les métadonnées
            await self.send(text_data=json.dumps({
                'type': 'message_complete',
                'conversation_id': conversation_id,
                'actions': full_response.get('actions', []),
                'sources': full_response.get('sources', []),
                'processing_time': full_response.get('processing_time', 0)
            }))
            
        except asyncio.CancelledError:
            # Le streaming a été annulé
            logger.info(f"Streaming annulé pour la conversation {conversation_id}")
            await self.send(text_data=json.dumps({
                'type': 'message_cancelled',
                'conversation_id': conversation_id
            }))
            raise
        except Exception as e:
            logger.exception(f"Erreur lors du streaming: {e}")
            await self.send_error(f"Erreur lors du streaming: {str(e)}")

    async def handle_command(self, data):
        """
        Gère une commande de l'utilisateur.
        
        Args:
            data: Données de la commande
        """
        command = data.get('command')
        command_type = data.get('command_type')
        conversation_id = data.get('conversation_id')
        
        if not command:
            await self.send_error("Commande manquante")
            return
            
        if not command_type:
            await self.send_error("Type de commande manquant")
            return
            
        if not conversation_id:
            await self.send_error("ID de conversation manquant")
            return
            
        # Envoyer un accusé de réception
        await self.send(text_data=json.dumps({
            'type': 'command_received',
            'command_id': data.get('command_id', str(uuid.uuid4())),
            'status': 'processing'
        }))
        
        # Exécuter la commande
        try:
            result = await self.execute_command(conversation_id, command, command_type)
            await self.send(text_data=json.dumps({
                'type': 'command_result',
                'conversation_id': conversation_id,
                'result': result,
                'command': command,
                'command_type': command_type
            }))
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de la commande: {e}")
            await self.send_error(f"Erreur lors de l'exécution de la commande: {str(e)}")

    async def handle_start_conversation(self, data):
        """
        Gère le démarrage d'une nouvelle conversation.
        
        Args:
            data: Données de la conversation
        """
        title = data.get('title', 'Nouvelle conversation')
        
        try:
            conversation = await self.create_conversation(title)
            await self.send(text_data=json.dumps({
                'type': 'conversation_created',
                'conversation_id': conversation['id'],
                'title': conversation['title']
            }))
        except Exception as e:
            logger.exception(f"Erreur lors de la création de la conversation: {e}")
            await self.send_error(f"Erreur lors de la création de la conversation: {str(e)}")

    async def handle_cancel_streaming(self):
        """Gère l'annulation du streaming en cours."""
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
            logger.info(f"Streaming annulé par l'utilisateur {self.user_id}")
            await self.send(text_data=json.dumps({
                'type': 'streaming_cancelled'
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': "Aucun streaming en cours"
            }))

    @database_sync_to_async
    def process_message(self, conversation_id, content):
        """
        Traite un message de manière synchrone.
        
        Args:
            conversation_id: ID de la conversation
            content: Contenu du message
            
        Returns:
            Réponse du service
        """
        service = di.get_ai_assistant_service()
        return service.process_message(conversation_id, self.user_id, content)

    @database_sync_to_async
    def execute_command(self, conversation_id, command, command_type):
        """
        Exécute une commande.
        
        Args:
            conversation_id: ID de la conversation
            command: Commande à exécuter
            command_type: Type de commande
            
        Returns:
            Résultat de la commande
        """
        service = di.get_ai_assistant_service()
        return service.execute_command(conversation_id, self.user_id, command, command_type)

    @database_sync_to_async
    def create_conversation(self, title):
        """
        Crée une nouvelle conversation.
        
        Args:
            title: Titre de la conversation
            
        Returns:
            Conversation créée
        """
        service = di.get_ai_assistant_service()
        return service.create_conversation(title, self.user_id)

    async def send_error(self, message):
        """
        Envoie un message d'erreur au client.
        
        Args:
            message: Message d'erreur
        """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    async def ai_message(self, event):
        """
        Gère les messages IA envoyés via le channel layer.
        
        Args:
            event: Événement reçu
        """
        # Transmettre le message au client
        await self.send(text_data=json.dumps(event))


class NetworkMonitoringConsumer(AsyncWebsocketConsumer):
    """Consumer pour le monitoring réseau en temps réel"""
    
    async def connect(self):
        """Connexion au monitoring réseau"""
        self.user = self.scope["user"]
        
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Groupe pour les mises à jour réseau
        self.group_name = "network_monitoring"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Déconnexion du monitoring"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Traiter les demandes de monitoring"""
        try:
            data = json.loads(text_data)
            request_type = data.get('type', 'status')
            
            if request_type == 'status':
                await self.send_network_status()
            elif request_type == 'metrics':
                await self.send_network_metrics()
        except Exception as e:
            logger.error(f"Erreur monitoring: {e}")
            await self.send_error(str(e))
    
    async def send_network_status(self):
        """Envoyer le statut réseau"""
        # Simulé pour l'instant - à implémenter avec vraies données
        await self.send(text_data=json.dumps({
            'type': 'status',
            'data': {
                'network_health': 'green',
                'devices_online': 25,
                'devices_total': 30,
                'bandwidth_usage': 45.2
            }
        }))
    
    async def send_network_metrics(self):
        """Envoyer les métriques réseau"""
        # Simulé pour l'instant - à implémenter avec vraies données
        await self.send(text_data=json.dumps({
            'type': 'metrics',
            'data': {
                'cpu_usage': 30.5,
                'memory_usage': 65.2,
                'network_latency': 12.3,
                'packet_loss': 0.1
            }
        }))
    
    async def send_error(self, error_message: str):
        """Envoyer une erreur"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))
    
    # Handlers pour les messages de groupe
    async def network_update(self, event):
        """Mise à jour réseau"""
        await self.send(text_data=json.dumps({
            'type': 'network_update',
            'data': event['data']
        }))
    
    async def alert_notification(self, event):
        """Notification d'alerte"""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'message': event['message'],
            'severity': event.get('severity', 'info')
        }))