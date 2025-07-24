"""
Signaux Django pour l'initialisation automatique des services d'intégration.
"""
from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
import logging
import threading
from .central_topology_service import central_topology_service
from .gns3_integration_service import gns3_integration_service
from .ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def initialize_integration_services(sender, **kwargs):
    """
    Initialise les services d'intégration après les migrations.
    """
    # S'assurer que nous n'initialisons qu'une seule fois
    if not hasattr(initialize_integration_services, 'initialized'):
        initialize_integration_services.initialized = True
        
        def delayed_initialization():
            """Initialisation retardée pour éviter les problèmes de démarrage."""
            try:
                logger.info("🚀 Initialisation des services d'intégration NMS")
                
                # Test des notifications Ubuntu
                if ubuntu_notification_service.test_notification():
                    logger.info("✅ Service de notification Ubuntu opérationnel")
                else:
                    logger.warning("⚠️ Service de notification Ubuntu non disponible")
                
                # Intégration automatique des modules
                central_topology_service.auto_integrate_modules()
                
                # Démarrer la surveillance GNS3 si configuré
                auto_monitor = getattr(settings, 'GNS3_AUTO_MONITOR', True)
                if auto_monitor:
                    monitor_interval = getattr(settings, 'GNS3_MONITOR_INTERVAL', 30)
                    central_topology_service.start_monitoring(monitor_interval)
                    logger.info(f"🔍 Surveillance GNS3 démarrée (intervalle: {monitor_interval}s)")
                
                # Effectuer une détection initiale de GNS3
                detection_result = gns3_integration_service.detect_gns3_server()
                if detection_result.get('available'):
                    logger.info("✅ Serveur GNS3 détecté et intégré")
                    
                    # Envoyer notification de succès
                    ubuntu_notification_service.send_notification(
                        title="🎉 NMS Intégration Complète",
                        message="Tous les services d'intégration sont opérationnels et le serveur GNS3 a été détecté",
                        urgency='low',
                        category='system.startup'
                    )
                else:
                    logger.info("ℹ️ Serveur GNS3 non détecté - surveillance active")
                    
                    ubuntu_notification_service.send_notification(
                        title="🔍 NMS en surveillance",
                        message="Services d'intégration initialisés. Recherche du serveur GNS3 en cours...",
                        urgency='low',
                        category='system.startup'
                    )
                
                logger.info("✅ Initialisation des services d'intégration terminée")
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'initialisation des services d'intégration: {e}")
                
                ubuntu_notification_service.send_notification(
                    title="❌ Erreur d'initialisation NMS",
                    message=f"Erreur lors de l'initialisation des services d'intégration: {str(e)}",
                    urgency='critical',
                    category='system.error'
                )
        
        # Démarrer l'initialisation dans un thread séparé avec un délai
        init_thread = threading.Timer(5.0, delayed_initialization)
        init_thread.daemon = True
        init_thread.start()
        
        logger.info("🔄 Initialisation des services d'intégration programmée") 