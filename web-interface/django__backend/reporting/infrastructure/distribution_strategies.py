"""
Implémentations des stratégies de distribution de rapports.

Ce module fournit les implémentations concrètes des stratégies de distribution
définies dans le domaine, pour différents canaux (email, Slack, webhook, etc.).
"""

from typing import Dict, List, Any, Optional
import logging
import requests
import json
import os
import math
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from ..domain.strategies import ReportDistributionStrategy

logger = logging.getLogger(__name__)

class EmailDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie de distribution de rapports par email.
    """
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport par email.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des destinataires avec leurs adresses email
            
        Returns:
            True si la distribution a réussi
        """
        try:
            # Vérifier que le rapport a un chemin de fichier
            if 'file_path' not in report_info:
                logger.error(f"Le rapport {report_info.get('id')} n'a pas de chemin de fichier")
                return False
            
            file_path = report_info['file_path']
            if not os.path.exists(file_path):
                logger.error(f"Le fichier {file_path} n'existe pas")
                return False
            
            # Préparer l'email
            subject = f"Rapport: {report_info.get('title', 'Rapport généré')}"
            
            # Construire le corps de l'email avec un template
            context = {
                'report': report_info,
                'recipient': 'Destinataire',  # Personnalisé pour chaque destinataire
            }
            
            # Liste des adresses email
            email_addresses = [recipient.get('address') for recipient in recipients if 'address' in recipient]
            if not email_addresses:
                logger.error("Aucune adresse email valide trouvée dans les destinataires")
                return False
            
            # Envoyer un email à chaque destinataire
            for recipient in recipients:
                if 'address' not in recipient:
                    continue
                
                # Personnaliser le message pour ce destinataire
                context['recipient'] = recipient.get('name', 'Destinataire')
                
                # Générer le corps HTML
                html_content = render_to_string('reporting/email/report_notification.html', context)
                
                # Créer l'email
                email = EmailMessage(
                    subject=subject,
                    body=html_content,
                    to=[recipient['address']],
                )
                email.content_subtype = "html"  # Pour envoyer en HTML
                
                # Joindre le rapport
                with open(file_path, 'rb') as f:
                    email.attach(
                        os.path.basename(file_path),
                        f.read(),
                        self._get_mimetype(file_path)
                    )
                
                # Envoyer l'email
                email.send(fail_silently=False)
                
                logger.info(f"Rapport {report_info.get('id')} envoyé par email à {recipient['address']}")
            
            return {
                'success': True,
                'message': f'Rapport envoyé par email à {len(recipients)} destinataire(s)',
                'recipients_count': len(recipients)
            }
        except Exception as e:
            logger.exception(f"Erreur lors de la distribution du rapport {report_info.get('id')} par email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Erreur lors de l\'envoi par email'
            }
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Valide les destinataires pour la distribution par email.
        
        Args:
            recipients: Liste des destinataires à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Aucun destinataire spécifié"
            return errors
        
        for i, recipient in enumerate(recipients):
            if 'address' not in recipient:
                errors[f'recipient_{i}'] = "Adresse email manquante"
            elif not self._validate_email(recipient['address']):
                errors[f'recipient_{i}'] = f"Adresse email invalide: {recipient['address']}"
        
        return errors
    
    def _validate_email(self, email: str) -> bool:
        """
        Valide une adresse email simple.
        
        Args:
            email: Adresse email à valider
            
        Returns:
            True si l'adresse semble valide
        """
        return '@' in email and '.' in email.split('@')[-1]
    
    def _get_mimetype(self, file_path: str) -> str:
        """
        Détermine le type MIME d'un fichier à partir de son extension.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Type MIME correspondant
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        mime_types = {
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        
        return mime_types.get(extension, 'application/octet-stream')

class SlackDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie de distribution de rapports via Slack.
    """
    
    def __init__(self, webhook_url: str = None):
        """
        Initialise la stratégie avec l'URL de webhook Slack.
        
        Args:
            webhook_url: URL du webhook Slack (optionnel, peut être spécifié par destinataire)
        """
        self.default_webhook_url = webhook_url
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport via Slack.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des canaux Slack ou webhooks
            
        Returns:
            True si la distribution a réussi
        """
        try:
            # Préparer le message Slack
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"📊 {report_info.get('title', 'Nouveau rapport')}",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Description:* {report_info.get('description', 'Aucune description')}\n\n*Type:* {report_info.get('report_type', 'Non spécifié')}\n*Créé par:* {report_info.get('created_by', 'Système')}"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }
            
            # Ajouter un lien si disponible
            if 'url' in report_info:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Vous pouvez consulter le rapport complet en cliquant sur le lien ci-dessous:"
                    }
                })
                message["blocks"].append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Voir le rapport",
                                "emoji": True
                            },
                            "url": report_info["url"],
                            "style": "primary"
                        }
                    ]
                })
            
            # Envoyer à chaque destinataire
            for recipient in recipients:
                webhook_url = recipient.get('webhook_url', self.default_webhook_url)
                
                if not webhook_url:
                    logger.error("Aucune URL de webhook Slack spécifiée")
                    continue
                
                # Personnaliser le message si un canal est spécifié
                if 'channel' in recipient:
                    channel_message = message.copy()
                    channel_message["channel"] = recipient['channel']
                    
                    response = requests.post(
                        webhook_url,
                        data=json.dumps(channel_message),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Erreur lors de l'envoi à Slack (canal {recipient['channel']}): {response.text}")
                else:
                    # Envoi sans spécifier de canal
                    response = requests.post(
                        webhook_url,
                        data=json.dumps(message),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Erreur lors de l'envoi à Slack: {response.text}")
                
                logger.info(f"Rapport {report_info.get('id')} envoyé à Slack")
            
            return True
        except Exception as e:
            logger.exception(f"Erreur lors de la distribution du rapport {report_info.get('id')} via Slack: {str(e)}")
            return False
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Valide les destinataires pour la distribution via Slack.
        
        Args:
            recipients: Liste des destinataires à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Aucun destinataire spécifié"
            return errors
        
        for i, recipient in enumerate(recipients):
            if 'webhook_url' not in recipient and not self.default_webhook_url:
                errors[f'recipient_{i}'] = "URL de webhook Slack manquante"
            elif 'webhook_url' in recipient and not recipient['webhook_url'].startswith(('http://', 'https://')):
                errors[f'recipient_{i}'] = "URL de webhook Slack invalide"
        
        return errors

class WebhookDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie de distribution de rapports via webhook générique.
    """
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport via des webhooks génériques.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des webhooks avec leurs URLs
            
        Returns:
            True si la distribution a réussi pour au moins un webhook
        """
        try:
            # Préparer les données à envoyer
            payload = {
                'report': {
                    'id': report_info.get('id'),
                    'title': report_info.get('title'),
                    'description': report_info.get('description'),
                    'type': report_info.get('report_type'),
                    'status': report_info.get('status'),
                    'created_at': report_info.get('created_at'),
                    'created_by': report_info.get('created_by')
                }
            }
            
            # Ajouter l'URL si disponible
            if 'url' in report_info:
                payload['report']['url'] = report_info['url']
            
            # Ajouter le contenu si disponible et pas trop volumineux
            if 'content' in report_info and isinstance(report_info['content'], dict):
                # Limiter la taille pour éviter des requêtes trop grandes
                content_str = json.dumps(report_info['content'])
                if len(content_str) < 10000:  # ~10KB max
                    payload['report']['content'] = report_info['content']
            
            # Compteur de succès
            success_count = 0
            
            # Envoyer à chaque destinataire
            for recipient in recipients:
                if 'url' not in recipient:
                    logger.error("URL de webhook manquante dans un destinataire")
                    continue
                
                webhook_url = recipient['url']
                
                # Configuration spécifique au webhook si présente
                headers = recipient.get('headers', {'Content-Type': 'application/json'})
                method = recipient.get('method', 'POST').upper()
                
                # Personnaliser le payload si nécessaire
                custom_payload = payload.copy()
                if 'payload_template' in recipient:
                    try:
                        # Permettre un format personnalisé de payload
                        template = recipient['payload_template']
                        for key, value_template in template.items():
                            if isinstance(value_template, str) and '{' in value_template:
                                # Format simple avec templates string
                                for report_key, report_value in payload['report'].items():
                                    placeholder = '{' + report_key + '}'
                                    if placeholder in value_template:
                                        value_template = value_template.replace(placeholder, str(report_value))
                                template[key] = value_template
                        custom_payload = template
                    except Exception as e:
                        logger.error(f"Erreur lors de la personnalisation du payload: {str(e)}")
                
                # Envoyer la requête
                if method == 'POST':
                    response = requests.post(
                        webhook_url,
                        data=json.dumps(custom_payload),
                        headers=headers
                    )
                elif method == 'PUT':
                    response = requests.put(
                        webhook_url,
                        data=json.dumps(custom_payload),
                        headers=headers
                    )
                else:
                    logger.error(f"Méthode HTTP non supportée: {method}")
                    continue
                
                # Vérifier la réponse
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"Rapport {report_info.get('id')} envoyé au webhook {webhook_url}")
                    success_count += 1
                else:
                    logger.error(f"Erreur lors de l'envoi au webhook {webhook_url}: {response.status_code} - {response.text}")
            
            # Considérer comme réussi si au moins un webhook a fonctionné
            return success_count > 0
            
        except Exception as e:
            logger.exception(f"Erreur lors de la distribution du rapport {report_info.get('id')} via webhook: {str(e)}")
            return False
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Valide les destinataires pour la distribution via webhook.
        
        Args:
            recipients: Liste des destinataires à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Aucun destinataire spécifié"
            return errors
        
        for i, recipient in enumerate(recipients):
            if 'url' not in recipient:
                errors[f'recipient_{i}'] = "URL du webhook manquante"
            elif not recipient['url'].startswith(('http://', 'https://')):
                errors[f'recipient_{i}'] = "URL du webhook invalide"
                
            if 'method' in recipient and recipient['method'] not in ['POST', 'PUT']:
                errors[f'recipient_{i}_method'] = f"Méthode HTTP non supportée: {recipient['method']}"
        
        return errors


class TelegramDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie de distribution de rapports via Telegram.
    """
    
    def __init__(self, bot_token: str = None):
        """
        Initialise la stratégie avec le token du bot Telegram.
        
        Args:
            bot_token: Token du bot Telegram (optionnel, peut être dans la config)
        """
        from .notification_config import NotificationConfig
        
        self.config = NotificationConfig.get_telegram_config()
        self.bot_token = bot_token or self.config['bot_token']
        self.api_url = self.config['api_url']
        self.timeout = self.config['timeout']
        self.max_retries = self.config['max_retries']
    
    def distribute(self, report_info: Dict[str, Any], recipients: Dict[str, Any]) -> Dict[str, Any]:
        """
        Distribue un rapport via Telegram.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Dict avec la clé 'telegram' contenant la liste des destinataires
            
        Returns:
            Dict avec le résultat de la distribution
        """
        try:
            # Extraire les destinataires Telegram
            telegram_recipients = recipients.get('telegram', [])
            if not telegram_recipients:
                return {
                    'success': False,
                    'error': 'Aucun destinataire Telegram spécifié',
                    'message': 'Aucun destinataire Telegram'
                }
            
            # Préparer le message
            message = self._prepare_message(report_info)
            
            # Envoyer à chaque destinataire
            success_count = 0
            for recipient in telegram_recipients:
                chat_id = recipient.get('chat_id', self.config['default_chat_id'])
                
                if self._send_message(chat_id, message):
                    success_count += 1
                    
                    # Envoyer le fichier si disponible
                    if 'file_path' in report_info and os.path.exists(report_info['file_path']):
                        self._send_document(chat_id, report_info['file_path'], report_info)
            
            logger.info(f"Rapport {report_info.get('id')} envoyé à {success_count}/{len(recipients)} destinataires Telegram")
            return {
                'success': success_count > 0,
                'message': f'Rapport envoyé à {success_count}/{len(recipients)} destinataires Telegram',
                'recipients_count': success_count
            }
            
        except Exception as e:
            logger.exception(f"Erreur lors de la distribution du rapport {report_info.get('id')} via Telegram: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Erreur lors de l\'envoi via Telegram'
            }
    
    def _prepare_message(self, report_info: Dict[str, Any]) -> str:
        """Prépare le message Telegram."""
        from .notification_config import NotificationConfig
        
        templates = NotificationConfig.get_notification_templates()
        template = templates['telegram']['report_ready']['message']
        
        # Formatter le message
        message = template.format(
            report_type=report_info.get('report_type', 'Rapport'),
            title=report_info.get('title', 'Rapport généré'),
            generated_at=report_info.get('created_at', 'Maintenant'),
            file_size=self._format_file_size(report_info.get('file_size', 0)),
            download_url=report_info.get('url', 'Non disponible')
        )
        
        return message
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formate la taille du fichier."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    
    def _send_message(self, chat_id: str, message: str) -> bool:
        """Envoie un message texte."""
        try:
            url = self.api_url.format(token=self.bot_token, method='sendMessage')
            
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Message Telegram envoyé avec succès au chat {chat_id}")
                    return True
                else:
                    logger.error(f"Erreur API Telegram: {result.get('description')}")
                    return False
            else:
                logger.error(f"Erreur HTTP lors de l'envoi Telegram: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message Telegram: {e}")
            return False
    
    def _send_document(self, chat_id: str, file_path: str, report_info: Dict[str, Any]) -> bool:
        """Envoie un fichier de rapport."""
        try:
            url = self.api_url.format(token=self.bot_token, method='sendDocument')
            
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': chat_id,
                    'caption': f"📄 {report_info.get('title', 'Rapport')} - {report_info.get('report_type', 'Document')}"
                }
                
                response = requests.post(url, files=files, data=data, timeout=self.timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.info(f"Fichier Telegram envoyé avec succès au chat {chat_id}")
                        return True
                    else:
                        logger.error(f"Erreur API Telegram pour fichier: {result.get('description')}")
                        return False
                else:
                    logger.error(f"Erreur HTTP lors de l'envoi du fichier Telegram: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du fichier Telegram: {e}")
            return False
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Valide les destinataires pour la distribution via Telegram.
        
        Args:
            recipients: Liste des destinataires à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Aucun destinataire spécifié"
            return errors
        
        for i, recipient in enumerate(recipients):
            chat_id = recipient.get('chat_id')
            if not chat_id:
                # Utiliser le chat ID par défaut si non spécifié
                recipient['chat_id'] = self.config['default_chat_id']
            elif not str(chat_id).isdigit() and not str(chat_id).startswith('-'):
                errors[f'recipient_{i}'] = f"Chat ID Telegram invalide: {chat_id}"
        
        return errors 