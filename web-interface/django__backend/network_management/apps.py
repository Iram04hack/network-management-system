"""
Module de configuration de l'application Django Network Management.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NetworkManagementConfig(AppConfig):
    """
    Configuration de l'application Django Network Management.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'network_management'
    verbose_name = 'Gestion de Réseau'

    def ready(self):
        """
        Méthode appelée lorsque l'application est prête.
        """
        # Importer les signaux si nécessaire
        # import network_management.signals
        pass

        # Import des signaux pour les enregistrer
        import network_management.signals  # noqa
        
        # Initialisation du conteneur d'injection de dépendances
        try:
            from network_management.di_container import init_container
            init_container()
            print("✅ Container d'injection de dépendances network_management initialisé avec succès")
        except Exception as e:
            # Ne pas masquer les erreurs d'initialisation en production
            print(f"❌ ERREUR CRITIQUE: Échec initialisation DI container network_management: {e}")
            raise  # Propager l'erreur pour être visible en développement/déploiement 