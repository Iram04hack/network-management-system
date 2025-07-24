"""
Interface pour le service d'alerte.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class AlertInterface(ABC):
    """Interface pour le service d'alerte."""

    @abstractmethod
    def notify_alert(self, alert: Any, channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Envoie une notification d'alerte via différents canaux.
        
        Args:
            alert: L'alerte à notifier (SecurityAlert ou Alert)
            channels: Liste des canaux à utiliser (email, webhook, sms, slack, telegram)
            
        Returns:
            Dict avec les résultats par canal
        """
        pass

    @abstractmethod
    def send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte par email.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        pass

    @abstractmethod
    def send_webhook_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte via webhook.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        pass

    @abstractmethod
    def send_sms_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte par SMS.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        pass

    @abstractmethod
    def send_slack_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte via Slack.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        pass

    @abstractmethod
    def send_telegram_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte via Telegram.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        pass 