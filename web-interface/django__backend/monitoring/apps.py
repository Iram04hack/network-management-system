"""
Configuration de l'application monitoring.
"""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    """Configuration de l'application monitoring."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Système de Monitoring Réseau'
    
    def ready(self):
        """
        Méthode exécutée au démarrage de l'application.
        
        Cette méthode est appelée lorsque l'application est prête.
        Elle peut être utilisée pour enregistrer des signaux, initialiser
        des services, etc.
        """
        # Import des signaux pour les enregistrer
        import monitoring.signals

        # Initialisation du conteneur d'injection de dépendances
        try:
            from monitoring.di_container import initialize_container
            initialize_container()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur lors de l'initialisation du conteneur d'injection de dépendances: {e}")
            logger.exception(e) 