"""
Configuration des WebSockets pour les mises à jour en temps réel.

Ce module contient les configurations et classes pour permettre la communication
en temps réel via WebSockets, utilisés pour les tableaux de bord, les alertes
et les mises à jour d'état des équipements.
"""

import json
import logging
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Groupes de canaux pour différentes fonctionnalités
DASHBOARD_GROUP = 'dashboard_updates'
ALERTS_GROUP = 'alerts_updates'
DEVICE_STATUS_GROUP = 'device_status_updates'
MONITORING_GROUP = 'monitoring_updates'
TOPOLOGY_GROUP = 'topology_updates'


class BaseWSConsumer(WebsocketConsumer):
    """Classe de base pour les consommateurs WebSocket."""
    
    def connect(self):
        """Gère la connexion d'un client WebSocket."""
        self.user = self.scope["user"]
        
        # Ne connecter que les utilisateurs authentifiés
        if not self.user.is_authenticated:
            logger.warning(f"Tentative de connexion WebSocket rejetée pour utilisateur non authentifié")
            self.close()
            return
            
        # Accepter la connexion
        self.accept()
        logger.info(f"Connexion WebSocket acceptée pour {self.user.username}")
        
    def disconnect(self, close_code):
        """Gère la déconnexion d'un client."""
        # Si l'utilisateur était dans des groupes, se désabonner
        if hasattr(self, 'groups') and self.groups:
            for group in self.groups:
                async_to_sync(self.channel_layer.group_discard)(
                    group,
                    self.channel_name
                )
        logger.info(f"Déconnexion WebSocket pour {self.user.username} (code: {close_code})")
        
    def receive(self, text_data):
        """
        Gère les messages reçus du client WebSocket.
        
        Args:
            text_data (str): Données en format JSON envoyées par le client
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Dispatcher selon le type de message
            if message_type == 'subscribe':
                self.handle_subscribe(data)
            elif message_type == 'unsubscribe':
                self.handle_unsubscribe(data)
            else:
                self.handle_message(data)
                
        except json.JSONDecodeError:
            logger.error(f"Message WebSocket invalide (non JSON): {text_data[:100]}")
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format de message invalide. JSON attendu.'
            }))
            
    def handle_subscribe(self, data):
        """Gère les requêtes d'abonnement à des groupes."""
        group = data.get('group')
        if not group:
            self.send_error('Groupe manquant dans la requête d\'abonnement')
            return
            
        # Vérifier les permissions pour ce groupe
        if not self.can_subscribe_to_group(group):
            self.send_error(f'Pas d\'autorisation pour s\'abonner au groupe {group}')
            return
            
        # S'abonner au groupe
        async_to_sync(self.channel_layer.group_add)(
            group,
            self.channel_name
        )
        
        # Conserver la trace des groupes auxquels l'utilisateur est abonné
        if not hasattr(self, 'groups'):
            self.groups = []
        self.groups.append(group)
        
        self.send(text_data=json.dumps({
            'type': 'subscribe_success',
            'group': group
        }))
        logger.info(f"Utilisateur {self.user.username} abonné au groupe {group}")
        
    def handle_unsubscribe(self, data):
        """Gère les requêtes de désabonnement."""
        group = data.get('group')
        if not group:
            self.send_error('Groupe manquant dans la requête de désabonnement')
            return
            
        if hasattr(self, 'groups') and group in self.groups:
            # Se désabonner du groupe
            async_to_sync(self.channel_layer.group_discard)(
                group,
                self.channel_name
            )
            self.groups.remove(group)
            
            self.send(text_data=json.dumps({
                'type': 'unsubscribe_success',
                'group': group
            }))
            logger.info(f"Utilisateur {self.user.username} désabonné du groupe {group}")
        else:
            self.send_error(f'Non abonné au groupe {group}')
            
    def handle_message(self, data):
        """Gère les messages génériques (à implémenter dans les sous-classes)."""
        self.send_error('Type de message non géré')
        
    def send_error(self, message):
        """Envoie un message d'erreur au client."""
        self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
        
    def can_subscribe_to_group(self, group):
        """
        Vérifie si l'utilisateur a le droit de s'abonner à un groupe.
        
        Args:
            group (str): Le nom du groupe
            
        Returns:
            bool: True si l'utilisateur peut s'abonner, False sinon
        """
        # Pour les administrateurs, autoriser tous les groupes
        if self.user.is_superuser or self.user.is_staff:
            return True
            
        # Pour les groupes publics, autoriser tous les utilisateurs authentifiés
        if group in [DASHBOARD_GROUP, ALERTS_GROUP]:
            return True
            
        # Pour les autres groupes, vérifier les permissions spécifiques
        # (à personnaliser selon les besoins de l'application)
        if group == DEVICE_STATUS_GROUP:
            return self.user.has_perm('network_management.view_networkdevice')
            
        if group == MONITORING_GROUP:
            return self.user.has_perm('monitoring.view_metrics')
            
        if group == TOPOLOGY_GROUP:
            return self.user.has_perm('network_management.view_networktopology')
            
        # Par défaut, refuser l'accès
        return False
        
        
class DashboardConsumer(BaseWSConsumer):
    """Consumer WebSocket pour les mises à jour de tableau de bord."""
    
    def connect(self):
        """Connexion au WebSocket avec abonnement automatique au groupe dashboard."""
        super().connect()
        if self.scope["user"].is_authenticated:
            # Abonnement automatique au groupe dashboard
            async_to_sync(self.channel_layer.group_add)(
                DASHBOARD_GROUP,
                self.channel_name
            )
            # Initialiser la liste des groupes
            self.groups = [DASHBOARD_GROUP]
            
    def dashboard_update(self, event):
        """
        Gère les mises à jour de tableau de bord et les transmet au client.
        
        Args:
            event (dict): Données de l'événement
        """
        # Transmettre les données au client WebSocket
        self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'dashboard_id': event['dashboard_id'],
            'data': event['data']
        }))
        
        
class AlertsConsumer(BaseWSConsumer):
    """Consumer WebSocket pour les alertes en temps réel."""
    
    def connect(self):
        """Connexion au WebSocket avec abonnement automatique au groupe alertes."""
        super().connect()
        if self.scope["user"].is_authenticated:
            # Abonnement automatique au groupe alertes
            async_to_sync(self.channel_layer.group_add)(
                ALERTS_GROUP,
                self.channel_name
            )
            # Initialiser la liste des groupes
            self.groups = [ALERTS_GROUP]
            
    def alert_notification(self, event):
        """
        Gère les notifications d'alerte et les transmet au client.
        
        Args:
            event (dict): Données de l'événement
        """
        # Transmettre les données au client WebSocket
        self.send(text_data=json.dumps({
            'type': 'alert_notification',
            'alert_id': event['alert_id'],
            'severity': event['severity'],
            'message': event['message'],
            'device_id': event.get('device_id'),
            'timestamp': event['timestamp']
        }))
        
        
class MonitoringConsumer(BaseWSConsumer):
    """Consumer WebSocket pour les mises à jour de monitoring."""
    
    def monitoring_update(self, event):
        """
        Gère les mises à jour de métriques et les transmet au client.
        
        Args:
            event (dict): Données de l'événement
        """
        # Transmettre les données au client WebSocket
        self.send(text_data=json.dumps({
            'type': 'monitoring_update',
            'source': event['source'],
            'metrics': event['metrics']
        }))


# Fonctions utilitaires pour envoyer des mises à jour aux groupes

def send_dashboard_update(dashboard_id, data):
    """
    Envoie une mise à jour de tableau de bord à tous les clients abonnés.
    
    Args:
        dashboard_id (int): ID du tableau de bord
        data (dict): Données de mise à jour
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        DASHBOARD_GROUP,
        {
            'type': 'dashboard_update',
            'dashboard_id': dashboard_id,
            'data': data
        }
    )

def send_alert_notification(alert_id, severity, message, device_id=None, timestamp=None):
    """
    Envoie une notification d'alerte à tous les clients abonnés.
    
    Args:
        alert_id (int): ID de l'alerte
        severity (str): Niveau de sévérité ('info', 'warning', 'critical', etc.)
        message (str): Message de l'alerte
        device_id (int, optional): ID de l'équipement concerné
        timestamp (str, optional): Horodatage de l'alerte
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        ALERTS_GROUP,
        {
            'type': 'alert_notification',
            'alert_id': alert_id,
            'severity': severity,
            'message': message,
            'device_id': device_id,
            'timestamp': timestamp or timezone.now().isoformat()
        }
    )

def send_monitoring_update(source, metrics):
    """
    Envoie une mise à jour de métriques de monitoring.
    
    Args:
        source (str): Source des métriques ('prometheus', 'grafana', etc.)
        metrics (dict): Données des métriques
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        MONITORING_GROUP,
        {
            'type': 'monitoring_update',
            'source': source,
            'metrics': metrics
        }
    ) 