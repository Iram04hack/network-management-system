"""
Configuration de l'application Django pour le module Dashboard.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DashboardConfig(AppConfig):
    """
    Configuration de l'application Dashboard.
    
    Cette classe définit les paramètres de l'application Django
    pour le module Dashboard.
    """
    
    name = 'dashboard'
    verbose_name = _('Tableau de bord')
    
    def ready(self):
        """
        Méthode appelée lorsque l'application est prête.
        
        Effectue les initialisations nécessaires au démarrage de l'application.
        """
        # Importer les signaux pour les enregistrer
        import dashboard.signals  # noqa
        
        # Initialiser les services nécessaires
        self._initialize_services()
        
        # Journaliser le démarrage de l'application
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Application Dashboard initialisée")
    
    def _initialize_services(self):
        """
        Initialise les services nécessaires au fonctionnement du tableau de bord.
        
        Cette méthode est appelée au démarrage de l'application pour
        préparer les services et les dépendances.
        """
        # Dans une implémentation réelle, on pourrait initialiser ici
        # des connexions aux services externes, des tâches périodiques, etc.
        pass 