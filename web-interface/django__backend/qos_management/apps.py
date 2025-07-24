"""
Configuration de l'application QoS Management
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class QoSManagementConfig(AppConfig):
    """Configuration de l'application QoS Management"""
    name = 'qos_management'
    verbose_name = 'QoS Management'
    
    def ready(self):
        """
        Préparation de l'application
        Cette méthode est appelée quand le registre d'applications est entièrement rempli
        """
        # Initialisation du conteneur d'injection de dépendances
        try:
            from .di_container import init_di_container
            init_di_container()
            logger.info("Conteneur d'injection de dépendances QoS initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du conteneur QoS: {e}")
            # Ne pas masquer l'erreur, elle doit être visible pour être corrigée
            raise
        
        # Importer les signaux
        try:
            import qos_management.signals
            logger.info("Signaux QoS chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'import des signaux QoS: {e}")
            raise 