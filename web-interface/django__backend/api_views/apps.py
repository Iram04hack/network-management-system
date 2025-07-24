"""
Configuration de l'application API Views.

Ce module configure l'application Django pour le module API Views
en suivant les bonnes pratiques Django.
"""

from django.apps import AppConfig


class ApiViewsConfig(AppConfig):
    """Configuration de l'application API Views."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_views'
    verbose_name = 'API Views - Network Management System'
    
    def ready(self):
        """
        Méthode appelée lorsque l'application est prête.
        Utilisée pour l'initialisation des signaux et autres configurations.
        """
        # Import des signaux si nécessaire
        # from . import signals
        
        # Configuration du cache pour les vues API
        self._configure_api_cache()
        
        # Configuration des permissions par défaut
        self._configure_default_permissions()
    
    def _configure_api_cache(self):
        """Configure le cache pour les vues API."""
        from django.core.cache import cache
        from django.conf import settings
        
        # Vérifier que le cache est configuré
        if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
            # Configuration des clés de cache pour les vues API
            cache_config = {
                'api_views_prefix': 'api_views',
                'default_timeout': 300,  # 5 minutes
                'dashboard_timeout': 120,  # 2 minutes
                'search_timeout': 300,  # 5 minutes
                'device_timeout': 900,  # 15 minutes
            }
            
            # Stocker la configuration dans le cache
            cache.set('api_views_cache_config', cache_config, timeout=None)
    
    def _configure_default_permissions(self):
        """Configure les permissions par défaut pour les vues API."""
        # Configuration des permissions par défaut
        # Ceci peut être étendu selon les besoins de sécurité
        pass
