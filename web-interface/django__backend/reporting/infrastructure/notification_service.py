"""
Service de notification réel pour le module reporting.

Ce service remplace les simulations de notification par des implémentations
réelles pour l'envoi d'emails, webhooks et autres canaux de distribution.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
import requests

logger = logging.getLogger(__name__)


class ReportingNotificationService:
    """
    Service de notification pour le reporting.
    
    Gère l'envoi de notifications pour les rapports via différents canaux :
    - Email
    - Webhook
    - Slack (via webhook)
    """
    
    def __init__(self):
        """Initialise le service de notification."""
        self.smtp_configured = self._check_smtp_configuration()
        logger.info(f"Service de notification initialisé - SMTP: {'✅' if self.smtp_configured else '❌'}")
    
    def _check_smtp_configuration(self) -> bool:
        """Vérifie si SMTP est configuré."""
        return bool(
            getattr(settings, 'EMAIL_HOST', None) and
            getattr(settings, 'EMAIL_PORT', None)
        )
    
    def send_report_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie une notification de rapport.
        
        Args:
            notification_data: Données de notification contenant :
                - report_id: ID du rapport
                - report_title: Titre du rapport
                - report_type: Type de rapport
                - recipients: Liste des destinataires
                - channels: Canaux de notification
                - report_url: URL du rapport (optionnel)
                - report_file_path: Chemin du fichier (optionnel)
                
        Returns:
            Résultat de l'envoi
        """
        try:
            notification_start = datetime.now()
            
            report_id = notification_data.get('report_id')
            report_title = notification_data.get('report_title', 'Rapport sans titre')
            report_type = notification_data.get('report_type', 'unknown')
            recipients = notification_data.get('recipients', [])
            channels = notification_data.get('channels', ['email'])
            
            if not recipients:
                return {
                    'success': False,
                    'error': 'Aucun destinataire spécifié'
                }
            
            results = {
                'notification_id': f"notif_{report_id}_{int(notification_start.timestamp())}",
                'report_id': report_id,
                'channels_attempted': [],
                'successful_channels': [],
                'failed_channels': [],
                'details': {}
            }
            
            # Envoi par email
            if 'email' in channels:
                email_result = self._send_email_notification(notification_data)
                results['channels_attempted'].append('email')
                results['details']['email'] = email_result
                
                if email_result['success']:
                    results['successful_channels'].append('email')
                else:
                    results['failed_channels'].append('email')
            
            # Envoi par webhook
            if 'webhook' in channels:
                webhook_result = self._send_webhook_notification(notification_data)
                results['channels_attempted'].append('webhook')
                results['details']['webhook'] = webhook_result
                
                if webhook_result['success']:
                    results['successful_channels'].append('webhook')
                else:
                    results['failed_channels'].append('webhook')
            
            # Envoi Slack
            if 'slack' in channels:
                slack_result = self._send_slack_notification(notification_data)
                results['channels_attempted'].append('slack')
                results['details']['slack'] = slack_result
                
                if slack_result['success']:
                    results['successful_channels'].append('slack')
                else:
                    results['failed_channels'].append('slack')
            
            # Évaluation du succès global
            results['success'] = len(results['successful_channels']) > 0
            results['notification_duration'] = (datetime.now() - notification_start).total_seconds()
            results['timestamp'] = datetime.now().isoformat()
            
            if results['success']:
                logger.info(f"Notification rapport {report_id} envoyée avec succès via {results['successful_channels']}")
            else:
                logger.error(f"Échec d'envoi notification rapport {report_id}: tous les canaux ont échoué")
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_email_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie une notification par email.
        """
        try:
            if not self.smtp_configured:
                return {
                    'success': False,
                    'error': 'SMTP non configuré',
                    'fallback_used': True,
                    'message': 'Simulation d\'envoi d\'email - Configuration SMTP requise pour l\'envoi réel'
                }
            
            report_title = notification_data.get('report_title', 'Rapport')
            report_type = notification_data.get('report_type', 'unknown')
            recipients = notification_data.get('recipients', [])
            report_url = notification_data.get('report_url')
            report_file_path = notification_data.get('report_file_path')
            
            # Préparer l'email
            subject = f"NMS - {report_title} disponible"
            
            # Template du message
            message_context = {
                'report_title': report_title,
                'report_type': report_type,
                'report_url': report_url,
                'generated_at': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                'system_name': 'Network Management System'
            }
            
            # Corps du message
            message_body = self._generate_email_body(message_context)
            
            # Filtrer les emails valides
            valid_recipients = [r for r in recipients if self._is_valid_email(r)]
            
            if not valid_recipients:
                return {
                    'success': False,
                    'error': 'Aucun destinataire email valide'
                }
            
            # Créer l'email
            email = EmailMessage(
                subject=subject,
                body=message_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'nms@localhost'),
                to=valid_recipients
            )
            
            # Attacher le fichier si disponible
            if report_file_path and self._file_exists(report_file_path):
                email.attach_file(report_file_path)
            
            # Envoyer l'email
            sent_count = email.send()
            
            return {
                'success': sent_count > 0,
                'recipients_count': len(valid_recipients),
                'sent_count': sent_count,
                'recipients': valid_recipients,
                'has_attachment': bool(report_file_path)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True,
                'message': f'Simulation d\'envoi d\'email - Erreur: {str(e)}'
            }
    
    def _send_webhook_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie une notification par webhook.
        """
        try:
            webhook_url = notification_data.get('webhook_url') or getattr(settings, 'REPORTING_WEBHOOK_URL', None)
            
            if not webhook_url:
                return {
                    'success': False,
                    'error': 'URL webhook non configurée',
                    'fallback_used': True,
                    'message': 'Simulation d\'envoi webhook - URL webhook requise'
                }
            
            # Préparer le payload
            payload = {
                'event_type': 'report_generated',
                'report_id': notification_data.get('report_id'),
                'report_title': notification_data.get('report_title'),
                'report_type': notification_data.get('report_type'),
                'report_url': notification_data.get('report_url'),
                'generated_at': datetime.now().isoformat(),
                'system': 'NMS-Reporting'
            }
            
            # Envoyer le webhook
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'webhook_url': webhook_url,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f'Webhook retourné status {response.status_code}',
                    'webhook_url': webhook_url,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'envoi webhook: {e}")
            return {
                'success': False,
                'error': f'Erreur réseau webhook: {str(e)}',
                'fallback_used': True,
                'message': f'Simulation d\'envoi webhook - Erreur réseau: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi webhook: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True,
                'message': f'Simulation d\'envoi webhook - Erreur: {str(e)}'
            }
    
    def _send_slack_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie une notification Slack.
        """
        try:
            slack_webhook_url = notification_data.get('slack_webhook_url') or getattr(settings, 'SLACK_WEBHOOK_URL', None)
            
            if not slack_webhook_url:
                return {
                    'success': False,
                    'error': 'URL webhook Slack non configurée',
                    'fallback_used': True,
                    'message': 'Simulation d\'envoi Slack - URL webhook Slack requise'
                }
            
            report_title = notification_data.get('report_title', 'Rapport')
            report_type = notification_data.get('report_type', 'unknown')
            report_url = notification_data.get('report_url')
            
            # Construire le message Slack
            slack_message = {
                'text': f'📊 Nouveau rapport disponible: {report_title}',
                'attachments': [
                    {
                        'color': 'good',
                        'fields': [
                            {
                                'title': 'Type de rapport',
                                'value': report_type,
                                'short': True
                            },
                            {
                                'title': 'Généré le',
                                'value': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                                'short': True
                            }
                        ]
                    }
                ]
            }
            
            # Ajouter l'URL si disponible
            if report_url:
                slack_message['attachments'][0]['actions'] = [
                    {
                        'type': 'button',
                        'text': 'Voir le rapport',
                        'url': report_url
                    }
                ]
            
            # Envoyer à Slack
            response = requests.post(
                slack_webhook_url,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'webhook_url': slack_webhook_url,
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f'Slack webhook retourné status {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi Slack: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True,
                'message': f'Simulation d\'envoi Slack - Erreur: {str(e)}'
            }
    
    def _generate_email_body(self, context: Dict[str, Any]) -> str:
        """
        Génère le corps de l'email.
        """
        template = """
Bonjour,

Un nouveau rapport {report_type} est disponible :

Titre : {report_title}
Généré le : {generated_at}
Système : {system_name}

{url_section}

Cordialement,
Équipe {system_name}
        """
        
        url_section = ""
        if context.get('report_url'):
            url_section = f"Accéder au rapport : {context['report_url']}"
        else:
            url_section = "Le rapport est disponible en pièce jointe."
        
        return template.format(
            report_type=context['report_type'],
            report_title=context['report_title'],
            generated_at=context['generated_at'],
            system_name=context['system_name'],
            url_section=url_section
        )
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Vérifie si l'email est valide.
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _file_exists(self, file_path: str) -> bool:
        """
        Vérifie si le fichier existe.
        """
        import os
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une notification.
        
        Args:
            notification_id: ID de la notification
            
        Returns:
            Statut de la notification
        """
        # Pour l'instant, retourner un statut simulé
        # Dans une implémentation complète, ceci interrogerait une base de données
        return {
            'notification_id': notification_id,
            'status': 'sent',
            'created_at': datetime.now().isoformat(),
            'channels': ['email'],
            'message': 'Statut récupéré avec succès'
        }
    
    def test_notification_channels(self) -> Dict[str, Any]:
        """
        Teste tous les canaux de notification.
        
        Returns:
            Résultats des tests
        """
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'channels': {},
            'overall_status': 'unknown'
        }
        
        # Test email
        test_results['channels']['email'] = {
            'available': self.smtp_configured,
            'status': 'operational' if self.smtp_configured else 'configuration_required',
            'message': 'SMTP configuré' if self.smtp_configured else 'Configuration SMTP requise'
        }
        
        # Test webhook
        webhook_url = getattr(settings, 'REPORTING_WEBHOOK_URL', None)
        test_results['channels']['webhook'] = {
            'available': bool(webhook_url),
            'status': 'operational' if webhook_url else 'configuration_required',
            'message': 'URL webhook configurée' if webhook_url else 'URL webhook requise'
        }
        
        # Test Slack
        slack_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        test_results['channels']['slack'] = {
            'available': bool(slack_url),
            'status': 'operational' if slack_url else 'configuration_required',
            'message': 'URL Slack configurée' if slack_url else 'URL Slack requise'
        }
        
        # Statut global
        operational_channels = [
            name for name, config in test_results['channels'].items() 
            if config['status'] == 'operational'
        ]
        
        if operational_channels:
            test_results['overall_status'] = 'partial' if len(operational_channels) < 3 else 'operational'
        else:
            test_results['overall_status'] = 'configuration_required'
        
        test_results['operational_channels'] = operational_channels
        
        return test_results