"""
Handler d'alertes pour Slack.

Ce module fournit un handler qui envoie des notifications sur Slack
lorsque des alertes sont déclenchées.
"""
import logging
import requests
from django.conf import settings
from ..infrastructure.registry import register_plugin
from ...domain.interfaces import AlertHandlerPlugin

logger = logging.getLogger(__name__)

@register_plugin('alert_handlers')
class SlackAlertHandler(AlertHandlerPlugin):
    """Handler pour envoyer des alertes sur Slack"""
    name = "slack"
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        self.enabled = bool(self.webhook_url)
    
    def initialize(self) -> bool:
        """Initialise le plugin."""
        return self.enabled
    
    def cleanup(self) -> bool:
        """Nettoie les ressources utilisées par le plugin."""
        return True
    
    def get_metadata(self):
        """Retourne les métadonnées du plugin."""
        return {
            'id': 'slack_alert_handler',
            'name': self.name,
            'version': '1.0.0',
            'description': 'Envoie des alertes sur Slack',
            'author': 'Équipe NMS',
            'dependencies': [],
            'provides': ['alert_notification']
        }
    
    def can_handle(self, alert):
        """Vérifie si ce handler peut traiter cette alerte"""
        # Ce handler peut traiter toutes les alertes si configuré
        return self.enabled
    
    def handle_alert(self, alert):
        """
        Envoie une alerte sur Slack.
        
        Args:
            alert: Objet SecurityAlert ou Alert
            
        Returns:
            Dict avec le résultat de l'opération
        """
        if not self.enabled:
            return {"success": False, "error": "Slack integration not configured"}
        
        try:
            # Importer ici pour éviter l'import circulaire
            from security_management.models import SecurityAlert
            from monitoring.models import Alert
            
            # Déterminer le type d'alerte
            if isinstance(alert, SecurityAlert):
                return self._handle_security_alert(alert)
            elif isinstance(alert, Alert):
                return self._handle_monitoring_alert(alert)
            else:
                return {"success": False, "error": f"Unsupported alert type: {type(alert).__name__}"}
        except Exception as e:
            logger.error(f"Error sending alert to Slack: {e}")
            return {"success": False, "error": str(e)}
    
    def _handle_security_alert(self, alert):
        """Traite une alerte de sécurité"""
        # Choisir une icône selon la sévérité
        severity_emoji = {
            'critical': ':red_circle:',
            'high': ':orange_circle:',
            'medium': ':large_yellow_circle:',
            'low': ':large_blue_circle:'
        }
        emoji = severity_emoji.get(alert.severity, ':bell:')
        
        # Créer le message
        message = {
            "text": f"{emoji} Alerte de sécurité - {alert.severity.upper()}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Alerte de sécurité - {alert.severity.upper()}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Source:* {alert.source}\n*Message:* {alert.message}\n*Horodatage:* {alert.timestamp.isoformat()}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Type:* {alert.event_type}"},
                        {"type": "mrkdwn", "text": f"*IP Source:* {alert.source_ip or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*IP Destination:* {alert.destination_ip or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Statut:* {alert.status}"}
                    ]
                }
            ]
        }
        
        # Envoyer le message
        response = requests.post(
            self.webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        response.raise_for_status()
        return {"success": True, "status_code": response.status_code}
    
    def _handle_monitoring_alert(self, alert):
        """Traite une alerte de monitoring"""
        # Choisir une icône selon la sévérité
        severity_emoji = {
            'critical': ':red_circle:',
            'warning': ':warning:',
            'unknown': ':grey_question:'
        }
        emoji = severity_emoji.get(alert.severity, ':bell:')
        
        # Créer le message
        device_name = alert.device.name if alert.device else "N/A"
        service_name = alert.service_check.name if alert.service_check else "N/A"
        
        message = {
            "text": f"{emoji} Alerte de monitoring - {alert.severity.upper()}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Alerte de monitoring - {alert.severity.upper()}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Équipement:* {device_name}\n*Message:* {alert.message}\n*Horodatage:* {alert.timestamp.isoformat()}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Service:* {service_name}"},
                        {"type": "mrkdwn", "text": f"*Statut:* {alert.status}"}
                    ]
                }
            ]
        }
        
        # Envoyer le message
        response = requests.post(
            self.webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        response.raise_for_status()
        return {"success": True, "status_code": response.status_code} 