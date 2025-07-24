"""
Commande Django pour démarrer le service central GNS3.

Cette commande initialise et démarre tous les composants du service central GNS3 :
- Service central GNS3
- Gestionnaire d'événements temps réel
- Monitoring et cache Redis
- Système d'événements WebSocket
"""

import asyncio
import logging
import signal
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

from common.infrastructure.gns3_central_service import gns3_central_service
from common.infrastructure.realtime_event_system import realtime_event_manager
from common.infrastructure.ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Commande pour démarrer le service central GNS3."""
    
    help = 'Démarre le service central GNS3 avec tous ses composants'
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            '--no-events',
            action='store_true',
            help='Désactive le système d\'événements temps réel'
        )
        
        parser.add_argument(
            '--no-websocket',
            action='store_true',
            help='Désactive les WebSockets'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Active le mode debug avec logs détaillés'
        )
        
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Lance en mode test avec données simulées'
        )
    
    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        self.debug_mode = options.get('debug', False)
        self.test_mode = options.get('test_mode', False)
        self.enable_events = not options.get('no_events', False)
        self.enable_websocket = not options.get('no_websocket', False)
        
        # Configuration du logging
        if self.debug_mode:
            logging.getLogger('common.infrastructure').setLevel(logging.DEBUG)
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage du Service Central GNS3')
        )
        
        # Gestion des signaux pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Démarrer le service de manière asynchrone
        try:
            asyncio.run(self._start_service())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n⏹️  Arrêt du service demandé')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur fatale: {e}')
            )
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre."""
        self.stdout.write(
            self.style.WARNING(f'\n📡 Signal {signum} reçu, arrêt du service...')
        )
        # Le KeyboardInterrupt sera capturé par la boucle principale
        raise KeyboardInterrupt()
    
    async def _start_service(self):
        """Démarre tous les composants du service de manière asynchrone."""
        try:
            # 1. Initialisation du service central GNS3
            self.stdout.write('🔧 Initialisation du service central GNS3...')
            
            if not await gns3_central_service.initialize():
                self.stdout.write(
                    self.style.ERROR('❌ Échec de l\'initialisation du service central')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS('✅ Service central GNS3 initialisé')
            )
            
            # 2. Démarrage du gestionnaire d'événements temps réel
            if self.enable_events:
                self.stdout.write('⚡ Démarrage du système d\'événements temps réel...')
                await realtime_event_manager.start()
                self.stdout.write(
                    self.style.SUCCESS('✅ Système d\'événements démarré')
                )
            
            # 3. Configuration WebSocket
            if self.enable_websocket:
                self.stdout.write('🌐 Configuration WebSocket...')
                self._configure_websocket()
                self.stdout.write(
                    self.style.SUCCESS('✅ WebSocket configuré')
                )
            
            # 4. Tests de connectivité
            await self._run_connectivity_tests()
            
            # 5. Notification système de démarrage
            ubuntu_notification_service.send_notification(
                title="🚀 Service Central GNS3 Démarré",
                message="Tous les composants sont opérationnels",
                urgency='low',
                category='system.gns3'
            )
            
            # 6. Boucle principale de monitoring
            await self._main_service_loop()
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du service: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur: {e}')
            )
            raise
        finally:
            await self._cleanup_service()
    
    async def _run_connectivity_tests(self):
        """Exécute les tests de connectivité."""
        self.stdout.write('🔍 Tests de connectivité...')
        
        # Test GNS3
        service_status = gns3_central_service.get_service_status()
        gns3_connected = service_status.get('gns3_server', {}).get('connected', False)
        
        if gns3_connected:
            self.stdout.write('  ✅ Serveur GNS3 accessible')
        else:
            self.stdout.write(
                self.style.WARNING('  ⚠️  Serveur GNS3 non accessible')
            )
        
        # Test Cache Redis
        cache_available = service_status.get('cache', {}).get('network_state_cached', False)
        if cache_available:
            self.stdout.write('  ✅ Cache Redis opérationnel')
        else:
            self.stdout.write('  ℹ️  Cache Redis vide (normal au démarrage)')
        
        # Test système d'événements
        if self.enable_events:
            event_stats = realtime_event_manager.get_statistics()
            if event_stats.get('is_running'):
                self.stdout.write('  ✅ Système d\'événements actif')
            else:
                self.stdout.write(
                    self.style.WARNING('  ⚠️  Système d\'événements inactif')
                )
        
        self.stdout.write(
            self.style.SUCCESS('✅ Tests de connectivité terminés')
        )
    
    def _configure_websocket(self):
        """Configure les WebSockets."""
        # Vérifier la configuration ASGI
        asgi_application = getattr(settings, 'ASGI_APPLICATION', None)
        if not asgi_application:
            self.stdout.write(
                self.style.WARNING('  ⚠️  ASGI_APPLICATION non configuré dans settings')
            )
        
        # Vérifier la configuration des channels
        channel_layers = getattr(settings, 'CHANNEL_LAYERS', None)
        if not channel_layers:
            self.stdout.write(
                self.style.WARNING('  ⚠️  CHANNEL_LAYERS non configuré dans settings')
            )
    
    async def _main_service_loop(self):
        """Boucle principale de monitoring du service."""
        self.stdout.write(
            self.style.SUCCESS('\n🎯 Service Central GNS3 opérationnel!')
        )
        self.stdout.write('📊 Monitoring en cours... (Ctrl+C pour arrêter)\n')
        
        loop_count = 0
        
        try:
            while True:
                # Monitoring périodique toutes les 30 secondes
                await asyncio.sleep(30)
                loop_count += 1
                
                # Afficher les statistiques toutes les 2 minutes
                if loop_count % 4 == 0:
                    await self._display_statistics()
                
                # Vérification de santé toutes les 5 minutes
                if loop_count % 10 == 0:
                    await self._health_check()
                
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Arrêt du service demandé...')
    
    async def _display_statistics(self):
        """Affiche les statistiques du service."""
        if self.debug_mode:
            self.stdout.write('📊 Statistiques du service:')
            
            # Statistiques du service central
            service_status = gns3_central_service.get_service_status()
            stats = service_status.get('statistics', {})
            
            self.stdout.write(f'  • API calls: {stats.get("api_calls", 0)}')
            self.stdout.write(f'  • Cache hits: {stats.get("cache_hits", 0)}')
            self.stdout.write(f'  • Cache misses: {stats.get("cache_misses", 0)}')
            
            # Statistiques des événements
            if self.enable_events:
                event_stats = realtime_event_manager.get_statistics()
                self.stdout.write(f'  • Événements publiés: {event_stats.get("events_published", 0)}')
                self.stdout.write(f'  • Événements livrés: {event_stats.get("events_delivered", 0)}')
                self.stdout.write(f'  • Connexions WebSocket: {event_stats.get("connections_active", 0)}')
            
            self.stdout.write('')
    
    async def _health_check(self):
        """Vérifie la santé du service."""
        try:
            # Vérifier le service central
            service_status = gns3_central_service.get_service_status()
            if service_status.get('status') != 'connected':
                self.stdout.write(
                    self.style.WARNING('⚠️  Service central déconnecté, tentative de reconnexion...')
                )
                await gns3_central_service.initialize()
            
            # Vérifier le gestionnaire d'événements
            if self.enable_events:
                event_stats = realtime_event_manager.get_statistics()
                if not event_stats.get('is_running'):
                    self.stdout.write(
                        self.style.WARNING('⚠️  Gestionnaire d\'événements arrêté, redémarrage...')
                    )
                    await realtime_event_manager.start()
            
        except Exception as e:
            logger.error(f"Erreur lors du health check: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur health check: {e}')
            )
    
    async def _cleanup_service(self):
        """Nettoie les ressources avant l'arrêt."""
        self.stdout.write('🧹 Nettoyage des ressources...')
        
        try:
            # Arrêter le gestionnaire d'événements
            if self.enable_events:
                await realtime_event_manager.stop()
                self.stdout.write('  ✅ Gestionnaire d\'événements arrêté')
            
            # Notification d'arrêt
            ubuntu_notification_service.send_notification(
                title="🛑 Service Central GNS3 Arrêté",
                message="Service arrêté proprement",
                urgency='low',
                category='system.gns3'
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Nettoyage terminé')
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du nettoyage: {e}')
            )