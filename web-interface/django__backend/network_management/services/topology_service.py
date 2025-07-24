"""
Service Central de Topologie - Pont entre GNS3 et tous les modules.

Ce service centralise la découverte réseau et fournit une API unifiée
pour tous les modules du système NMS.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone

from ..models import NetworkDevice, NetworkInterface, NetworkTopology
from gns3_integration.infrastructure.gns3_detection_service import get_gns3_server_status

logger = logging.getLogger(__name__)


class NetworkTopologyService:
    """
    Service central pour la gestion de la topologie réseau.
    
    Fonctionnalités principales :
    - Synchronisation avec GNS3
    - Découverte automatique d'équipements
    - Cartographie réseau temps réel
    - API unifiée pour tous les modules
    """
    
    def __init__(self):
        """Initialise le service de topologie."""
        self.cache_timeout = 300  # 5 minutes
        self.discovery_cache_key = "network_topology_discovery"
        self.gns3_sync_key = "gns3_topology_sync"
        
    async def sync_with_gns3(self, force_sync: bool = False) -> Dict[str, Any]:
        """
        Synchronise la topologie avec GNS3.
        
        Args:
            force_sync: Force la synchronisation même si GNS3 n'est pas disponible
            
        Returns:
            Résultat de la synchronisation
        """
        sync_result = {
            'success': False,
            'devices_synced': 0,
            'interfaces_synced': 0,
            'topologies_synced': 0,
            'errors': [],
            'gns3_available': False,
            'sync_timestamp': timezone.now().isoformat()
        }
        
        try:
            # Vérifier la disponibilité de GNS3
            gns3_status = await get_gns3_server_status()
            sync_result['gns3_available'] = gns3_status.is_available
            
            if not gns3_status.is_available and not force_sync:
                sync_result['errors'].append("GNS3 server non disponible")
                return sync_result
            
            if gns3_status.is_available:
                # Synchroniser avec GNS3 réel
                sync_result = await self._sync_from_gns3_server(sync_result)
            else:
                # Mode dégradé : utiliser les données en cache
                sync_result = await self._sync_from_cache(sync_result)
                
            # Mettre à jour le cache de synchronisation
            cache.set(self.gns3_sync_key, sync_result, timeout=3600)
            
            sync_result['success'] = True
            logger.info(f"Synchronisation GNS3 terminée - Équipements: {sync_result['devices_synced']}, "
                       f"Interfaces: {sync_result['interfaces_synced']}")
            
        except Exception as e:
            error_msg = f"Erreur lors de la synchronisation GNS3: {e}"
            logger.error(error_msg)
            sync_result['errors'].append(error_msg)
            
        return sync_result
    
    async def _sync_from_gns3_server(self, sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronise depuis le serveur GNS3 réel."""
        try:
            import requests
            
            # Récupérer les projets GNS3
            projects_response = requests.get("http://localhost:3080/v2/projects", timeout=10)
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                
                for project in projects:
                    project_id = project['project_id']
                    project_name = project['name']
                    
                    # Récupérer les nœuds du projet
                    nodes_response = requests.get(
                        f"http://localhost:3080/v2/projects/{project_id}/nodes",
                        timeout=10
                    )
                    
                    if nodes_response.status_code == 200:
                        nodes = nodes_response.json()
                        
                        # Créer/Mettre à jour la topologie
                        topology, created = NetworkTopology.objects.get_or_create(
                            name=f"GNS3-{project_name}",
                            defaults={
                                'description': f"Topologie importée de GNS3 - Projet: {project_name}",
                                'topology_type': 'gns3_imported',
                                'is_active': True,
                                'gns3_project_id': project_id
                            }
                        )
                        
                        if not created:
                            topology.last_sync = timezone.now()
                            topology.save()
                        
                        sync_result['topologies_synced'] += 1
                        
                        # Synchroniser les nœuds comme équipements
                        for node in nodes:
                            device_result = await self._sync_gns3_node_to_device(
                                node, project_id, topology
                            )
                            
                            if device_result['success']:
                                sync_result['devices_synced'] += 1
                                sync_result['interfaces_synced'] += device_result['interfaces_count']
                            else:
                                sync_result['errors'].extend(device_result['errors'])
                        
                        # Récupérer les liens du projet
                        links_response = requests.get(
                            f"http://localhost:3080/v2/projects/{project_id}/links",
                            timeout=10
                        )
                        
                        if links_response.status_code == 200:
                            links = links_response.json()
                            await self._sync_gns3_links(links, topology)
                            
        except Exception as e:
            sync_result['errors'].append(f"Erreur synchronisation serveur GNS3: {e}")
            
        return sync_result
    
    async def _sync_gns3_node_to_device(self, node: Dict, project_id: str, topology: NetworkTopology) -> Dict[str, Any]:
        """Synchronise un nœud GNS3 vers un équipement réseau."""
        result = {
            'success': False,
            'interfaces_count': 0,
            'errors': []
        }
        
        try:
            # Extraire les informations du nœud
            node_id = node['node_id']
            node_name = node['name']
            node_type = node.get('node_type', 'unknown')
            
            # Mapper les types GNS3 vers les types NMS
            device_type_mapping = {
                'dynamips': 'router',
                'qemu': 'server', 
                'vpcs': 'host',
                'ethernet_switch': 'switch',
                'ethernet_hub': 'hub',
                'frame_relay_switch': 'switch',
                'atm_switch': 'switch',
                'docker': 'container',
                'iou': 'router'
            }
            
            device_type = device_type_mapping.get(node_type, 'unknown')
            
            # Récupérer ou créer l'équipement
            device, created = NetworkDevice.objects.get_or_create(
                name=node_name,
                defaults={
                    'device_type': device_type,
                    'vendor': 'GNS3',
                    'model': node.get('template', {}).get('name', 'Unknown'),
                    'ip_address': self._extract_node_ip(node),
                    'status': 'running' if node.get('status') == 'started' else 'stopped',
                    'location': f"GNS3 Project: {project_id}",
                    'is_managed': True,
                    'is_monitored': True,
                    'gns3_node_id': node_id,
                    'gns3_project_id': project_id,
                    'description': f"Importé depuis GNS3 - Type: {node_type}"
                }
            )
            
            # Ajouter à la topologie
            topology.devices.add(device)
            
            # Synchroniser les interfaces (ports GNS3)
            if 'ports' in node:
                interfaces_synced = await self._sync_gns3_ports_to_interfaces(
                    node['ports'], device
                )
                result['interfaces_count'] = interfaces_synced
            
            result['success'] = True
            logger.debug(f"Équipement synchronisé: {node_name} ({device_type})")
            
        except Exception as e:
            error_msg = f"Erreur synchronisation nœud {node.get('name', 'unknown')}: {e}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            
        return result
    
    def _extract_node_ip(self, node: Dict) -> Optional[str]:
        """Extrait l'adresse IP d'un nœud GNS3."""
        try:
            # Chercher dans les propriétés du nœud
            properties = node.get('properties', {})
            
            # Pour les équipements VPCS
            if 'startup_script' in properties:
                script = properties['startup_script']
                if 'ip' in script:
                    # Parser le script VPCS pour extraire l'IP
                    import re
                    ip_match = re.search(r'ip (\d+\.\d+\.\d+\.\d+)', script)
                    if ip_match:
                        return ip_match.group(1)
            
            # Pour les routeurs Dynamips
            if 'startup_config' in properties:
                config = properties['startup_config']
                # Parser la configuration pour les IPs d'interfaces
                import re
                ip_matches = re.findall(r'ip address (\d+\.\d+\.\d+\.\d+)', config)
                if ip_matches:
                    return ip_matches[0]  # Retourner la première IP trouvée
            
            # IP par défaut basée sur la position
            if 'x' in node and 'y' in node:
                # Générer une IP basée sur la position (pour démonstration)
                x = int(node['x']) % 254 + 1
                y = int(node['y']) % 254 + 1
                return f"192.168.{x}.{y}"
                
        except Exception as e:
            logger.debug(f"Impossible d'extraire l'IP du nœud: {e}")
            
        return None
    
    async def _sync_gns3_ports_to_interfaces(self, ports: List[Dict], device: NetworkDevice) -> int:
        """Synchronise les ports GNS3 vers les interfaces réseau."""
        interfaces_synced = 0
        
        try:
            for port in ports:
                port_name = port.get('name', f"Port-{port.get('port_number', 0)}")
                
                interface, created = NetworkInterface.objects.get_or_create(
                    device=device,
                    name=port_name,
                    defaults={
                        'interface_type': 'ethernet',
                        'status': 'up' if port.get('link_type') else 'down',
                        'speed': 1000,  # 1Gbps par défaut
                        'mtu': 1500,
                        'description': f"Interface GNS3 - Port {port.get('port_number', 0)}"
                    }
                )
                
                if created:
                    interfaces_synced += 1
                    
        except Exception as e:
            logger.error(f"Erreur synchronisation interfaces: {e}")
            
        return interfaces_synced
    
    async def _sync_gns3_links(self, links: List[Dict], topology: NetworkTopology):
        """Synchronise les liens GNS3."""
        try:
            for link in links:
                # Traiter les connexions entre nœuds
                nodes = link.get('nodes', [])
                if len(nodes) >= 2:
                    # Créer les relations entre équipements
                    # TODO: Implémenter la gestion des liens dans le modèle
                    pass
                    
        except Exception as e:
            logger.error(f"Erreur synchronisation liens: {e}")
    
    async def _sync_from_cache(self, sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronise depuis les données en cache."""
        try:
            cached_sync = cache.get(self.gns3_sync_key)
            if cached_sync:
                sync_result.update({
                    'devices_synced': cached_sync.get('devices_synced', 0),
                    'interfaces_synced': cached_sync.get('interfaces_synced', 0),
                    'topologies_synced': cached_sync.get('topologies_synced', 0),
                    'cache_mode': True
                })
                logger.info("Utilisation des données de synchronisation en cache")
            else:
                sync_result['errors'].append("Aucune donnée de synchronisation en cache")
                
        except Exception as e:
            sync_result['errors'].append(f"Erreur accès cache: {e}")
            
        return sync_result
    
    async def discover_network_devices(self, scan_ranges: List[str] = None) -> Dict[str, Any]:
        """
        Découvre automatiquement les équipements réseau.
        
        Args:
            scan_ranges: Plages IP à scanner (ex: ['192.168.1.0/24'])
            
        Returns:
            Résultat de la découverte
        """
        discovery_result = {
            'success': False,
            'devices_discovered': 0,
            'devices_updated': 0,
            'scan_ranges': scan_ranges or [],
            'discovery_methods': [],
            'errors': [],
            'timestamp': timezone.now().isoformat()
        }
        
        try:
            # Méthode 1: Découverte via GNS3
            gns3_result = await self.sync_with_gns3()
            if gns3_result['success']:
                discovery_result['devices_discovered'] += gns3_result['devices_synced']
                discovery_result['discovery_methods'].append('gns3_sync')
            
            # Méthode 2: Scan SNMP des plages IP
            if scan_ranges:
                snmp_result = await self._snmp_network_scan(scan_ranges)
                discovery_result['devices_discovered'] += snmp_result['devices_found']
                discovery_result['discovery_methods'].append('snmp_scan')
                discovery_result['errors'].extend(snmp_result['errors'])
            
            # Méthode 3: Découverte ARP
            arp_result = await self._arp_discovery()
            discovery_result['devices_discovered'] += arp_result['devices_found']
            discovery_result['discovery_methods'].append('arp_discovery')
            
            # Méthode 4: Enrichissement avec SNMP des équipements existants
            enrich_result = await self._enrich_existing_devices()
            discovery_result['devices_updated'] += enrich_result['devices_updated']
            discovery_result['discovery_methods'].append('snmp_enrichment')
            
            discovery_result['success'] = True
            
            # Mettre en cache le résultat
            cache.set(self.discovery_cache_key, discovery_result, timeout=self.cache_timeout)
            
            logger.info(f"Découverte réseau terminée - "
                       f"Découverts: {discovery_result['devices_discovered']}, "
                       f"Mis à jour: {discovery_result['devices_updated']}")
            
        except Exception as e:
            error_msg = f"Erreur lors de la découverte réseau: {e}"
            discovery_result['errors'].append(error_msg)
            logger.error(error_msg)
            
        return discovery_result
    
    async def _snmp_network_scan(self, scan_ranges: List[str]) -> Dict[str, Any]:
        """Scan SNMP des plages réseau."""
        result = {
            'devices_found': 0,
            'errors': []
        }
        
        try:
            from api_clients.network.snmp_client import SNMPClient
            import ipaddress
            import asyncio
            
            for range_str in scan_ranges:
                try:
                    network = ipaddress.ip_network(range_str, strict=False)
                    
                    # Scanner en parallèle avec limite de concurrence
                    semaphore = asyncio.Semaphore(10)
                    
                    async def scan_ip(ip):
                        async with semaphore:
                            try:
                                snmp_client = SNMPClient(
                                    host=str(ip),
                                    community='public',
                                    timeout=3,
                                    retries=1
                                )
                                
                                # Test SNMP basique
                                system_info = await asyncio.get_event_loop().run_in_executor(
                                    None, snmp_client.get, '1.3.6.1.2.1.1.1.0'
                                )
                                
                                if system_info and 'value' in system_info:
                                    # Équipement SNMP trouvé
                                    await self._create_discovered_device(str(ip), system_info['value'])
                                    return 1
                                    
                            except:
                                pass
                            return 0
                    
                    # Scanner seulement quelques IPs pour ne pas surcharger
                    ips_to_scan = list(network.hosts())[:50]  # Limiter à 50 IPs
                    tasks = [scan_ip(ip) for ip in ips_to_scan]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    result['devices_found'] += sum(r for r in results if isinstance(r, int))
                    
                except Exception as e:
                    result['errors'].append(f"Erreur scan plage {range_str}: {e}")
                    
        except Exception as e:
            result['errors'].append(f"Erreur scan SNMP: {e}")
            
        return result
    
    async def _arp_discovery(self) -> Dict[str, Any]:
        """Découverte via table ARP."""
        result = {
            'devices_found': 0,
            'errors': []
        }
        
        try:
            import subprocess
            import re
            
            # Exécuter arp -a pour découvrir les équipements
            arp_output = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if arp_output.returncode == 0:
                # Parser la sortie ARP
                arp_lines = arp_output.stdout.strip().split('\n')
                
                for line in arp_lines:
                    # Parser: hostname (ip) at mac [ether] on interface
                    ip_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
                    mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
                    
                    if ip_match and mac_match:
                        ip = ip_match.group(1)
                        mac = mac_match.group(1)
                        
                        # Créer l'équipement découvert
                        created = await self._create_discovered_device(ip, f"ARP Discovery - MAC: {mac}")
                        if created:
                            result['devices_found'] += 1
                            
        except Exception as e:
            result['errors'].append(f"Erreur découverte ARP: {e}")
            
        return result
    
    async def _create_discovered_device(self, ip: str, description: str) -> bool:
        """Crée un équipement découvert."""
        try:
            device, created = NetworkDevice.objects.get_or_create(
                ip_address=ip,
                defaults={
                    'name': f"Discovered-{ip.replace('.', '-')}",
                    'device_type': 'unknown',
                    'vendor': 'Unknown',
                    'model': 'Unknown',
                    'status': 'discovered',
                    'location': 'Auto-discovered',
                    'is_managed': False,
                    'is_monitored': False,
                    'description': description,
                    'discovered_at': timezone.now()
                }
            )
            
            return created
            
        except Exception as e:
            logger.error(f"Erreur création équipement découvert {ip}: {e}")
            return False
    
    async def _enrich_existing_devices(self) -> Dict[str, Any]:
        """Enrichit les équipements existants avec SNMP."""
        result = {
            'devices_updated': 0,
            'errors': []
        }
        
        try:
            from api_clients.network.snmp_client import SNMPClient
            import asyncio
            
            # Récupérer les équipements avec IP mais informations incomplètes
            devices = NetworkDevice.objects.filter(
                ip_address__isnull=False,
                vendor__in=['Unknown', 'GNS3', '']
            ).exclude(ip_address='')
            
            semaphore = asyncio.Semaphore(5)
            
            async def enrich_device(device):
                async with semaphore:
                    try:
                        snmp_client = SNMPClient(
                            host=str(device.ip_address),
                            community='public',
                            timeout=5,
                            retries=2
                        )
                        
                        # Récupérer les informations système
                        system_oids = {
                            'sysDescr': '1.3.6.1.2.1.1.1.0',
                            'sysName': '1.3.6.1.2.1.1.5.0',
                            'sysLocation': '1.3.6.1.2.1.1.6.0',
                            'sysContact': '1.3.6.1.2.1.1.4.0'
                        }
                        
                        updated = False
                        for name, oid in system_oids.items():
                            try:
                                result_data = await asyncio.get_event_loop().run_in_executor(
                                    None, snmp_client.get, oid
                                )
                                
                                if result_data and 'value' in result_data:
                                    value = result_data['value']
                                    
                                    if name == 'sysDescr' and device.description in ['', 'Unknown']:
                                        device.description = value
                                        updated = True
                                    elif name == 'sysName' and device.name.startswith('Discovered-'):
                                        device.name = value
                                        updated = True
                                    elif name == 'sysLocation' and not device.location:
                                        device.location = value
                                        updated = True
                                        
                            except:
                                continue
                        
                        if updated:
                            device.last_seen = timezone.now()
                            device.save()
                            return 1
                            
                    except:
                        pass
                    return 0
            
            # Enrichir en parallèle
            tasks = [enrich_device(device) for device in devices[:20]]  # Limiter à 20
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            result['devices_updated'] = sum(r for r in results if isinstance(r, int))
            
        except Exception as e:
            result['errors'].append(f"Erreur enrichissement: {e}")
            
        return result
    
    def get_topology_summary(self) -> Dict[str, Any]:
        """Récupère un résumé de la topologie réseau."""
        try:
            summary = {
                'devices_total': NetworkDevice.objects.count(),
                'devices_managed': NetworkDevice.objects.filter(is_managed=True).count(),
                'devices_monitored': NetworkDevice.objects.filter(is_monitored=True).count(),
                'devices_online': NetworkDevice.objects.filter(status='running').count(),
                'interfaces_total': NetworkInterface.objects.count(),
                'topologies_total': NetworkTopology.objects.count(),
                'gns3_devices': NetworkDevice.objects.filter(gns3_node_id__isnull=False).count(),
                'discovered_devices': NetworkDevice.objects.filter(status='discovered').count(),
                'device_types': {},
                'vendors': {},
                'last_discovery': cache.get(self.discovery_cache_key, {}).get('timestamp'),
                'last_gns3_sync': cache.get(self.gns3_sync_key, {}).get('sync_timestamp')
            }
            
            # Compter par type d'équipement
            from django.db.models import Count
            device_types = NetworkDevice.objects.values('device_type').annotate(
                count=Count('device_type')
            )
            summary['device_types'] = {dt['device_type']: dt['count'] for dt in device_types}
            
            # Compter par fournisseur
            vendors = NetworkDevice.objects.values('vendor').annotate(
                count=Count('vendor')
            )
            summary['vendors'] = {v['vendor']: v['count'] for v in vendors}
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur récupération résumé topologie: {e}")
            return {}
    
    def get_devices_for_module(self, module_name: str, device_filter: Dict = None) -> List[NetworkDevice]:
        """
        Récupère les équipements pour un module spécifique.
        
        Args:
            module_name: Nom du module (monitoring, dashboard, ai_assistant, etc.)
            device_filter: Filtres supplémentaires
            
        Returns:
            Liste des équipements filtrés
        """
        try:
            # Filtres de base selon le module
            module_filters = {
                'monitoring': {'is_monitored': True, 'status__in': ['running', 'stopped']},
                'dashboard': {'is_managed': True},
                'ai_assistant': {'is_managed': True},
                'api_views': {},  # Tous les équipements
                'gns3_integration': {'gns3_node_id__isnull': False}
            }
            
            base_filter = module_filters.get(module_name, {})
            
            # Ajouter les filtres personnalisés
            if device_filter:
                base_filter.update(device_filter)
            
            devices = NetworkDevice.objects.filter(**base_filter).select_related().prefetch_related('interfaces')
            
            return list(devices)
            
        except Exception as e:
            logger.error(f"Erreur récupération équipements pour {module_name}: {e}")
            return []


# Instance globale du service
topology_service = NetworkTopologyService()