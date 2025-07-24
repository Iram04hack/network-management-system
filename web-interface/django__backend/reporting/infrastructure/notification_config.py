"""
Configuration des notifications pour le module reporting.

IMPORTANT : Ce fichier contient des informations sensibles et doit être protégé.
Les valeurs réelles doivent être définies via des variables d'environnement.
"""

import os
from typing import Dict, Any
from django.conf import settings

class NotificationConfig:
    """Configuration centralisée pour les notifications."""
    
    @staticmethod
    def get_email_config() -> Dict[str, Any]:
        """
        Configuration email avec support Gmail et SMTP personnalisé.
        
        IMPORTANT : Pour Gmail, créez un "Mot de passe d'application" :
        1. Allez sur https://myaccount.google.com/security
        2. Activez la "Vérification en 2 étapes"
        3. Allez dans "Mots de passe des applications"
        4. Générez un mot de passe pour "Mail"
        5. Utilisez ce mot de passe généré (pas votre mot de passe principal)
        """
        return {
            'smtp_host': os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'smtp_username': os.getenv('EMAIL_SMTP_USERNAME', 'amiromalade@gmail.com'),
            'smtp_password': os.getenv('EMAIL_SMTP_PASSWORD', 'ohpd muwa cllb prek'),  # Mot de passe d'application Gmail
            'from_email': os.getenv('EMAIL_FROM_ADDRESS', 'equipe_nms@gmail.com'),
            'from_name': os.getenv('EMAIL_FROM_NAME', 'Équipe NMS'),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true',
            'timeout': int(os.getenv('EMAIL_TIMEOUT', '30')),
            'max_retries': int(os.getenv('EMAIL_MAX_RETRIES', '3'))
        }
    
    @staticmethod
    def get_telegram_config() -> Dict[str, Any]:
        """Configuration Telegram."""
        return {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', '8049013662:AAFXhhW_7B9ZPz_IHpq4tb_AdU25JgEKj1k'),
            'default_chat_id': os.getenv('TELEGRAM_DEFAULT_CHAT_ID', '1791851047'),
            'api_url': 'https://api.telegram.org/bot{token}/{method}',
            'timeout': int(os.getenv('TELEGRAM_TIMEOUT', '30')),
            'max_retries': int(os.getenv('TELEGRAM_MAX_RETRIES', '3'))
        }
    
    @staticmethod
    def get_notification_templates() -> Dict[str, Any]:
        """Templates de notification."""
        return {
            'email': {
                'report_ready': {
                    'subject': '[NMS] Rapport {report_type} disponible',
                    'template': 'reporting/email/report_ready.html',
                    'text_template': 'reporting/email/report_ready.txt'
                },
                'report_error': {
                    'subject': '[NMS] Erreur lors de la génération du rapport',
                    'template': 'reporting/email/report_error.html',
                    'text_template': 'reporting/email/report_error.txt'
                }
            },
            'telegram': {
                'report_ready': {
                    'message': '📊 *Rapport {report_type} disponible*\n\n'
                              '📝 *Titre :* {title}\n'
                              '🕒 *Généré le :* {generated_at}\n'
                              '📏 *Taille :* {file_size}\n'
                              '🔗 *Lien :* {download_url}',
                    'parse_mode': 'Markdown'
                },
                'report_error': {
                    'message': '❌ *Erreur lors de la génération du rapport*\n\n'
                              '📝 *Titre :* {title}\n'
                              '🕒 *Tentative le :* {attempted_at}\n'
                              '⚠️ *Erreur :* {error_message}',
                    'parse_mode': 'Markdown'
                }
            }
        }

# Configuration par défaut pour les tests
DEFAULT_CONFIG = {
    'email': {
        'enabled': True,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'from_email': 'equipe_nms@gmail.com',
        'from_name': 'Équipe NMS'
    },
    'telegram': {
        'enabled': True,
        'api_url': 'https://api.telegram.org/bot{token}/{method}'
    }
}