"""
Interface pour le service de notification.
"""
from abc import ABC, abstractmethod
from typing import List, Union, Optional, Any


class NotificationInterface(ABC):
    """Interface pour le service de gestion des notifications."""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Marque une notification comme lue.
        
        Args:
            notification_id: ID de la notification
            user_id: ID de l'utilisateur
            
        Returns:
            True si la notification a été marquée comme lue, False sinon
        """
        pass 