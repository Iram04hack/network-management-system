"""
Service Central de Topologie pour l'intégration GNS3 avec tous les modules NMS.
"""
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from django.conf import settings
from django.utils import timezone
from .gns3_integration_service import gns3_integration_service
from .inter_module_service import inter_module_service, MessageType, ModuleInterface
from .ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)

class TopologyModule(ModuleInterface):
    """Module d'interface pour l'intégration topologique."""
    
    def __init__(self, module_name: str, service_instance: Any):
        super().__init__(module_name)
        self.service = service_instance
        self.gns3_data = {}
        self.last_update = None
        
        # S'abonner aux messages de topologie
        self.subscribe_to([
            MessageType.TOPOLOGY_UPDATE,
            MessageType.NODE_STATUS_CHANGE,
            MessageType.NETWORK_EVENT,
            MessageType.CONFIGURATION_CHANGE
        ])
        
    def handle_message(self, message_type: MessageType, data: Dict[str, Any], sender: str):
        """Traite les messages reçus."""
        try:
            if message_type == MessageType.TOPOLOGY_UPDATE:
                self._handle_topology_update(data, sender)
            elif message_type == MessageType.NODE_STATUS_CHANGE:
                self._handle_node_status_change(data, sender)
            elif message_type == MessageType.NETWORK_EVENT:
                self._handle_network_event(data, sender)
            elif message_type == MessageType.CONFIGURATION_CHANGE:
                self._handle_configuration_change(data, sender)
                
            logger.debug(f"Module {self.module_name} a traité le message {message_type.value} de {sender}")
            
        except Exception as e:
            logger.error(f"Erreur dans {self.module_name} lors du traitement du message {message_type.value}: {e}")
            
    def _handle_topology_update(self, data: Dict[str, Any], sender: str):
        """Traite une mise à jour de topologie."""
        self.gns3_data = data.get('topology_data', {})
        self.last_update = timezone.now()
        
        # Notifier le service spécifique du module s'il a une méthode d'intégration
        if hasattr(self.service, 'integrate_gns3_topology'):
            self.service.integrate_gns3_topology(self.gns3_data)
            
    def _handle_node_status_change(self, data: Dict[str, Any], sender: str):
        """Traite un changement de statut de nœud."""
        if hasattr(self.service, 'handle_node_status_change'):
            self.service.handle_node_status_change(data)
            
    def _handle_network_event(self, data: Dict[str, Any], sender: str):
        """Traite un événement réseau."""
        if hasattr(self.service, 'handle_network_event'):
            self.service.handle_network_event(data)
            
    def _handle_configuration_change(self, data: Dict[str, Any], sender: str):
        """Traite un changement de configuration."""
        if hasattr(self.service, 'handle_configuration_change'):
            self.service.handle_configuration_change(data)
            
    def get_topology_data(self) -> Dict[str, Any]:
        """Récupère les données de topologie du module."""
        base_data = {
            'module_name': self.module_name,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'gns3_integration': bool(self.gns3_data),
            'gns3_data': self.gns3_data
        }
        
        # Ajouter des données spécifiques au module s'il a une méthode dédiée
        if hasattr(self.service, 'get_topology_data'):
            try:
                module_specific_data = self.service.get_topology_data()
                base_data.update(module_specific_data)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des données de topologie de {self.module_name}: {e}")
                base_data['error'] = str(e)
                
        return base_data
        
    def health_check(self) -> Dict[str, Any]:
        """Effectue un health check du module."""
        status = {
            'status': 'ok',
            'message': f'Module {self.module_name} opérationnel',
            'gns3_integrated': bool(self.gns3_data),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
        
        # Health check spécifique au module s'il existe
        if hasattr(self.service, 'health_check'):
            try:
                module_health = self.service.health_check()
                status.update(module_health)
            except Exception as e:
                status['status'] = 'error'
                status['message'] = f'Erreur health check: {str(e)}'
                
        return status

class CentralTopologyService:
    """
    Service Central de Topologie qui orchestre l'intégration GNS3 
    avec tous les modules du NMS.
    """
    
    def __init__(self):
        self.integrated_modules: Dict[str, TopologyModule] = {}
        self.topology_data: Dict[str, Any] = {}
        self.is_monitoring = False
        self.monitor_interval = 30
        self._lock = threading.Lock()
        
        # Enregistrer les callbacks GNS3
        gns3_integration_service.register_detection_callback(self._on_gns3_detected)
        
        # Services disponibles pour l'intégration
        self.available_modules = {
            'monitoring': None,
            'network_management': None,
            'security_management': None,
            'qos_management': None,
            'reporting': None,
            'dashboard': None,
            'ai_assistant': None
        }
        
        logger.info("Service Central de Topologie initialisé")
        
    def integrate_module(self, module_name: str, service_instance: Any) -> bool:
        """
        Intègre un module avec le service central de topologie.
        
        Args:
            module_name: Nom du module
            service_instance: Instance du service du module
            
        Returns:
            True si l'intégration a réussi
        """
        try:
            with self._lock:
                # Créer un module d'interface topologique
                topology_module = TopologyModule(module_name, service_instance)
                
                # Enregistrer dans le système inter-modules
                inter_module_service.register_module(topology_module)
                
                # Enregistrer dans GNS3
                gns3_integration_service.register_module_service(module_name, service_instance)
                
                # Ajouter à nos modules intégrés
                self.integrated_modules[module_name] = topology_module
                self.available_modules[module_name] = service_instance
                
                logger.info(f"Module '{module_name}' intégré avec succès au Service Central de Topologie")
                
                # Envoyer notification
                ubuntu_notification_service.send_notification(
                    title="🔧 Module intégré",
                    message=f"Le module '{module_name}' a été intégré au Service Central de Topologie",
                    urgency='low',
                    category='system.integration'
                )
                
                # Si GNS3 est déjà détecté, envoyer les données existantes
                if gns3_integration_service.last_detection_time:
                    self._send_topology_update_to_module(module_name)
                    
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration du module '{module_name}': {e}")
            return False
            
    def _send_topology_update_to_module(self, module_name: str):
        """Envoie une mise à jour de topologie à un module spécifique."""
        try:
            topology_data = gns3_integration_service.get_topology_data()
            
            inter_module_service.send_message(
                MessageType.TOPOLOGY_UPDATE,
                {
                    'topology_data': topology_data,
                    'source': 'gns3',
                    'timestamp': timezone.now().isoformat()
                },
                sender='central_topology_service',
                target=module_name
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de mise à jour topologique vers {module_name}: {e}")
            
    def _on_gns3_detected(self, gns3_info: Dict[str, Any]):
        """Callback appelé lors de la détection de GNS3."""
        try:
            logger.info("GNS3 détecté - Mise à jour de la topologie pour tous les modules")
            
            # Récupérer les données de topologie
            topology_data = gns3_integration_service.get_topology_data()
            
            # Mettre à jour nos données locales
            with self._lock:
                self.topology_data = {
                    'gns3_info': gns3_info,
                    'topology': topology_data,
                    'last_update': timezone.now().isoformat()
                }
            
            # Diffuser la mise à jour à tous les modules intégrés
            inter_module_service.send_message(
                MessageType.TOPOLOGY_UPDATE,
                {
                    'gns3_info': gns3_info,
                    'topology_data': topology_data,
                    'source': 'gns3',
                    'event': 'gns3_detected',
                    'timestamp': timezone.now().isoformat()
                },
                sender='central_topology_service'
            )
            
            # Envoyer notification Ubuntu
            ubuntu_notification_service.send_gns3_detection_notification(gns3_info)
            
            # Notifier les services Docker de l'événement
            inter_module_service.notify_docker_service_change(
                'gns3_integration',
                'active',
                {
                    'gns3_version': gns3_info.get('version'),
                    'projects_count': gns3_info.get('projects_count', 0),
                    'integrated_modules': list(self.integrated_modules.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la détection GNS3: {e}")
            
    def start_monitoring(self, interval: int = 30):
        """
        Démarre la surveillance continue de la topologie.
        
        Args:
            interval: Intervalle de surveillance en secondes
        """
        if self.is_monitoring:
            logger.warning("La surveillance topologique est déjà active")
            return
            
        self.is_monitoring = True
        self.monitor_interval = interval
        
        # Démarrer la surveillance GNS3
        gns3_integration_service.start_monitoring(interval)
        
        def topology_monitor_loop():
            """Boucle de surveillance de la topologie."""
            while self.is_monitoring:
                try:
                    # Vérifier les changements de topologie
                    self._check_topology_changes()
                    
                    # Health check des modules intégrés
                    self._check_integrated_modules_health()
                    
                    time.sleep(self.monitor_interval)
                    
                except Exception as e:
                    logger.error(f"Erreur dans la boucle de surveillance topologique: {e}")
                    time.sleep(self.monitor_interval)
                    
        # Démarrer le thread de surveillance
        monitor_thread = threading.Thread(target=topology_monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info(f"Surveillance de la topologie démarrée (intervalle: {interval}s)")
        
        # Notification
        ubuntu_notification_service.send_notification(
            title="🔍 Surveillance topologique active",
            message=f"Surveillance de la topologie GNS3 démarrée (intervalle: {interval}s)",
            urgency='low',
            category='monitoring'
        )
        
    def stop_monitoring(self):
        """Arrête la surveillance de la topologie."""
        self.is_monitoring = False
        gns3_integration_service.stop_monitoring()
        
        logger.info("Surveillance de la topologie arrêtée")
        
        ubuntu_notification_service.send_notification(
            title="⏹️ Surveillance topologique arrêtée",
            message="La surveillance de la topologie GNS3 a été arrêtée",
            urgency='low',
            category='monitoring'
        )
        
    def _check_topology_changes(self):
        """Vérifie les changements dans la topologie GNS3."""
        try:
            current_topology = gns3_integration_service.get_topology_data()
            
            with self._lock:
                previous_topology = self.topology_data.get('topology', {})
                
                # Comparer les topologies (simple comparaison du nombre de projets/nœuds)
                current_projects = len(current_topology)
                previous_projects = len(previous_topology)
                
                if current_projects != previous_projects:
                    logger.info(f"Changement de topologie détecté: {previous_projects} -> {current_projects} projets")
                    
                    # Diffuser le changement
                    inter_module_service.send_message(
                        MessageType.TOPOLOGY_UPDATE,
                        {
                            'topology_data': current_topology,
                            'change_type': 'projects_count_changed',
                            'previous_count': previous_projects,
                            'current_count': current_projects,
                            'timestamp': timezone.now().isoformat()
                        },
                        sender='central_topology_service'
                    )
                    
                    # Mettre à jour nos données
                    self.topology_data['topology'] = current_topology
                    self.topology_data['last_update'] = timezone.now().isoformat()
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des changements de topologie: {e}")
            
    def _check_integrated_modules_health(self):
        """Vérifie la santé des modules intégrés."""
        try:
            health_status = inter_module_service.health_check_all_modules()
            
            # Vérifier s'il y a des modules en erreur
            error_modules = [name for name, status in health_status.items() 
                           if status.get('status') == 'error']
                           
            if error_modules:
                logger.warning(f"Modules en erreur détectés: {error_modules}")
                
                ubuntu_notification_service.send_notification(
                    title="⚠️ Modules en erreur",
                    message=f"Les modules suivants sont en erreur: {', '.join(error_modules)}",
                    urgency='normal',
                    category='monitoring.health'
                )
                
        except Exception as e:
            logger.error(f"Erreur lors du health check des modules: {e}")
            
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet de l'intégration.
        
        Returns:
            Statut de l'intégration
        """
        with self._lock:
            return {
                'service_status': 'active',
                'monitoring_active': self.is_monitoring,
                'monitor_interval': self.monitor_interval,
                'integrated_modules': list(self.integrated_modules.keys()),
                'available_modules': list(self.available_modules.keys()),
                'gns3_status': gns3_integration_service.get_status(),
                'inter_module_status': inter_module_service.get_status(),
                'topology_data': self.topology_data,
                'last_update': timezone.now().isoformat()
            }
            
    def get_consolidated_topology(self) -> Dict[str, Any]:
        """
        Récupère la topologie consolidée de tous les modules.
        
        Returns:
            Topologie consolidée
        """
        consolidated = {
            'gns3_topology': gns3_integration_service.get_topology_data(),
            'docker_services': inter_module_service.get_all_docker_services(),
            'modules_topology': {},
            'integration_map': {},
            'consolidation_time': timezone.now().isoformat()
        }
        
        # Récupérer les données de chaque module intégré
        for module_name, topology_module in self.integrated_modules.items():
            try:
                module_topology = topology_module.get_topology_data()
                consolidated['modules_topology'][module_name] = module_topology
                
                # Mapper l'intégration GNS3
                consolidated['integration_map'][module_name] = {
                    'gns3_integrated': bool(module_topology.get('gns3_data')),
                    'last_update': module_topology.get('last_update'),
                    'health_status': topology_module.health_check()
                }
                
            except Exception as e:
                logger.error(f"Erreur lors de la consolidation du module {module_name}: {e}")
                consolidated['integration_map'][module_name] = {
                    'error': str(e),
                    'gns3_integrated': False
                }
                
        return consolidated
        
    def auto_integrate_modules(self):
        """Intègre automatiquement tous les modules disponibles."""
        try:
            # Importer et intégrer les modules disponibles
            modules_to_integrate = [
                ('monitoring', 'monitoring.infrastructure.services'),
                ('network_management', 'network_management.infrastructure.services'),
                ('security_management', 'security_management.infrastructure.services'),
                ('qos_management', 'qos_management.infrastructure.services'),
                ('reporting', 'reporting.infrastructure.services'),
                ('dashboard', 'dashboard.infrastructure.services'),
                ('ai_assistant', 'ai_assistant.infrastructure.services')
            ]
            
            integrated_count = 0
            
            for module_name, service_path in modules_to_integrate:
                try:
                    # Tenter d'importer le service du module
                    from django.utils.module_loading import import_string
                    
                    # Construire le chemin du service principal
                    service_class_path = f"{service_path}.MainService"
                    
                    try:
                        service_class = import_string(service_class_path)
                        service_instance = service_class()
                        
                        if self.integrate_module(module_name, service_instance):
                            integrated_count += 1
                            
                    except ImportError:
                        logger.info(f"Service principal non trouvé pour {module_name}, tentative avec d'autres noms")
                        # Essayer d'autres noms de services communs
                        service_names = ['Service', 'Manager', 'Handler']
                        
                        for service_name in service_names:
                            try:
                                alt_path = f"{service_path}.{module_name.title()}{service_name}"
                                service_class = import_string(alt_path)
                                service_instance = service_class()
                                
                                if self.integrate_module(module_name, service_instance):
                                    integrated_count += 1
                                    break
                                    
                            except ImportError:
                                continue
                                
                except Exception as e:
                    logger.warning(f"Impossible d'intégrer automatiquement le module {module_name}: {e}")
                    
            logger.info(f"Intégration automatique terminée: {integrated_count} modules intégrés")
            
            if integrated_count > 0:
                ubuntu_notification_service.send_notification(
                    title="🔗 Intégration automatique terminée",
                    message=f"{integrated_count} modules ont été intégrés automatiquement au Service Central de Topologie",
                    urgency='low',
                    category='system.integration'
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration automatique: {e}")

# Instance globale du service
central_topology_service = CentralTopologyService()