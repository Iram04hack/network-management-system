"""
Commande Django pour contrôler les services d'intégration GNS3.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import json

from common.infrastructure.central_topology_service import central_topology_service
from common.infrastructure.gns3_integration_service import gns3_integration_service
from common.infrastructure.inter_module_service import inter_module_service
from common.infrastructure.ubuntu_notification_service import ubuntu_notification_service


class Command(BaseCommand):
    """Commande pour contrôler les services d'intégration NMS."""
    
    help = 'Contrôle les services d\'intégration GNS3 et inter-modules'
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            'action',
            choices=[
                'status', 'start', 'stop', 'restart', 'detect', 
                'topology', 'modules', 'test-notification', 
                'health-check', 'integrate-module', 'monitor'
            ],
            help='Action à effectuer'
        )
        
        parser.add_argument(
            '--module',
            type=str,
            help='Nom du module pour l\'action integrate-module'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Intervalle de surveillance en secondes (défaut: 30)'
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Sortie au format JSON'
        )
        
    def handle(self, *args, **options):
        """Traite la commande."""
        action = options['action']
        
        try:
            if action == 'status':
                self._show_status(options.get('json', False))
            elif action == 'start':
                self._start_monitoring(options['interval'])
            elif action == 'stop':
                self._stop_monitoring()
            elif action == 'restart':
                self._restart_monitoring(options['interval'])
            elif action == 'detect':
                self._detect_gns3(options.get('json', False))
            elif action == 'topology':
                self._show_topology(options.get('json', False))
            elif action == 'modules':
                self._show_modules(options.get('json', False))
            elif action == 'test-notification':
                self._test_notification()
            elif action == 'health-check':
                self._health_check(options.get('json', False))
            elif action == 'integrate-module':
                module_name = options.get('module')
                if not module_name:
                    raise CommandError("--module est requis pour l'action integrate-module")
                self._integrate_module(module_name)
            elif action == 'monitor':
                self._continuous_monitor(options['interval'])
                
        except Exception as e:
            raise CommandError(f"Erreur lors de l'exécution de l'action '{action}': {e}")
            
    def _show_status(self, json_output=False):
        """Affiche le statut des services d'intégration."""
        self.stdout.write(self.style.HTTP_INFO("=== Statut des Services d'Intégration NMS ==="))
        
        # Statut du service central de topologie
        topology_status = central_topology_service.get_integration_status()
        
        # Statut GNS3
        gns3_status = gns3_integration_service.get_status()
        
        # Statut inter-modules
        inter_module_status = inter_module_service.get_status()
        
        # Statut notifications Ubuntu
        notification_status = ubuntu_notification_service.get_status()
        
        if json_output:
            status_data = {
                'topology_service': topology_status,
                'gns3_service': gns3_status,
                'inter_module_service': inter_module_status,
                'notification_service': notification_status,
                'timestamp': timezone.now().isoformat()
            }
            self.stdout.write(json.dumps(status_data, indent=2, ensure_ascii=False))
        else:
            self._format_status_output(topology_status, gns3_status, inter_module_status, notification_status)
            
    def _format_status_output(self, topology_status, gns3_status, inter_module_status, notification_status):
        """Formate la sortie du statut."""
        # Service Central de Topologie
        self.stdout.write(self.style.SUCCESS("📊 Service Central de Topologie:"))
        self.stdout.write(f"  • État: {topology_status['service_status']}")
        self.stdout.write(f"  • Surveillance active: {topology_status['monitoring_active']}")
        self.stdout.write(f"  • Modules intégrés: {len(topology_status['integrated_modules'])}")
        if topology_status['integrated_modules']:
            self.stdout.write(f"    - {', '.join(topology_status['integrated_modules'])}")
        
        # Service GNS3
        self.stdout.write(self.style.SUCCESS("\n🌐 Service GNS3:"))
        self.stdout.write(f"  • Client initialisé: {gns3_status['gns3_client_initialized']}")
        self.stdout.write(f"  • Serveur disponible: {gns3_status['gns3_server_available']}")
        self.stdout.write(f"  • Surveillance active: {gns3_status['monitoring_active']}")
        if gns3_status['last_detection_time']:
            self.stdout.write(f"  • Dernière détection: {gns3_status['last_detection_time']}")
        self.stdout.write(f"  • Configuration: {gns3_status['gns3_config']['host']}:{gns3_status['gns3_config']['port']}")
        
        # Service Inter-Modules
        self.stdout.write(self.style.SUCCESS("\n🔗 Service Inter-Modules:"))
        self.stdout.write(f"  • Modules enregistrés: {len(inter_module_status['registered_modules'])}")
        if inter_module_status['registered_modules']:
            self.stdout.write(f"    - {', '.join(inter_module_status['registered_modules'])}")
        self.stdout.write(f"  • Services Docker: {len(inter_module_status['docker_services'])}")
        self.stdout.write(f"  • Historique messages: {inter_module_status['message_history_size']}")
        
        # Service Notifications
        self.stdout.write(self.style.SUCCESS("\n🔔 Service Notifications Ubuntu:"))
        self.stdout.write(f"  • notify-send disponible: {notification_status['notify_send_available']}")
        self.stdout.write(f"  • Historique: {notification_status['notification_history_size']} notifications")
        
    def _start_monitoring(self, interval):
        """Démarre la surveillance."""
        self.stdout.write(f"Démarrage de la surveillance (intervalle: {interval}s)...")
        central_topology_service.start_monitoring(interval)
        self.stdout.write(self.style.SUCCESS("✅ Surveillance démarrée"))
        
    def _stop_monitoring(self):
        """Arrête la surveillance."""
        self.stdout.write("Arrêt de la surveillance...")
        central_topology_service.stop_monitoring()
        self.stdout.write(self.style.SUCCESS("✅ Surveillance arrêtée"))
        
    def _restart_monitoring(self, interval):
        """Redémarre la surveillance."""
        self.stdout.write("Redémarrage de la surveillance...")
        central_topology_service.stop_monitoring()
        central_topology_service.start_monitoring(interval)
        self.stdout.write(self.style.SUCCESS(f"✅ Surveillance redémarrée (intervalle: {interval}s)"))
        
    def _detect_gns3(self, json_output=False):
        """Force une détection GNS3."""
        self.stdout.write("Détection du serveur GNS3...")
        detection_result = gns3_integration_service.detect_gns3_server()
        
        if json_output:
            self.stdout.write(json.dumps(detection_result, indent=2, ensure_ascii=False))
        else:
            if detection_result.get('available'):
                self.stdout.write(self.style.SUCCESS("✅ Serveur GNS3 détecté:"))
                self.stdout.write(f"  • Host: {detection_result.get('host')}:{detection_result.get('port')}")
                self.stdout.write(f"  • Version: {detection_result.get('version')}")
                self.stdout.write(f"  • Projets: {detection_result.get('projects_count', 0)}")
            else:
                self.stdout.write(self.style.ERROR("❌ Serveur GNS3 non disponible:"))
                self.stdout.write(f"  • Erreur: {detection_result.get('error')}")
                
    def _show_topology(self, json_output=False):
        """Affiche la topologie consolidée."""
        self.stdout.write("Récupération de la topologie consolidée...")
        topology = central_topology_service.get_consolidated_topology()
        
        if json_output:
            self.stdout.write(json.dumps(topology, indent=2, ensure_ascii=False))
        else:
            self.stdout.write(self.style.HTTP_INFO("=== Topologie Consolidée ==="))
            
            # Topologie GNS3
            gns3_topology = topology.get('gns3_topology', [])
            self.stdout.write(f"🌐 Projets GNS3: {len(gns3_topology)}")
            for project in gns3_topology:
                self.stdout.write(f"  • {project.get('name')} ({project.get('node_count', 0)} nœuds)")
                
            # Services Docker
            docker_services = topology.get('docker_services', {})
            self.stdout.write(f"\n🐳 Services Docker: {len(docker_services)}")
            for service_name, service_info in docker_services.items():
                self.stdout.write(f"  • {service_name}: {service_info.get('description', 'N/A')}")
                
            # Modules intégrés
            modules = topology.get('modules_topology', {})
            self.stdout.write(f"\n🔧 Modules intégrés: {len(modules)}")
            for module_name in modules.keys():
                integration_status = topology.get('integration_map', {}).get(module_name, {})
                gns3_integrated = "✅" if integration_status.get('gns3_integrated') else "❌"
                self.stdout.write(f"  • {module_name}: {gns3_integrated}")
                
    def _show_modules(self, json_output=False):
        """Affiche les modules enregistrés."""
        health_status = inter_module_service.health_check_all_modules()
        
        if json_output:
            self.stdout.write(json.dumps(health_status, indent=2, ensure_ascii=False))
        else:
            self.stdout.write(self.style.HTTP_INFO("=== Modules Enregistrés ==="))
            for module_name, status in health_status.items():
                status_icon = "✅" if status.get('status') == 'ok' else "❌"
                response_time = status.get('response_time_ms')
                time_str = f" ({response_time:.1f}ms)" if response_time else ""
                self.stdout.write(f"{status_icon} {module_name}{time_str}")
                if status.get('message'):
                    self.stdout.write(f"    {status['message']}")
                    
    def _test_notification(self):
        """Teste les notifications Ubuntu."""
        self.stdout.write("Test de notification Ubuntu...")
        success = ubuntu_notification_service.test_notification()
        
        if success:
            self.stdout.write(self.style.SUCCESS("✅ Notification de test envoyée"))
        else:
            self.stdout.write(self.style.ERROR("❌ Échec de l'envoi de la notification"))
            
    def _health_check(self, json_output=False):
        """Effectue un health check complet."""
        self.stdout.write("Health check complet en cours...")
        
        # Health check des modules
        modules_health = inter_module_service.health_check_all_modules()
        
        # Statut GNS3
        gns3_available = gns3_integration_service.gns3_client and gns3_integration_service.gns3_client.is_available()
        
        # Statut notifications
        notifications_available = ubuntu_notification_service.notify_send_available
        
        health_data = {
            'overall_status': 'ok',
            'modules': modules_health,
            'gns3_available': gns3_available,
            'notifications_available': notifications_available,
            'timestamp': timezone.now().isoformat()
        }
        
        # Déterminer le statut global
        error_modules = [name for name, status in modules_health.items() if status.get('status') == 'error']
        if error_modules or not gns3_available:
            health_data['overall_status'] = 'warning'
            
        if json_output:
            self.stdout.write(json.dumps(health_data, indent=2, ensure_ascii=False))
        else:
            status_color = self.style.SUCCESS if health_data['overall_status'] == 'ok' else self.style.WARNING
            self.stdout.write(status_color(f"Statut global: {health_data['overall_status'].upper()}"))
            self.stdout.write(f"GNS3 disponible: {'✅' if gns3_available else '❌'}")
            self.stdout.write(f"Notifications Ubuntu: {'✅' if notifications_available else '❌'}")
            
            if error_modules:
                self.stdout.write(self.style.ERROR(f"Modules en erreur: {', '.join(error_modules)}"))
                
    def _integrate_module(self, module_name):
        """Intègre un module spécifique."""
        self.stdout.write(f"Intégration du module '{module_name}'...")
        
        try:
            # Tenter d'importer le module dynamiquement
            from django.utils.module_loading import import_string
            
            service_paths = [
                f"{module_name}.infrastructure.services.MainService",
                f"{module_name}.application.services.{module_name.title()}Service",
                f"{module_name}.services.{module_name.title()}Manager"
            ]
            
            service_instance = None
            for service_path in service_paths:
                try:
                    service_class = import_string(service_path)
                    service_instance = service_class()
                    break
                except ImportError:
                    continue
                    
            if service_instance:
                success = central_topology_service.integrate_module(module_name, service_instance)
                if success:
                    self.stdout.write(self.style.SUCCESS(f"✅ Module '{module_name}' intégré avec succès"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Échec de l'intégration du module '{module_name}'"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Service principal non trouvé pour le module '{module_name}'"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de l'intégration: {e}"))
            
    def _continuous_monitor(self, interval):
        """Surveillance continue avec affichage."""
        self.stdout.write(f"Surveillance continue démarrée (Ctrl+C pour arrêter)")
        self.stdout.write(f"Intervalle: {interval}s")
        
        try:
            import time
            while True:
                detection_result = gns3_integration_service.detect_gns3_server()
                status = "✅ Disponible" if detection_result.get('available') else "❌ Indisponible"
                timestamp = timezone.now().strftime("%H:%M:%S")
                
                self.stdout.write(f"[{timestamp}] GNS3: {status}", ending='\r')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write("\n\nSurveillance arrêtée")