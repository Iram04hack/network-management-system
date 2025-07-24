"""
Configuration de l'application API.

Ce module contient la configuration Django pour l'application API.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration de l'application API."""
    
    name = 'ai_assistant.api'
    verbose_name = "Assistant IA - API"
    
    def ready(self):
        """
        Initialise l'application API.
        
        Cette méthode est appelée lorsque l'application est prête.
        Elle peut être utilisée pour effectuer des initialisations
        ou des configurations supplémentaires.
        """
        # Import des signaux pour les enregistrer
        import ai_assistant.api.signals  # noqa 