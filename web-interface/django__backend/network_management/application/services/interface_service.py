"""
Module contenant le service d'interface.
"""

from typing import List, Optional, Dict, Any

from ...domain.entities import NetworkInterfaceEntity
from ...domain.interfaces import NetworkInterfaceRepository
from ..ports.input_ports import NetworkInterfaceUseCases
from ...domain.exceptions import NetworkInterfaceNotFoundException, ValidationException


class InterfaceService(NetworkInterfaceUseCases):
    """
    Service pour la gestion des interfaces réseau.

    Cette classe implémente l'interface NetworkInterfaceUseCases
    et fournit les fonctionnalités de gestion des interfaces réseau.
    """
    
    def __init__(self, interface_repository: NetworkInterfaceRepository):
        """
        Initialise une nouvelle instance de InterfaceService.

        Args:
            interface_repository (NetworkInterfaceRepository): Le repository d'interfaces à utiliser.
        """
        self._repository = interface_repository
    
    def get_interface(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère une interface par son ID.

        Args:
            interface_id (int): L'ID de l'interface à récupérer.

        Returns:
            Dict[str, Any]: Les informations de l'interface.

        Raises:
            NetworkInterfaceNotFoundException: Si l'interface n'a pas été trouvée.
        """
        interface = self._repository.get_by_id(interface_id)
        if not interface:
            raise NetworkInterfaceNotFoundException(str(interface_id))
        
        return {
            'id': interface.id,
            'name': interface.name,
            'device_id': interface.device_id,
            'description': interface.description,
            'interface_type': interface.interface_type,
            'status': interface.status,
            'mac_address': interface.mac_address,
            'ip_address': interface.ip_address,
            'subnet_mask': interface.subnet_mask,
            'speed': interface.speed,
            'duplex': interface.duplex,
            'mtu': interface.mtu,
            'is_trunk': interface.is_trunk,
            'vlan_id': interface.vlan_id,
            'enabled': interface.enabled,
            'created_at': interface.created_at,
            'updated_at': interface.updated_at
        }
    
    def get_interface_by_name_and_device(self, device_id: int, name: str) -> Dict[str, Any]:
        """
        Récupère une interface réseau par son nom et l'ID de son équipement.
        
        Args:
            device_id: ID de l'équipement
            name: Nom de l'interface
            
        Returns:
            Informations sur l'interface
        """
        interface = self._repository.get_by_name_and_device(device_id, name)
        if not interface:
            raise NetworkInterfaceNotFoundException(f"Interface '{name}' on device {device_id}")
        
        return {
            'id': interface.id,
            'name': interface.name,
            'device_id': interface.device_id,
            'description': interface.description,
            'interface_type': interface.interface_type,
            'status': interface.status,
            'mac_address': interface.mac_address,
            'ip_address': interface.ip_address,
            'subnet_mask': interface.subnet_mask,
            'speed': interface.speed,
            'duplex': interface.duplex,
            'mtu': interface.mtu,
            'is_trunk': interface.is_trunk,
            'vlan_id': interface.vlan_id,
            'enabled': interface.enabled,
            'created_at': interface.created_at,
            'updated_at': interface.updated_at
        }
    
    def update_interface(self, interface_id: int, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une interface réseau.
        
        Args:
            interface_id: ID de l'interface
            interface_data: Nouvelles données
            
        Returns:
            Interface mise à jour
        """
        # Récupérer l'interface existante
        existing_interface = self._repository.get_by_id(interface_id)
        if not existing_interface:
            raise NetworkInterfaceNotFoundException(str(interface_id))
        
        # Valider les données
        self._validate_interface_data(interface_data)
        
        # Mettre à jour l'interface
        for key, value in interface_data.items():
            if hasattr(existing_interface, key):
                setattr(existing_interface, key, value)
        
        updated_interface = self._repository.update(existing_interface)
        
        return {
            'id': updated_interface.id,
            'name': updated_interface.name,
            'device_id': updated_interface.device_id,
            'description': updated_interface.description,
            'interface_type': updated_interface.interface_type,
            'status': updated_interface.status,
            'mac_address': updated_interface.mac_address,
            'ip_address': updated_interface.ip_address,
            'subnet_mask': updated_interface.subnet_mask,
            'speed': updated_interface.speed,
            'duplex': updated_interface.duplex,
            'mtu': updated_interface.mtu,
            'is_trunk': updated_interface.is_trunk,
            'vlan_id': updated_interface.vlan_id,
            'enabled': updated_interface.enabled,
            'created_at': updated_interface.created_at,
            'updated_at': updated_interface.updated_at
        }
    
    def get_interface_statistics(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une interface réseau.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Statistiques de l'interface
        """
        # Vérifier que l'interface existe
        interface = self._repository.get_by_id(interface_id)
        if not interface:
            raise NetworkInterfaceNotFoundException(str(interface_id))
        
        # Implémenter la collecte de statistiques réelles via SNMP
        return self._collect_real_interface_statistics(interface_id, interface)
    
    def _collect_real_interface_statistics(self, interface_id: int, interface) -> Dict[str, Any]:
        """
        Collecte les vraies statistiques d'interface via SNMP.
        
        Args:
            interface_id: ID de l'interface
            interface: Entité interface
            
        Returns:
            Statistiques réelles de l'interface
        """
        try:
            from api_clients.network.snmp_client import SNMPClient
            from datetime import datetime
            import asyncio
            
            # Récupérer l'équipement parent
            device = self._device_repository.get_by_id(interface.device_id)
            if not device or not device.ip_address:
                return self._get_default_stats(interface_id, "Équipement sans IP")
            
            # Initialiser le client SNMP
            snmp_client = SNMPClient(
                host=str(device.ip_address),
                community=device.snmp_community or 'public',
                port=device.snmp_port or 161,
                timeout=5,
                retries=2
            )
            
            # OIDs pour les statistiques d'interface (RFC 1213 - MIB-II)
            interface_index = interface.snmp_index or self._get_interface_index(interface, snmp_client)
            
            if not interface_index:
                return self._get_default_stats(interface_id, "Index SNMP introuvable")
            
            # OIDs pour les compteurs d'interface
            oids = {
                'ifInOctets': f'1.3.6.1.2.1.2.2.1.10.{interface_index}',      # Octets entrants
                'ifOutOctets': f'1.3.6.1.2.1.2.2.1.16.{interface_index}',     # Octets sortants
                'ifInUcastPkts': f'1.3.6.1.2.1.2.2.1.11.{interface_index}',   # Paquets unicast entrants
                'ifOutUcastPkts': f'1.3.6.1.2.1.2.2.1.17.{interface_index}',  # Paquets unicast sortants
                'ifInErrors': f'1.3.6.1.2.1.2.2.1.14.{interface_index}',      # Erreurs entrantes
                'ifOutErrors': f'1.3.6.1.2.1.2.2.1.20.{interface_index}',     # Erreurs sortantes
                'ifInDiscards': f'1.3.6.1.2.1.2.2.1.13.{interface_index}',    # Drops entrants
                'ifOutDiscards': f'1.3.6.1.2.1.2.2.1.19.{interface_index}',   # Drops sortants
                'ifSpeed': f'1.3.6.1.2.1.2.2.1.5.{interface_index}',          # Vitesse interface
                'ifOperStatus': f'1.3.6.1.2.1.2.2.1.8.{interface_index}'      # Statut opérationnel
            }
            
            # Collecter les données SNMP
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                stats_data = {}
                for name, oid in oids.items():
                    try:
                        result = loop.run_until_complete(
                            asyncio.get_event_loop().run_in_executor(
                                None, snmp_client.get, oid
                            )
                        )
                        if result and 'value' in result:
                            stats_data[name] = int(result['value'])
                        else:
                            stats_data[name] = 0
                    except (ValueError, TypeError):
                        stats_data[name] = 0
                    except Exception as e:
                        logger.debug(f"Erreur SNMP pour {name}: {e}")
                        stats_data[name] = 0
            finally:
                loop.close()
            
            # Calculer l'utilisation (si vitesse disponible)
            utilization = 0.0
            if stats_data.get('ifSpeed', 0) > 0:
                total_octets = stats_data.get('ifInOctets', 0) + stats_data.get('ifOutOctets', 0)
                # Approximation basique : octets/sec par rapport à la capacité
                utilization = min((total_octets * 8) / stats_data['ifSpeed'] * 100, 100.0)
            
            # Retourner les statistiques réelles
            return {
                'interface_id': interface_id,
                'bytes_in': stats_data.get('ifInOctets', 0),
                'bytes_out': stats_data.get('ifOutOctets', 0),
                'packets_in': stats_data.get('ifInUcastPkts', 0),
                'packets_out': stats_data.get('ifOutUcastPkts', 0),
                'errors_in': stats_data.get('ifInErrors', 0),
                'errors_out': stats_data.get('ifOutErrors', 0),
                'drops_in': stats_data.get('ifInDiscards', 0),
                'drops_out': stats_data.get('ifOutDiscards', 0),
                'utilization': round(utilization, 2),
                'speed_bps': stats_data.get('ifSpeed', 0),
                'operational_status': stats_data.get('ifOperStatus', 1),
                'last_updated': datetime.now().isoformat(),
                'collection_method': 'snmp_real'
            }
            
        except ImportError:
            logger.warning("Client SNMP non disponible - utilisation de données par défaut")
            return self._get_default_stats(interface_id, "Client SNMP indisponible")
        except Exception as e:
            logger.error(f"Erreur collecte statistiques interface {interface_id}: {e}")
            return self._get_default_stats(interface_id, f"Erreur SNMP: {str(e)}")
    
    def _get_interface_index(self, interface, snmp_client) -> Optional[int]:
        """
        Trouve l'index SNMP d'une interface.
        
        Args:
            interface: Entité interface
            snmp_client: Client SNMP
            
        Returns:
            Index SNMP de l'interface ou None
        """
        try:
            import asyncio
            
            # Table des noms d'interfaces (ifName)
            ifname_base_oid = '1.3.6.1.2.1.2.2.1.2'
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Parcourir les index pour trouver le nom correspondant
                for index in range(1, 50):  # Limiter à 50 interfaces
                    try:
                        result = loop.run_until_complete(
                            asyncio.get_event_loop().run_in_executor(
                                None, snmp_client.get, f'{ifname_base_oid}.{index}'
                            )
                        )
                        
                        if result and 'value' in result:
                            if result['value'].lower() == interface.name.lower():
                                return index
                    except:
                        continue
            finally:
                loop.close()
            
        except Exception as e:
            logger.debug(f"Erreur recherche index SNMP: {e}")
        
        return None
    
    def _get_default_stats(self, interface_id: int, reason: str = "Données par défaut") -> Dict[str, Any]:
        """
        Retourne des statistiques par défaut quand SNMP n'est pas disponible.
        
        Args:
            interface_id: ID de l'interface
            reason: Raison du fallback
            
        Returns:
            Statistiques par défaut
        """
        from datetime import datetime
        
        return {
            'interface_id': interface_id,
            'bytes_in': 0,
            'bytes_out': 0,
            'packets_in': 0,
            'packets_out': 0,
            'errors_in': 0,
            'errors_out': 0,
            'drops_in': 0,
            'drops_out': 0,
            'utilization': 0.0,
            'speed_bps': 0,
            'operational_status': 1,
            'last_updated': datetime.now().isoformat(),
            'collection_method': 'default',
            'reason': reason
        }
    
    def get_interfaces_by_device(self, device_id: int) -> List[NetworkInterfaceEntity]:
        """
        Récupère les interfaces d'un équipement.

        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les interfaces.

        Returns:
            List[NetworkInterfaceEntity]: Une liste contenant les interfaces de l'équipement.
        """
        return self._repository.get_by_device_id(device_id)
    
    def create_interface(self, interface_data: Dict[str, Any]) -> NetworkInterfaceEntity:
        """
        Crée une nouvelle interface.

        Args:
            interface_data (Dict[str, Any]): Les données de l'interface à créer.

        Returns:
            NetworkInterfaceEntity: L'interface créée.

        Raises:
            ValidationException: Si les données de l'interface sont invalides.
        """
        # Valider les données
        self._validate_interface_data(interface_data)

        # Créer l'interface
        interface = NetworkInterfaceEntity(**interface_data)
        return self._repository.create(interface)
    
    def delete_interface(self, interface_id: int) -> bool:
        """
        Supprime une interface.
        
        Args:
            interface_id (int): L'ID de l'interface à supprimer.
            
        Returns:
            bool: True si l'interface a été supprimée, False sinon.
            
        Raises:
            NetworkInterfaceNotFoundException: Si l'interface n'a pas été trouvée.
        """
        # Vérifier que l'interface existe
        if not self._repository.get_by_id(interface_id):
            raise NetworkInterfaceNotFoundException(str(interface_id))
        
        # Supprimer l'interface
        return self._repository.delete(interface_id)
    
    def search_interfaces(self, query: str) -> List[NetworkInterfaceEntity]:
        """
        Recherche des interfaces.

        Args:
            query (str): Le terme de recherche.

        Returns:
            List[NetworkInterfaceEntity]: Une liste contenant les interfaces trouvées.
        """
        return self._repository.search(query)
    
    def _validate_interface_data(self, interface_data: Dict[str, Any]) -> None:
        """
        Valide les données d'une interface.
        
        Args:
            interface_data (Dict[str, Any]): Les données de l'interface à valider.
            
        Raises:
            ValidationException: Si les données de l'interface sont invalides.
        """
        # Vérifier que les champs obligatoires sont présents pour la création
        if 'name' in interface_data and not interface_data['name']:
            raise ValidationException("Interface name cannot be empty")
        
        # Vérifier que l'adresse MAC est valide si elle est présente
        if 'mac_address' in interface_data and interface_data['mac_address']:
            if not self._is_valid_mac_address(interface_data['mac_address']):
                raise ValidationException("Invalid MAC address format")
        
        # Vérifier que l'adresse IP est valide si elle est présente
        if 'ip_address' in interface_data and interface_data['ip_address']:
            if not self._is_valid_ip_address(interface_data['ip_address']):
                raise ValidationException("Invalid IP address format")
    
    def _is_valid_mac_address(self, mac_address: str) -> bool:
        """
        Vérifie si une adresse MAC est valide.
        
        Args:
            mac_address (str): L'adresse MAC à vérifier.
            
        Returns:
            bool: True si l'adresse MAC est valide, False sinon.
        """
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac_address))
    
    def _is_valid_ip_address(self, ip_address: str) -> bool:
        """
        Vérifie si une adresse IP est valide.
        
        Args:
            ip_address (str): L'adresse IP à vérifier.
            
        Returns:
            bool: True si l'adresse IP est valide, False sinon.
        """
        import re
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip_address)
        if not match:
            return False
        
        # Vérifier que chaque octet est entre 0 et 255
        octets = [int(group) for group in match.groups()]
        return all(0 <= octet <= 255 for octet in octets) 