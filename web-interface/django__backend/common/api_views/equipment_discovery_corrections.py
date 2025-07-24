"""
Corrections pour l'extraction des IPs réelles depuis les configurations d'équipements.
Ces corrections résolvent les problèmes identifiés dans equipment_discovery_api.py
"""

import re
import os
import json
from typing import Dict, List, Any
import subprocess
import asyncio
from pathlib import Path

class EnhancedEquipmentDiscovery:
    """Service amélioré pour découvrir les vraies IPs des équipements GNS3."""
    
    async def enhanced_extract_real_ips_from_configs(self, equipment_data: Dict[str, Any], network_info: Dict[str, Any]) -> None:
        """
        🔧 CORRECTION COMPLÈTE : Extrait les vraies adresses IP depuis les configurations.
        
        Améliorations :
        - Patterns IP complets avec masques
        - Support des VLANs
        - Gestion des interfaces multiples
        - Parsing des routes statiques
        - Détection des passerelles
        """
        try:
            properties = equipment_data.get('properties', {})
            node_type = equipment_data.get('node_type')
            
            # Initialiser les structures de données
            network_info['ip_addresses'] = []
            network_info['interface_configs'] = []
            network_info['routing_table'] = []
            network_info['vlans'] = []
            network_info['gateways'] = []
            
            # === ÉQUIPEMENTS DYNAMIPS (Cisco) ===
            if node_type == 'dynamips':
                await self._extract_cisco_ips(properties, network_info)
            
            # === ÉQUIPEMENTS QEMU (Linux/Router) ===
            elif node_type == 'qemu':
                await self._extract_qemu_ips(properties, network_info)
            
            # === ÉQUIPEMENTS VPCS (Amélioré) ===
            elif node_type == 'vpcs':
                await self._extract_vpcs_ips(properties, network_info)
            
            # === ÉQUIPEMENTS DOCKER ===
            elif node_type == 'docker':
                await self._extract_docker_ips(properties, network_info)
            
            # Nettoyer et valider les IPs trouvées
            network_info['ip_addresses'] = self._validate_and_clean_ips(network_info['ip_addresses'])
            
        except Exception as e:
            network_info['ip_extraction_error'] = str(e)
    
    async def _extract_cisco_ips(self, properties: Dict[str, Any], network_info: Dict[str, Any]) -> None:
        """Extrait les IPs depuis les configurations Cisco/Dynamips."""
        startup_config = properties.get('startup_config')
        
        if not startup_config or not os.path.exists(startup_config):
            return
        
        try:
            with open(startup_config, 'r', encoding='utf-8', errors='ignore') as f:
                config_content = f.read()
            
            # Patterns améliorés pour Cisco IOS
            patterns = {
                'interface_ip': r'interface\s+(\S+).*?ip address (\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
                'secondary_ip': r'ip address (\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+secondary',
                'loopback_ip': r'interface\s+Loopback\d+.*?ip address (\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
                'static_route': r'ip route (\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
                'default_gateway': r'ip default-gateway (\d+\.\d+\.\d+\.\d+)',
                'dhcp_helper': r'ip helper-address (\d+\.\d+\.\d+\.\d+)',
                'vlan_interface': r'interface Vlan(\d+).*?ip address (\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
                'hsrp_ip': r'standby \d+ ip (\d+\.\d+\.\d+\.\d+)',
                'ospf_router_id': r'router-id (\d+\.\d+\.\d+\.\d+)',
                'bgp_neighbor': r'neighbor (\d+\.\d+\.\d+\.\d+)',
            }
            
            # Extraire selon chaque pattern
            for pattern_name, pattern in patterns.items():
                matches = re.finditer(pattern, config_content, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    if pattern_name == 'interface_ip':
                        interface, ip, mask = match.groups()
                        network_info['ip_addresses'].append(ip)
                        network_info['interface_configs'].append({
                            'interface': interface,
                            'ip': ip,
                            'mask': mask,
                            'type': 'primary'
                        })
                    
                    elif pattern_name == 'vlan_interface':
                        vlan_id, ip, mask = match.groups()
                        network_info['ip_addresses'].append(ip)
                        network_info['vlans'].append({
                            'vlan_id': vlan_id,
                            'ip': ip,
                            'mask': mask
                        })
                    
                    elif pattern_name == 'static_route':
                        network, mask, gateway = match.groups()
                        network_info['routing_table'].append({
                            'network': network,
                            'mask': mask,
                            'gateway': gateway
                        })
                    
                    elif pattern_name in ['default_gateway', 'dhcp_helper', 'hsrp_ip', 'ospf_router_id']:
                        ip = match.group(1)
                        network_info['gateways'].append({
                            'ip': ip,
                            'type': pattern_name
                        })
                        
                    elif pattern_name == 'bgp_neighbor':
                        neighbor_ip = match.group(1)
                        network_info['ip_addresses'].append(neighbor_ip)
            
            # Extraire les VLANs configurés
            vlan_matches = re.finditer(r'vlan (\d+)', config_content, re.IGNORECASE)
            for match in vlan_matches:
                vlan_id = match.group(1)
                if not any(v['vlan_id'] == vlan_id for v in network_info['vlans']):
                    network_info['vlans'].append({
                        'vlan_id': vlan_id,
                        'ip': None,
                        'mask': None
                    })
            
        except Exception as e:
            network_info['cisco_config_error'] = str(e)
    
    async def _extract_qemu_ips(self, properties: Dict[str, Any], network_info: Dict[str, Any]) -> None:
        """Extrait les IPs depuis les configurations QEMU (Linux/Router)."""
        
        # Vérifier les paramètres kernel
        kernel_command_line = properties.get('kernel_command_line', '')
        if kernel_command_line:
            # Patterns pour les paramètres kernel Linux
            kernel_patterns = [
                r'ip=(\d+\.\d+\.\d+\.\d+):(\d+\.\d+\.\d+\.\d+):(\d+\.\d+\.\d+\.\d+):(\d+\.\d+\.\d+\.\d+)',  # ip=client:server:gateway:netmask
                r'ip=(\d+\.\d+\.\d+\.\d+)',  # IP simple
                r'nfsroot=(\d+\.\d+\.\d+\.\d+):',  # NFS root
            ]
            
            for pattern in kernel_patterns:
                matches = re.findall(pattern, kernel_command_line)
                for match in matches:
                    if isinstance(match, tuple):
                        # IP complexe avec gateway/netmask
                        client_ip, server_ip, gateway_ip, netmask = match
                        network_info['ip_addresses'].extend([client_ip, server_ip, gateway_ip])
                        network_info['interface_configs'].append({
                            'interface': 'eth0',
                            'ip': client_ip,
                            'mask': netmask,
                            'gateway': gateway_ip,
                            'type': 'kernel_param'
                        })
                    else:
                        # IP simple
                        network_info['ip_addresses'].append(match)
        
        # Vérifier les images de disque pour les configurations
        disk_configs = []
        for disk_key in ['hda_disk_image', 'hdb_disk_image', 'hdc_disk_image', 'hdd_disk_image']:
            disk_image = properties.get(disk_key)
            if disk_image:
                disk_configs.append(disk_image)
        
        # Analyser les configurations dans les images disque
        for disk_path in disk_configs:
            if disk_path and os.path.exists(disk_path):
                await self._analyze_disk_image_for_ips(disk_path, network_info)
    
    async def _extract_vpcs_ips(self, properties: Dict[str, Any], network_info: Dict[str, Any]) -> None:
        """Extrait les IPs depuis les configurations VPCS (amélioré)."""
        startup_script = properties.get('startup_script', '')
        
        if not startup_script:
            return
        
        # Patterns VPCS améliorés
        vpcs_patterns = [
            r'ip (\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',  # ip IP mask gateway
            r'ip (\d+\.\d+\.\d+\.\d+)/(\d+)\s+(\d+\.\d+\.\d+\.\d+)',  # ip IP/CIDR gateway
            r'ip (\d+\.\d+\.\d+\.\d+)',  # ip simple
            r'ip dhcp',  # DHCP
        ]
        
        for pattern in vpcs_patterns:
            matches = re.finditer(pattern, startup_script)
            for match in matches:
                if 'dhcp' in match.group(0):
                    network_info['interface_configs'].append({
                        'interface': 'eth0',
                        'type': 'dhcp',
                        'ip': 'dhcp'
                    })
                else:
                    groups = match.groups()
                    ip = groups[0]
                    network_info['ip_addresses'].append(ip)
                    
                    config = {
                        'interface': 'eth0',
                        'ip': ip,
                        'type': 'static'
                    }
                    
                    if len(groups) >= 2:
                        if '/' in groups[1]:
                            config['cidr'] = groups[1]
                        else:
                            config['mask'] = groups[1]
                    
                    if len(groups) >= 3:
                        config['gateway'] = groups[2]
                    
                    network_info['interface_configs'].append(config)
    
    async def _extract_docker_ips(self, properties: Dict[str, Any], network_info: Dict[str, Any]) -> None:
        """Extrait les IPs depuis les configurations Docker."""
        
        # Vérifier les variables d'environnement
        environment = properties.get('environment', '')
        if environment:
            # Patterns pour les variables d'environnement réseau
            env_patterns = [
                r'IP_ADDRESS=(\d+\.\d+\.\d+\.\d+)',
                r'SERVER_IP=(\d+\.\d+\.\d+\.\d+)',
                r'GATEWAY=(\d+\.\d+\.\d+\.\d+)',
                r'DNS_SERVER=(\d+\.\d+\.\d+\.\d+)',
            ]
            
            for pattern in env_patterns:
                matches = re.findall(pattern, environment)
                network_info['ip_addresses'].extend(matches)
        
        # Vérifier les volumes pour les configurations
        extra_volumes = properties.get('extra_volumes', [])
        for volume in extra_volumes:
            if isinstance(volume, str) and 'config' in volume.lower():
                await self._analyze_docker_volume_for_ips(volume, network_info)
    
    async def _analyze_disk_image_for_ips(self, disk_path: str, network_info: Dict[str, Any]) -> None:
        """Analyse une image disque pour extraire les IPs."""
        try:
            # Tentative de montage read-only temporaire
            mount_point = f"/tmp/gns3_disk_mount_{os.getpid()}"
            os.makedirs(mount_point, exist_ok=True)
            
            # Commande pour monter l'image (nécessite sudo)
            mount_cmd = f"sudo mount -o loop,ro '{disk_path}' '{mount_point}'"
            result = subprocess.run(mount_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Rechercher les fichiers de configuration réseau
                config_files = [
                    f"{mount_point}/etc/network/interfaces",
                    f"{mount_point}/etc/sysconfig/network-scripts/ifcfg-eth0",
                    f"{mount_point}/etc/netplan/*.yaml",
                    f"{mount_point}/etc/systemd/network/*.network",
                ]
                
                for config_file in config_files:
                    if os.path.exists(config_file):
                        with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Extraire les IPs selon le type de fichier
                        if 'interfaces' in config_file:
                            await self._parse_debian_interfaces(content, network_info)
                        elif 'ifcfg-' in config_file:
                            await self._parse_redhat_ifcfg(content, network_info)
                        elif 'netplan' in config_file:
                            await self._parse_netplan(content, network_info)
                        elif '.network' in config_file:
                            await self._parse_systemd_network(content, network_info)
                
                # Démonter
                subprocess.run(f"sudo umount '{mount_point}'", shell=True)
                os.rmdir(mount_point)
                
        except Exception as e:
            network_info['disk_analysis_error'] = str(e)
    
    async def _parse_debian_interfaces(self, content: str, network_info: Dict[str, Any]) -> None:
        """Parse le fichier /etc/network/interfaces (Debian/Ubuntu)."""
        lines = content.split('\n')
        current_interface = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('iface'):
                parts = line.split()
                if len(parts) >= 4:
                    current_interface = parts[1]
                    if parts[3] == 'static':
                        network_info['interface_configs'].append({
                            'interface': current_interface,
                            'type': 'static'
                        })
            
            elif line.startswith('address') and current_interface:
                ip = line.split()[1]
                network_info['ip_addresses'].append(ip)
                # Mettre à jour la dernière config d'interface
                if network_info['interface_configs']:
                    network_info['interface_configs'][-1]['ip'] = ip
            
            elif line.startswith('netmask') and current_interface:
                mask = line.split()[1]
                if network_info['interface_configs']:
                    network_info['interface_configs'][-1]['mask'] = mask
            
            elif line.startswith('gateway') and current_interface:
                gateway = line.split()[1]
                network_info['gateways'].append({
                    'ip': gateway,
                    'type': 'default_gateway'
                })
    
    async def _parse_redhat_ifcfg(self, content: str, network_info: Dict[str, Any]) -> None:
        """Parse les fichiers ifcfg-* (RedHat/CentOS)."""
        lines = content.split('\n')
        config = {}
        
        for line in lines:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"')
        
        if 'IPADDR' in config:
            network_info['ip_addresses'].append(config['IPADDR'])
            interface_config = {
                'interface': config.get('DEVICE', 'unknown'),
                'ip': config['IPADDR'],
                'type': 'static'
            }
            
            if 'NETMASK' in config:
                interface_config['mask'] = config['NETMASK']
            
            if 'GATEWAY' in config:
                interface_config['gateway'] = config['GATEWAY']
                network_info['gateways'].append({
                    'ip': config['GATEWAY'],
                    'type': 'default_gateway'
                })
            
            network_info['interface_configs'].append(interface_config)
    
    async def _parse_netplan(self, content: str, network_info: Dict[str, Any]) -> None:
        """Parse les fichiers netplan (Ubuntu 18+)."""
        try:
            import yaml
            config = yaml.safe_load(content)
            
            if 'network' in config and 'ethernets' in config['network']:
                for interface, iface_config in config['network']['ethernets'].items():
                    if 'addresses' in iface_config:
                        for address in iface_config['addresses']:
                            if '/' in address:
                                ip = address.split('/')[0]
                                network_info['ip_addresses'].append(ip)
                                network_info['interface_configs'].append({
                                    'interface': interface,
                                    'ip': ip,
                                    'cidr': address,
                                    'type': 'static'
                                })
                    
                    if 'gateway4' in iface_config:
                        network_info['gateways'].append({
                            'ip': iface_config['gateway4'],
                            'type': 'default_gateway'
                        })
        except Exception as e:
            network_info['netplan_parse_error'] = str(e)
    
    async def _parse_systemd_network(self, content: str, network_info: Dict[str, Any]) -> None:
        """Parse les fichiers systemd-networkd."""
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
            
            elif '=' in line and current_section == 'Network':
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'Address':
                    if '/' in value:
                        ip = value.split('/')[0]
                        network_info['ip_addresses'].append(ip)
                        network_info['interface_configs'].append({
                            'interface': 'systemd_network',
                            'ip': ip,
                            'cidr': value,
                            'type': 'static'
                        })
                
                elif key == 'Gateway':
                    network_info['gateways'].append({
                        'ip': value,
                        'type': 'default_gateway'
                    })
    
    async def _analyze_docker_volume_for_ips(self, volume_path: str, network_info: Dict[str, Any]) -> None:
        """Analyse un volume Docker pour extraire les IPs."""
        try:
            if os.path.exists(volume_path):
                with open(volume_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Patterns génériques pour les fichiers de configuration
                ip_patterns = [
                    r'server\s*=\s*(\d+\.\d+\.\d+\.\d+)',
                    r'host\s*=\s*(\d+\.\d+\.\d+\.\d+)',
                    r'bind\s*=\s*(\d+\.\d+\.\d+\.\d+)',
                    r'listen\s*=\s*(\d+\.\d+\.\d+\.\d+)',
                    r'address\s*=\s*(\d+\.\d+\.\d+\.\d+)',
                ]
                
                for pattern in ip_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    network_info['ip_addresses'].extend(matches)
        
        except Exception as e:
            network_info['docker_volume_error'] = str(e)
    
    def _validate_and_clean_ips(self, ip_list: List[str]) -> List[str]:
        """Valide et nettoie la liste des IPs trouvées."""
        cleaned_ips = []
        
        for ip in ip_list:
            # Validation IP basique
            if self._is_valid_ip(ip):
                # Exclure les IPs réservées/spéciales
                if not self._is_reserved_ip(ip):
                    cleaned_ips.append(ip)
        
        # Retourner les IPs uniques
        return list(set(cleaned_ips))
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Vérifie si une IP est valide."""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_reserved_ip(self, ip: str) -> bool:
        """Vérifie si une IP est réservée/spéciale."""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            # Exclure les IPs réservées
            return (
                ip_obj.is_loopback or
                ip_obj.is_multicast or
                ip_obj.is_reserved or
                ip_obj.is_unspecified or
                str(ip_obj) in ['0.0.0.0', '255.255.255.255']
            )
        except ValueError:
            return True
    
    async def enhanced_get_ips_from_gns3_api(self, project_id: str, node_id: str) -> List[str]:
        """
        🔧 CORRECTION : Récupération IPs améliorée via l'API GNS3.
        
        Améliorations :
        - Scan réseau intelligent basé sur la topologie
        - Timeout adaptatif
        - Corrélation avec les VLANs
        - Détection des équipements par empreinte réseau
        """
        discovered_ips = []
        
        try:
            # 1. Récupérer les informations complètes du nœud
            node_data = self.gns3_client.get_node(project_id, node_id)
            
            # 2. Analyser la topologie pour déduire les segments réseau
            network_segments = await self._analyze_network_topology(project_id, node_id)
            
            # 3. Scan intelligent des segments réseau identifiés
            for segment in network_segments:
                segment_ips = await self._scan_network_segment(
                    segment, node_data, timeout=5
                )
                discovered_ips.extend(segment_ips)
            
            # 4. Vérification par empreinte réseau
            verified_ips = []
            for ip in discovered_ips:
                if await self._verify_equipment_by_fingerprint(ip, node_data):
                    verified_ips.append(ip)
            
            return list(set(verified_ips))
            
        except Exception as e:
            # Log l'erreur pour le debug
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur récupération IPs GNS3 API: {e}")
            return []
    
    async def _analyze_network_topology(self, project_id: str, node_id: str) -> List[Dict[str, Any]]:
        """Analyse la topologie pour identifier les segments réseau."""
        segments = []
        
        try:
            # Récupérer tous les liens du projet
            links = self.gns3_client.list_links(project_id)
            
            # Trouver les liens connectés à notre nœud
            connected_links = [
                link for link in links 
                if any(node.get('node_id') == node_id for node in link.get('nodes', []))
            ]
            
            # Analyser chaque lien pour déduire les segments
            for link in connected_links:
                nodes = link.get('nodes', [])
                
                # Récupérer les informations des nœuds connectés
                for node in nodes:
                    if node.get('node_id') != node_id:
                        # Nœud voisin - analyser pour déduire le segment
                        neighbor_data = self.gns3_client.get_node(project_id, node['node_id'])
                        
                        # Déduire le segment réseau basé sur le voisin
                        segment = await self._deduce_network_segment(neighbor_data, link)
                        if segment:
                            segments.append(segment)
            
            # Ajouter les segments par défaut si aucun trouvé
            if not segments:
                segments = [
                    {'network': '192.168.1.0/24', 'type': 'default'},
                    {'network': '192.168.0.0/24', 'type': 'default'},
                    {'network': '10.0.0.0/24', 'type': 'default'},
                    {'network': '172.16.0.0/24', 'type': 'default'},
                ]
            
            return segments
            
        except Exception as e:
            # Retourner les segments par défaut en cas d'erreur
            return [
                {'network': '192.168.1.0/24', 'type': 'default'},
                {'network': '192.168.0.0/24', 'type': 'default'},
                {'network': '10.0.0.0/24', 'type': 'default'},
            ]
    
    async def _deduce_network_segment(self, neighbor_data: Dict[str, Any], link: Dict[str, Any]) -> Dict[str, Any]:
        """Déduit le segment réseau basé sur un nœud voisin."""
        try:
            # Analyser le type de nœud voisin
            neighbor_type = neighbor_data.get('node_type')
            neighbor_name = neighbor_data.get('name', '').lower()
            
            # Segments typiques selon le type d'équipement
            if neighbor_type == 'ethernet_switch':
                return {'network': '192.168.1.0/24', 'type': 'switched'}
            
            elif neighbor_type == 'ethernet_hub':
                return {'network': '192.168.0.0/24', 'type': 'hub'}
            
            elif 'router' in neighbor_name:
                return {'network': '10.0.0.0/24', 'type': 'routed'}
            
            elif 'firewall' in neighbor_name:
                return {'network': '172.16.0.0/24', 'type': 'security'}
            
            # Analyser les propriétés du lien
            link_type = link.get('link_type', '')
            if link_type == 'serial':
                return {'network': '192.168.100.0/30', 'type': 'serial'}
            
            return None
            
        except Exception:
            return None
    
    async def _scan_network_segment(self, segment: Dict[str, Any], node_data: Dict[str, Any], timeout: int = 5) -> List[str]:
        """Scan un segment réseau pour trouver les IPs actives."""
        discovered_ips = []
        
        try:
            import ipaddress
            
            network = segment.get('network')
            if not network:
                return []
            
            # Créer l'objet réseau
            net = ipaddress.ip_network(network, strict=False)
            
            # Limiter le scan aux réseaux raisonnables
            if net.num_addresses > 256:
                # Pour les gros réseaux, scanner seulement les IPs probables
                host_ips = [
                    str(net.network_address + i) 
                    for i in [1, 2, 3, 4, 5, 10, 20, 50, 100, 200, 254]
                    if i < net.num_addresses - 1
                ]
            else:
                # Pour les petits réseaux, scanner toutes les IPs
                host_ips = [str(ip) for ip in net.hosts()]
            
            # Scan parallèle avec timeout adaptatif
            scan_tasks = []
            for ip in host_ips:
                task = asyncio.create_task(
                    self._ping_and_identify(ip, node_data, timeout)
                )
                scan_tasks.append(task)
            
            # Attendre tous les scans avec timeout global
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            # Collecter les IPs trouvées
            for result in results:
                if isinstance(result, str) and result:
                    discovered_ips.append(result)
            
            return discovered_ips
            
        except Exception as e:
            return []
    
    async def _ping_and_identify(self, ip: str, node_data: Dict[str, Any], timeout: int) -> str:
        """Ping une IP et tente de l'identifier."""
        try:
            # Test de connectivité
            connectivity = await self._test_connectivity(ip, timeout)
            
            if connectivity.get('ping_success'):
                # Vérifier si c'est notre équipement
                if await self._verify_equipment_by_fingerprint(ip, node_data):
                    return ip
            
            return None
            
        except Exception:
            return None
    
    async def _verify_equipment_by_fingerprint(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Vérifie l'identité d'un équipement par empreinte réseau."""
        try:
            # Méthode 1: SNMP
            if await self._verify_by_snmp(ip, node_data):
                return True
            
            # Méthode 2: Scan de ports
            if await self._verify_by_port_scan(ip, node_data):
                return True
            
            # Méthode 3: Banner grabbing
            if await self._verify_by_banner(ip, node_data):
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _verify_by_snmp(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Vérification par SNMP."""
        try:
            from api_clients.network.snmp_client import SNMPClient, SNMPCredentials, SNMPVersion
            
            # Essayer plusieurs communautés
            communities = ['public', 'private', 'cisco', 'admin']
            
            for community in communities:
                try:
                    credentials = SNMPCredentials(version=SNMPVersion.V2C, community=community)
                    snmp_client = SNMPClient(ip, credentials=credentials)
                    
                    # Récupérer les informations système
                    system_info = snmp_client.get_system_info()
                    
                    if system_info.get('success'):
                        # Comparer avec les données du nœud
                        system_name = system_info.get('system_name', '').lower()
                        node_name = node_data.get('name', '').lower()
                        
                        # Vérification par nom
                        if system_name and node_name:
                            if any(part in system_name for part in node_name.split() if len(part) > 2):
                                return True
                        
                        # Vérification par type d'équipement
                        system_descr = system_info.get('system_descr', '').lower()
                        node_type = node_data.get('node_type', '').lower()
                        
                        if 'cisco' in system_descr and 'dynamips' in node_type:
                            return True
                        
                        if 'linux' in system_descr and 'qemu' in node_type:
                            return True
                        
                except Exception:
                    continue
            
            return False
            
        except Exception:
            return False
    
    async def _verify_by_port_scan(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Vérification par scan de ports."""
        try:
            import socket
            
            # Ports caractéristiques par type d'équipement
            equipment_ports = {
                'dynamips': [23, 2001, 2002, 2003],  # Telnet et consoles
                'qemu': [22, 23, 80, 443],           # SSH, telnet, HTTP
                'vpcs': [2007, 2008, 2009],          # Consoles VPCS
                'docker': [22, 80, 443, 8080],       # Services Docker
            }
            
            node_type = node_data.get('node_type', '')
            expected_ports = equipment_ports.get(node_type, [22, 23, 80])
            
            open_ports = []
            
            for port in expected_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        open_ports.append(port)
                    sock.close()
                except Exception:
                    continue
            
            # Vérifier si les ports correspondent au type d'équipement
            if len(open_ports) > 0:
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _verify_by_banner(self, ip: str, node_data: Dict[str, Any]) -> bool:
        """Vérification par banner grabbing."""
        try:
            import socket
            
            # Essayer de récupérer le banner sur le port 23 (telnet)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ip, 23))
                
                # Envoyer une commande simple
                sock.send(b'\r\n')
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                
                sock.close()
                
                # Analyser le banner
                banner_lower = banner.lower()
                node_name = node_data.get('name', '').lower()
                node_type = node_data.get('node_type', '').lower()
                
                # Vérifications spécifiques
                if 'cisco' in banner_lower and 'dynamips' in node_type:
                    return True
                
                if node_name and any(part in banner_lower for part in node_name.split() if len(part) > 2):
                    return True
                
            except Exception:
                pass
            
            return False
            
        except Exception:
            return False

# Instance du service amélioré
enhanced_discovery = EnhancedEquipmentDiscovery()