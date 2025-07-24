"""
API avancée pour la découverte et collecte d'informations complètes sur les équipements GNS3.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import asyncio
import json
import socket
import subprocess
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

from ..infrastructure.gns3_integration_service import gns3_integration_service
from api_clients.network.snmp_client import SNMPClient, SNMPCredentials, SNMPVersion
from api_clients.network.gns3_client import GNS3Client

# Schémas Swagger
equipment_detail_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'equipment_id': openapi.Schema(type=openapi.TYPE_STRING),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'type': openapi.Schema(type=openapi.TYPE_STRING),
        'status': openapi.Schema(type=openapi.TYPE_STRING),
        'project_info': openapi.Schema(type=openapi.TYPE_OBJECT),
        'network_info': openapi.Schema(type=openapi.TYPE_OBJECT),
        'hardware_info': openapi.Schema(type=openapi.TYPE_OBJECT),
        'interfaces': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'snmp_data': openapi.Schema(type=openapi.TYPE_OBJECT),
        'console_info': openapi.Schema(type=openapi.TYPE_OBJECT),
        'performance_metrics': openapi.Schema(type=openapi.TYPE_OBJECT),
        'configuration': openapi.Schema(type=openapi.TYPE_OBJECT),
        'discovery_timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

class EquipmentDiscoveryService:
    """Service avancé de découverte d'équipements."""
    
    def __init__(self):
        self.gns3_client = GNS3Client()
        self.snmp_client = None  # Sera initialisé par IP lors de l'utilisation
        
    async def discover_equipment_details(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Découvre tous les détails possibles d'un équipement.
        
        Args:
            project_id: ID du projet GNS3
            node_id: ID du nœud/équipement
            
        Returns:
            Informations complètes de l'équipement
        """
        equipment_data = {
            'equipment_id': node_id,
            'project_id': project_id,
            'discovery_timestamp': timezone.now().isoformat(),
            'discovery_status': 'in_progress'
        }
        
        try:
            # 1. Informations de base GNS3
            basic_info = await self._get_gns3_basic_info(project_id, node_id)
            equipment_data.update(basic_info)
            
            # 2. Informations réseau détaillées
            network_info = await self._discover_network_info(equipment_data)
            equipment_data['network_info'] = network_info
            
            # 3. Informations SNMP si disponible
            snmp_data = await self._discover_snmp_info(equipment_data)
            equipment_data['snmp_data'] = snmp_data
            
            # 4. Informations de performance
            performance_data = await self._discover_performance_metrics(equipment_data)
            equipment_data['performance_metrics'] = performance_data
            
            # 5. Configuration et capacités
            config_data = await self._discover_configuration(equipment_data)
            equipment_data['configuration'] = config_data
            
            # 6. Informations de console
            console_info = await self._discover_console_info(project_id, node_id)
            equipment_data['console_info'] = console_info
            
            # 7. Liens et topologie
            topology_info = await self._discover_topology_links(project_id, node_id)
            equipment_data['topology_links'] = topology_info
            
            equipment_data['discovery_status'] = 'completed'
            equipment_data['discovery_completion_time'] = timezone.now().isoformat()
            
        except Exception as e:
            equipment_data['discovery_status'] = 'failed'
            equipment_data['error'] = str(e)
            
        return equipment_data
        
    async def _get_gns3_basic_info(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """Récupère les informations de base depuis GNS3."""
        try:
            node_data = self.gns3_client.get_node(project_id, node_id)
            project_data = self.gns3_client.get_project(project_id)
            
            return {
                'name': node_data.get('name', 'Unknown'),
                'node_type': node_data.get('node_type', 'unknown'),
                'status': node_data.get('status', 'unknown'),
                'compute_id': node_data.get('compute_id'),
                'x': node_data.get('x', 0),
                'y': node_data.get('y', 0),
                'z': node_data.get('z', 1),
                'width': node_data.get('width', 60),
                'height': node_data.get('height', 45),
                'symbol': node_data.get('symbol'),
                'label': node_data.get('label', {}),
                'properties': node_data.get('properties', {}),
                'project_info': {
                    'project_name': project_data.get('name', 'Unknown'),
                    'project_status': project_data.get('status', 'unknown'),
                    'auto_start': project_data.get('auto_start', False),
                    'auto_open': project_data.get('auto_open', False),
                    'auto_close': project_data.get('auto_close', True)
                },
                'command_line': node_data.get('command_line', ''),
                'environment': node_data.get('environment', ''),
                'ports': node_data.get('ports', []),
                'custom_adapters': node_data.get('custom_adapters', [])
            }
            
        except Exception as e:
            return {'error': f'Erreur récupération GNS3: {str(e)}'}
            
    async def _discover_network_info(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Découvre les informations réseau de l'équipement."""
        network_info = {
            'interfaces': [],
            'ip_addresses': [],
            'mac_addresses': [],
            'vlans': [],
            'routing_info': {},
            'connectivity_tests': {}
        }
        
        try:
            # Analyser les ports GNS3
            ports = equipment_data.get('ports', [])
            for port in ports:
                interface_info = {
                    'name': port.get('name', 'Unknown'),
                    'adapter_number': port.get('adapter_number', 0),
                    'port_number': port.get('port_number', 0),
                    'adapter_type': port.get('adapter_type', 'unknown'),
                    'link_type': port.get('link_type', 'unknown'),
                    'short_name': port.get('short_name', ''),
                    'data_link_types': port.get('data_link_types', {}),
                    'connected': False,
                    'link_info': None
                }
                
                # Vérifier si le port est connecté
                if 'link_type' in port and port['link_type'] != 'none':
                    interface_info['connected'] = True
                    
                network_info['interfaces'].append(interface_info)
                
            # Extraire les adresses IP depuis les propriétés
            properties = equipment_data.get('properties', {})
            
            # Pour les équipements VPCS
            if equipment_data.get('node_type') == 'vpcs':
                startup_script = properties.get('startup_script', '')
                if startup_script:
                    ip_matches = re.findall(r'ip (\d+\.\d+\.\d+\.\d+)', startup_script)
                    network_info['ip_addresses'].extend(ip_matches)
                
                # 🔄 SYNCHRONISATION DHCP pour VPCS
                project_id = equipment_data.get('project_id')
                node_id = equipment_data.get('equipment_id')
                if project_id and node_id:
                    dhcp_ips = await self._get_dhcp_configured_ips(project_id, node_id, equipment_data)
                    network_info['ip_addresses'].extend(dhcp_ips)
                    
                    # Également essayer la console pour VPCS
                    console_ips = await self._get_ips_from_console(project_id, node_id, equipment_data)
                    network_info['ip_addresses'].extend(console_ips)
                    
            # Pour les routeurs/switches avec config
            elif equipment_data.get('node_type') in ['qemu', 'dynamips']:
                # 🔧 CORRECTION: Extraire vraiment les IPs depuis les configs
                await self._extract_real_ips_from_configs(equipment_data, network_info)
                
                # Essayer d'obtenir les IPs via l'API GNS3 directement
                project_id = equipment_data.get('project_id')
                node_id = equipment_data.get('equipment_id')
                if project_id and node_id:
                    gns3_ips = await self._get_ips_from_gns3_api(project_id, node_id)
                    network_info['ip_addresses'].extend(gns3_ips)
                    
                    # NOUVEAU: Tenter la découverte via console pour les IPs configurées par DHCP
                    console_ips = await self._get_ips_from_console(project_id, node_id, equipment_data)
                    network_info['ip_addresses'].extend(console_ips)
                    
                    # 🔄 SYNCHRONISATION DHCP: Récupérer les IPs configurées automatiquement
                    dhcp_ips = await self._get_dhcp_configured_ips(project_id, node_id, equipment_data)
                    network_info['ip_addresses'].extend(dhcp_ips)
                    
            # Pour les équipements IOU (switches)
            elif equipment_data.get('node_type') == 'iou':
                project_id = equipment_data.get('project_id')
                node_id = equipment_data.get('equipment_id')
                if project_id and node_id:
                    # Tenter la découverte via console pour les switches IOU
                    console_ips = await self._get_ips_from_console(project_id, node_id, equipment_data)
                    network_info['ip_addresses'].extend(console_ips)
                    
                    # 🔄 SYNCHRONISATION DHCP: Récupérer les IPs configurées automatiquement
                    dhcp_ips = await self._get_dhcp_configured_ips(project_id, node_id, equipment_data)
                    network_info['ip_addresses'].extend(dhcp_ips)
            
            # 🧹 Nettoyer et dédupliquer les IPs découvertes
            unique_ips = []
            for ip in network_info['ip_addresses']:
                if ip and ip not in unique_ips and ip != '0.0.0.0':
                    unique_ips.append(ip)
            network_info['ip_addresses'] = unique_ips
            
            logger.info(f"📊 IPs finales découvertes pour {equipment_data.get('name', 'Unknown')}: {unique_ips}")
                    
            # Test de connectivité basique
            for ip in network_info['ip_addresses']:
                if ip:
                    connectivity = await self._test_connectivity(ip)
                    network_info['connectivity_tests'][ip] = connectivity
                    
        except Exception as e:
            network_info['error'] = str(e)
            
        return network_info
        
    async def _discover_snmp_info(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tente de découvrir les informations SNMP."""
        snmp_data = {
            'snmp_available': False,
            'community_tested': [],
            'system_info': {},
            'interfaces_snmp': [],
            'performance_counters': {},
            'vendor_specific': {}
        }
        
        try:
            # Récupérer les IPs potentielles
            network_info = equipment_data.get('network_info', {})
            ip_addresses = network_info.get('ip_addresses', [])
            
            # Communautés SNMP communes à tester
            communities = ['public', 'private', 'cisco', 'admin', 'monitor']
            
            for ip in ip_addresses:
                if not ip:
                    continue
                    
                for community in communities:
                    try:
                        # Test SNMP avec timeout court
                        credentials = SNMPCredentials(version=SNMPVersion.V2C, community=community)
                        snmp_client = SNMPClient(ip, credentials=credentials)
                        snmp_result = snmp_client.get_system_info()
                        
                        if snmp_result['success']:
                            snmp_data['snmp_available'] = True
                            snmp_data['active_ip'] = ip
                            snmp_data['active_community'] = community
                            snmp_data['system_info'] = snmp_result
                            
                            # Collecter plus d'informations SNMP
                            interfaces_result = snmp_client.get_interfaces_info()
                            if interfaces_result['success']:
                                snmp_data['interfaces_snmp'] = interfaces_result['interfaces']
                                
                            # Métriques de performance SNMP
                            performance_result = snmp_client.get_performance_metrics()
                            if performance_result['success']:
                                snmp_data['performance_counters'] = performance_result['metrics']
                                
                            break  # Arrêter si une communauté fonctionne
                            
                    except Exception as e:
                        snmp_data['community_tested'].append({
                            'ip': ip,
                            'community': community,
                            'error': str(e)
                        })
                        
                if snmp_data['snmp_available']:
                    break  # Arrêter si SNMP fonctionne
                    
        except Exception as e:
            snmp_data['error'] = str(e)
            
        return snmp_data
        
    async def _test_connectivity(self, ip: str, timeout: int = 2) -> Dict[str, Any]:
        """Teste la connectivité réseau vers une IP."""
        connectivity = {
            'ip': ip,
            'ping_success': False,
            'response_time_ms': None,
            'traceroute': [],
            'port_scan': {}
        }
        
        try:
            # Test ping
            import subprocess
            ping_result = subprocess.run(
                ['ping', '-c', '1', '-W', str(timeout), ip],
                capture_output=True,
                text=True,
                timeout=timeout + 1
            )
            
            if ping_result.returncode == 0:
                connectivity['ping_success'] = True
                
                # Extraire le temps de réponse
                output = ping_result.stdout
                time_match = re.search(r'time=(\d+\.?\d*)', output)
                if time_match:
                    connectivity['response_time_ms'] = float(time_match.group(1))
                    
            # Test de ports communs
            common_ports = [22, 23, 80, 161, 443, 8080]
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, port))
                    connectivity['port_scan'][port] = result == 0
                    sock.close()
                except Exception:
                    connectivity['port_scan'][port] = False
                    
        except Exception as e:
            connectivity['error'] = str(e)
            
        return connectivity
        
    async def _discover_performance_metrics(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Découvre les métriques de performance."""
        performance = {
            'cpu_usage': None,
            'memory_usage': None,
            'disk_usage': None,
            'network_throughput': {},
            'system_load': None,
            'uptime': None,
            'process_count': None,
            'error_counters': {}
        }
        
        try:
            # Si SNMP est disponible, utiliser les métriques SNMP
            snmp_data = equipment_data.get('snmp_data', {})
            if snmp_data.get('snmp_available'):
                snmp_performance = snmp_data.get('performance_counters', {})
                performance.update(snmp_performance)
                
            # Métriques spécifiques par type de nœud
            node_type = equipment_data.get('node_type')
            if node_type == 'qemu':
                performance.update(await self._get_qemu_metrics(equipment_data))
            elif node_type == 'docker':
                performance.update(await self._get_docker_metrics(equipment_data))
            elif node_type == 'dynamips':
                performance.update(await self._get_dynamips_metrics(equipment_data))
                
        except Exception as e:
            performance['error'] = str(e)
            
        return performance
        
    async def _get_qemu_metrics(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère les métriques spécifiques QEMU."""
        qemu_metrics = {
            'vm_type': 'qemu',
            'emulated_architecture': None,
            'allocated_memory': None,
            'allocated_cpus': None,
            'disk_images': []
        }
        
        try:
            properties = equipment_data.get('properties', {})
            qemu_metrics.update({
                'emulated_architecture': properties.get('platform'),
                'allocated_memory': properties.get('ram'),
                'allocated_cpus': properties.get('cpus'),
                'boot_priority': properties.get('boot_priority'),
                'cpu_throttling': properties.get('cpu_throttling'),
                'process_priority': properties.get('process_priority')
            })
            
            # Informations sur les disques
            for i in range(4):  # QEMU supporte jusqu'à 4 disques
                disk_key = f'hd{chr(97+i)}_disk_image'
                if disk_key in properties:
                    qemu_metrics['disk_images'].append({
                        'slot': f'hd{chr(97+i)}',
                        'image': properties[disk_key],
                        'interface': properties.get(f'hd{chr(97+i)}_disk_interface', 'ide')
                    })
                    
        except Exception as e:
            qemu_metrics['error'] = str(e)
            
        return qemu_metrics
        
    async def _get_docker_metrics(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère les métriques spécifiques Docker."""
        docker_metrics = {
            'container_type': 'docker',
            'image': None,
            'container_id': None,
            'environment_vars': {},
            'volumes': [],
            'networks': []
        }
        
        try:
            properties = equipment_data.get('properties', {})
            docker_metrics.update({
                'image': properties.get('image'),
                'container_id': properties.get('container_id'),
                'start_command': properties.get('start_command'),
                'environment': properties.get('environment'),
                'extra_hosts': properties.get('extra_hosts'),
                'extra_volumes': properties.get('extra_volumes')
            })
            
        except Exception as e:
            docker_metrics['error'] = str(e)
            
        return docker_metrics
        
    async def _get_dynamips_metrics(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère les métriques spécifiques Dynamips (Cisco)."""
        dynamips_metrics = {
            'simulator_type': 'dynamips',
            'platform': None,
            'chassis': None,
            'ios_image': None,
            'ram': None,
            'nvram': None,
            'startup_config': None,
            'private_config': None
        }
        
        try:
            properties = equipment_data.get('properties', {})
            dynamips_metrics.update({
                'platform': properties.get('platform'),
                'chassis': properties.get('chassis'),
                'ios_image': properties.get('image'),
                'ram': properties.get('ram'),
                'nvram': properties.get('nvram'),
                'startup_config': properties.get('startup_config'),
                'private_config': properties.get('private_config'),
                'auto_delete_disks': properties.get('auto_delete_disks'),
                'disk0': properties.get('disk0'),
                'disk1': properties.get('disk1')
            })
            
        except Exception as e:
            dynamips_metrics['error'] = str(e)
            
        return dynamips_metrics
        
    async def _discover_configuration(self, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Découvre les informations de configuration."""
        config_data = {
            'startup_config': None,
            'running_config': None,
            'configuration_files': [],
            'scripts': [],
            'capabilities': [],
            'supported_features': []
        }
        
        try:
            properties = equipment_data.get('properties', {})
            node_type = equipment_data.get('node_type')
            
            # Configuration selon le type
            if node_type == 'vpcs':
                config_data['startup_script'] = properties.get('startup_script')
                config_data['capabilities'] = ['basic_ip', 'ping', 'traceroute', 'dhcp_client']
                
            elif node_type in ['qemu', 'vmware']:
                config_data['capabilities'] = ['full_os', 'routing', 'switching', 'services']
                config_data['boot_files'] = {
                    'kernel_image': properties.get('kernel_image'),
                    'kernel_command_line': properties.get('kernel_command_line'),
                    'initrd': properties.get('initrd')
                }
                
            elif node_type == 'dynamips':
                config_data['startup_config'] = properties.get('startup_config')
                config_data['private_config'] = properties.get('private_config')
                config_data['capabilities'] = ['cisco_ios', 'routing', 'switching', 'acl', 'qos']
                
            elif node_type == 'docker':
                config_data['capabilities'] = ['linux_services', 'networking', 'applications']
                config_data['docker_config'] = {
                    'image': properties.get('image'),
                    'start_command': properties.get('start_command'),
                    'environment': properties.get('environment')
                }
                
            # Features supportées selon les adaptateurs
            adapters = equipment_data.get('custom_adapters', [])
            for adapter in adapters:
                adapter_type = adapter.get('adapter_type')
                if adapter_type:
                    config_data['supported_features'].append(f'adapter_{adapter_type}')
                    
        except Exception as e:
            config_data['error'] = str(e)
            
        return config_data
        
    async def _discover_console_info(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """Découvre les informations de console."""
        console_info = {
            'console_available': False,
            'console_type': None,
            'console_host': None,
            'console_port': None,
            'console_auto_start': False,
            'telnet_access': False,
            'vnc_access': False
        }
        
        try:
            console_data = self.gns3_client.get_node_console(project_id, node_id)
            
            console_info.update({
                'console_available': bool(console_data.get('console_port')),
                'console_type': console_data.get('console_type'),
                'console_host': console_data.get('console_host'),
                'console_port': console_data.get('console_port'),
                'console_auto_start': console_data.get('console_auto_start', False)
            })
            
            # Test d'accès console
            if console_info['console_available']:
                console_host = console_info['console_host'] or 'localhost'
                console_port = console_info['console_port']
                
                if console_info['console_type'] == 'telnet':
                    connectivity = await self._test_connectivity(console_host)
                    console_info['telnet_access'] = connectivity['port_scan'].get(console_port, False)
                elif console_info['console_type'] == 'vnc':
                    connectivity = await self._test_connectivity(console_host)
                    console_info['vnc_access'] = connectivity['port_scan'].get(console_port, False)
                    
        except Exception as e:
            console_info['error'] = str(e)
            
        return console_info
        
    async def _discover_topology_links(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """Découvre les liens topologiques."""
        topology_info = {
            'connected_links': [],
            'neighbor_nodes': [],
            'network_segments': [],
            'link_statistics': {
                'total_links': 0,
                'active_links': 0,
                'link_types': {}
            }
        }
        
        try:
            # Récupérer tous les liens du projet
            links = self.gns3_client.list_links(project_id)
            
            node_links = []
            neighbor_nodes = set()
            
            for link in links:
                nodes = link.get('nodes', [])
                
                # Vérifier si ce nœud est impliqué dans le lien
                node_in_link = any(node.get('node_id') == node_id for node in nodes)
                
                if node_in_link:
                    node_links.append(link)
                    topology_info['link_statistics']['total_links'] += 1
                    
                    # Identifier les nœuds voisins
                    for node in nodes:
                        if node.get('node_id') != node_id:
                            neighbor_nodes.add(node.get('node_id'))
                            
                    # Statistiques par type de lien
                    link_type = link.get('link_type', 'unknown')
                    if link_type not in topology_info['link_statistics']['link_types']:
                        topology_info['link_statistics']['link_types'][link_type] = 0
                    topology_info['link_statistics']['link_types'][link_type] += 1
                    
            topology_info['connected_links'] = node_links
            topology_info['neighbor_nodes'] = list(neighbor_nodes)
            
            # Récupérer les détails des nœuds voisins
            neighbor_details = []
            for neighbor_id in neighbor_nodes:
                try:
                    neighbor_info = self.gns3_client.get_node(project_id, neighbor_id)
                    neighbor_details.append({
                        'node_id': neighbor_id,
                        'name': neighbor_info.get('name'),
                        'node_type': neighbor_info.get('node_type'),
                        'status': neighbor_info.get('status')
                    })
                except Exception:
                    pass
                    
            topology_info['neighbor_details'] = neighbor_details
            
        except Exception as e:
            topology_info['error'] = str(e)
            
        return topology_info
    
    async def _extract_real_ips_from_configs(self, equipment_data: Dict[str, Any], network_info: Dict[str, Any]) -> None:
        """🔧 CORRECTION: Extrait les vraies adresses IP depuis les fichiers de configuration."""
        try:
            properties = equipment_data.get('properties', {})
            node_type = equipment_data.get('node_type')
            
            # Pour les équipements Dynamips (Cisco)
            if node_type == 'dynamips':
                startup_config = properties.get('startup_config')
                if startup_config:
                    # Lire le fichier de configuration startup
                    try:
                        with open(startup_config, 'r') as f:
                            config_content = f.read()
                            
                        # Extraire les adresses IP des interfaces
                        ip_patterns = [
                            r'ip address (\d+\.\d+\.\d+\.\d+)',  # Cisco IOS
                            r'ip (\d+\.\d+\.\d+\.\d+)',          # Configuration basique
                            r'address (\d+\.\d+\.\d+\.\d+)',     # Autres formats
                        ]
                        
                        for pattern in ip_patterns:
                            ip_matches = re.findall(pattern, config_content)
                            network_info['ip_addresses'].extend(ip_matches)
                            
                    except Exception as e:
                        network_info['config_read_error'] = f"Erreur lecture config Dynamips: {str(e)}"
            
            # Pour les équipements QEMU
            elif node_type == 'qemu':
                # Vérifier les scripts de démarrage et configurations
                kernel_command_line = properties.get('kernel_command_line', '')
                if kernel_command_line:
                    # Extraire IPs des paramètres kernel
                    ip_matches = re.findall(r'ip=(\d+\.\d+\.\d+\.\d+)', kernel_command_line)
                    network_info['ip_addresses'].extend(ip_matches)
                
                # Vérifier les fichiers de configuration de disque
                for disk_key in ['hda_disk_image', 'hdb_disk_image', 'hdc_disk_image', 'hdd_disk_image']:
                    disk_image = properties.get(disk_key)
                    if disk_image and 'config' in disk_image.lower():
                        try:
                            # Pour les images de configuration, essayer de monter et lire
                            network_info['disk_configs_found'] = network_info.get('disk_configs_found', [])
                            network_info['disk_configs_found'].append(disk_image)
                        except Exception:
                            pass
                            
        except Exception as e:
            network_info['ip_extraction_error'] = str(e)
    
    async def _get_ips_from_gns3_api(self, project_id: str, node_id: str) -> List[str]:
        """🔧 CORRECTION COMPLÈTE: Récupère les vraies IPs runtime des équipements GNS3."""
        discovered_ips = []
        
        try:
            # 1. Récupérer les informations complètes du nœud
            node_data = self.gns3_client.get_node(project_id, node_id)
            node_name = node_data.get('name', 'Unknown')
            node_type = node_data.get('node_type', 'unknown')
            node_status = node_data.get('status', 'stopped')
            
            logger.info(f"🔍 Découverte IP pour {node_name} (type: {node_type}, statut: {node_status})")
            
            # Si le nœud n'est pas démarré, essayer de le démarrer d'abord
            if node_status != 'started':
                logger.info(f"⚡ Démarrage du nœud {node_name} pour découverte IP")
                try:
                    start_result = self.gns3_client.start_node(project_id, node_id)
                    if start_result:
                        # Attendre quelques secondes pour que l'équipement démarre
                        import asyncio
                        await asyncio.sleep(3)
                        node_data = self.gns3_client.get_node(project_id, node_id)
                        node_status = node_data.get('status', 'stopped')
                        logger.info(f"✅ Nœud {node_name} démarré, nouveau statut: {node_status}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de démarrer le nœud {node_name}: {e}")
            
            # 2. Méthode principale: Scanner via console (plus fiable)
            if node_status == 'started':
                console_ips = await self._get_ips_via_console(project_id, node_id, node_data)
                if console_ips:
                    discovered_ips.extend(console_ips)
                    logger.info(f"✅ IPs trouvées via console pour {node_name}: {console_ips}")
            
            # 3. Méthode alternative: Scanner les réseaux GNS3 intelligemment
            if not discovered_ips:
                network_ips = await self._smart_network_scan(project_id, node_id, node_data)
                if network_ips:
                    discovered_ips.extend(network_ips)
                    logger.info(f"✅ IPs trouvées via scan réseau pour {node_name}: {network_ips}")
            
            # 4. Méthode de dernier recours: Extraction depuis les liens/topologie
            if not discovered_ips:
                topology_ips = await self._extract_ips_from_topology(project_id, node_id, node_data)
                if topology_ips:
                    discovered_ips.extend(topology_ips)
                    logger.info(f"✅ IPs trouvées via topologie pour {node_name}: {topology_ips}")
            
            # Valider toutes les IPs trouvées
            validated_ips = []
            for ip in discovered_ips:
                if await self._validate_equipment_ip(ip, node_data):
                    validated_ips.append(ip)
                    logger.info(f"✅ IP validée pour {node_name}: {ip}")
                else:
                    logger.warning(f"⚠️ IP non validée pour {node_name}: {ip}")
            
            return list(set(validated_ips))
                                    
        except Exception as e:
            logger.error(f"❌ Erreur récupération IPs pour nœud {node_id}: {e}")
            return []
    
    async def _get_ips_via_console(self, project_id: str, node_id: str, node_data: Dict[str, Any]) -> List[str]:
        """Récupère les IPs via la console Telnet/VNC de l'équipement."""
        console_ips = []
        
        try:
            console_port = node_data.get('console')
            console_type = node_data.get('console_type', 'telnet')
            console_host = node_data.get('console_host', 'localhost')
            
            if not console_port:
                return console_ips
                
            if console_type == 'telnet':
                # Connexion Telnet pour récupérer les IPs
                import telnetlib
                import time
                
                try:
                    tn = telnetlib.Telnet(console_host, console_port, timeout=5)
                    
                    # Selon le type d'équipement, utiliser différentes commandes
                    node_type = node_data.get('node_type', 'unknown')
                    
                    if 'cisco' in node_data.get('properties', {}).get('platform', '').lower():
                        # Commandes Cisco IOS
                        tn.write(b"\n")
                        time.sleep(1)
                        tn.write(b"show ip interface brief\n")
                        time.sleep(2)
                        output = tn.read_very_eager().decode('utf-8', errors='ignore')
                        
                        # Extraire les IPs de la sortie
                        import re
                        ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                        ips = re.findall(ip_pattern, output)
                        console_ips.extend([ip for ip in ips if not ip.startswith('127.')])
                        
                    elif node_type == 'vpcs':
                        # Commandes VPCS
                        tn.write(b"\n")
                        time.sleep(1)
                        tn.write(b"show ip\n")
                        time.sleep(1)
                        output = tn.read_very_eager().decode('utf-8', errors='ignore')
                        
                        # Extraire les IPs VPCS
                        import re
                        ip_pattern = r'IP\s+(\d+\.\d+\.\d+\.\d+)'
                        ips = re.findall(ip_pattern, output)
                        console_ips.extend(ips)
                        
                    else:
                        # Commandes génériques Linux
                        tn.write(b"\n")
                        time.sleep(1)
                        tn.write(b"ip addr show\n")
                        time.sleep(2)
                        output = tn.read_very_eager().decode('utf-8', errors='ignore')
                        
                        # Extraire les IPs Linux
                        import re
                        ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
                        ips = re.findall(ip_pattern, output)
                        console_ips.extend([ip for ip in ips if not ip.startswith('127.')])
                    
                    tn.close()
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur connexion console Telnet: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération IPs via console: {e}")
            
        return console_ips
    
    async def _smart_network_scan(self, project_id: str, node_id: str, node_data: Dict[str, Any]) -> List[str]:
        """Scanner intelligent des réseaux GNS3 pour trouver les équipements."""
        network_ips = []
        
        try:
            # 1. Récupérer tous les liens du projet pour identifier les segments réseau
            links = self.gns3_client.list_links(project_id)
            
            # 2. Identifier les réseaux connectés à ce nœud
            connected_networks = set()
            
            for link in links:
                nodes = link.get('nodes', [])
                node_in_link = any(node.get('node_id') == node_id for node in nodes)
                
                if node_in_link:
                    # Ce nœud est dans ce lien - identifier le segment réseau
                    for node in nodes:
                        if node.get('node_id') != node_id:
                            # C'est un nœud voisin - essayer de deviner le réseau
                            neighbor_data = self.gns3_client.get_node(project_id, node.get('node_id'))
                            neighbor_name = neighbor_data.get('name', '')
                            
                            # Déduire le réseau depuis le nom ou la position
                            if 'switch' in neighbor_name.lower():
                                connected_networks.add('192.168.1.0/24')
                            elif 'router' in neighbor_name.lower():
                                connected_networks.add('192.168.0.0/24')
                                connected_networks.add('10.0.0.0/24')
                            elif 'server' in neighbor_name.lower():
                                connected_networks.add('192.168.100.0/24')
            
            # Ajouter des réseaux communs si aucun détecté
            if not connected_networks:
                connected_networks = {
                    '192.168.1.0/24', '192.168.0.0/24', '192.168.100.0/24',
                    '10.0.0.0/24', '172.16.0.0/24', '192.168.10.0/24'
                }
            
            # 3. Scanner chaque réseau identifié
            for network in connected_networks:
                base_ip = network.split('/')[0].rsplit('.', 1)[0]
                
                # Scanner les IPs probables de ce réseau
                for host in [1, 2, 10, 20, 50, 100, 150, 200, 254]:
                    test_ip = f"{base_ip}.{host}"
                    
                    # Test de connectivité rapide
                    connectivity = await self._test_connectivity(test_ip, timeout=1)
                    if connectivity.get('ping_success'):
                        # Vérifier si cette IP appartient à notre équipement
                        if await self._verify_ip_belongs_to_node(test_ip, node_data):
                            network_ips.append(test_ip)
                            logger.info(f"🎯 IP trouvée via scan intelligent: {test_ip}")
                            
        except Exception as e:
            logger.error(f"❌ Erreur scan intelligent réseau: {e}")
            
        return network_ips
    
    async def _extract_ips_from_topology(self, project_id: str, node_id: str, node_data: Dict[str, Any]) -> List[str]:
        """Extrait les IPs depuis les informations de topologie GNS3."""
        topology_ips = []
        
        try:
            # Analyser les propriétés spécifiques au type de nœud
            properties = node_data.get('properties', {})
            node_type = node_data.get('node_type', 'unknown')
            
            # Pour VPCS - vérifier startup_script en détail
            if node_type == 'vpcs':
                startup_script = properties.get('startup_script', '')
                if startup_script:
                    import re
                    # Patterns plus complets pour VPCS
                    patterns = [
                        r'ip (\d+\.\d+\.\d+\.\d+)',
                        r'set pcname ip (\d+\.\d+\.\d+\.\d+)', 
                        r'(\d+\.\d+\.\d+\.\d+)/\d+',
                        r'address (\d+\.\d+\.\d+\.\d+)'
                    ]
                    
                    for pattern in patterns:
                        ips = re.findall(pattern, startup_script)
                        topology_ips.extend(ips)
            
            # Pour équipements Cisco/Dynamips
            elif node_type == 'dynamips':
                configs = [
                    properties.get('startup_config'),
                    properties.get('private_config')
                ]
                
                for config_file in configs:
                    if config_file:
                        try:
                            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                                config_content = f.read()
                                
                            # Patterns Cisco IOS
                            import re
                            patterns = [
                                r'ip address (\d+\.\d+\.\d+\.\d+) \d+\.\d+\.\d+\.\d+',
                                r'ip (\d+\.\d+\.\d+\.\d+) \d+\.\d+\.\d+\.\d+',
                                r'interface.*?ip address (\d+\.\d+\.\d+\.\d+)',
                                r'loopback.*?ip address (\d+\.\d+\.\d+\.\d+)'
                            ]
                            
                            for pattern in patterns:
                                ips = re.findall(pattern, config_content, re.MULTILINE | re.DOTALL)
                                topology_ips.extend(ips)
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur lecture config {config_file}: {e}")
            
            # Pour équipements QEMU/KVM
            elif node_type == 'qemu':
                kernel_cmd = properties.get('kernel_command_line', '')
                if kernel_cmd:
                    import re
                    # Extraire IPs des paramètres kernel
                    patterns = [
                        r'ip=(\d+\.\d+\.\d+\.\d+)',
                        r'ipaddr=(\d+\.\d+\.\d+\.\d+)',
                        r'host_ip=(\d+\.\d+\.\d+\.\d+)'
                    ]
                    
                    for pattern in patterns:
                        ips = re.findall(pattern, kernel_cmd)
                        topology_ips.extend(ips)
                        
        except Exception as e:
            logger.error(f"❌ Erreur extraction IPs topologie: {e}")
            
        return topology_ips
    
    async def _verify_ip_belongs_to_node(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Vérifie intelligemment si une IP appartient au nœud spécifié."""
        try:
            node_name = node_data.get('name', '').lower()
            
            # 1. Test SNMP avec nom système
            try:
                from api_clients.network.snmp_client import SNMPClient, SNMPCredentials, SNMPVersion
                
                credentials = SNMPCredentials(version=SNMPVersion.V2C, community='public')
                snmp_client = SNMPClient(ip, credentials=credentials)
                system_info = snmp_client.get_system_info()
                
                if system_info.get('success'):
                    system_name = system_info.get('system_name', '').lower()
                    # Vérifier si les noms correspondent
                    if node_name and system_name:
                        name_parts = node_name.replace('-', ' ').split()
                        for part in name_parts:
                            if len(part) > 2 and part in system_name:
                                return True
                                
            except Exception:
                pass
            
            # 2. Test des ports typiques selon le type d'équipement
            connectivity = await self._test_connectivity(ip, timeout=2)
            open_ports = connectivity.get('port_scan', {})
            
            node_type = node_data.get('node_type', 'unknown')
            properties = node_data.get('properties', {})
            
            # Ports attendus selon le type
            if 'router' in node_name or 'cisco' in properties.get('platform', '').lower():
                # Routeur Cisco - ports SSH/Telnet/SNMP
                if open_ports.get(22) or open_ports.get(23) or open_ports.get(161):
                    return True
            elif 'switch' in node_name:
                # Switch - ports de gestion
                if open_ports.get(23) or open_ports.get(161) or open_ports.get(80):
                    return True
            elif 'server' in node_name or node_type == 'qemu':
                # Serveur - ports HTTP/SSH
                if open_ports.get(22) or open_ports.get(80) or open_ports.get(443):
                    return True
            elif node_type == 'vpcs':
                # VPCS - répond au ping
                if connectivity.get('ping_success'):
                    return True
            
            # 3. Test général: si ça répond au ping et a des ports ouverts
            if connectivity.get('ping_success') and any(open_ports.values()):
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur vérification IP {ip}: {e}")
            
        return False
    
    async def _validate_equipment_ip(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Validation finale d'une IP d'équipement."""
        try:
            # Exclure les IPs invalides
            if ip.startswith('127.') or ip.startswith('0.') or ip == '0.0.0.0':
                return False
                
            # Vérifier que l'IP est dans une plage valide
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_global:
                # Vérifier la connectivité
                connectivity = await self._test_connectivity(ip, timeout=3)
                return connectivity.get('ping_success', False)
                
        except Exception:
            pass
            
        return False
    
    async def _verify_equipment_ip(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Vérifie si une IP appartient à l'équipement spécifié."""
        try:
            # Essayer SNMP pour vérifier l'identité
            from api_clients.network.snmp_client import SNMPClient, SNMPCredentials, SNMPVersion
            
            credentials = SNMPCredentials(version=SNMPVersion.V2C, community='public')
            snmp_client = SNMPClient(ip, credentials=credentials)
            system_info = snmp_client.get_system_info()
            
            if system_info.get('success'):
                # Comparer le nom système avec le nom du nœud
                system_name = system_info.get('system_name', '').lower()
                node_name = node_data.get('name', '').lower()
                
                # Si les noms correspondent partiellement, c'est probablement le bon équipement
                if system_name and node_name:
                    return any(part in system_name for part in node_name.split() if len(part) > 2)
            
            # Essayer d'autres méthodes de vérification
            connectivity = await self._test_connectivity(ip)
            open_ports = connectivity.get('port_scan', {})
            
            # Si l'équipement a des ports typiques ouverts, c'est probablement le bon
            typical_ports = [22, 23, 80, 161, 443]
            if any(open_ports.get(port, False) for port in typical_ports):
                return True
                
        except Exception:
            pass
            
        return False
    
    async def _get_ips_from_console(self, project_id: str, node_id: str, equipment_data: Dict[str, Any]) -> List[str]:
        """
        Récupère les IPs configurées via console des équipements.
        
        Cette méthode se connecte à la console telnet des équipements
        et exécute des commandes pour récupérer les IPs configurées.
        """
        discovered_ips = []
        
        try:
            # Obtenir les informations de console
            console_info = await self._discover_console_info(project_id, node_id)
            
            if not console_info.get('console_available'):
                logger.warning(f"⚠️ Console non disponible pour {equipment_data.get('name', 'Unknown')}")
                return []
            
            if console_info.get('console_type') != 'telnet':
                logger.warning(f"⚠️ Type console non supporté: {console_info.get('console_type')}")
                return []
            
            # Informations de connexion console
            console_host = console_info.get('console_host', 'localhost')
            console_port = console_info.get('console_port')
            node_name = equipment_data.get('name', 'Unknown')
            node_type = equipment_data.get('node_type', 'unknown')
            
            if not console_port:
                logger.warning(f"⚠️ Port console non défini pour {node_name}")
                return []
            
            logger.info(f"🔌 Connexion console {node_name} ({node_type}) sur {console_host}:{console_port}")
            
            # Connexion telnet avec timeout
            import telnetlib
            import time
            
            try:
                tn = telnetlib.Telnet(console_host, console_port, timeout=10)
                time.sleep(2)  # Attendre l'initialisation
                
                # Commandes selon le type d'équipement
                if node_type == 'vpcs':
                    # Commandes VPCS
                    tn.write(b"\n")
                    time.sleep(1)
                    tn.write(b"show ip\n")
                    time.sleep(2)
                    
                    # Lire la réponse
                    response = tn.read_very_eager().decode('ascii', errors='ignore')
                    
                    # Extraire les IPs
                    import re
                    ip_matches = re.findall(r'IP address: (\d+\.\d+\.\d+\.\d+)', response)
                    discovered_ips.extend(ip_matches)
                    
                elif node_type == 'iou':
                    # Commandes IOU/Cisco
                    tn.write(b"\n")
                    time.sleep(1)
                    tn.write(b"show ip interface brief\n")
                    time.sleep(2)
                    
                    # Lire la réponse
                    response = tn.read_very_eager().decode('ascii', errors='ignore')
                    
                    # Extraire les IPs
                    import re
                    ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)\\s+YES', response)
                    discovered_ips.extend(ip_matches)
                    
                elif node_type == 'qemu':
                    # Commandes Linux/QEMU
                    tn.write(b"\n")
                    time.sleep(1)
                    tn.write(b"ip addr show\n")
                    time.sleep(2)
                    
                    # Lire la réponse
                    response = tn.read_very_eager().decode('ascii', errors='ignore')
                    
                    # Extraire les IPs
                    import re
                    ip_matches = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', response)
                    # Filtrer les IPs locales
                    discovered_ips.extend([ip for ip in ip_matches if not ip.startswith('127.')])
                    
                elif node_type == 'dynamips':
                    # Commandes Cisco IOS
                    tn.write(b"\n")
                    time.sleep(1)
                    tn.write(b"show ip interface brief\n")
                    time.sleep(2)
                    
                    # Lire la réponse
                    response = tn.read_very_eager().decode('ascii', errors='ignore')
                    
                    # Extraire les IPs
                    import re
                    ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)\\s+YES', response)
                    discovered_ips.extend(ip_matches)
                
                # Fermer la connexion telnet
                tn.close()
                
                if discovered_ips:
                    logger.info(f"✅ IPs découvertes via console {node_name}: {discovered_ips}")
                else:
                    logger.warning(f"⚠️ Aucune IP découverte via console {node_name}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur connexion console {node_name}: {e}")
                
        except Exception as e:
            logger.error(f"❌ Erreur découverte IPs console: {e}")
            
        return discovered_ips
    
    async def _get_dhcp_configured_ips(self, project_id: str, node_id: str, equipment_data: Dict[str, Any]) -> List[str]:
        """
        Récupère les IPs configurées par le système DHCP automatique.
        
        Cette méthode interroge le système DHCP pour récupérer les IPs
        qui ont été configurées automatiquement sur les équipements.
        """
        dhcp_ips = []
        
        try:
            # Importer le gestionnaire DHCP
            import sys
            import os
            
            # Ajouter le répertoire du framework de sécurité au path
            security_framework_path = '/home/adjada/network-management-system/real_security_testing_framework'
            if security_framework_path not in sys.path:
                sys.path.append(security_framework_path)
            
            from auto_dhcp_configuration import DHCPConfigurationManager
            
            # Créer une instance du gestionnaire DHCP
            dhcp_manager = DHCPConfigurationManager('http://localhost:8000')
            
            # Récupérer les configurations DHCP pour ce projet
            devices_config = dhcp_manager.get_devices_for_project(project_id)
            
            # Chercher l'équipement correspondant
            node_name = equipment_data.get('name', '')
            node_type = equipment_data.get('node_type', '')
            
            for device in devices_config:
                if (device.node_id == node_id or 
                    device.name == node_name):
                    
                    # Récupérer l'IP configurée
                    if hasattr(device, 'ip_address') and device.ip_address:
                        dhcp_ips.append(device.ip_address)
                        logger.info(f"✅ IP DHCP trouvée pour {node_name}: {device.ip_address}")
                    
                    # Vérifier si l'IP a été effectivement configurée
                    if hasattr(dhcp_manager, 'verify_ip_configuration'):
                        verification = dhcp_manager.verify_ip_configuration(device)
                        if verification and verification.get('configured'):
                            configured_ip = verification.get('ip_address')
                            if configured_ip and configured_ip not in dhcp_ips:
                                dhcp_ips.append(configured_ip)
                                logger.info(f"✅ IP DHCP vérifiée pour {node_name}: {configured_ip}")
            
            if dhcp_ips:
                logger.info(f"🔄 Synchronisation DHCP réussie pour {node_name}: {dhcp_ips}")
            else:
                logger.warning(f"⚠️ Aucune IP DHCP trouvée pour {node_name}")
                
        except Exception as e:
            logger.error(f"❌ Erreur synchronisation DHCP pour {equipment_data.get('name', 'Unknown')}: {e}")
            
        return dhcp_ips

# Instance globale du service
equipment_discovery_service = EquipmentDiscoveryService()

@swagger_auto_schema(
    method='get',
    operation_description="Récupère tous les équipements d'un projet avec leurs informations de base",
    manual_parameters=[
        openapi.Parameter('project_id', openapi.IN_PATH, description="ID du projet GNS3", type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: openapi.Response(
            description="Liste des équipements du projet",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'project_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'equipment_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'equipment_list': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'equipment_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'type': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'basic_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        )
                    ),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def list_project_equipment(request, project_id):
    """
    Liste tous les équipements d'un projet GNS3 avec informations de base.
    
    Retourne une vue d'ensemble de tous les équipements du projet.
    """
    try:
        # Récupérer les informations du projet
        gns3_client = GNS3Client()
        project_info = gns3_client.get_project(project_id)
        nodes = gns3_client.get_nodes(project_id)
        
        equipment_list = []
        for node in nodes:
            equipment_info = {
                'equipment_id': node.get('node_id'),
                'name': node.get('name', 'Unknown'),
                'type': node.get('node_type', 'unknown'),
                'status': node.get('status', 'unknown'),
                'console_port': node.get('console'),
                'console_type': node.get('console_type'),
                'position': {
                    'x': node.get('x', 0),
                    'y': node.get('y', 0),
                    'z': node.get('z', 1)
                },
                'properties_summary': {
                    'platform': node.get('properties', {}).get('platform'),
                    'image': node.get('properties', {}).get('image'),
                    'ram': node.get('properties', {}).get('ram'),
                },
                'port_count': len(node.get('ports', [])),
                'custom_adapters': len(node.get('custom_adapters', []))
            }
            equipment_list.append(equipment_info)
            
        response_data = {
            'project_id': project_id,
            'project_name': project_info.get('name', 'Unknown'),
            'project_status': project_info.get('status', 'unknown'),
            'equipment_count': len(equipment_list),
            'equipment_list': equipment_list,
            'discovery_timestamp': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des équipements: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Découverte complète d'un équipement spécifique",
    manual_parameters=[
        openapi.Parameter('project_id', openapi.IN_PATH, description="ID du projet GNS3", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('equipment_id', openapi.IN_PATH, description="ID de l'équipement", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('include_snmp', openapi.IN_QUERY, description="Inclure la découverte SNMP", type=openapi.TYPE_BOOLEAN, default=True),
        openapi.Parameter('include_performance', openapi.IN_QUERY, description="Inclure les métriques de performance", type=openapi.TYPE_BOOLEAN, default=True),
        openapi.Parameter('include_topology', openapi.IN_QUERY, description="Inclure les informations de topologie", type=openapi.TYPE_BOOLEAN, default=True),
    ],
    responses={
        200: openapi.Response(description="Informations complètes de l'équipement", schema=equipment_detail_response)
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def discover_equipment_details(request, project_id, equipment_id):
    """
    Découverte complète d'un équipement spécifique.
    
    Collecte toutes les informations possibles sur un équipement :
    - Informations GNS3 de base
    - Configuration réseau
    - Données SNMP si disponibles
    - Métriques de performance
    - Informations de topologie
    - Capacités et fonctionnalités
    """
    try:
        # Paramètres optionnels
        include_snmp = request.GET.get('include_snmp', 'true').lower() == 'true'
        include_performance = request.GET.get('include_performance', 'true').lower() == 'true'
        include_topology = request.GET.get('include_topology', 'true').lower() == 'true'
        
        # Découverte asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            equipment_data = loop.run_until_complete(
                equipment_discovery_service.discover_equipment_details(project_id, equipment_id)
            )
        finally:
            loop.close()
            
        # Filtrer les données selon les paramètres
        if not include_snmp:
            equipment_data.pop('snmp_data', None)
        if not include_performance:
            equipment_data.pop('performance_metrics', None)
        if not include_topology:
            equipment_data.pop('topology_links', None)
            
        return Response(equipment_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la découverte de l\'équipement: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Découverte complète de tous les équipements d'un projet",
    manual_parameters=[
        openapi.Parameter('project_id', openapi.IN_PATH, description="ID du projet GNS3", type=openapi.TYPE_STRING, required=True),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'include_snmp': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
            'include_performance': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
            'include_topology': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
            'parallel_discovery': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
            'max_concurrent': openapi.Schema(type=openapi.TYPE_INTEGER, default=5),
        }
    ),
    responses={
        200: openapi.Response(
            description="Découverte complète du projet",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'discovery_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'total_equipment': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'successful_discoveries': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'failed_discoveries': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'equipment_details': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'discovery_duration_seconds': openapi.Schema(type=openapi.TYPE_NUMBER),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def discover_project_complete(request, project_id):
    """
    Découverte complète de tous les équipements d'un projet.
    
    Lance une découverte approfondie de tous les équipements du projet avec possibilité de traitement en parallèle.
    """
    try:
        # Paramètres de configuration
        include_snmp = request.data.get('include_snmp', True)
        include_performance = request.data.get('include_performance', True)
        include_topology = request.data.get('include_topology', True)
        parallel_discovery = request.data.get('parallel_discovery', True)
        max_concurrent = request.data.get('max_concurrent', 5)
        
        start_time = timezone.now()
        
        # Récupérer la liste des équipements
        gns3_client = GNS3Client()
        project_info = gns3_client.get_project(project_id)
        nodes = gns3_client.get_nodes(project_id)
        
        discovery_results = {
            'project_id': project_id,
            'project_name': project_info.get('name', 'Unknown'),
            'discovery_start_time': start_time.isoformat(),
            'total_equipment': len(nodes),
            'successful_discoveries': 0,
            'failed_discoveries': 0,
            'equipment_details': {},
            'discovery_summary': {}
        }
        
        async def discover_all_equipment():
            """Fonction asynchrone pour découvrir tous les équipements."""
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def discover_single_equipment(node):
                async with semaphore:
                    try:
                        node_id = node.get('node_id')
                        equipment_data = await equipment_discovery_service.discover_equipment_details(
                            project_id, node_id
                        )
                        
                        # Filtrer selon les paramètres
                        if not include_snmp:
                            equipment_data.pop('snmp_data', None)
                        if not include_performance:
                            equipment_data.pop('performance_metrics', None)
                        if not include_topology:
                            equipment_data.pop('topology_links', None)
                        
                        return equipment_data
                        
                    except Exception as e:
                        logger.error(f"Erreur découverte équipement {node.get('node_id')}: {e}")
                        return None
            
            # Exécuter la découverte en parallèle ou séquentiel
            if parallel_discovery and len(nodes) > 1:
                tasks = [discover_single_equipment(node) for node in nodes]
                equipment_results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                equipment_results = []
                for node in nodes:
                    result = await discover_single_equipment(node)
                    equipment_results.append(result)
            
            return equipment_results
        
        # Initialiser le service de découverte
        equipment_discovery_service = EquipmentDiscoveryService()
        
        # Exécuter la découverte asynchrone
        equipment_results = asyncio.run(discover_all_equipment())
        
        # Traiter les résultats
        for result in equipment_results:
            if result and not isinstance(result, Exception):
                equipment_id = result.get('equipment_id')
                discovery_results['equipment_details'][equipment_id] = result
                
                if result.get('discovery_status') == 'completed':
                    discovery_results['successful_discoveries'] += 1
                else:
                    discovery_results['failed_discoveries'] += 1
            else:
                discovery_results['failed_discoveries'] += 1
        
        # Calculer le résumé de découverte
        success_rate = (discovery_results['successful_discoveries'] / len(nodes) * 100) if nodes else 0
        
        # Analyser les types d'équipements
        equipment_types = {}
        snmp_enabled_count = 0
        console_enabled_count = 0
        total_interfaces = 0
        
        for equipment_data in discovery_results['equipment_details'].values():
            # Types d'équipements
            eq_type = equipment_data.get('node_type', 'unknown')
            equipment_types[eq_type] = equipment_types.get(eq_type, 0) + 1
            
            # SNMP activé
            snmp_data = equipment_data.get('snmp_data', {})
            if snmp_data.get('snmp_available', False):
                snmp_enabled_count += 1
            
            # Console activée
            console_info = equipment_data.get('console_info', {})
            if console_info.get('console_available', False):
                console_enabled_count += 1
            
            # Interfaces
            network_info = equipment_data.get('network_info', {})
            interfaces = network_info.get('interfaces', [])
            total_interfaces += len(interfaces)
        
        discovery_results['discovery_summary'] = {
            'success_rate': success_rate,
            'equipment_types': equipment_types,
            'snmp_enabled_count': snmp_enabled_count,
            'console_enabled_count': console_enabled_count,
            'total_interfaces': total_interfaces
        }
        
        # Finaliser
        discovery_results['discovery_end_time'] = timezone.now().isoformat()
        discovery_results['discovery_duration_seconds'] = (
            timezone.now() - start_time
        ).total_seconds()
        discovery_results['discovery_status'] = 'completed'
        
        return Response(discovery_results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur découverte projet {project_id}: {e}")
        return Response({
            'project_id': project_id,
            'discovery_status': 'failed',
            'error_message': str(e),
            'discovery_end_time': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
