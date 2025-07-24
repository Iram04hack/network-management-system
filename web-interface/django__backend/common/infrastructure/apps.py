"""
Configuration de l'application Common.

Ce module définit les paramètres de configuration de l'application Django
'common' qui fournit des fonctionnalités partagées pour tout le système.

La configuration gère notamment l'enregistrement des signaux et autres
initialisations nécessaires au bon fonctionnement de l'application.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonConfig(AppConfig):
    """
    Configuration de l'application Common.
    
    Cette classe définit les métadonnées et le comportement de l'application
    'common' au sein du projet Django.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = _('Services communs')
    
    def ready(self):
        """
        Méthode appelée lorsque l'application est prête.
        
        Cette méthode est invoquée par Django lors du démarrage pour
        effectuer les initialisations nécessaires, notamment l'enregistrement
        des signaux pour éviter les imports circulaires.
        """
        # Importer les signaux ici pour éviter les imports circulaires
        try:
            from .signals import initialize_integration_services
            # Les signaux sont automatiquement enregistrés via le décorateur @receiver
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Impossible d'importer les signaux d'intégration: {e}")
        
        # Journaliser le chargement de l'application
        import logging
        logger = logging.getLogger(__name__)
        logger.info("L'application Common a été chargée avec succès - Services d'intégration disponibles") 