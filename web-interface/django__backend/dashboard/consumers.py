"""
Consommateurs WebSocket pour le module dashboard.

Ce module contient les consommateurs WebSocket pour les mises à jour
en temps réel du tableau de bord.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from .application.use_cases import (
    GetDashboardOverviewUseCase,
    GetNetworkOverviewUseCase,
    GetSystemHealthMetricsUseCase
)
from .di_container import get_container

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour les mises à jour du tableau de bord en temps réel."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_task = None
        self.update_interval = 30  # 30 secondes par défaut
        
    async def connect(self):
        """Connexion au WebSocket."""
        # Vérifier l'authentification
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return
        
        # Rejoindre le groupe dashboard
        self.group_name = "dashboard_updates"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accepter la connexion
        await self.accept()
        
        # Envoyer les données initiales
        try:
            initial_data = await self._get_dashboard_data()
            await self.send(text_data=json.dumps({
                'type': 'dashboard_update',
                'data': initial_data,
                'timestamp': initial_data.get('timestamp')
            }))
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données initiales: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Erreur lors du chargement des données initiales'
            }))
        
        # Démarrer les mises à jour périodiques
        self.update_task = asyncio.create_task(self._periodic_updates())
    
    async def disconnect(self, close_code):
        """Déconnexion du WebSocket."""
        # Arrêter les mises à jour périodiques
        if self.update_task:
            self.update_task.cancel()
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Réception de messages du client."""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'get_dashboard':
                # Récupérer les données du dashboard immédiatement
                dashboard_data = await self._get_dashboard_data()
                await self.send(text_data=json.dumps({
                    'type': 'dashboard_update',
                    'data': dashboard_data,
                    'timestamp': dashboard_data.get('timestamp')
                }))
                
            elif command == 'get_network_overview':
                # Récupérer les données réseau
                network_data = await self._get_network_data()
                await self.send(text_data=json.dumps({
                    'type': 'network_update',
                    'data': network_data,
                    'timestamp': network_data.get('timestamp')
                }))
                
            elif command == 'get_health_metrics':
                # Récupérer les métriques de santé
                health_data = await self._get_health_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'health_update',
                    'data': health_data
                }))
                
            elif command == 'set_update_interval':
                # Modifier l'intervalle de mise à jour
                new_interval = data.get('interval', 30)
                if 5 <= new_interval <= 300:  # Entre 5 secondes et 5 minutes
                    self.update_interval = new_interval
                    await self.send(text_data=json.dumps({
                        'type': 'interval_updated',
                        'interval': self.update_interval
                    }))
                    
                    # Redémarrer la tâche de mise à jour avec le nouvel intervalle
                    if self.update_task:
                        self.update_task.cancel()
                    self.update_task = asyncio.create_task(self._periodic_updates())
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Intervalle doit être entre 5 et 300 secondes'
                    }))
                    
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Erreur lors du traitement de la demande'
            }))
    
    async def dashboard_update(self, event):
        """Réception d'une mise à jour du dashboard du groupe."""
        await self.send(text_data=json.dumps(event))
    
    async def _periodic_updates(self):
        """Envoie périodiquement des mises à jour du dashboard."""
        try:
            while True:
                await asyncio.sleep(self.update_interval)
                
                # Récupérer les nouvelles données
                dashboard_data = await self._get_dashboard_data()
                
                # Envoyer au groupe
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'dashboard_update',
                        'data': dashboard_data,
                        'timestamp': dashboard_data.get('timestamp')
                    }
                )
                
        except asyncio.CancelledError:
            # La tâche a été annulée normalement
            pass
        except Exception as e:
            logger.error(f"Erreur dans les mises à jour périodiques: {e}")
    
    @database_sync_to_async
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Récupère les données du dashboard via les cas d'utilisation."""
        try:
            container = get_container()
            dashboard_use_case = container.resolve(GetDashboardOverviewUseCase)
            return dashboard_use_case.execute()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données dashboard: {e}")
            return {'error': str(e)}
    
    @database_sync_to_async
    def _get_network_data(self) -> Dict[str, Any]:
        """Récupère les données réseau via les cas d'utilisation."""
        try:
            container = get_container()
            network_use_case = container.resolve(GetNetworkOverviewUseCase)
            return network_use_case.execute()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données réseau: {e}")
            return {'error': str(e)}
    
    @database_sync_to_async
    def _get_health_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de santé via les cas d'utilisation."""
        try:
            container = get_container()
            health_use_case = container.resolve(GetSystemHealthMetricsUseCase)
            return health_use_case.execute()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de santé: {e}")
            return {'error': str(e)}


class TopologyConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour les mises à jour de topologie en temps réel."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topology_id = None
        self.update_task = None
        
    async def connect(self):
        """Connexion au WebSocket."""
        # Vérifier l'authentification
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return
        
        # Récupérer l'ID de la topologie depuis l'URL
        self.topology_id = self.scope['url_route']['kwargs'].get('topology_id')
        
        if not self.topology_id:
            await self.close()
            return
        
        # Rejoindre le groupe spécifique à cette topologie
        self.group_name = f"topology_{self.topology_id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accepter la connexion
        await self.accept()
        
        # Envoyer les données initiales de la topologie
        try:
            topology_data = await self._get_topology_data()
            await self.send(text_data=json.dumps({
                'type': 'topology_update',
                'data': topology_data
            }))
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données de topologie: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Erreur lors du chargement de la topologie'
            }))
        
        # Démarrer les mises à jour périodiques
        self.update_task = asyncio.create_task(self._periodic_topology_updates())
    
    async def disconnect(self, close_code):
        """Déconnexion du WebSocket."""
        # Arrêter les mises à jour périodiques
        if self.update_task:
            self.update_task.cancel()
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def topology_update(self, event):
        """Réception d'une mise à jour de topologie du groupe."""
        await self.send(text_data=json.dumps(event))
    
    async def _periodic_topology_updates(self):
        """Envoie périodiquement des mises à jour de topologie."""
        try:
            while True:
                await asyncio.sleep(60)  # Mise à jour toutes les minutes
                
                topology_data = await self._get_topology_data()
                
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'topology_update',
                        'data': topology_data
                    }
                )
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Erreur dans les mises à jour de topologie: {e}")
    
    @database_sync_to_async
    def _get_topology_data(self) -> Dict[str, Any]:
        """Récupère les données de topologie."""
        try:
            container = get_container()
            from .application.use_cases import GetIntegratedTopologyUseCase
            topology_use_case = container.resolve(GetIntegratedTopologyUseCase)
            return topology_use_case.execute(self.topology_id)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de topologie: {e}")
            return {'error': str(e)}