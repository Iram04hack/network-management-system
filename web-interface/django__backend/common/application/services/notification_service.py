"""
Service de notification pour le module Common.
"""
import logging
from typing import List, Union, Any
from django.apps import apps
from django.contrib.auth.models import User
from ...domain.interfaces.notification import NotificationInterface

logger = logging.getLogger(__name__)

class NotificationService(NotificationInterface):
    """Implémentation du service de gestion des notifications."""
    
    def send_notification(
        self, 
        user_ids: Union[List[int], int], 
        title: str, 
        message: str, 
        level: str = 'info', 
        source: str = 'system'
    ) -> List[Any]:
        """
        Envoie une notification à un ou plusieurs utilisateurs.
        
        Args:
            user_ids: Liste des IDs utilisateurs ou ID unique
            title: Titre de la notification
            message: Contenu de la notification
            level: Niveau de la notification (info, warning, critical)
            source: Source de la notification
            
        Returns:
            Liste des notifications créées
        """
        # Récupérer le modèle Notification de manière différée
        Notification = apps.get_model('monitoring', 'Notification')
        
        notifications = []
        
        # Convertir l'ID en liste s'il n'en est pas une
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
            
        # Récupérer les utilisateurs
        users = User.objects.filter(id__in=user_ids)
        
        if not users:
            logger.warning(f"Aucun utilisateur trouvé pour les IDs: {user_ids}")
            return []
            
        # Créer les notifications
        for user in users:
            try:
                notification = Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    level=level,
                    source=source
                )
                notifications.append(notification)
                logger.info(f"Notification envoyée à {user.username}: {title}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification à {user.username}: {e}")
        
        return notifications
    
    def send_notification_to_admins(
        self, 
        title: str, 
        message: str, 
        level: str = 'info', 
        source: str = 'system'
    ) -> List[Any]:
        """
        Envoie une notification à tous les administrateurs.
        
        Args:
            title: Titre de la notification
            message: Contenu de la notification
            level: Niveau de la notification (info, warning, critical)
            source: Source de la notification
            
        Returns:
            Liste des notifications créées
        """
        admin_ids = User.objects.filter(is_staff=True).values_list('id', flat=True)
        return self.send_notification(list(admin_ids), title, message, level, source)
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Marque une notification comme lue.
        
        Args:
            notification_id: ID de la notification
            user_id: ID de l'utilisateur
            
        Returns:
            True si la notification a été marquée comme lue, False sinon
        """
        # Récupérer le modèle Notification de manière différée
        Notification = apps.get_model('monitoring', 'Notification')
        
        try:
            notification = Notification.objects.get(id=notification_id, user_id=user_id)
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} non trouvée pour l'utilisateur {user_id}")
            return False 