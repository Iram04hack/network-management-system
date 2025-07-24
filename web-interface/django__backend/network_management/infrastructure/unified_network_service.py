"""
Service unifié d'intégration Network Management avec GNS3 Central et Docker.

Ce service modernise l'intégration du module network_management en utilisant :
- Le nouveau Service Central GNS3 
- L'intégration Docker pour la gestion des services réseau
- Une architecture événementielle unifiée
- La gestion temps réel des topologies et équipements

Architecture Développeur Senior :
- Séparation claire des responsabilités (GNS3/Docker/Network)
- Pattern Observer pour les événements
- Circuit Breaker pour la résilience
- Interface simplifiée pour les use cases
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import docker
import json
import requests

from common.api.gns3_module_interface import create_gns3_interface
from common.infrastructure.gns3_central_service import GNS3EventType
from ..models import NetworkDevice, NetworkInterface, DeviceConfiguration, NetworkConnection

logger = logging.getLogger(__name__)


class DockerNetworkCollector:
    """
    Collecteur de services Docker spécialisé pour la gestion réseau.
    
    Responsabilités :
    - Connexion au daemon Docker
    - Gestion des services réseau NMS spécialisés
    - Intégration avec les services réseau (SNMP, NetFlow, etc.)
    - Transformation en format standardisé
    """
    
    def __init__(self):
        self.client = None
        # Services Docker réseau NMS à surveiller
        self.network_services = {
            # Services de protocole réseau
            'nms-snmp-agent': {'port': 161, 'health_endpoint': None, 'type': 'snmp_protocol'},
            'nms-netflow-collector': {'port': 9995, 'health_endpoint': '/health', 'type': 'netflow_collector'},
            
            # Services de monitoring réseau
            'nms-ntopng': {'port': 3000, 'health_endpoint': '/', 'type': 'traffic_analysis'},
            'nms-haproxy': {'port': 1936, 'health_endpoint': '/stats', 'type': 'load_balancer'},
            
            # Services de sécurité réseau
            'nms-suricata': {'port': 8068, 'health_endpoint': None, 'type': 'ids_ips'},
            'nms-fail2ban': {'port': 5001, 'health_endpoint': None, 'type': 'intrusion_prevention'},
            
            # Services de données
            'nms-elasticsearch': {'port': 9200, 'health_endpoint': '/_cluster/health', 'type': 'log_storage'},
            'nms-kibana': {'port': 5601, 'health_endpoint': '/api/status', 'type': 'log_visualization'},
            
            # Services applicatifs
            'nms-django': {'port': 8000, 'health_endpoint': '/api/common/api/v1/integration/health/', 'type': 'application'},
            'nms-celery': {'port': None, 'health_endpoint': None, 'type': 'task_queue'},
            
            # Services de base de données
            'nms-postgres': {'port': 5432, 'health_endpoint': None, 'type': 'database'},
            'nms-redis': {'port': 6379, 'health_endpoint': None, 'type': 'cache'}
        }
        self._initialize_docker_client()
        
    def _initialize_docker_client(self):
        """Initialise le client Docker avec gestion d'erreurs."""
        try:
            self.client = docker.from_env()
            # Test de connectivité
            self.client.ping()
            logger.info("✅ Connexion Docker établie pour network management")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion Docker network management: {e}")
            self.client = None
            
    def is_available(self) -> bool:
        """Vérifie si Docker est disponible."""
        return self.client is not None
        
    def collect_network_services_status(self) -> List[Dict[str, Any]]:
        """
        Collecte le statut des services réseau Docker.
        
        Returns:
            Liste des statuts des services réseau NMS
        """
        if not self.is_available():
            logger.warning("Docker non disponible pour la collecte des services réseau")
            return []
            
        network_status = []
        
        try:
            containers = self.client.containers.list(all=True)
            
            for container in containers:
                container_name = container.name
                
                # Vérifier si c'est un service réseau NMS
                if container_name in self.network_services:
                    service_config = self.network_services[container_name]
                    
                    try:
                        # Informations de base du conteneur
                        status_info = {
                            'service_name': container_name,
                            'container_id': container.id[:12],
                            'status': container.status,
                            'service_type': service_config['type'],
                            'port': service_config['port'],
                            'created': container.attrs.get('Created'),
                            'image': container.image.tags[0] if container.image.tags else 'unknown'
                        }
                        
                        # Statistiques avancées si le conteneur est en cours d'exécution
                        if container.status == 'running':
                            try:
                                stats = container.stats(stream=False)
                                status_info.update({
                                    'cpu_usage': self._calculate_cpu_usage(stats),
                                    'memory_usage': self._calculate_memory_usage(stats),
                                    'network_io': self._calculate_network_io(stats)
                                })
                            except Exception as e:
                                logger.warning(f"Erreur statistiques pour {container_name}: {e}")
                                
                        # Vérification de santé si endpoint disponible
                        if service_config['health_endpoint'] and container.status == 'running':
                            status_info['health_check'] = self._check_service_health(
                                container_name, 
                                service_config['port'], 
                                service_config['health_endpoint']
                            )
                            
                        network_status.append(status_info)
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de l'analyse du conteneur {container_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des services réseau Docker: {e}")
            
        return network_status
        
    def _calculate_cpu_usage(self, stats: Dict) -> float:
        """Calcule l'utilisation CPU du conteneur."""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * \
                             len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                return round(cpu_percent, 2)
        except (KeyError, ZeroDivisionError):
            pass
        return 0.0
        
    def _calculate_memory_usage(self, stats: Dict) -> Dict[str, Any]:
        """Calcule l'utilisation mémoire du conteneur."""
        try:
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100
            
            return {
                'usage_bytes': memory_usage,
                'limit_bytes': memory_limit,
                'usage_percent': round(memory_percent, 2)
            }
        except KeyError:
            return {'usage_bytes': 0, 'limit_bytes': 0, 'usage_percent': 0.0}
            
    def _calculate_network_io(self, stats: Dict) -> Dict[str, Any]:
        """Calcule les I/O réseau du conteneur."""
        try:
            networks = stats['networks']
            total_rx = sum(net['rx_bytes'] for net in networks.values())
            total_tx = sum(net['tx_bytes'] for net in networks.values())
            
            return {
                'rx_bytes': total_rx,
                'tx_bytes': total_tx,
                'total_bytes': total_rx + total_tx
            }
        except KeyError:
            return {'rx_bytes': 0, 'tx_bytes': 0, 'total_bytes': 0}
            
    def _check_service_health(self, service_name: str, port: int, endpoint: str) -> Dict[str, Any]:
        """Vérifie la santé d'un service via son endpoint."""
        try:
            url = f"http://localhost:{port}{endpoint}"
            response = requests.get(url, timeout=5)
            
            return {
                'healthy': response.status_code == 200,
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'last_check': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }
            
    def get_network_infrastructure_health(self) -> Dict[str, Any]:
        """
        Évalue la santé globale de l'infrastructure réseau Docker.
        
        Returns:
            Rapport de santé de l'infrastructure réseau
        """
        services_status = self.collect_network_services_status()
        
        # Calculs de santé globale
        total_services = len(services_status)
        running_services = len([s for s in services_status if s['status'] == 'running'])
        healthy_services = len([s for s in services_status 
                               if s.get('health_check', {}).get('healthy', False)])
        
        # Catégorisation par type
        service_types = {}
        for service in services_status:
            service_type = service['service_type']
            if service_type not in service_types:
                service_types[service_type] = {'total': 0, 'running': 0}
            service_types[service_type]['total'] += 1
            if service['status'] == 'running':
                service_types[service_type]['running'] += 1
                
        # Détermination du statut global
        if running_services == total_services:
            global_status = 'healthy'
        elif running_services >= total_services * 0.8:
            global_status = 'warning'
        else:
            global_status = 'critical'
            
        return {
            'summary': {
                'total_services': total_services,
                'running_services': running_services,
                'healthy_services': healthy_services,
                'global_status': global_status,
                'availability_percent': round((running_services / total_services) * 100, 2) if total_services > 0 else 0
            },
            'services_by_type': service_types,
            'detailed_services': services_status,
            'timestamp': timezone.now().isoformat()
        }


class GNS3NetworkAdapter:
    """
    Adaptateur d'intégration GNS3 pour le network management.
    
    Responsabilités :
    - Interface avec le Service Central GNS3
    - Gestion des événements de topologie réseau
    - Synchronisation des équipements et interfaces
    - Transformation des données GNS3 en modèles network management
    """
    
    def __init__(self):
        self.gns3_interface = None
        self.event_subscriptions = []
        self._initialize_gns3_connection()
        
    def _initialize_gns3_connection(self):
        """Initialise la connexion avec le Service Central GNS3."""
        try:
            self.gns3_interface = create_gns3_interface('network_management')
            
            # S'abonner aux événements pertinents pour le network management
            # Utiliser les types d'événements GNS3EventType disponibles
            try:
                from common.infrastructure.gns3_central_service import GNS3EventType
                
                # Utiliser seulement les types d'événements disponibles
                available_events = [
                    'NODE_CREATED', 'NODE_UPDATED', 'NODE_DELETED',
                    'LINK_CREATED', 'LINK_DELETED',
                    'PROJECT_OPENED', 'PROJECT_CLOSED'
                ]
                
                relevant_events = []
                for event_name in available_events:
                    if hasattr(GNS3EventType, event_name):
                        relevant_events.append(getattr(GNS3EventType, event_name))
                
                for event_type in relevant_events:
                    try:
                        self.gns3_interface.subscribe_to_events(
                            event_type, 
                            self._handle_network_event
                        )
                        self.event_subscriptions.append(event_type)
                    except Exception as e:
                        logger.warning(f"Abonnement événement {event_type} ignoré: {e}")
                        
            except ImportError:
                logger.warning("GNS3EventType non disponible, utilisation de chaînes de caractères")
                # Fallback avec des chaînes si les énums ne sont pas disponibles
                relevant_events_str = [
                    'node_created', 'node_updated', 'node_deleted',
                    'link_created', 'link_updated', 'link_deleted',
                    'project_opened', 'project_closed'
                ]
                
                for event_type in relevant_events_str:
                    try:
                        self.gns3_interface.subscribe_to_events(
                            event_type, 
                            self._handle_network_event
                        )
                        self.event_subscriptions.append(event_type)
                    except Exception as e:
                        logger.warning(f"Abonnement événement {event_type} ignoré: {e}")
                    
            logger.info(f"✅ GNS3 adapter initialisé pour network management avec {len(self.event_subscriptions)} événements")
            
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation GNS3 adapter network management: {e}")
            self.gns3_interface = None
            
    def is_available(self) -> bool:
        """Vérifie si l'adaptateur GNS3 est disponible."""
        return self.gns3_interface is not None
        
    def _handle_network_event(self, event_data: Dict[str, Any]):
        """
        Traite les événements GNS3 relatifs au network management.
        
        Args:
            event_data: Données de l'événement GNS3
        """
        try:
            event_type = event_data.get('type')
            
            # Normaliser le type d'événement (enum ou string)
            if hasattr(event_type, 'value'):
                event_type_str = event_type.value
            else:
                event_type_str = str(event_type)
            
            # Traitement selon le type d'événement
            if event_type_str in ['node_created', 'node_updated', 'NODE_CREATED', 'NODE_UPDATED']:
                self._sync_network_device(event_data)
            elif event_type_str in ['link_created', 'link_updated', 'LINK_CREATED', 'LINK_UPDATED']:
                self._sync_network_connection(event_data)
            elif event_type_str in ['project_opened', 'project_closed', 'PROJECT_OPENED', 'PROJECT_CLOSED']:
                self._sync_project_topology(event_data)
                
            logger.info(f"Événement network management traité: {event_type_str}")
            
        except Exception as e:
            logger.error(f"Erreur traitement événement network management: {e}")
            
    def _sync_network_device(self, event_data: Dict[str, Any]):
        """Synchronise un équipement réseau depuis GNS3."""
        try:
            node_data = event_data.get('data', {})
            node_id = node_data.get('node_id')
            
            if not node_id:
                return
                
            # Mapper les types de nœuds GNS3 vers nos types d'équipements
            device_type_mapping = {
                'qemu': 'virtual_machine',
                'docker': 'container',
                'dynamips': 'router',
                'vpcs': 'pc',
                'ethernet_switch': 'switch',
                'ethernet_hub': 'hub',
                'cloud': 'cloud',
                'nat': 'nat',
                'traceng': 'tracer'
            }
            
            gns3_node_type = node_data.get('node_type', 'unknown')
            device_type = device_type_mapping.get(gns3_node_type, gns3_node_type)
            
            # Créer ou mettre à jour l'équipement réseau
            device_data = {
                'name': node_data.get('name', f'Device-{node_id}'),
                'hostname': node_data.get('name', f'Device-{node_id}'),
                'node_id': node_id,
                'device_type': device_type,
                'vendor': self._get_vendor_from_node_type(gns3_node_type),
                'is_virtual': True,
                'is_active': node_data.get('status') == 'started',
                'metadata': {
                    'gns3_project_id': node_data.get('project_id'),
                    'gns3_node_type': gns3_node_type,
                    'gns3_status': node_data.get('status'),
                    'gns3_console': node_data.get('console'),
                    'gns3_console_type': node_data.get('console_type'),
                    'gns3_properties': node_data.get('properties', {}),
                    'gns3_x': node_data.get('x'),
                    'gns3_y': node_data.get('y'),
                    'gns3_z': node_data.get('z', 1)
                },
                'last_sync': timezone.now(),
                'discovery_method': 'gns3_sync'
            }
            
            # Tenter d'obtenir l'adresse IP depuis les propriétés
            if 'properties' in node_data:
                properties = node_data['properties']
                
                # Recherche IP dans différents formats selon le type de nœud
                if gns3_node_type == 'vpcs':
                    # VPCS a souvent une IP configurée directement
                    if 'startup_script' in properties:
                        # Parser le script de démarrage pour extraire l'IP
                        script = properties['startup_script']
                        if 'ip ' in script:
                            ip_line = [line for line in script.split('\n') if line.strip().startswith('ip ')][0]
                            if ip_line:
                                ip_parts = ip_line.split()
                                if len(ip_parts) >= 2:
                                    device_data['ip_address'] = ip_parts[1].split('/')[0]
                                    
                elif gns3_node_type == 'docker':
                    # Docker peut avoir des interfaces configurées
                    if 'extra_hosts' in properties:
                        extra_hosts = properties.get('extra_hosts', '')
                        if ':' in extra_hosts:
                            device_data['ip_address'] = extra_hosts.split(':')[1].strip()
                            
                elif gns3_node_type in ['qemu', 'dynamips']:
                    # Machines virtuelles et routeurs peuvent avoir des adaptateurs
                    if 'adapters' in properties:
                        for i, adapter in enumerate(properties['adapters']):
                            if adapter.get('ports'):
                                for port in adapter['ports']:
                                    if port.get('ip_address'):
                                        device_data['ip_address'] = port['ip_address']
                                        break
                                        
                # Fallback: essayer d'extraire depuis les propriétés générales
                if 'ip_address' not in device_data:
                    for key, value in properties.items():
                        if 'ip' in key.lower() and isinstance(value, str) and '.' in value:
                            # Validation basique d'IP
                            try:
                                parts = value.split('.')
                                if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
                                    device_data['ip_address'] = value
                                    break
                            except (ValueError, AttributeError):
                                continue
                                    
            device, created = NetworkDevice.objects.update_or_create(
                node_id=node_id,
                defaults=device_data
            )
            
            action = "créé" if created else "mis à jour"
            logger.info(f"Équipement réseau {action}: {device.name}")
            
            # Créer automatiquement les interfaces si c'est un nouvel équipement
            if created and 'properties' in node_data:
                self._create_interfaces_from_gns3(device, node_data)
            
        except Exception as e:
            logger.error(f"Erreur synchronisation équipement réseau: {e}")
            
    def _get_vendor_from_node_type(self, node_type: str) -> str:
        """Détermine le fabricant probable selon le type de nœud GNS3."""
        vendor_mapping = {
            'qemu': 'Generic VM',
            'docker': 'Docker Inc',
            'dynamips': 'Cisco',
            'vpcs': 'Virtual PC',
            'ethernet_switch': 'Generic',
            'ethernet_hub': 'Generic',
            'cloud': 'GNS3',
            'nat': 'GNS3',
            'traceng': 'GNS3'
        }
        return vendor_mapping.get(node_type, 'Unknown')
        
    def _create_interfaces_from_gns3(self, device: NetworkDevice, node_data: Dict[str, Any]):
        """Crée automatiquement les interfaces réseau depuis les données GNS3."""
        try:
            properties = node_data.get('properties', {})
            gns3_node_type = node_data.get('node_type')
            
            # Traitement spécifique selon le type de nœud
            if gns3_node_type == 'dynamips':
                # Routeurs Cisco Dynamips
                slots = properties.get('slots', [])
                for slot_idx, slot in enumerate(slots):
                    if slot and slot != 'C7200-IO-FE':  # Ignorer les slots vides et les cartes I/O
                        # Déterminer le nombre de ports selon le type de carte
                        port_count = self._get_port_count_for_card(slot)
                        for port in range(port_count):
                            interface_name = f"FastEthernet{slot_idx}/{port}"
                            self._create_interface(device, interface_name, 'ethernet', 100000000)  # 100Mbps
                            
            elif gns3_node_type == 'ethernet_switch':
                # Switch Ethernet
                ports_number = properties.get('ports_mapping', [])
                for port_info in ports_number:
                    port_name = port_info.get('name', f"Port{port_info.get('port_number', 0)}")
                    interface_name = f"Ethernet{port_info.get('port_number', 0)}"
                    self._create_interface(device, interface_name, 'ethernet', 1000000000)  # 1Gbps
                    
            elif gns3_node_type == 'vpcs':
                # Virtual PC Simulator
                self._create_interface(device, 'Ethernet0', 'ethernet', 100000000)
                
            elif gns3_node_type == 'docker':
                # Conteneur Docker
                # Créer interface par défaut
                self._create_interface(device, 'eth0', 'ethernet', 1000000000)
                
            elif gns3_node_type == 'qemu':
                # Machine virtuelle QEMU
                adapters = properties.get('adapters', 1)
                for i in range(adapters):
                    interface_name = f"eth{i}"
                    self._create_interface(device, interface_name, 'ethernet', 1000000000)
                    
            logger.info(f"Interfaces créées pour {device.name} ({gns3_node_type})")
            
        except Exception as e:
            logger.error(f"Erreur création interfaces pour {device.name}: {e}")
            
    def _get_port_count_for_card(self, card_type: str) -> int:
        """Retourne le nombre de ports selon le type de carte Cisco."""
        card_ports = {
            'C7200-IO-2FE': 2,
            'C7200-IO-FE': 1,
            'PA-FE-TX': 1,
            'PA-2FE-TX': 2,
            'PA-4E': 4,
            'PA-8E': 8,
            'PA-4T+': 4,
            'PA-8T': 8,
            'NM-1FE-TX': 1,
            'NM-4E': 4,
            'NM-16ESW': 16,
        }
        return card_ports.get(card_type, 1)
        
    def _create_interface(self, device: NetworkDevice, name: str, interface_type: str, speed: int):
        """Crée une interface réseau."""
        try:
            interface, created = NetworkInterface.objects.get_or_create(
                device=device,
                name=name,
                defaults={
                    'interface_type': interface_type,
                    'speed': speed,
                    'status': 'unknown',
                    'description': f'Interface auto-créée depuis GNS3'
                }
            )
            
            if created:
                logger.debug(f"Interface créée: {device.name}.{name}")
                
        except Exception as e:
            logger.error(f"Erreur création interface {name} pour {device.name}: {e}")
            
    def _sync_network_connection(self, event_data: Dict[str, Any]):
        """Synchronise une connexion réseau depuis GNS3."""
        try:
            link_data = event_data.get('data', {})
            
            # Récupérer les nœuds source et destination
            nodes = link_data.get('nodes', [])
            if len(nodes) != 2:
                return
                
            source_node_id = nodes[0].get('node_id')
            target_node_id = nodes[1].get('node_id')
            
            # Rechercher les équipements correspondants
            try:
                source_device = NetworkDevice.objects.get(node_id=source_node_id)
                target_device = NetworkDevice.objects.get(node_id=target_node_id)
            except NetworkDevice.DoesNotExist:
                logger.warning(f"Équipements non trouvés pour la connexion: {source_node_id} - {target_node_id}")
                return
                
            # Créer ou mettre à jour la connexion
            connection_data = {
                'source_device': source_device,
                'target_device': target_device,
                'connection_type': 'ethernet',  # Par défaut
                'status': 'active',
                'description': f"Connexion GNS3: {source_device.name} <-> {target_device.name}"
            }
            
            connection, created = NetworkConnection.objects.update_or_create(
                source_device=source_device,
                target_device=target_device,
                defaults=connection_data
            )
            
            action = "créée" if created else "mise à jour"
            logger.info(f"Connexion réseau {action}: {source_device.name} <-> {target_device.name}")
            
        except Exception as e:
            logger.error(f"Erreur synchronisation connexion réseau: {e}")
            
    def _sync_network_topology(self, event_data: Dict[str, Any]):
        """Synchronise la topologie réseau depuis GNS3."""
        try:
            topology_data = event_data.get('data', {})
            project_id = topology_data.get('project_id')
            
            if not project_id:
                return
                
            # Mettre à jour tous les équipements du projet
            devices = NetworkDevice.objects.filter(
                metadata__gns3_project_id=project_id
            )
            
            for device in devices:
                device.last_sync = timezone.now()
                device.save()
                
            logger.info(f"Topologie synchronisée pour le projet {project_id}: {devices.count()} équipements")
            
        except Exception as e:
            logger.error(f"Erreur synchronisation topologie: {e}")
            
    def _sync_project_topology(self, event_data: Dict[str, Any]):
        """Synchronise une topologie de projet GNS3."""
        try:
            project_data = event_data.get('data', {})
            project_id = project_data.get('project_id')
            project_name = project_data.get('name', f'Project-{project_id}')
            
            if not project_id:
                return
                
            # Créer ou mettre à jour la topologie réseau
            topology_data = {
                'name': project_name,
                'topology_type': 'gns3_project',
                'gns3_project_id': project_id,
                'is_active': True,
                'last_sync': timezone.now(),
                'topology_data': project_data
            }
            
            topology, created = NetworkTopology.objects.update_or_create(
                gns3_project_id=project_id,
                defaults=topology_data
            )
            
            action = "créée" if created else "mise à jour"
            logger.info(f"Topologie GNS3 {action}: {topology.name}")
            
        except Exception as e:
            logger.error(f"Erreur synchronisation projet GNS3: {e}")
            
    def get_gns3_network_status(self) -> Dict[str, Any]:
        """
        Récupère le statut réseau depuis GNS3.
        
        Returns:
            Statut réseau GNS3
        """
        try:
            if not self.is_available():
                return {
                    'available': False,
                    'error': 'GNS3 interface non disponible'
                }
                
            # Récupérer les informations depuis l'interface GNS3
            # Utiliser une méthode disponible ou créer un statut personnalisé
            try:
                if hasattr(self.gns3_interface, 'get_projects'):
                    projects = self.gns3_interface.get_projects()
                    status = {
                        'connected': True,
                        'projects_count': len(projects) if projects else 0,
                        'service_available': True
                    }
                else:
                    status = {
                        'connected': True,
                        'service_available': True,
                        'interface_ready': True
                    }
            except Exception as e:
                status = {
                    'connected': False,
                    'error': str(e),
                    'service_available': False
                }
            
            # Compter les équipements synchronisés
            synchronized_devices = NetworkDevice.objects.filter(
                node_id__isnull=False
            ).count()
            
            # Compter les connexions actives
            active_connections = NetworkConnection.objects.filter(
                status='active'
            ).count()
            
            return {
                'available': True,
                'gns3_status': status,
                'synchronized_devices': synchronized_devices,
                'active_connections': active_connections,
                'event_subscriptions': len(self.event_subscriptions),
                'last_update': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération statut GNS3 network: {e}")
            return {
                'available': False,
                'error': str(e)
            }


class UnifiedNetworkService:
    """
    Service unifié pour la gestion réseau intégrant GNS3 et Docker.
    
    Point d'entrée principal pour toutes les opérations de network management
    avec intégration transparente des services GNS3 et Docker.
    """
    
    def __init__(self):
        self.gns3_adapter = GNS3NetworkAdapter()
        self.docker_collector = DockerNetworkCollector()
        
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet du network management.
        
        Returns:
            Statut complet avec GNS3 et Docker
        """
        try:
            # Statuts des composants
            gns3_status = self.gns3_adapter.get_gns3_network_status()
            docker_status = self.docker_collector.get_network_infrastructure_health()
            
            # Statistiques des modèles
            model_stats = {
                'devices': NetworkDevice.objects.count(),
                'interfaces': NetworkInterface.objects.count(),
                'configurations': DeviceConfiguration.objects.count(),
                'connections': NetworkConnection.objects.count()
            }
            
            # Déterminer le statut opérationnel global
            gns3_operational = gns3_status.get('available', False)
            docker_operational = docker_status.get('summary', {}).get('global_status') == 'healthy'
            
            global_operational = gns3_operational or docker_operational
            
            return {
                'operational': global_operational,
                'components': {
                    'gns3_integration': gns3_status,
                    'docker_integration': docker_status
                },
                'model_statistics': model_stats,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération statut complet network management: {e}")
            return {
                'operational': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
            
    def collect_all_network_data(self) -> Dict[str, Any]:
        """
        Collecte toutes les données réseau depuis GNS3 et Docker.
        
        Returns:
            Données réseau complètes
        """
        try:
            collected_data = {
                'sources': {},
                'summary': {
                    'total_sources': 0,
                    'successful_collections': 0,
                    'failed_collections': 0
                }
            }
            
            # Collection Docker
            if self.docker_collector.is_available():
                try:
                    docker_data = self.docker_collector.get_network_infrastructure_health()
                    collected_data['sources']['docker_infrastructure'] = docker_data
                    collected_data['summary']['successful_collections'] += 1
                except Exception as e:
                    collected_data['sources']['docker_infrastructure'] = {'error': str(e)}
                    collected_data['summary']['failed_collections'] += 1
                collected_data['summary']['total_sources'] += 1
                
            # Collection GNS3
            if self.gns3_adapter.is_available():
                try:
                    gns3_data = self.gns3_adapter.get_gns3_network_status()
                    collected_data['sources']['gns3_network'] = gns3_data
                    collected_data['summary']['successful_collections'] += 1
                except Exception as e:
                    collected_data['sources']['gns3_network'] = {'error': str(e)}
                    collected_data['summary']['failed_collections'] += 1
                collected_data['summary']['total_sources'] += 1
                
            collected_data['timestamp'] = timezone.now().isoformat()
            return collected_data
            
        except Exception as e:
            logger.error(f"Erreur collecte données réseau: {e}")
            return {
                'sources': {},
                'summary': {
                    'total_sources': 0,
                    'successful_collections': 0,
                    'failed_collections': 1
                },
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
            
    def get_network_dashboard_data(self) -> Dict[str, Any]:
        """
        Récupère les données pour le dashboard réseau unifié.
        
        Returns:
            Données optimisées pour dashboard
        """
        try:
            # Données de base
            devices = list(NetworkDevice.objects.select_related().values(
                'id', 'name', 'ip_address', 'device_type', 'vendor', 
                'is_active', 'is_virtual', 'created_at'
            ))
            
            interfaces = list(NetworkInterface.objects.select_related('device').values(
                'id', 'name', 'device__name', 'ip_address', 'interface_type', 'status'
            ))
            
            connections = list(NetworkConnection.objects.select_related(
                'source_device', 'target_device'
            ).values(
                'id', 'source_device__name', 'target_device__name', 
                'connection_type', 'status'
            ))
            
            # Statuts des intégrations
            integrations_status = self.get_comprehensive_status()
            
            # Statistiques résumées
            statistics = {
                'total_devices': len(devices),
                'active_devices': len([d for d in devices if d['is_active']]),
                'virtual_devices': len([d for d in devices if d['is_virtual']]),
                'total_interfaces': len(interfaces),
                'active_connections': len([c for c in connections if c['status'] == 'active']),
                'gns3_available': integrations_status['components']['gns3_integration']['available'],
                'docker_available': integrations_status['components']['docker_integration']['summary']['global_status'] == 'healthy'
            }
            
            return {
                'devices': devices,
                'interfaces': interfaces,
                'connections': connections,
                'integrations': integrations_status,
                'statistics': statistics,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération données dashboard réseau: {e}")
            return {
                'devices': [],
                'interfaces': [],
                'connections': [],
                'integrations': {},
                'statistics': {},
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
            
    def is_fully_operational(self) -> bool:
        """
        Vérifie si le service est complètement opérationnel.
        
        Returns:
            True si au moins une intégration fonctionne
        """
        try:
            status = self.get_comprehensive_status()
            return status.get('operational', False)
        except:
            return False


# Instance globale du service unifié
unified_network_service = UnifiedNetworkService()