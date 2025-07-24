# nms_backend/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class NmsBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nms_backend'
    
    def ready(self):
        """
        Méthode appelée lors du démarrage de l'application.
        Découvre et charge tous les plugins.
        """
        try:
            # Importer ici pour éviter les imports circulaires
            from services.plugin_service import PluginService
            
            # Découvrir les plugins
            stats = PluginService.discover_plugins()
            logger.info(f"Plugin discovery complete: {stats}")
        except Exception as e:
            logger.error(f"Error during plugin discovery: {e}")
