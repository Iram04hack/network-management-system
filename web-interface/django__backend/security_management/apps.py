"""
Configuration de l'application Django Security Management.

Ce module définit la configuration de l'application Django pour le module
de gestion de la sécurité.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class SecurityManagementConfig(AppConfig):
    """
    Configuration de l'application Security Management.
    
    Cette application implémente les fonctionnalités de gestion de la sécurité
    du système, y compris les règles de sécurité, les alertes, les événements
    et l'intégration avec des systèmes de sécurité externes comme Suricata et Fail2Ban.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security_management'
    verbose_name = _('Gestion de la Sécurité')
    
    def ready(self):
        """
        Initialisation de l'application au démarrage.
        
        Cette méthode est appelée une fois que l'application est prête.
        Elle initialise le conteneur d'injection de dépendances et
        configure les signaux Django nécessaires.
        """
        try:
            # Import du conteneur d'injection de dépendances
            from security_management.di_container import initialize_container
            # Initialisation du conteneur
            initialize_container()
            logger.info("Conteneur d'injection de dépendances de sécurité initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du conteneur de sécurité: {e}")
            logger.exception("Détail de l'erreur:")
        
        # Importer les signaux
        try:
            import security_management.signals
            logger.info("Signaux de sécurité importés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'import des signaux de sécurité: {e}")
            logger.exception("Détail de l'erreur:") 