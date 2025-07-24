"""
Commande Django pour démarrer le serveur Django avec le service central GNS3.

Cette commande combine le démarrage du serveur Django avec l'initialisation
du service central GNS3 pour un fonctionnement complet.
"""

import asyncio
import logging
import signal
import sys
import threading
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.core.wsgi import get_wsgi_application

from common.infrastructure.gns3_central_service import gns3_central_service
from common.infrastructure.realtime_event_system import realtime_event_manager
from common.infrastructure.ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Commande pour démarrer Django avec le service central GNS3."""
    
    help = 'Démarre le serveur Django avec le service central GNS3 intégré'
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port sur lequel démarrer le serveur Django (défaut: 8000)'
        )
        
        parser.add_argument(
            '--host',
            type=str,
            default='0.0.0.0',
            help='Adresse IP sur laquelle démarrer le serveur (défaut: 0.0.0.0)'
        )
        
        parser.add_argument(
            '--no-gns3',
            action='store_true',
            help='Désactive l\'initialisation du service GNS3'
        )
        
        parser.add_argument(
            '--no-events',
            action='store_true',
            help='Désactive le système d\'événements temps réel'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Active le mode debug avec logs détaillés'
        )
    
    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        self.port = options.get('port', 8000)
        self.host = options.get('host', '0.0.0.0')
        self.enable_gns3 = not options.get('no_gns3', False)
        self.enable_events = not options.get('no_events', False)
        self.debug_mode = options.get('debug', False)
        
        # Configuration du logging
        if self.debug_mode:
            logging.getLogger('common.infrastructure').setLevel(logging.DEBUG)
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Démarrage du serveur Django + GNS3 sur {self.host}:{self.port}')
        )
        
        # Gestion des signaux pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialiser GNS3 en arrière-plan
            if self.enable_gns3:
                self._start_gns3_background()
            
            # Démarrer le serveur Django
            self._start_django_server()
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n⏹️  Arrêt du serveur demandé')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur fatale: {e}')
            )
            sys.exit(1)
        finally:
            self._cleanup()
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre."""
        self.stdout.write(
            self.style.WARNING(f'\n📡 Signal {signum} reçu, arrêt du serveur...')
        )
        raise KeyboardInterrupt()
    
    def _start_gns3_background(self):
        """Démarre le service GNS3 en arrière-plan."""
        def gns3_worker():
            """Worker thread pour le service GNS3."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Initialiser le service GNS3
                self.stdout.write('🔧 Initialisation du service GNS3...')
                result = loop.run_until_complete(gns3_central_service.initialize())
                
                if result:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Service GNS3 initialisé')
                    )
                    
                    # Démarrer les événements si activés
                    if self.enable_events:
                        self.stdout.write('⚡ Démarrage des événements temps réel...')
                        loop.run_until_complete(realtime_event_manager.start())
                        self.stdout.write(
                            self.style.SUCCESS('✅ Événements temps réel démarrés')
                        )
                    
                    # Notification de démarrage
                    ubuntu_notification_service.send_notification(
                        title="🚀 Service GNS3 + Django Démarré",
                        message=f"Serveur accessible sur http://{self.host}:{self.port}",
                        urgency='low',
                        category='system.gns3'
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'🌐 Documentation Swagger: http://{self.host}:{self.port}/swagger/')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'📖 API Root: http://{self.host}:{self.port}/api/')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'🔧 Service Central GNS3: http://{self.host}:{self.port}/api/common/')
                    )
                    
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  Service GNS3 non disponible, serveur Django seul')
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur service GNS3: {e}')
                )
                logger.error(f"Erreur dans le worker GNS3: {e}")
        
        # Démarrer le worker GNS3 en arrière-plan
        if self.enable_gns3:
            gns3_thread = threading.Thread(target=gns3_worker, daemon=True)
            gns3_thread.start()
            time.sleep(2)  # Laisser le temps au service de s'initialiser
    
    def _start_django_server(self):
        """Démarre le serveur Django."""
        self.stdout.write(
            self.style.SUCCESS(f'🌐 Démarrage du serveur Django sur {self.host}:{self.port}')
        )
        
        # Vérifier que les migrations sont appliquées
        self.stdout.write('🔍 Vérification des migrations...')
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('✅ Migrations à jour')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Problème de migrations: {e}')
            )
        
        # Collecter les fichiers statiques si nécessaire
        if not settings.DEBUG:
            self.stdout.write('📁 Collecte des fichiers statiques...')
            try:
                call_command('collectstatic', verbosity=0, interactive=False)
                self.stdout.write(
                    self.style.SUCCESS('✅ Fichiers statiques collectés')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Problème fichiers statiques: {e}')
                )
        
        # Afficher les URLs importantes
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('🎯 URLs Importantes:')
        )
        self.stdout.write(f'   📖 Documentation Swagger: http://{self.host}:{self.port}/swagger/')
        self.stdout.write(f'   📋 API Root: http://{self.host}:{self.port}/api/')
        self.stdout.write(f'   🔧 Service Central GNS3: http://{self.host}:{self.port}/api/common/')
        self.stdout.write(f'   ⚡ GNS3 Central ViewSet: http://{self.host}:{self.port}/api/common/api/gns3-central/')
        self.stdout.write(f'   📊 Événements GNS3: http://{self.host}:{self.port}/api/common/api/gns3-events/')
        self.stdout.write(f'   🔗 WebSocket GNS3: ws://{self.host}:{self.port}/ws/gns3/events/')
        self.stdout.write(f'   🎛️  Interface Admin: http://{self.host}:{self.port}/admin/')
        self.stdout.write('='*60 + '\n')
        
        # Démarrer le serveur Django
        try:
            call_command('runserver', f'{self.host}:{self.port}', verbosity=1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur serveur Django: {e}')
            )
            raise
    
    def _cleanup(self):
        """Nettoie les ressources avant l'arrêt."""
        self.stdout.write('🧹 Nettoyage des ressources...')
        
        try:
            # Arrêter le gestionnaire d'événements
            if self.enable_events:
                # Note: Dans un thread séparé, difficile d'arrêter proprement
                # En production, utiliser un gestionnaire de processus approprié
                pass
            
            # Notification d'arrêt
            ubuntu_notification_service.send_notification(
                title="🛑 Serveur Django + GNS3 Arrêté",
                message="Services arrêtés proprement",
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
    
    def _display_startup_info(self):
        """Affiche les informations de démarrage."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('🎉 Serveur Django + GNS3 Opérationnel!')
        )
        self.stdout.write('='*60)
        
        # Informations de configuration
        self.stdout.write('📋 Configuration:')
        self.stdout.write(f'   • Host: {self.host}')
        self.stdout.write(f'   • Port: {self.port}')
        self.stdout.write(f'   • Debug: {settings.DEBUG}')
        self.stdout.write(f'   • Service GNS3: {"✅ Activé" if self.enable_gns3 else "❌ Désactivé"}')
        self.stdout.write(f'   • Événements: {"✅ Activé" if self.enable_events else "❌ Désactivé"}')
        
        # Informations sur les services
        if self.enable_gns3:
            try:
                status = gns3_central_service.get_service_status()
                self.stdout.write(f'   • GNS3 Status: {status.get("status", "unknown")}')
                self.stdout.write(f'   • GNS3 Server: {status.get("gns3_server", {}).get("connected", False)}')
            except:
                self.stdout.write('   • GNS3 Status: Non disponible')
        
        self.stdout.write('\n🚀 Serveur prêt pour les requêtes!')
        self.stdout.write('   (Appuyez sur Ctrl+C pour arrêter)\n')