"""
WebSocket consumers pour le monitoring en temps réel.

Ce module fournit les consumers WebSocket pour diffuser les métriques,
alertes et états des équipements en temps réel.
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class MonitoringWebSocketConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket principal pour le monitoring.
    
    Gère les connexions en temps réel pour les métriques,
    alertes et statuts des équipements.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.device_id = None
        self.room_group_name = None
        self.update_task = None
    
    async def connect(self):
        """Gère la connexion WebSocket."""
        # Vérifier l'authentification
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close(code=4001)
            return
        
        self.user = self.scope["user"]
        self.device_id = self.scope["url_route"]["kwargs"].get("device_id")
        
        # Définir le nom du groupe
        if self.device_id:
            self.room_group_name = f"monitoring_device_{self.device_id}"
        else:
            self.room_group_name = "monitoring_global"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accepter la connexion
        await self.accept()
        
        # Envoyer les données initiales
        await self.send_initial_data()
        
        # Démarrer les mises à jour périodiques
        self.update_task = asyncio.create_task(self.periodic_updates())
        
        logger.info(f"WebSocket connecté pour utilisateur {self.user.username}, dispositif {self.device_id}")
    
    async def disconnect(self, close_code):
        """Gère la déconnexion WebSocket."""
        # Quitter le groupe
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        # Arrêter les mises à jour périodiques
        if self.update_task:
            self.update_task.cancel()
        
        logger.info(f"WebSocket déconnecté pour utilisateur {self.user.username if self.user else 'Anonyme'}")
    
    async def receive(self, text_data):
        """Traite les messages reçus du client."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            if message_type == "get_metrics":
                await self.handle_get_metrics(data)
            elif message_type == "get_alerts":
                await self.handle_get_alerts(data)
            elif message_type == "subscribe":
                await self.handle_subscribe(data)
            elif message_type == "unsubscribe":
                await self.handle_unsubscribe(data)
            else:
                await self.send_error("Type de message non supporté")
                
        except json.JSONDecodeError:
            await self.send_error("Format JSON invalide")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            await self.send_error("Erreur interne du serveur")
    
    async def send_initial_data(self):
        """Envoie les données initiales lors de la connexion."""
        try:
            if self.device_id:
                # Données spécifiques à un équipement
                device_data = await self.get_device_data(self.device_id)
                await self.send(text_data=json.dumps({
                    "type": "initial_data",
                    "device_id": self.device_id,
                    "data": device_data
                }))
            else:
                # Données globales
                global_data = await self.get_global_data()
                await self.send(text_data=json.dumps({
                    "type": "initial_data",
                    "data": global_data
                }))
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données initiales: {e}")
            await self.send_error("Erreur lors du chargement des données")
    
    async def periodic_updates(self):
        """Envoie des mises à jour périodiques."""
        try:
            while True:
                await asyncio.sleep(5)  # Mise à jour toutes les 5 secondes
                
                if self.device_id:
                    metrics = await self.get_device_metrics(self.device_id)
                    await self.send(text_data=json.dumps({
                        "type": "metrics_update",
                        "device_id": self.device_id,
                        "timestamp": datetime.now().isoformat(),
                        "metrics": metrics
                    }))
                else:
                    # Mise à jour globale
                    stats = await self.get_global_stats()
                    await self.send(text_data=json.dumps({
                        "type": "global_update",
                        "timestamp": datetime.now().isoformat(),
                        "stats": stats
                    }))
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Erreur lors des mises à jour périodiques: {e}")
    
    async def handle_get_metrics(self, data):
        """Traite la demande de métriques."""
        try:
            device_id = data.get("device_id", self.device_id)
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            
            if device_id:
                metrics = await self.get_device_metrics_history(
                    device_id, start_time, end_time
                )
                await self.send(text_data=json.dumps({
                    "type": "metrics_response",
                    "device_id": device_id,
                    "metrics": metrics
                }))
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques: {e}")
            await self.send_error("Erreur lors de la récupération des métriques")
    
    async def handle_get_alerts(self, data):
        """Traite la demande d'alertes."""
        try:
            device_id = data.get("device_id", self.device_id)
            severity = data.get("severity")
            limit = data.get("limit", 50)
            
            alerts = await self.get_alerts(device_id, severity, limit)
            await self.send(text_data=json.dumps({
                "type": "alerts_response",
                "device_id": device_id,
                "alerts": alerts
            }))
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes: {e}")
            await self.send_error("Erreur lors de la récupération des alertes")
    
    async def handle_subscribe(self, data):
        """Traite la demande d'abonnement."""
        try:
            new_device_id = data.get("device_id")
            
            # Quitter l'ancien groupe
            if self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            
            # Rejoindre le nouveau groupe
            self.device_id = new_device_id
            if self.device_id:
                self.room_group_name = f"monitoring_device_{self.device_id}"
            else:
                self.room_group_name = "monitoring_global"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Envoyer confirmation
            await self.send(text_data=json.dumps({
                "type": "subscription_confirmed",
                "device_id": self.device_id
            }))
            
            # Envoyer les nouvelles données initiales
            await self.send_initial_data()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'abonnement: {e}")
            await self.send_error("Erreur lors de l'abonnement")
    
    async def handle_unsubscribe(self, data):
        """Traite la demande de désabonnement."""
        try:
            if self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                
                await self.send(text_data=json.dumps({
                    "type": "unsubscription_confirmed"
                }))
                
        except Exception as e:
            logger.error(f"Erreur lors du désabonnement: {e}")
            await self.send_error("Erreur lors du désabonnement")
    
    async def send_error(self, message: str):
        """Envoie un message d'erreur au client."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }))
    
    # Handlers pour les messages du groupe
    async def metrics_update(self, event):
        """Traite les mises à jour de métriques du groupe."""
        await self.send(text_data=json.dumps(event["data"]))
    
    async def alert_notification(self, event):
        """Traite les notifications d'alertes du groupe."""
        await self.send(text_data=json.dumps(event["data"]))
    
    async def device_status_update(self, event):
        """Traite les mises à jour de statut d'équipement du groupe."""
        await self.send(text_data=json.dumps(event["data"]))
    
    # Méthodes d'accès aux données (interface avec la base de données)
    @database_sync_to_async
    def get_device_data(self, device_id: int) -> Dict[str, Any]:
        """Récupère les données complètes d'un équipement."""
        # Cette méthode doit être connectée aux repositories réels
        # Pour l'instant, simulation avec des données statiques
        return {
            "device_id": device_id,
            "status": "online",
            "last_update": datetime.now().isoformat(),
            "metrics_count": 5,
            "alerts_count": 2
        }
    
    @database_sync_to_async
    def get_global_data(self) -> Dict[str, Any]:
        """Récupère les données globales de monitoring."""
        return {
            "total_devices": 10,
            "online_devices": 8,
            "offline_devices": 2,
            "active_alerts": 3,
            "critical_alerts": 1,
            "last_update": datetime.now().isoformat()
        }
    
    @database_sync_to_async
    def get_device_metrics(self, device_id: int) -> list[Dict[str, Any]]:
        """Récupère les métriques actuelles d'un équipement."""
        # Connexion aux repositories réels nécessaire
        return [
            {
                "name": "CPU Usage",
                "value": 75.5,
                "unit": "%",
                "timestamp": datetime.now().isoformat()
            },
            {
                "name": "Memory Usage",
                "value": 60.2,
                "unit": "%",
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    @database_sync_to_async
    def get_device_metrics_history(
        self,
        device_id: int,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """Récupère l'historique des métriques d'un équipement."""
        # Implémentation avec repositories nécessaire
        return []
    
    @database_sync_to_async
    def get_alerts(
        self,
        device_id: Optional[int] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """Récupère les alertes."""
        # Connexion aux repositories réels nécessaire
        return [
            {
                "id": 1,
                "title": "CPU Usage élevé",
                "severity": "warning",
                "device_id": device_id,
                "created_at": datetime.now().isoformat()
            }
        ]
    
    @database_sync_to_async
    def get_global_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques globales."""
        return {
            "devices_online": 8,
            "devices_total": 10,
            "active_alerts": 3,
            "avg_cpu_usage": 45.2,
            "avg_memory_usage": 67.8
        }


class AlertsWebSocketConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket spécialisé pour les alertes.
    
    Diffuse les nouvelles alertes en temps réel et permet
    la gestion des alertes via WebSocket.
    """
    
    async def connect(self):
        """Gère la connexion WebSocket pour les alertes."""
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close(code=4001)
            return
        
        self.user = self.scope["user"]
        self.room_group_name = "alerts_notifications"
        
        # Rejoindre le groupe d'alertes
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les alertes actives
        active_alerts = await self.get_active_alerts()
        await self.send(text_data=json.dumps({
            "type": "active_alerts",
            "alerts": active_alerts
        }))
        
        logger.info(f"Connexion alertes WebSocket pour {self.user.username}")
    
    async def disconnect(self, close_code):
        """Gère la déconnexion WebSocket pour les alertes."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"Déconnexion alertes WebSocket pour {self.user.username if self.user else 'Anonyme'}")
    
    async def receive(self, text_data):
        """Traite les actions sur les alertes."""
        try:
            data = json.loads(text_data)
            action = data.get("action")
            
            if action == "acknowledge":
                await self.handle_acknowledge_alert(data)
            elif action == "dismiss":
                await self.handle_dismiss_alert(data)
            elif action == "get_details":
                await self.handle_get_alert_details(data)
            
        except json.JSONDecodeError:
            await self.send_error("Format JSON invalide")
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'action d'alerte: {e}")
            await self.send_error("Erreur lors du traitement de l'action")
    
    async def handle_acknowledge_alert(self, data):
        """Traite l'accusé de réception d'une alerte."""
        try:
            alert_id = data.get("alert_id")
            comment = data.get("comment", "")
            
            # Mettre à jour l'alerte dans la base de données
            success = await self.acknowledge_alert(alert_id, self.user.id, comment)
            
            if success:
                # Notifier tous les clients connectés
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "alert_acknowledged",
                        "data": {
                            "alert_id": alert_id,
                            "acknowledged_by": self.user.username,
                            "comment": comment,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'accusé de réception: {e}")
            await self.send_error("Erreur lors de l'accusé de réception")
    
    async def handle_dismiss_alert(self, data):
        """Traite la fermeture d'une alerte."""
        try:
            alert_id = data.get("alert_id")
            reason = data.get("reason", "")
            
            success = await self.dismiss_alert(alert_id, self.user.id, reason)
            
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "alert_dismissed",
                        "data": {
                            "alert_id": alert_id,
                            "dismissed_by": self.user.username,
                            "reason": reason,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture d'alerte: {e}")
            await self.send_error("Erreur lors de la fermeture d'alerte")
    
    async def handle_get_alert_details(self, data):
        """Récupère les détails d'une alerte."""
        try:
            alert_id = data.get("alert_id")
            details = await self.get_alert_details(alert_id)
            
            await self.send(text_data=json.dumps({
                "type": "alert_details",
                "alert_id": alert_id,
                "details": details
            }))
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {e}")
            await self.send_error("Erreur lors de la récupération des détails")
    
    async def send_error(self, message: str):
        """Envoie un message d'erreur."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }))
    
    # Handlers pour les messages du groupe
    async def new_alert(self, event):
        """Diffuse une nouvelle alerte."""
        await self.send(text_data=json.dumps(event["data"]))
    
    async def alert_acknowledged(self, event):
        """Diffuse l'accusé de réception d'une alerte."""
        await self.send(text_data=json.dumps(event["data"]))
    
    async def alert_dismissed(self, event):
        """Diffuse la fermeture d'une alerte."""
        await self.send(text_data=json.dumps(event["data"]))
    
    # Méthodes d'accès aux données
    @database_sync_to_async
    def get_active_alerts(self) -> list[Dict[str, Any]]:
        """Récupère les alertes actives."""
        # Connexion aux repositories nécessaire
        return []
    
    @database_sync_to_async
    def acknowledge_alert(self, alert_id: int, user_id: int, comment: str) -> bool:
        """Marque une alerte comme accusée réception."""
        # Implémentation avec repositories nécessaire
        return True
    
    @database_sync_to_async
    def dismiss_alert(self, alert_id: int, user_id: int, reason: str) -> bool:
        """Ferme une alerte."""
        # Implémentation avec repositories nécessaire
        return True
    
    @database_sync_to_async
    def get_alert_details(self, alert_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une alerte."""
        # Implémentation avec repositories nécessaire
        return {}