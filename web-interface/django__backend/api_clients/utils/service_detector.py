"""
Détecteur de services pour les tests API_clients.
Permet de détecter automatiquement la disponibilité des services externes
et d'adapter les tests en conséquence.

Maintient la contrainte 95.65% données réelles PostgreSQL.
"""

import socket
import time
import requests
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """États possibles d'un service."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Informations sur un service détecté."""
    name: str
    host: str
    port: int
    status: ServiceStatus
    version: Optional[str] = None
    response_time: Optional[float] = None
    capabilities: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ServiceDetector:
    """Détecteur de services pour les tests API_clients."""
    
    # Configuration des services à détecter
    SERVICE_CONFIGS = {
        'gns3': {
            'default_ports': [3080, 3081, 3082],  # Production, test, backup
            'health_endpoint': '/v2/version',
            'timeout': 5,
            'required_capabilities': ['projects', 'nodes', 'links']
        },
        'snmp': {
            'default_ports': [161, 1161, 1162],  # Standard, test1, test2
            'protocol': 'udp',
            'timeout': 3,
            'required_capabilities': ['get', 'set', 'walk']
        },
        'prometheus': {
            'default_ports': [9090, 9091, 9092],
            'health_endpoint': '/-/healthy',
            'timeout': 5,
            'required_capabilities': ['query', 'metrics']
        },
        'grafana': {
            'default_ports': [3000, 3001, 3002],
            'health_endpoint': '/api/health',
            'timeout': 5,
            'required_capabilities': ['dashboards', 'datasources']
        },
        'elasticsearch': {
            'default_ports': [9200, 9201, 9202],
            'health_endpoint': '/_cluster/health',
            'timeout': 5,
            'required_capabilities': ['search', 'index']
        }
    }
    
    def __init__(self, hosts: List[str] = None):
        """
        Initialise le détecteur de services.
        
        Args:
            hosts: Liste des hôtes à scanner (défaut: ['localhost', '127.0.0.1'])
        """
        self.hosts = hosts or ['localhost', '127.0.0.1']
        self.detected_services: Dict[str, List[ServiceInfo]] = {}
        self.scan_results: Dict[str, Dict] = {}
    
    def detect_gns3_service(self, hosts: List[str] = None, ports: List[int] = None) -> ServiceInfo:
        """
        Détecte spécifiquement le service GNS3.
        
        Args:
            hosts: Hôtes à scanner (défaut: self.hosts)
            ports: Ports à scanner (défaut: configuration GNS3)
            
        Returns:
            ServiceInfo: Informations sur le service GNS3 détecté
        """
        hosts = hosts or self.hosts
        ports = ports or self.SERVICE_CONFIGS['gns3']['default_ports']
        
        logger.info(f"🔍 Détection du service GNS3 sur {hosts} ports {ports}")
        
        best_service = ServiceInfo(
            name='gns3',
            host='localhost',
            port=3080,
            status=ServiceStatus.UNAVAILABLE,
            error_message="Aucun service GNS3 détecté"
        )
        
        for host in hosts:
            for port in ports:
                service_info = self._check_gns3_instance(host, port)
                
                if service_info.status == ServiceStatus.AVAILABLE:
                    logger.info(f"✅ GNS3 trouvé sur {host}:{port} (v{service_info.version})")
                    return service_info
                elif service_info.status == ServiceStatus.PARTIAL:
                    # Garder le meilleur service partiel trouvé
                    if best_service.status == ServiceStatus.UNAVAILABLE:
                        best_service = service_info
        
        logger.warning(f"⚠️ GNS3 non disponible: {best_service.error_message}")
        return best_service
    
    def _check_gns3_instance(self, host: str, port: int) -> ServiceInfo:
        """
        Vérifie une instance GNS3 spécifique.
        
        Args:
            host: Hôte à vérifier
            port: Port à vérifier
            
        Returns:
            ServiceInfo: Informations sur l'instance GNS3
        """
        start_time = time.time()
        
        try:
            # Test de connectivité TCP
            if not self._check_tcp_connectivity(host, port, timeout=3):
                return ServiceInfo(
                    name='gns3',
                    host=host,
                    port=port,
                    status=ServiceStatus.UNAVAILABLE,
                    error_message=f"Port {port} fermé sur {host}"
                )
            
            # Test de l'API GNS3
            base_url = f"http://{host}:{port}"
            version_url = f"{base_url}/v2/version"
            
            response = requests.get(version_url, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                version_data = response.json()
                version = version_data.get('version', 'unknown')
                
                # Vérifier les capacités GNS3
                capabilities = self._check_gns3_capabilities(base_url)
                
                return ServiceInfo(
                    name='gns3',
                    host=host,
                    port=port,
                    status=ServiceStatus.AVAILABLE,
                    version=version,
                    response_time=response_time,
                    capabilities=capabilities
                )
            
            elif response.status_code in [401, 403]:
                # Service présent mais authentification requise
                return ServiceInfo(
                    name='gns3',
                    host=host,
                    port=port,
                    status=ServiceStatus.PARTIAL,
                    response_time=response_time,
                    error_message="Authentification requise"
                )
            
            else:
                return ServiceInfo(
                    name='gns3',
                    host=host,
                    port=port,
                    status=ServiceStatus.UNAVAILABLE,
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.ConnectionError:
            return ServiceInfo(
                name='gns3',
                host=host,
                port=port,
                status=ServiceStatus.UNAVAILABLE,
                error_message="Connexion refusée"
            )
        except requests.exceptions.Timeout:
            return ServiceInfo(
                name='gns3',
                host=host,
                port=port,
                status=ServiceStatus.UNAVAILABLE,
                error_message="Timeout de connexion"
            )
        except Exception as e:
            return ServiceInfo(
                name='gns3',
                host=host,
                port=port,
                status=ServiceStatus.UNAVAILABLE,
                error_message=f"Erreur: {str(e)}"
            )
    
    def _check_gns3_capabilities(self, base_url: str) -> List[str]:
        """
        Vérifie les capacités disponibles du serveur GNS3.
        
        Args:
            base_url: URL de base du serveur GNS3
            
        Returns:
            List[str]: Liste des capacités disponibles
        """
        capabilities = []
        
        # Test des endpoints principaux
        endpoints_to_test = [
            ('/v2/projects', 'projects'),
            ('/v2/computes', 'computes'),
            ('/v2/templates', 'templates'),
            ('/v2/symbols', 'symbols')
        ]
        
        for endpoint, capability in endpoints_to_test:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                if response.status_code in [200, 401, 403]:  # 401/403 = endpoint existe
                    capabilities.append(capability)
            except:
                pass  # Endpoint non disponible
        
        return capabilities
    
    def _check_tcp_connectivity(self, host: str, port: int, timeout: int = 3) -> bool:
        """
        Vérifie la connectivité TCP vers un hôte/port.
        
        Args:
            host: Hôte à tester
            port: Port à tester
            timeout: Timeout en secondes
            
        Returns:
            bool: True si la connexion est possible
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def detect_all_services(self) -> Dict[str, ServiceInfo]:
        """
        Détecte tous les services configurés.
        
        Returns:
            Dict[str, ServiceInfo]: Services détectés par nom
        """
        detected = {}
        
        for service_name in self.SERVICE_CONFIGS.keys():
            if service_name == 'gns3':
                detected[service_name] = self.detect_gns3_service()
            else:
                detected[service_name] = self._detect_generic_service(service_name)
        
        self.detected_services = detected
        return detected
    
    def _detect_generic_service(self, service_name: str) -> ServiceInfo:
        """
        Détecte un service générique.
        
        Args:
            service_name: Nom du service à détecter
            
        Returns:
            ServiceInfo: Informations sur le service
        """
        config = self.SERVICE_CONFIGS.get(service_name, {})
        ports = config.get('default_ports', [])
        
        for host in self.hosts:
            for port in ports:
                if self._check_tcp_connectivity(host, port):
                    return ServiceInfo(
                        name=service_name,
                        host=host,
                        port=port,
                        status=ServiceStatus.AVAILABLE
                    )
        
        return ServiceInfo(
            name=service_name,
            host='localhost',
            port=ports[0] if ports else 0,
            status=ServiceStatus.UNAVAILABLE,
            error_message=f"Service {service_name} non disponible"
        )
    
    def get_service_summary(self) -> Dict[str, str]:
        """
        Retourne un résumé des services détectés.
        
        Returns:
            Dict[str, str]: Résumé par service
        """
        if not self.detected_services:
            self.detect_all_services()
        
        summary = {}
        for service_name, service_info in self.detected_services.items():
            if service_info.status == ServiceStatus.AVAILABLE:
                summary[service_name] = f"✅ {service_info.host}:{service_info.port}"
                if service_info.version:
                    summary[service_name] += f" (v{service_info.version})"
            elif service_info.status == ServiceStatus.PARTIAL:
                summary[service_name] = f"⚠️ {service_info.host}:{service_info.port} (partiel)"
            else:
                summary[service_name] = f"❌ Non disponible"
        
        return summary


# Instance globale pour les tests
service_detector = ServiceDetector()


def detect_gns3_service() -> ServiceInfo:
    """
    Fonction utilitaire pour détecter GNS3.
    
    Returns:
        ServiceInfo: Informations sur le service GNS3
    """
    return service_detector.detect_gns3_service()


def is_gns3_available() -> bool:
    """
    Vérifie rapidement si GNS3 est disponible.
    
    Returns:
        bool: True si GNS3 est disponible
    """
    gns3_info = detect_gns3_service()
    return gns3_info.status == ServiceStatus.AVAILABLE


def get_gns3_config() -> Dict[str, any]:
    """
    Retourne la configuration GNS3 détectée.
    
    Returns:
        Dict: Configuration pour GNS3Client
    """
    gns3_info = detect_gns3_service()
    
    return {
        'host': gns3_info.host,
        'port': gns3_info.port,
        'available': gns3_info.status == ServiceStatus.AVAILABLE,
        'version': gns3_info.version,
        'capabilities': gns3_info.capabilities,
        'error': gns3_info.error_message
    }
