"""
Configuration de l'application Reporting.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class ReportingConfig(AppConfig):
    """Configuration de l'application Reporting"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reporting'
    verbose_name = "Reporting"

    def ready(self):
        """
        Initialise les services et les gestionnaires d'événements
        lors du démarrage de l'application.
        """
        logger.info("Initialisation du module de reporting")

        # Temporairement désactivé pour éviter les erreurs de démarrage
        # TODO: Corriger les imports manquants et réactiver l'initialisation du DI container
        try:
            # Logique d'initialisation du conteneur désactivée temporairement
            # pour permettre le démarrage de Django sans erreurs
            pass
        except Exception as e:
            logger.warning(f"Erreur lors de l'initialisation du conteneur reporting: {e}")

        # Importer les signaux ici pour éviter les imports circulaires
        try:
            import reporting.signals
        except Exception as e:
            logger.warning(f"Erreur lors de l'import des signaux reporting: {e}")
