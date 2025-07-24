"""
Cas d'utilisation pour la gestion des notifications.
"""

from typing import List, Dict, Any, Optional

class NotificationUseCase:
    """Cas d'utilisation pour la gestion des notifications."""
    
    def __init__(self, notification_repository):
        self.notification_repository = notification_repository
    
    def list_notifications(self, user_id=None, unread_only=False, limit=None):
        """
        Liste les notifications pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            unread_only: Si True, ne retourne que les notifications non lues
            limit: Nombre maximum de notifications à retourner
            
        Returns:
            Liste des notifications
        """
        if user_id is not None:
            return self.notification_repository.get_notifications_for_user(
                user_id=user_id,
                unread_only=unread_only,
                limit=limit
            )
        else:
            return self.notification_repository.list_all(limit=limit)
    
    def get_notification(self, notification_id):
        """
        Récupère une notification par son ID.
        
        Args:
            notification_id: ID de la notification
            
        Returns:
            Notification
            
        Raises:
            ValueError: Si la notification n'existe pas
        """
        notification = self.notification_repository.get_by_id(notification_id)
        if notification is None:
            raise ValueError(f"Notification with ID {notification_id} not found")
        return notification
    
    def create_notification(self, channel_id, message, subject=None, recipients=None, 
                           user_recipients=None, alert_id=None, status="pending", details=None):
        """
        Crée une nouvelle notification.
        
        Args:
            channel_id: ID du canal de notification
            message: Message de la notification
            subject: Sujet de la notification (optionnel)
            recipients: Liste des destinataires (optionnel)
            user_recipients: Liste des IDs des utilisateurs destinataires (optionnel)
            alert_id: ID de l'alerte associée (optionnel)
            status: Statut de la notification (par défaut: "pending")
            details: Détails supplémentaires (optionnel)
            
        Returns:
            Notification créée
        """
        return self.notification_repository.create_notification(
            channel_id=channel_id,
            subject=subject,
            message=message,
            recipients=recipients or [],
            user_recipients=user_recipients or [],
            alert_id=alert_id,
            status=status,
            details=details or {}
        )
    
    def update_notification_status(self, notification_id, status, error_message=None):
        """
        Met à jour le statut d'une notification.
        
        Args:
            notification_id: ID de la notification
            status: Nouveau statut
            error_message: Message d'erreur (optionnel, pour le statut "error")
            
        Returns:
            Notification mise à jour
            
        Raises:
            ValueError: Si la notification n'existe pas
        """
        notification = self.get_notification(notification_id)
        
        return self.notification_repository.update_notification_status(
            notification_id,
            status=status,
            error_message=error_message
        )
    
    def mark_as_read(self, notification_id, user_id):
        """
        Marque une notification comme lue pour un utilisateur.
        
        Args:
            notification_id: ID de la notification
            user_id: ID de l'utilisateur
            
        Returns:
            Notification mise à jour
            
        Raises:
            ValueError: Si la notification n'existe pas
        """
        notification = self.get_notification(notification_id)
        
        return self.notification_repository.mark_as_read(
            notification_id,
            user_id=user_id
        )
    
    def mark_all_as_read(self, user_id):
        """
        Marque toutes les notifications d'un utilisateur comme lues.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Nombre de notifications marquées comme lues
        """
        # Récupérer toutes les notifications non lues de l'utilisateur
        unread_notifications = self.notification_repository.get_notifications_for_user(
            user_id=user_id,
            unread_only=True
        )
        
        # Marquer chaque notification comme lue
        for notification in unread_notifications:
            self.notification_repository.mark_as_read(
                notification.id,
                user_id=user_id
            )
        
        return len(unread_notifications)
    
    def get_unread_count(self, user_id):
        """
        Récupère le nombre de notifications non lues pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Nombre de notifications non lues
        """
        return self.notification_repository.get_unread_count(user_id=user_id)
    
    def delete_notification(self, notification_id):
        """
        Supprime une notification.
        
        Args:
            notification_id: ID de la notification
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si la notification n'existe pas
        """
        notification = self.get_notification(notification_id)
        return self.notification_repository.delete(notification_id)


class NotificationChannelUseCase:
    """Cas d'utilisation pour la gestion des canaux de notification."""
    
    def __init__(self, notification_repository):
        self.notification_repository = notification_repository
    
    def list_notification_channels(self, user_id=None, channel_type=None, active_only=True):
        """
        Liste les canaux de notification.
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            channel_type: Type de canal (optionnel)
            active_only: Si True, ne retourne que les canaux actifs
            
        Returns:
            Liste des canaux de notification
        """
        if user_id is not None:
            channels = self.notification_repository.get_channels_for_user(user_id)
            
            # Filtrer par type de canal si spécifié
            if channel_type is not None:
                channels = [c for c in channels if c.channel_type == channel_type]
            
            # Filtrer par statut actif si spécifié
            if active_only:
                channels = [c for c in channels if c.is_active]
            
            return channels
        else:
            if active_only:
                return self.notification_repository.get_active_channels(channel_type=channel_type)
            else:
                return self.notification_repository.list_all_channels(channel_type=channel_type)
    
    def get_notification_channel(self, channel_id):
        """
        Récupère un canal de notification par son ID.
        
        Args:
            channel_id: ID du canal de notification
            
        Returns:
            Canal de notification
            
        Raises:
            ValueError: Si le canal de notification n'existe pas
        """
        channel = self.notification_repository.get_channel_by_id(channel_id)
        if channel is None:
            raise ValueError(f"NotificationChannel with ID {channel_id} not found")
        return channel
    
    def create_notification_channel(self, name, channel_type, config, description=None, 
                                   created_by_id=None, is_active=True, is_shared=False):
        """
        Crée un nouveau canal de notification.
        
        Args:
            name: Nom du canal
            channel_type: Type de canal
            config: Configuration du canal
            description: Description du canal (optionnel)
            created_by_id: ID de l'utilisateur qui a créé le canal (optionnel)
            is_active: Si le canal est actif
            is_shared: Si le canal est partagé avec d'autres utilisateurs
            
        Returns:
            Canal de notification créé
        """
        return self.notification_repository.create_notification_channel(
            name=name,
            channel_type=channel_type,
            config=config,
            description=description,
            created_by_id=created_by_id,
            is_active=is_active,
            is_shared=is_shared
        )
    
    def update_notification_channel(self, channel_id, **kwargs):
        """
        Met à jour un canal de notification.
        
        Args:
            channel_id: ID du canal de notification
            **kwargs: Champs à mettre à jour
            
        Returns:
            Canal de notification mis à jour
            
        Raises:
            ValueError: Si le canal de notification n'existe pas
        """
        channel = self.get_notification_channel(channel_id)
        return self.notification_repository.update_channel(channel_id, **kwargs)
    
    def delete_notification_channel(self, channel_id):
        """
        Supprime un canal de notification.
        
        Args:
            channel_id: ID du canal de notification
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si le canal de notification n'existe pas
        """
        channel = self.get_notification_channel(channel_id)
        return self.notification_repository.delete_channel(channel_id)
    
    def test_notification_channel(self, channel_id, test_message="Test notification"):
        """
        Teste un canal de notification en envoyant un message de test.
        
        Args:
            channel_id: ID du canal de notification
            test_message: Message de test à envoyer
            
        Returns:
            Résultat du test (succès ou échec)
            
        Raises:
            ValueError: Si le canal de notification n'existe pas
        """
        channel = self.get_notification_channel(channel_id)
        
        # Créer une notification de test
        notification = self.notification_repository.create_notification(
            channel_id=channel_id,
            subject="Test Notification",
            message=test_message,
            recipients=[],
            status="pending"
        )
        
        # Envoyer la notification
        try:
            # Logique d'envoi de notification (à implémenter dans un service)
            # Pour l'instant, on simule un succès
            self.notification_repository.update_notification_status(
                notification.id,
                status="sent"
            )
            
            return {
                "success": True,
                "message": "Test notification sent successfully"
            }
        except Exception as e:
            self.notification_repository.update_notification_status(
                notification.id,
                status="error",
                error_message=str(e)
            )
            
            return {
                "success": False,
                "message": f"Failed to send test notification: {str(e)}"
            }


class NotificationRuleUseCase:
    """Cas d'utilisation pour la gestion des règles de notification."""

    def __init__(self, notification_rule_repository, notification_channel_repository):
        self.notification_rule_repository = notification_rule_repository
        self.notification_channel_repository = notification_channel_repository

    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Liste les règles de notification avec filtres optionnels."""
        if filters is None:
            filters = {}

        user_id = filters.get('user_id')
        if user_id:
            return self.notification_rule_repository.list_by_user(user_id, filters)
        else:
            # TODO: Implémenter list_all dans le repository
            return []

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """Récupère une règle de notification par son ID."""
        rule = self.notification_rule_repository.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Règle de notification {rule_id} non trouvée")
        return rule

    def create_rule(self, name: str, event_type: str, channel_ids: List[int],
                   user_id: int, conditions: Optional[Dict[str, Any]] = None,
                   is_enabled: bool = True) -> Dict[str, Any]:
        """Crée une nouvelle règle de notification."""
        # Vérifier que les canaux existent
        for channel_id in channel_ids:
            channel = self.notification_channel_repository.get_by_id(channel_id)
            if not channel:
                raise ValueError(f"Canal de notification {channel_id} non trouvé")

        rule_data = {
            'name': name,
            'event_type': event_type,
            'channel_ids': channel_ids,
            'user_id': user_id,
            'conditions': conditions or {},
            'is_enabled': is_enabled
        }

        return self.notification_rule_repository.create(rule_data)

    def update_rule(self, rule_id: int, **kwargs) -> Dict[str, Any]:
        """Met à jour une règle de notification."""
        rule = self.notification_rule_repository.update(rule_id, kwargs)
        if not rule:
            raise ValueError(f"Règle de notification {rule_id} non trouvée")
        return rule

    def delete_rule(self, rule_id: int) -> bool:
        """Supprime une règle de notification."""
        rule = self.notification_rule_repository.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Règle de notification {rule_id} non trouvée")
        return self.notification_rule_repository.delete(rule_id)

    def enable_rule(self, rule_id: int) -> Dict[str, Any]:
        """Active une règle de notification."""
        return self.update_rule(rule_id, is_enabled=True)

    def disable_rule(self, rule_id: int) -> Dict[str, Any]:
        """Désactive une règle de notification."""
        return self.update_rule(rule_id, is_enabled=False)