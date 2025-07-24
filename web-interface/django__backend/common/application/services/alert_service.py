"""
Service d'alerte pour le module Common.
"""
import logging
import requests
import json
from typing import Dict, List, Any, Optional
from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from ...domain.interfaces.alert import AlertInterface

logger = logging.getLogger(__name__)

class AlertService(AlertInterface):
    """Implémentation du service de gestion des alertes."""
    
    def notify_alert(self, alert: Any, channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Envoie une notification d'alerte via différents canaux.
        
        Args:
            alert: L'alerte à notifier (SecurityAlert ou Alert)
            channels: Liste des canaux à utiliser (email, webhook, sms, slack, telegram)
            
        Returns:
            Dict avec les résultats par canal
        """
        # Déterminer les canaux à utiliser
        if not channels:
            channels = getattr(settings, 'DEFAULT_ALERT_CHANNELS', ['email'])
        
        results = {}
        
        # Préparer les données de l'alerte
        alert_data = {
            "id": alert.id,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat()
        }
        
        # Ajouter les attributs spécifiques selon le type d'alerte
        if hasattr(alert, 'source'):  # SecurityAlert
            alert_data.update({
                "type": "security",
                "source": alert.source,
                "event_type": alert.event_type,
                "source_ip": alert.source_ip,
                "destination_ip": alert.destination_ip
            })
        elif hasattr(alert, 'device'):  # Monitoring Alert
            alert_data.update({
                "type": "monitoring",
                "device": alert.device.name if alert.device else None,
                "service_check": alert.service_check.name if alert.service_check else None,
                "metric": alert.metric.name if alert.metric else None
            })
        
        # Envoyer les notifications via les différents canaux
        for channel in channels:
            try:
                if channel == 'email':
                    results['email'] = self.send_email_alert(alert_data)
                elif channel == 'webhook':
                    results['webhook'] = self.send_webhook_alert(alert_data)
                elif channel == 'sms':
                    results['sms'] = self.send_sms_alert(alert_data)
                elif channel == 'slack':
                    results['slack'] = self.send_slack_alert(alert_data)
                elif channel == 'telegram':
                    results['telegram'] = self.send_telegram_alert(alert_data)
                else:
                    logger.warning(f"Canal de notification non pris en charge: {channel}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'alerte via {channel}: {e}")
                results[channel] = False
        
        return results
    
    def send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte par email.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Configuration de l'email
            subject = f"Alerte {alert_data['type'].capitalize()} - {alert_data['severity'].upper()}"
            recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
            
            if not recipients:
                logger.warning("Aucun destinataire configuré pour les alertes par email")
                return False
            
            # Rendre le template HTML
            html_message = render_to_string('alerts/email_alert.html', {'alert': alert_data})
            plain_message = strip_tags(html_message)
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'nms@example.com'),
                recipient_list=recipients,
                fail_silently=False
            )
            
            logger.info(f"Alerte envoyée par email: {alert_data['id']}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte par email: {e}")
            return False
    
    def send_webhook_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte via webhook.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', None)
            
            if not webhook_url:
                logger.warning("Aucune URL de webhook configurée pour les alertes")
                return False
            
            # Envoyer la requête webhook
            response = requests.post(
                webhook_url,
                json=alert_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            response.raise_for_status()
            logger.info(f"Alerte envoyée via webhook: {alert_data['id']}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte via webhook: {e}")
            return False
    
    def send_sms_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte par SMS.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        # À implémenter avec un service SMS comme Twilio, Nexmo, etc.
        return False
    
    def send_slack_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte via Slack.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            slack_webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            
            if not slack_webhook_url:
                logger.warning("Aucune URL de webhook Slack configurée pour les alertes")
                return False
            
            # Préparer le message Slack
            severity_emoji = {
                'critical': ':red_circle:',
                'high': ':orange_circle:',
                'medium': ':large_yellow_circle:',
                'low': ':large_blue_circle:',
                'warning': ':warning:',
                'unknown': ':grey_question:'
            }
            
            emoji = severity_emoji.get(alert_data['severity'], ':bell:')
            
            slack_message = {
                "text": f"{emoji} Alerte {alert_data['type'].capitalize()} - {alert_data['severity'].upper()}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} Alerte {alert_data['type'].capitalize()} - {alert_data['severity'].upper()}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message:* {alert_data['message']}\n*Horodatage:* {alert_data['timestamp']}"
                        }
                    }
                ]
            }
            
            # Ajouter des champs spécifiques au type d'alerte
            fields = []
            
            if alert_data['type'] == 'security':
                fields.extend([
                    {"type": "mrkdwn", "text": f"*Source:* {alert_data.get('source', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Type d'événement:* {alert_data.get('event_type', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*IP source:* {alert_data.get('source_ip', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*IP destination:* {alert_data.get('destination_ip', 'N/A')}"}
                ])
            elif alert_data['type'] == 'monitoring':
                fields.extend([
                    {"type": "mrkdwn", "text": f"*Appareil:* {alert_data.get('device', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Vérification:* {alert_data.get('service_check', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Métrique:* {alert_data.get('metric', 'N/A')}"}
                ])
            
            if fields:
                slack_message["blocks"].append({
                    "type": "section",
                    "fields": fields
                })
            
            # Envoyer le message Slack
            response = requests.post(
                slack_webhook_url,
                json=slack_message,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            response.raise_for_status()
            logger.info(f"Alerte envoyée via Slack: {alert_data['id']}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte via Slack: {e}")
            return False
    
    def send_telegram_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Envoie une alerte via Telegram.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        # À implémenter avec l'API Telegram
        return False 