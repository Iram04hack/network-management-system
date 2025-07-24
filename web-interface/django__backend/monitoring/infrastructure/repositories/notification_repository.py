"""
Implémentation concrète du repository pour les notifications.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from django.db.models import Q, Count

from ...domain.interfaces.repositories import NotificationRepository as INotificationRepository
from ...models import Notification, NotificationChannel, NotificationRule
from .base_repository import BaseRepository

# Configuration du logger
logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification], INotificationRepository):
    """
    Repository pour les notifications.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle Notification.
        """
        super().__init__(Notification)
    
    def create_notification(self, channel_id: int, message: str, 
                           subject: Optional[str] = None,
                           recipients: List[str] = None,
                           user_recipients: List[int] = None,
                           alert_id: Optional[int] = None,
                           status: str = "pending",
                           details: Dict[str, Any] = None) -> Notification:
        """
        Crée une nouvelle notification.
        
        Args:
            channel_id: ID du canal de notification
            message: Message de la notification
            subject: Sujet de la notification (optionnel)
            recipients: Liste des adresses email des destinataires (optionnel)
            user_recipients: Liste des IDs des utilisateurs destinataires (optionnel)
            alert_id: ID de l'alerte associée (optionnel)
            status: Statut initial de la notification ('pending', 'sent', 'error')
            details: Détails supplémentaires de la notification (optionnel)
            
        Returns:
            La notification créée
        """
        try:
            notification = Notification(
                channel_id=channel_id,
                message=message,
                subject=subject,
                recipients=recipients or [],
                user_recipients=user_recipients or [],
                alert_id=alert_id,
                status=status,
                details=details or {},
                created_at=datetime.now(timezone.utc)
            )
            
            notification.save()
            logger.info(f"Notification créée: {notification.id}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une notification: {e}")
            raise
    
    def update_notification_status(self, notification_id: int, status: str,
                                  error_message: Optional[str] = None) -> Optional[Notification]:
        """
        Met à jour le statut d'une notification.
        
        Args:
            notification_id: ID de la notification
            status: Nouveau statut ('pending', 'sent', 'error')
            error_message: Message d'erreur (optionnel)
            
        Returns:
            La notification mise à jour ou None si elle n'existe pas
        """
        notification = self.get_by_id(notification_id)
        if not notification:
            return None
        
        try:
            notification.status = status
            
            if status == 'sent':
                notification.sent_at = datetime.now(timezone.utc)
                
            if error_message:
                # Ajouter le message d'erreur aux détails
                if notification.details:
                    notification.details['error_message'] = error_message
                else:
                    notification.details = {'error_message': error_message}
            
            notification.save()
            logger.info(f"Notification {notification_id} mise à jour avec le statut: {status}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut de la notification {notification_id}: {e}")
            raise
    
    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Marque une notification comme lue par un utilisateur.
        
        Args:
            notification_id: ID de la notification
            user_id: ID de l'utilisateur
            
        Returns:
            La notification mise à jour ou None si elle n'existe pas
        """
        notification = self.get_by_id(notification_id)
        if not notification:
            return None
        
        try:
            read_by = notification.read_by or []
            
            if user_id not in read_by:
                read_by.append(user_id)
                notification.read_by = read_by
                notification.save()
                logger.info(f"Notification {notification_id} marquée comme lue par l'utilisateur {user_id}")
            
            return notification
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la notification {notification_id} comme lue: {e}")
            raise
    
    def get_notifications_for_user(self, user_id: int, 
                                 email: Optional[str] = None,
                                 status: Optional[str] = None,
                                 unread_only: bool = False,
                                 limit: int = 100) -> List[Notification]:
        """
        Récupère les notifications pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            email: Email de l'utilisateur (optionnel)
            status: Filtrer par statut (optionnel)
            unread_only: Si on ne récupère que les notifications non lues
            limit: Nombre maximum de notifications à récupérer
            
        Returns:
            Liste des notifications
        """
        # Construire la requête pour les notifications destinées à cet utilisateur
        query = Q(user_recipients__contains=[user_id])
        
        if email:
            query |= Q(recipients__contains=[email])
        
        if status:
            query &= Q(status=status)
            
        if unread_only:
            query &= ~Q(read_by__contains=[user_id])
        
        return list(Notification.objects.filter(query).order_by('-created_at')[:limit])
    
    def get_notifications_for_alert(self, alert_id: int) -> List[Notification]:
        """
        Récupère les notifications pour une alerte.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            Liste des notifications
        """
        return self.filter(alert_id=alert_id)
    
    def get_unread_count(self, user_id: int, email: Optional[str] = None) -> int:
        """
        Récupère le nombre de notifications non lues pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            email: Email de l'utilisateur (optionnel)
            
        Returns:
            Nombre de notifications non lues
        """
        # Construire la requête pour les notifications destinées à cet utilisateur
        query = Q(user_recipients__contains=[user_id])
        
        if email:
            query |= Q(recipients__contains=[email])
        
        # Exclure les notifications déjà lues par cet utilisateur
        query &= ~Q(read_by__contains=[user_id])
        
        return Notification.objects.filter(query).count()
    
    def create_notification_channel(self, name: str, channel_type: str,
                                   config: Dict[str, Any],
                                   description: Optional[str] = None,
                                   created_by_id: Optional[int] = None,
                                   is_active: bool = True,
                                   is_shared: bool = False) -> NotificationChannel:
        """
        Crée un nouveau canal de notification.
        
        Args:
            name: Nom du canal
            channel_type: Type de canal ('email', 'sms', 'webhook', etc.)
            config: Configuration du canal
            description: Description du canal (optionnel)
            created_by_id: ID de l'utilisateur qui a créé le canal (optionnel)
            is_active: Si le canal est actif
            is_shared: Si le canal est partagé avec d'autres utilisateurs
            
        Returns:
            Le canal de notification créé
        """
        try:
            channel = NotificationChannel(
                name=name,
                channel_type=channel_type,
                config=config,
                description=description,
                created_by_id=created_by_id,
                is_active=is_active,
                is_shared=is_shared,
                created_at=datetime.now(timezone.utc)
            )
            
            channel.save()
            logger.info(f"Canal de notification créé: {channel.id} - {name}")
            return channel
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un canal de notification: {e}")
            raise
    
    def get_active_channels(self, channel_type: Optional[str] = None) -> List[NotificationChannel]:
        """
        Récupère les canaux de notification actifs.
        
        Args:
            channel_type: Type de canal à filtrer (optionnel)
            
        Returns:
            Liste des canaux de notification actifs
        """
        query = Q(is_active=True)
        
        if channel_type:
            query &= Q(channel_type=channel_type)
            
        return list(NotificationChannel.objects.filter(query))
    
    def get_channels_for_user(self, user_id: int) -> List[NotificationChannel]:
        """
        Récupère les canaux de notification pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des canaux de notification
        """
        # Récupérer les canaux créés par l'utilisateur ou partagés
        query = Q(created_by_id=user_id) | Q(is_shared=True)
        
        return list(NotificationChannel.objects.filter(query))
    
    def create_notification_template(self, name: str, template_type: str,
                                    content: str,
                                    description: Optional[str] = None,
                                    created_by_id: Optional[int] = None,
                                    is_active: bool = True,
                                    is_shared: bool = False) -> NotificationRule:
        """
        Crée un nouveau modèle de notification.
        
        Args:
            name: Nom du modèle
            template_type: Type de modèle ('email', 'sms', 'webhook', etc.)
            content: Contenu du modèle
            description: Description du modèle (optionnel)
            created_by_id: ID de l'utilisateur qui a créé le modèle (optionnel)
            is_active: Si le modèle est actif
            is_shared: Si le modèle est partagé avec d'autres utilisateurs
            
        Returns:
            Le modèle de notification créé
        """
        try:
            template = NotificationRule(
                name=name,
                template_type=template_type,
                content=content,
                description=description,
                created_by_id=created_by_id,
                is_active=is_active,
                is_shared=is_shared,
                created_at=datetime.now(timezone.utc)
            )
            
            template.save()
            logger.info(f"Modèle de notification créé: {template.id} - {name}")
            return template
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un modèle de notification: {e}")
            raise
    
    def get_active_templates(self, template_type: Optional[str] = None) -> List[NotificationRule]:
        """
        Récupère les modèles de notification actifs.
        
        Args:
            template_type: Type de modèle à filtrer (optionnel)
            
        Returns:
            Liste des modèles de notification actifs
        """
        query = Q(is_active=True)
        
        if template_type:
            query &= Q(template_type=template_type)
            
        return list(NotificationRule.objects.filter(query))
    
    def get_templates_for_user(self, user_id: int) -> List[NotificationRule]:
        """
        Récupère les modèles de notification pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des modèles de notification
        """
        # Récupérer les modèles créés par l'utilisateur ou partagés
        query = Q(created_by_id=user_id) | Q(is_shared=True)
        
        return list(NotificationRule.objects.filter(query)) 

    def list_by_user(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les notifications pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            filters: Filtres optionnels
            
        Returns:
            Liste des notifications
        """
        try:
            queryset = Notification.objects.filter(user_recipients__contains=[user_id])
            
            if filters:
                if 'status' in filters:
                    queryset = queryset.filter(status=filters['status'])
                if 'channel_id' in filters:
                    queryset = queryset.filter(channel_id=filters['channel_id'])
                if 'created_after' in filters:
                    queryset = queryset.filter(created_at__gte=filters['created_after'])
            
            # Convertir en dictionnaires
            notifications = []
            for notification in queryset.order_by('-created_at'):
                notification_dict = {
                    'id': notification.id,
                    'channel_id': notification.channel_id,
                    'message': notification.message,
                    'subject': notification.subject,
                    'recipients': notification.recipients or [],
                    'user_recipients': notification.user_recipients or [],
                    'alert_id': notification.alert_id,
                    'status': notification.status,
                    'details': notification.details or {},
                    'created_at': notification.created_at.isoformat() if notification.created_at else None,
                    'updated_at': notification.updated_at.isoformat() if notification.updated_at else None,
                    'sent_at': notification.sent_at.isoformat() if notification.sent_at else None
                }
                notifications.append(notification_dict)
            
            return notifications
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications: {e}")
            return []


class NotificationChannelRepository(BaseRepository[NotificationChannel]):
    """
    Repository pour les canaux de notification.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle NotificationChannel.
        """
        super().__init__(NotificationChannel)
    
    def create(self, name: str, channel_type: str, config: Dict[str, Any],
               description: Optional[str] = None, created_by_id: Optional[int] = None,
               is_active: bool = True, is_shared: bool = False) -> NotificationChannel:
        """
        Crée un nouveau canal de notification.
        """
        try:
            channel = NotificationChannel(
                name=name,
                channel_type=channel_type,
                config=config,
                description=description,
                created_by_id=created_by_id,
                is_active=is_active,
                is_shared=is_shared,
                created_at=datetime.now(timezone.utc)
            )
            
            channel.save()
            logger.info(f"Canal de notification créé: {channel.id} - {name}")
            return channel
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un canal de notification: {e}")
            raise
    
    def list_by_user(self, user_id: int) -> List[NotificationChannel]:
        """
        Récupère les canaux de notification pour un utilisateur.
        """
        query = Q(created_by_id=user_id) | Q(is_shared=True)
        return list(NotificationChannel.objects.filter(query))
    
    def list_active(self, channel_type: Optional[str] = None) -> List[NotificationChannel]:
        """
        Récupère les canaux de notification actifs.
        """
        query = Q(is_active=True)
        
        if channel_type:
            query &= Q(channel_type=channel_type)
            
        return list(NotificationChannel.objects.filter(query))


class NotificationRuleRepository(BaseRepository[NotificationRule]):
    """
    Repository pour les règles de notification.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle NotificationRule.
        """
        super().__init__(NotificationRule)
    
    def create(self, name: str, rule_type: str, conditions: Dict[str, Any],
               actions: Dict[str, Any], description: Optional[str] = None,
               created_by_id: Optional[int] = None, is_active: bool = True,
               is_shared: bool = False) -> NotificationRule:
        """
        Crée une nouvelle règle de notification.
        """
        try:
            rule = NotificationRule(
                name=name,
                rule_type=rule_type,
                conditions=conditions,
                actions=actions,
                description=description,
                created_by_id=created_by_id,
                is_active=is_active,
                is_shared=is_shared,
                created_at=datetime.now(timezone.utc)
            )
            
            rule.save()
            logger.info(f"Règle de notification créée: {rule.id} - {name}")
            return rule
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une règle de notification: {e}")
            raise
    
    def list_by_user(self, user_id: int) -> List[NotificationRule]:
        """
        Récupère les règles de notification pour un utilisateur.
        """
        query = Q(created_by_id=user_id) | Q(is_shared=True)
        return list(NotificationRule.objects.filter(query))
    
    def list_active(self, rule_type: Optional[str] = None) -> List[NotificationRule]:
        """
        Récupère les règles de notification actives.
        """
        query = Q(is_active=True)
        
        if rule_type:
            query &= Q(rule_type=rule_type)
            
        return list(NotificationRule.objects.filter(query)) 