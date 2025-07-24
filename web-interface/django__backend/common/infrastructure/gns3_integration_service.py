"""
Service d'intégration GNS3 centralisé pour tous les modules.
"""
import logging
import subprocess
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from django.conf import settings
from django.utils import timezone
from api_clients.network.gns3_client import GNS3Client
from ..application.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class GNS3IntegrationService:
    """
    Service central d'intégration GNS3 qui permet à tous les modules 
    de communiquer avec GNS3 et entre eux.
    """
    
    def __init__(self):
        self.gns3_client = None
        self.notification_service = NotificationService()
        self.is_monitoring = False
        self.last_detection_time = None
        self.detection_callbacks = []
        self.module_services = {}
        self._lock = threading.Lock()
        
        # Configuration GNS3 depuis les variables d'environnement
        self.gns3_config = {
            'host': getattr(settings, 'GNS3_HOST', 'localhost'),
            'port': getattr(settings, 'GNS3_PORT', 3080),
            'protocol': getattr(settings, 'GNS3_PROTOCOL', 'http'),
            'username': getattr(settings, 'GNS3_USERNAME', ''),
            'password': getattr(settings, 'GNS3_PASSWORD', ''),
            'verify_ssl': getattr(settings, 'GNS3_VERIFY_SSL', True),
            'timeout': getattr(settings, 'GNS3_TIMEOUT', 30)
        }
        
        # Initialiser le client GNS3
        self._initialize_gns3_client()
        
    def _initialize_gns3_client(self):
        """Initialise le client GNS3."""
        try:
            self.gns3_client = GNS3Client(
                host=self.gns3_config['host'],
                port=self.gns3_config['port'],
                protocol=self.gns3_config['protocol'],
                username=self.gns3_config['username'],
                password=self.gns3_config['password'],
                verify_ssl=self.gns3_config['verify_ssl'],
                timeout=self.gns3_config['timeout'],
                use_mock=False
            )
            logger.info("Client GNS3 initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client GNS3: {e}")
            
    def register_module_service(self, module_name: str, service_instance: Any):
        """
        Enregistre un service de module pour la communication inter-modules.
        
        Args:
            module_name: Nom du module
            service_instance: Instance du service du module
        """
        with self._lock:
            self.module_services[module_name] = service_instance
            logger.info(f"Service du module '{module_name}' enregistré")
            
    def get_module_service(self, module_name: str) -> Any:
        """
        Récupère le service d'un module enregistré.
        
        Args:
            module_name: Nom du module
            
        Returns:
            Instance du service ou None si non trouvé
        """
        return self.module_services.get(module_name)
        
    def register_detection_callback(self, callback: Callable):
        """
        Enregistre un callback à appeler lors de la détection de GNS3.
        
        Args:
            callback: Fonction à appeler avec les informations GNS3
        """
        self.detection_callbacks.append(callback)
        logger.info(f"Callback de détection enregistré: {callback.__name__}")
        
    def detect_gns3_server(self) -> Dict[str, Any]:
        """
        Détecte et vérifie la disponibilité du serveur GNS3.
        
        Returns:
            Dictionnaire avec les informations de détection
        """
        try:
            if not self.gns3_client:
                return {
                    'available': False,
                    'error': 'Client GNS3 non initialisé',
                    'detection_time': timezone.now()
                }
                
            # Vérifier la disponibilité
            is_available = self.gns3_client.is_available()
            
            if is_available:
                # Récupérer la version
                version_info = self.gns3_client.get_version()
                
                detection_info = {
                    'available': True,
                    'host': self.gns3_config['host'],
                    'port': self.gns3_config['port'],
                    'version': version_info.get('version', 'Inconnue'),
                    'detection_time': timezone.now(),
                    'projects_count': len(self.gns3_client.get_projects() or [])
                }
                
                # Mettre à jour le temps de dernière détection
                self.last_detection_time = detection_info['detection_time']
                
                # Envoyer notification système Ubuntu
                self._send_ubuntu_notification(
                    "Serveur GNS3 détecté",
                    f"Serveur GNS3 v{detection_info['version']} disponible sur {self.gns3_config['host']}:{self.gns3_config['port']}"
                )
                
                # Envoyer notification dans l'application
                self.notification_service.send_notification_to_admins(
                    "Serveur GNS3 détecté",
                    f"Le serveur GNS3 v{detection_info['version']} a été détecté et est disponible. "
                    f"Nombre de projets: {detection_info['projects_count']}",
                    level='info',
                    source='gns3_integration'
                )
                
                # Appeler les callbacks enregistrés
                for callback in self.detection_callbacks:
                    try:
                        callback(detection_info)
                    except Exception as e:
                        logger.error(f"Erreur dans le callback {callback.__name__}: {e}")
                        
                logger.info(f"Serveur GNS3 détecté: {detection_info}")
                return detection_info
                
            else:
                return {
                    'available': False,
                    'error': 'Serveur GNS3 non disponible',
                    'host': self.gns3_config['host'],
                    'port': self.gns3_config['port'],
                    'detection_time': timezone.now()
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la détection GNS3: {e}")
            return {
                'available': False,
                'error': str(e),
                'detection_time': timezone.now()
            }
            
    def _send_ubuntu_notification(self, title: str, message: str):
        """
        Envoie une notification système Ubuntu 24.04.
        
        Args:
            title: Titre de la notification
            message: Message de la notification
        """
        try:
            # Utiliser notify-send pour les notifications Ubuntu
            subprocess.run([
                'notify-send',
                '--app-name=NMS',
                '--icon=network-workgroup',
                '--category=network',
                '--urgency=normal',
                title,
                message
            ], check=False, timeout=5)
            
            logger.info(f"Notification Ubuntu envoyée: {title}")
            
        except Exception as e:
            logger.warning(f"Impossible d'envoyer la notification Ubuntu: {e}")
            
    def start_monitoring(self, interval: int = 30):
        """
        Démarre la surveillance continue du serveur GNS3.
        
        Args:
            interval: Intervalle de vérification en secondes
        """
        if self.is_monitoring:
            logger.warning("La surveillance GNS3 est déjà active")
            return
            
        self.is_monitoring = True
        
        def monitor_loop():
            while self.is_monitoring:
                try:
                    detection_info = self.detect_gns3_server()
                    
                    # Log de l'état
                    if detection_info['available']:
                        logger.debug(f"GNS3 surveillé: serveur disponible")
                    else:
                        logger.warning(f"GNS3 surveillé: serveur indisponible - {detection_info.get('error', 'Erreur inconnue')}")
                        
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Erreur dans la boucle de surveillance GNS3: {e}")
                    time.sleep(interval)
                    
        # Démarrer le thread de surveillance
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info(f"Surveillance GNS3 démarrée (intervalle: {interval}s)")
        
    def stop_monitoring(self):
        """Arrête la surveillance du serveur GNS3."""
        self.is_monitoring = False
        logger.info("Surveillance GNS3 arrêtée")
        
    def get_topology_data(self) -> List[Dict[str, Any]]:
        """
        Récupère les données de topologie de tous les projets GNS3.
        
        Returns:
            Liste des projets avec leurs nœuds et liens
        """
        try:
            if not self.gns3_client or not self.gns3_client.is_available():
                return []
                
            projects = self.gns3_client.get_projects() or []
            topology_data = []
            
            for project in projects:
                project_id = project.get('project_id')
                if not project_id:
                    continue
                    
                # Récupérer les nœuds du projet
                nodes = self.gns3_client.get_nodes(project_id) or []
                
                project_data = {
                    'project_id': project_id,
                    'name': project.get('name', 'Projet sans nom'),
                    'status': project.get('status', 'unknown'),
                    'nodes': nodes,
                    'node_count': len(nodes)
                }
                
                topology_data.append(project_data)
                
            return topology_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la topologie: {e}")
            return []
            
    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails complets d'un projet GNS3.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Détails du projet ou None si erreur
        """
        try:
            if not self.gns3_client or not self.gns3_client.is_available():
                return None
                
            project = self.gns3_client.get_project(project_id)
            if not project:
                return None
                
            nodes = self.gns3_client.get_nodes(project_id) or []
            
            return {
                'project': project,
                'nodes': nodes,
                'topology': self._build_topology_graph(nodes)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du projet {project_id}: {e}")
            return None
            
    def _build_topology_graph(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Construit un graphe de topologie à partir des nœuds.
        
        Args:
            nodes: Liste des nœuds
            
        Returns:
            Graphe de topologie
        """
        graph = {
            'nodes': [],
            'edges': [],
            'statistics': {
                'total_nodes': len(nodes),
                'node_types': {},
                'status_counts': {}
            }
        }
        
        for node in nodes:
            # Ajouter le nœud au graphe
            graph['nodes'].append({
                'id': node.get('node_id'),
                'name': node.get('name'),
                'type': node.get('node_type'),
                'status': node.get('status'),
                'x': node.get('x', 0),
                'y': node.get('y', 0)
            })
            
            # Compter les types et statuts
            node_type = node.get('node_type', 'unknown')
            status = node.get('status', 'unknown')
            
            graph['statistics']['node_types'][node_type] = graph['statistics']['node_types'].get(node_type, 0) + 1
            graph['statistics']['status_counts'][status] = graph['statistics']['status_counts'].get(status, 0) + 1
            
        return graph
        
    def notify_modules(self, event_type: str, data: Dict[str, Any]):
        """
        Notifie tous les modules enregistrés d'un événement.
        
        Args:
            event_type: Type d'événement
            data: Données de l'événement
        """
        with self._lock:
            for module_name, service in self.module_services.items():
                try:
                    if hasattr(service, 'handle_gns3_event'):
                        service.handle_gns3_event(event_type, data)
                        logger.debug(f"Événement {event_type} envoyé au module {module_name}")
                except Exception as e:
                    logger.error(f"Erreur lors de la notification du module {module_name}: {e}")
                    
    def get_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet du service d'intégration.
        
        Returns:
            Statut du service
        """
        return {
            'gns3_client_initialized': self.gns3_client is not None,
            'gns3_server_available': self.gns3_client.is_available() if self.gns3_client else False,
            'monitoring_active': self.is_monitoring,
            'last_detection_time': self.last_detection_time.isoformat() if self.last_detection_time else None,
            'registered_modules': list(self.module_services.keys()),
            'detection_callbacks_count': len(self.detection_callbacks),
            'gns3_config': {
                'host': self.gns3_config['host'],
                'port': self.gns3_config['port'],
                'protocol': self.gns3_config['protocol']
            }
        }

# Instance globale du service
gns3_integration_service = GNS3IntegrationService()