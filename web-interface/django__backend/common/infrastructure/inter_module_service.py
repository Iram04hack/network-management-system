"""
Service de communication inter-modules pour le NMS.
"""
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from django.conf import settings
from django.utils import timezone
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types de messages inter-modules."""
    TOPOLOGY_UPDATE = "topology_update"
    NODE_STATUS_CHANGE = "node_status_change"
    NETWORK_EVENT = "network_event"
    SECURITY_ALERT = "security_alert"
    MONITORING_DATA = "monitoring_data"
    QOS_POLICY_UPDATE = "qos_policy_update"
    CONFIGURATION_CHANGE = "configuration_change"
    SERVICE_DISCOVERY = "service_discovery"
    HEALTH_CHECK = "health_check"
    NOTIFICATION = "notification"

class ModuleInterface:
    """Interface de base pour les modules."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.subscriptions: Set[MessageType] = set()
        
    def handle_message(self, message_type: MessageType, data: Dict[str, Any], sender: str):
        """
        Traite un message reçu d'un autre module.
        
        Args:
            message_type: Type du message
            data: Données du message
            sender: Module expéditeur
        """
        pass
        
    def subscribe_to(self, message_types: List[MessageType]):
        """
        S'abonne à des types de messages.
        
        Args:
            message_types: Types de messages à écouter
        """
        self.subscriptions.update(message_types)

class InterModuleService:
    """
    Service central de communication inter-modules.
    Permet aux modules de s'envoyer des messages et de partager des données.
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleInterface] = {}
        self.docker_services: Dict[str, Dict[str, Any]] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self._lock = threading.Lock()
        
        # Initialiser la découverte des services Docker
        self._initialize_docker_services()
        
    def _initialize_docker_services(self):
        """Initialise la configuration des services Docker disponibles."""
        self.docker_services = {
            'postgresql': {
                'host': settings.DATABASES['default']['HOST'],
                'port': settings.DATABASES['default']['PORT'],
                'type': 'database',
                'health_endpoint': None,
                'description': 'Base de données PostgreSQL'
            },
            'redis': {
                'host': getattr(settings, 'REDIS_HOST', 'redis'),
                'port': getattr(settings, 'REDIS_PORT', '6379'),
                'type': 'cache',
                'health_endpoint': None,
                'description': 'Cache Redis'
            },
            'elasticsearch': {
                'host': 'elasticsearch',
                'port': '9200',
                'type': 'search',
                'health_endpoint': '/_cluster/health',
                'description': 'Moteur de recherche Elasticsearch'
            },
            'kibana': {
                'host': 'kibana',
                'port': '5601',
                'type': 'visualization',
                'health_endpoint': '/api/status',
                'description': 'Interface Kibana'
            },
            'suricata': {
                'host': 'suricata',
                'port': '3000',
                'type': 'security',
                'health_endpoint': None,
                'description': 'IDS/IPS Suricata'
            },
            'fail2ban': {
                'host': 'fail2ban',
                'port': None,
                'type': 'security',
                'health_endpoint': None,
                'description': 'Service Fail2ban'
            },
            'netdata': {
                'host': 'netdata',
                'port': '19999',
                'type': 'monitoring',
                'health_endpoint': '/api/v1/info',
                'description': 'Monitoring Netdata'
            },
            'ntopng': {
                'host': 'ntopng',
                'port': '3000',
                'type': 'monitoring',
                'health_endpoint': None,
                'description': 'Analyse de trafic ntopng'
            },
            'haproxy': {
                'host': 'haproxy',
                'port': '80',
                'type': 'load_balancer',
                'health_endpoint': '/stats',
                'description': 'Load Balancer HAProxy'
            },
            'traffic_control': {
                'host': 'traffic-control',
                'port': '8080',
                'type': 'qos',
                'health_endpoint': '/health',
                'description': 'Contrôle de trafic QoS'
            }
        }
        
        logger.info(f"Services Docker initialisés: {list(self.docker_services.keys())}")
        
    def register_module(self, module: ModuleInterface):
        """
        Enregistre un module dans le système.
        
        Args:
            module: Instance du module à enregistrer
        """
        with self._lock:
            self.modules[module.module_name] = module
            logger.info(f"Module '{module.module_name}' enregistré")
            
            # Envoyer un message de découverte de service
            self._broadcast_message(
                MessageType.SERVICE_DISCOVERY,
                {
                    'action': 'module_registered',
                    'module_name': module.module_name,
                    'subscriptions': [msg_type.value for msg_type in module.subscriptions],
                    'timestamp': timezone.now().isoformat()
                },
                sender='inter_module_service'
            )
            
    def unregister_module(self, module_name: str):
        """
        Désenregistre un module.
        
        Args:
            module_name: Nom du module à désenregistrer
        """
        with self._lock:
            if module_name in self.modules:
                del self.modules[module_name]
                logger.info(f"Module '{module_name}' désenregistré")
                
                # Envoyer un message de découverte de service
                self._broadcast_message(
                    MessageType.SERVICE_DISCOVERY,
                    {
                        'action': 'module_unregistered',
                        'module_name': module_name,
                        'timestamp': timezone.now().isoformat()
                    },
                    sender='inter_module_service'
                )
                
    def send_message(self, message_type: MessageType, data: Dict[str, Any], 
                    sender: str, target: Optional[str] = None):
        """
        Envoie un message à un module spécifique ou diffuse à tous les modules abonnés.
        
        Args:
            message_type: Type du message
            data: Données du message
            sender: Module expéditeur
            target: Module cible (None pour diffusion)
        """
        message = {
            'type': message_type,
            'data': data,
            'sender': sender,
            'target': target,
            'timestamp': timezone.now().isoformat()
        }
        
        # Ajouter à l'historique
        self._add_to_history(message)
        
        with self._lock:
            if target:
                # Envoi ciblé
                if target in self.modules:
                    try:
                        self.modules[target].handle_message(message_type, data, sender)
                        logger.debug(f"Message {message_type.value} envoyé de {sender} vers {target}")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'envoi du message vers {target}: {e}")
                else:
                    logger.warning(f"Module cible '{target}' non trouvé")
            else:
                # Diffusion à tous les modules abonnés
                self._broadcast_message(message_type, data, sender)
                
    def _broadcast_message(self, message_type: MessageType, data: Dict[str, Any], sender: str):
        """
        Diffuse un message à tous les modules abonnés.
        
        Args:
            message_type: Type du message
            data: Données du message
            sender: Module expéditeur
        """
        recipients = []
        
        for module_name, module in self.modules.items():
            if module_name != sender and message_type in module.subscriptions:
                try:
                    module.handle_message(message_type, data, sender)
                    recipients.append(module_name)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du message vers {module_name}: {e}")
                    
        logger.debug(f"Message {message_type.value} diffusé de {sender} vers {recipients}")
        
    def _add_to_history(self, message: Dict[str, Any]):
        """
        Ajoute un message à l'historique.
        
        Args:
            message: Message à ajouter
        """
        self.message_history.append(message)
        
        # Limiter la taille de l'historique
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
            
    def get_message_history(self, module_name: Optional[str] = None, 
                           message_type: Optional[MessageType] = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des messages.
        
        Args:
            module_name: Filtrer par module (None pour tous)
            message_type: Filtrer par type de message (None pour tous)
            limit: Nombre maximum de messages à retourner
            
        Returns:
            Liste des messages filtrés
        """
        history = self.message_history.copy()
        
        # Filtrer par module
        if module_name:
            history = [msg for msg in history 
                      if msg['sender'] == module_name or msg['target'] == module_name]
                      
        # Filtrer par type
        if message_type:
            history = [msg for msg in history if msg['type'] == message_type]
            
        # Limiter et retourner les plus récents
        return history[-limit:]
        
    def get_docker_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un service Docker.
        
        Args:
            service_name: Nom du service Docker
            
        Returns:
            Informations du service ou None si non trouvé
        """
        return self.docker_services.get(service_name)
        
    def get_all_docker_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Récupère toutes les informations des services Docker.
        
        Returns:
            Dictionnaire des services Docker
        """
        return self.docker_services.copy()
        
    def notify_docker_service_change(self, service_name: str, status: str, details: Dict[str, Any]):
        """
        Notifie un changement d'état d'un service Docker.
        
        Args:
            service_name: Nom du service
            status: Nouveau statut
            details: Détails supplémentaires
        """
        self.send_message(
            MessageType.SERVICE_DISCOVERY,
            {
                'action': 'docker_service_change',
                'service_name': service_name,
                'status': status,
                'details': details,
                'timestamp': timezone.now().isoformat()
            },
            sender='inter_module_service'
        )
        
    def health_check_all_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        Effectue un health check de tous les modules enregistrés.
        
        Returns:
            État de santé de tous les modules
        """
        health_status = {}
        
        with self._lock:
            for module_name, module in self.modules.items():
                try:
                    # Envoyer un ping au module
                    start_time = timezone.now()
                    
                    if hasattr(module, 'health_check'):
                        status = module.health_check()
                    else:
                        status = {'status': 'unknown', 'message': 'Pas de health check implémenté'}
                        
                    response_time = (timezone.now() - start_time).total_seconds() * 1000
                    
                    health_status[module_name] = {
                        'status': status.get('status', 'unknown'),
                        'message': status.get('message', ''),
                        'response_time_ms': response_time,
                        'last_check': timezone.now().isoformat()
                    }
                    
                except Exception as e:
                    health_status[module_name] = {
                        'status': 'error',
                        'message': str(e),
                        'response_time_ms': None,
                        'last_check': timezone.now().isoformat()
                    }
                    
        return health_status
        
    def get_topology_integration_data(self) -> Dict[str, Any]:
        """
        Récupère les données d'intégration topologique de tous les modules.
        
        Returns:
            Données consolidées de topologie
        """
        topology_data = {
            'modules': {},
            'docker_services': self.docker_services,
            'integration_status': {},
            'last_update': timezone.now().isoformat()
        }
        
        # Demander les données de topologie à chaque module
        for module_name, module in self.modules.items():
            try:
                if hasattr(module, 'get_topology_data'):
                    module_topology = module.get_topology_data()
                    topology_data['modules'][module_name] = module_topology
                    topology_data['integration_status'][module_name] = 'active'
                else:
                    topology_data['integration_status'][module_name] = 'no_topology_interface'
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la topologie du module {module_name}: {e}")
                topology_data['integration_status'][module_name] = f'error: {str(e)}'
                
        return topology_data
        
    def get_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet du service inter-modules.
        
        Returns:
            Statut du service
        """
        with self._lock:
            return {
                'registered_modules': list(self.modules.keys()),
                'docker_services': list(self.docker_services.keys()),
                'message_history_size': len(self.message_history),
                'max_history_size': self.max_history,
                'service_status': 'active',
                'last_update': timezone.now().isoformat()
            }

# Instance globale du service
inter_module_service = InterModuleService()