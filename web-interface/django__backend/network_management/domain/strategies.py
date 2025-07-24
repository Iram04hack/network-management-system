"""
Stratégies de découverte réseau pour le module Network Management.

Ce module définit les différentes stratégies de découverte réseau
qui peuvent être utilisées pour découvrir les équipements et topologies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set


class NetworkDiscoveryStrategy(ABC):
    """
    Interface pour les stratégies de découverte réseau.
    
    Cette interface définit le contrat que doit respecter
    toute stratégie de découverte réseau.
    """
    
    @abstractmethod
    def discover_device(self, ip_address: str) -> Dict[str, Any]:
        """
        Découvre un équipement réseau à partir de son adresse IP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement découvert
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        pass
    
    @abstractmethod
    def discover_subnet(self, subnet: str) -> List[Dict[str, Any]]:
        """
        Découvre tous les équipements d'un sous-réseau.
        
        Args:
            subnet: Sous-réseau à découvrir (format CIDR)
            
        Returns:
            Liste des équipements découverts
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        pass
    
    @abstractmethod
    def get_device_interfaces(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des interfaces de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        pass
    
    @abstractmethod
    def get_device_connections(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les connexions d'un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des connexions de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        pass


class SNMPDiscoveryStrategy(NetworkDiscoveryStrategy):
    """
    Stratégie de découverte réseau via SNMP.
    
    Cette stratégie utilise le protocole SNMP pour découvrir
    les équipements et leurs caractéristiques.
    """
    
    def __init__(self, snmp_client, community: str = "public", version: int = 2):
        """
        Initialise la stratégie de découverte SNMP.
        
        Args:
            snmp_client: Client SNMP à utiliser
            community: Communauté SNMP
            version: Version SNMP
        """
        self.snmp_client = snmp_client
        self.community = community
        self.version = version
    
    def discover_device(self, ip_address: str) -> Dict[str, Any]:
        """
        Découvre un équipement réseau via SNMP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement découvert
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # OIDs standards pour les informations de base de l'équipement
        oids = {
            "sysDescr": "1.3.6.1.2.1.1.1.0",
            "sysObjectID": "1.3.6.1.2.1.1.2.0",
            "sysName": "1.3.6.1.2.1.1.5.0",
            "sysLocation": "1.3.6.1.2.1.1.6.0",
            "sysContact": "1.3.6.1.2.1.1.4.0",
            "sysUpTime": "1.3.6.1.2.1.1.3.0",
        }
        
        try:
            # Récupérer les informations de base
            results = self.snmp_client.get_bulk(ip_address, list(oids.values()), self.community, self.version)
            
            # Construire les informations de l'équipement
            device_info = {
                "ip_address": ip_address,
                "description": results.get(oids["sysDescr"], ""),
                "name": results.get(oids["sysName"], f"Device-{ip_address}"),
                "location": results.get(oids["sysLocation"], ""),
                "contact": results.get(oids["sysContact"], ""),
                "uptime": results.get(oids["sysUpTime"], ""),
                "object_id": results.get(oids["sysObjectID"], ""),
            }
            
            # Déterminer le type d'équipement à partir de la description
            if "router" in device_info["description"].lower():
                device_info["device_type"] = "router"
            elif "switch" in device_info["description"].lower():
                device_info["device_type"] = "switch"
            elif "firewall" in device_info["description"].lower():
                device_info["device_type"] = "firewall"
            else:
                device_info["device_type"] = "unknown"
            
            # Ajouter les interfaces
            device_info["interfaces"] = self.get_device_interfaces(ip_address)
            
            return device_info
            
        except Exception as e:
            from ..domain.exceptions import DiscoveryException
            raise DiscoveryException(
                ip_address=ip_address,
                operation="discover_device",
                message=f"Erreur lors de la découverte de l'équipement: {str(e)}"
            )
    
    def discover_subnet(self, subnet: str) -> List[Dict[str, Any]]:
        """
        Découvre tous les équipements d'un sous-réseau via SNMP.
        
        Args:
            subnet: Sous-réseau à découvrir (format CIDR)
            
        Returns:
            Liste des équipements découverts
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        try:
            import ipaddress
            
            # Générer toutes les adresses IP du sous-réseau
            network = ipaddress.IPv4Network(subnet, strict=False)
            
            devices = []
            
            # Scanner chaque adresse IP
            for ip in network.hosts():
                ip_str = str(ip)
                
                try:
                    # Vérifier si l'équipement répond au ping
                    if self._ping(ip_str):
                        # Essayer de récupérer des informations via SNMP
                        try:
                            sysDescr = self.snmp_client.get(ip_str, "1.3.6.1.2.1.1.1.0", self.community, self.version)
                            # Si on arrive ici, l'équipement répond à SNMP
                            device_info = self.discover_device(ip_str)
                            devices.append(device_info)
                        except:
                            # L'équipement ne répond pas à SNMP, l'ignorer
                            pass
                except:
                    # L'équipement ne répond pas au ping, l'ignorer
                    pass
            
            return devices
            
        except Exception as e:
            from ..domain.exceptions import DiscoveryException
            raise DiscoveryException(
                operation="discover_subnet",
                message=f"Erreur lors de la découverte du sous-réseau {subnet}: {str(e)}"
            )
    
    def get_device_interfaces(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau via SNMP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des interfaces de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        try:
            # Récupérer la table des interfaces
            ifTable = self.snmp_client.walk(ip_address, "1.3.6.1.2.1.2.2", self.community, self.version)
            
            interfaces = []
            interface_indexes = set()
            
            # Extraire les index d'interfaces
            for oid, value in ifTable.items():
                if oid.startswith("1.3.6.1.2.1.2.2.1.1."):
                    index = oid.split(".")[-1]
                    interface_indexes.add(index)
            
            # Récupérer les informations pour chaque interface
            for index in interface_indexes:
                interface = {
                    "index": index,
                    "name": ifTable.get(f"1.3.6.1.2.1.2.2.1.2.{index}", ""),
                    "type": ifTable.get(f"1.3.6.1.2.1.2.2.1.3.{index}", ""),
                    "mtu": ifTable.get(f"1.3.6.1.2.1.2.2.1.4.{index}", ""),
                    "speed": ifTable.get(f"1.3.6.1.2.1.2.2.1.5.{index}", ""),
                    "physical_address": ifTable.get(f"1.3.6.1.2.1.2.2.1.6.{index}", ""),
                    "admin_status": ifTable.get(f"1.3.6.1.2.1.2.2.1.7.{index}", ""),
                    "oper_status": ifTable.get(f"1.3.6.1.2.1.2.2.1.8.{index}", ""),
                }
                
                # Convertir le type en texte
                interface_type = int(interface["type"]) if interface["type"].isdigit() else 0
                if interface_type == 6:
                    interface["type_name"] = "ethernet"
                elif interface_type == 24:
                    interface["type_name"] = "loopback"
                elif interface_type == 131:
                    interface["type_name"] = "tunnel"
                elif interface_type == 53:
                    interface["type_name"] = "vlan"
                elif interface_type == 23:
                    interface["type_name"] = "ppp"
                elif interface_type == 1:
                    interface["type_name"] = "other"
                else:
                    interface["type_name"] = "unknown"
                
                # Convertir les statuts en texte
                admin_status = int(interface["admin_status"]) if interface["admin_status"].isdigit() else 0
                if admin_status == 1:
                    interface["admin_status_name"] = "up"
                elif admin_status == 2:
                    interface["admin_status_name"] = "down"
                elif admin_status == 3:
                    interface["admin_status_name"] = "testing"
                else:
                    interface["admin_status_name"] = "unknown"
                
                oper_status = int(interface["oper_status"]) if interface["oper_status"].isdigit() else 0
                if oper_status == 1:
                    interface["oper_status_name"] = "up"
                elif oper_status == 2:
                    interface["oper_status_name"] = "down"
                elif oper_status == 3:
                    interface["oper_status_name"] = "testing"
                elif oper_status == 4:
                    interface["oper_status_name"] = "unknown"
                elif oper_status == 5:
                    interface["oper_status_name"] = "dormant"
                elif oper_status == 6:
                    interface["oper_status_name"] = "not_present"
                else:
                    interface["oper_status_name"] = "unknown"
                
                interfaces.append(interface)
            
            return interfaces
            
        except Exception as e:
            from ..domain.exceptions import DiscoveryException
            raise DiscoveryException(
                ip_address=ip_address,
                operation="get_device_interfaces",
                message=f"Erreur lors de la récupération des interfaces: {str(e)}"
            )
    
    def get_device_connections(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les connexions d'un équipement réseau via SNMP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des connexions de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        # Cette méthode n'utilise pas SNMP pour récupérer les connexions
        # car SNMP ne permet pas de connaître les connexions physiques
        # entre équipements. On utilise plutôt LLDP ou CDP pour cela.
        return []
    
    def _ping(self, ip_address: str) -> bool:
        """
        Vérifie si une adresse IP répond au ping.
        
        Args:
            ip_address: Adresse IP à tester
            
        Returns:
            True si l'adresse répond au ping
        """
        import subprocess
        import platform
        
        # Déterminer la commande ping selon le système d'exploitation
        if platform.system().lower() == "windows":
            ping_cmd = ["ping", "-n", "1", "-w", "1000", ip_address]
        else:
            ping_cmd = ["ping", "-c", "1", "-W", "1", ip_address]
        
        # Exécuter la commande
        try:
            subprocess.check_output(ping_cmd, stderr=subprocess.STDOUT)
            return True
        except:
            return False


class LLDPDiscoveryStrategy(NetworkDiscoveryStrategy):
    """
    Stratégie de découverte réseau via LLDP.
    
    Cette stratégie utilise le protocole LLDP pour découvrir
    les équipements et leurs connexions.
    """
    
    def __init__(self, snmp_client, community: str = "public", version: int = 2):
        """
        Initialise la stratégie de découverte LLDP.
        
        Args:
            snmp_client: Client SNMP à utiliser
            community: Communauté SNMP
            version: Version SNMP
        """
        self.snmp_client = snmp_client
        self.community = community
        self.version = version
        self.snmp_strategy = SNMPDiscoveryStrategy(snmp_client, community, version)
    
    def discover_device(self, ip_address: str) -> Dict[str, Any]:
        """
        Découvre un équipement réseau via LLDP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement découvert
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # Utiliser la stratégie SNMP pour découvrir l'équipement
        return self.snmp_strategy.discover_device(ip_address)
    
    def discover_subnet(self, subnet: str) -> List[Dict[str, Any]]:
        """
        Découvre tous les équipements d'un sous-réseau via LLDP.
        
        Args:
            subnet: Sous-réseau à découvrir (format CIDR)
            
        Returns:
            Liste des équipements découverts
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # Utiliser la stratégie SNMP pour découvrir le sous-réseau
        devices = self.snmp_strategy.discover_subnet(subnet)
        
        # Pour chaque équipement découvert, essayer de récupérer ses voisins LLDP
        discovered_devices = set(device["ip_address"] for device in devices)
        to_discover = set(discovered_devices)
        
        while to_discover:
            ip_address = to_discover.pop()
            
            try:
                # Récupérer les voisins LLDP
                neighbors = self.get_device_connections(ip_address)
                
                for neighbor in neighbors:
                    neighbor_ip = neighbor.get("neighbor_ip")
                    
                    if neighbor_ip and neighbor_ip not in discovered_devices:
                        # Découvrir le voisin
                        try:
                            neighbor_device = self.discover_device(neighbor_ip)
                            devices.append(neighbor_device)
                            discovered_devices.add(neighbor_ip)
                            to_discover.add(neighbor_ip)
                        except:
                            # Ignorer les erreurs
                            pass
            except:
                # Ignorer les erreurs
                pass
        
        return devices
    
    def get_device_interfaces(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau via LLDP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des interfaces de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        # Utiliser la stratégie SNMP pour récupérer les interfaces
        return self.snmp_strategy.get_device_interfaces(ip_address)
    
    def get_device_connections(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les voisins LLDP d'un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des voisins LLDP de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        try:
            # Récupérer la table LLDP des voisins
            lldpRemTable = self.snmp_client.walk(ip_address, "1.0.8802.1.1.2.1.4", self.community, self.version)
            
            connections = []
            
            # Chercher les voisins
            for oid, value in lldpRemTable.items():
                if oid.startswith("1.0.8802.1.1.2.1.4.1.1.9."):  # lldpRemSysName
                    # Extraire les informations de l'OID
                    parts = oid.split(".")
                    if len(parts) >= 3:
                        local_if_index = parts[-3]
                        remote_if_index = parts[-2]
                        
                        # Récupérer les informations du voisin
                        neighbor_name = value
                        neighbor_port_id = lldpRemTable.get(f"1.0.8802.1.1.2.1.4.1.1.7.{local_if_index}.{remote_if_index}", "")
                        neighbor_port_desc = lldpRemTable.get(f"1.0.8802.1.1.2.1.4.1.1.8.{local_if_index}.{remote_if_index}", "")
                        neighbor_ip = lldpRemTable.get(f"1.0.8802.1.1.2.1.4.1.1.5.{local_if_index}.{remote_if_index}", "")
                        
                        # Récupérer le nom de l'interface locale
                        local_if_name = ""
                        interfaces = self.get_device_interfaces(ip_address)
                        for interface in interfaces:
                            if interface["index"] == local_if_index:
                                local_if_name = interface["name"]
                                break
                        
                        connection = {
                            "local_if_index": local_if_index,
                            "local_if_name": local_if_name,
                            "neighbor_name": neighbor_name,
                            "neighbor_port_id": neighbor_port_id,
                            "neighbor_port_desc": neighbor_port_desc,
                            "neighbor_ip": neighbor_ip,
                            "discovery_protocol": "LLDP",
                        }
                        
                        connections.append(connection)
            
            return connections
            
        except Exception as e:
            from ..domain.exceptions import DiscoveryException
            raise DiscoveryException(
                ip_address=ip_address,
                operation="get_device_connections",
                message=f"Erreur lors de la récupération des voisins LLDP: {str(e)}"
            )


class CDPDiscoveryStrategy(NetworkDiscoveryStrategy):
    """
    Stratégie de découverte réseau via CDP.
    
    Cette stratégie utilise le protocole CDP pour découvrir
    les équipements et leurs connexions.
    """
    
    def __init__(self, snmp_client, community: str = "public", version: int = 2):
        """
        Initialise la stratégie de découverte CDP.
        
        Args:
            snmp_client: Client SNMP à utiliser
            community: Communauté SNMP
            version: Version SNMP
        """
        self.snmp_client = snmp_client
        self.community = community
        self.version = version
        self.snmp_strategy = SNMPDiscoveryStrategy(snmp_client, community, version)
    
    def discover_device(self, ip_address: str) -> Dict[str, Any]:
        """
        Découvre un équipement réseau via CDP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement découvert
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # Utiliser la stratégie SNMP pour découvrir l'équipement
        return self.snmp_strategy.discover_device(ip_address)
    
    def discover_subnet(self, subnet: str) -> List[Dict[str, Any]]:
        """
        Découvre tous les équipements d'un sous-réseau via CDP.
        
        Args:
            subnet: Sous-réseau à découvrir (format CIDR)
            
        Returns:
            Liste des équipements découverts
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # Utiliser la stratégie SNMP pour découvrir le sous-réseau
        devices = self.snmp_strategy.discover_subnet(subnet)
        
        # Pour chaque équipement découvert, essayer de récupérer ses voisins CDP
        discovered_devices = set(device["ip_address"] for device in devices)
        to_discover = set(discovered_devices)
        
        while to_discover:
            ip_address = to_discover.pop()
            
            try:
                # Récupérer les voisins CDP
                neighbors = self.get_device_connections(ip_address)
                
                for neighbor in neighbors:
                    neighbor_ip = neighbor.get("neighbor_ip")
                    
                    if neighbor_ip and neighbor_ip not in discovered_devices:
                        # Découvrir le voisin
                        try:
                            neighbor_device = self.discover_device(neighbor_ip)
                            devices.append(neighbor_device)
                            discovered_devices.add(neighbor_ip)
                            to_discover.add(neighbor_ip)
                        except:
                            # Ignorer les erreurs
                            pass
            except:
                # Ignorer les erreurs
                pass
        
        return devices
    
    def get_device_interfaces(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau via CDP.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des interfaces de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        # Utiliser la stratégie SNMP pour récupérer les interfaces
        return self.snmp_strategy.get_device_interfaces(ip_address)
    
    def get_device_connections(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les voisins CDP d'un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des voisins CDP de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        try:
            # Récupérer la table CDP des voisins
            cdpCacheTable = self.snmp_client.walk(ip_address, "1.3.6.1.4.1.9.9.23.1.2.1.1", self.community, self.version)
            
            connections = []
            
            # Chercher les voisins
            for oid, value in cdpCacheTable.items():
                if oid.startswith("1.3.6.1.4.1.9.9.23.1.2.1.1.6."):  # cdpCacheDeviceId
                    # Extraire les informations de l'OID
                    parts = oid.split(".")
                    if len(parts) >= 3:
                        local_if_index = parts[-2]
                        cache_index = parts[-1]
                        
                        # Récupérer les informations du voisin
                        neighbor_name = value
                        neighbor_port_id = cdpCacheTable.get(f"1.3.6.1.4.1.9.9.23.1.2.1.1.7.{local_if_index}.{cache_index}", "")
                        neighbor_ip = cdpCacheTable.get(f"1.3.6.1.4.1.9.9.23.1.2.1.1.4.{local_if_index}.{cache_index}", "")
                        
                        # Récupérer le nom de l'interface locale
                        local_if_name = ""
                        interfaces = self.get_device_interfaces(ip_address)
                        for interface in interfaces:
                            if interface["index"] == local_if_index:
                                local_if_name = interface["name"]
                                break
                        
                        connection = {
                            "local_if_index": local_if_index,
                            "local_if_name": local_if_name,
                            "neighbor_name": neighbor_name,
                            "neighbor_port_id": neighbor_port_id,
                            "neighbor_ip": neighbor_ip,
                            "discovery_protocol": "CDP",
                        }
                        
                        connections.append(connection)
            
            return connections
            
        except Exception as e:
            from ..domain.exceptions import DiscoveryException
            raise DiscoveryException(
                ip_address=ip_address,
                operation="get_device_connections",
                message=f"Erreur lors de la récupération des voisins CDP: {str(e)}"
            )


class MultiProtocolDiscoveryStrategy(NetworkDiscoveryStrategy):
    """
    Stratégie de découverte réseau multi-protocoles.
    
    Cette stratégie combine plusieurs protocoles (LLDP, CDP, SNMP)
    pour découvrir les équipements et leurs connexions.
    """
    
    def __init__(self, snmp_client, community: str = "public", version: int = 2):
        """
        Initialise la stratégie de découverte multi-protocoles.
        
        Args:
            snmp_client: Client SNMP à utiliser
            community: Communauté SNMP
            version: Version SNMP
        """
        self.snmp_client = snmp_client
        self.community = community
        self.version = version
        
        # Initialiser les stratégies individuelles
        self.snmp_strategy = SNMPDiscoveryStrategy(snmp_client, community, version)
        self.lldp_strategy = LLDPDiscoveryStrategy(snmp_client, community, version)
        self.cdp_strategy = CDPDiscoveryStrategy(snmp_client, community, version)
    
    def discover_device(self, ip_address: str) -> Dict[str, Any]:
        """
        Découvre un équipement réseau en utilisant plusieurs protocoles.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Informations sur l'équipement découvert
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # Utiliser SNMP pour la découverte de base
        device_info = self.snmp_strategy.discover_device(ip_address)
        
        # Ajouter les connexions LLDP et CDP
        device_info["connections"] = self.get_device_connections(ip_address)
        
        return device_info
    
    def discover_subnet(self, subnet: str) -> List[Dict[str, Any]]:
        """
        Découvre tous les équipements d'un sous-réseau.
        
        Args:
            subnet: Sous-réseau à découvrir (format CIDR)
            
        Returns:
            Liste des équipements découverts
            
        Raises:
            DiscoveryException: Si la découverte échoue
        """
        # Utiliser SNMP pour la découverte initiale
        devices = self.snmp_strategy.discover_subnet(subnet)
        
        # Pour chaque équipement découvert, essayer de récupérer ses voisins
        discovered_devices = {device["ip_address"]: device for device in devices}
        to_discover = set(discovered_devices.keys())
        
        while to_discover:
            ip_address = to_discover.pop()
            
            try:
                # Récupérer les voisins
                connections = self.get_device_connections(ip_address)
                
                # Mettre à jour l'équipement avec ses connexions
                if ip_address in discovered_devices:
                    discovered_devices[ip_address]["connections"] = connections
                
                for connection in connections:
                    neighbor_ip = connection.get("neighbor_ip")
                    
                    if neighbor_ip and neighbor_ip not in discovered_devices:
                        # Découvrir le voisin
                        try:
                            neighbor_device = self.discover_device(neighbor_ip)
                            discovered_devices[neighbor_ip] = neighbor_device
                            to_discover.add(neighbor_ip)
                        except:
                            # Ignorer les erreurs
                            pass
            except:
                # Ignorer les erreurs
                pass
        
        return list(discovered_devices.values())
    
    def get_device_interfaces(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des interfaces de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        # Utiliser SNMP pour récupérer les interfaces
        return self.snmp_strategy.get_device_interfaces(ip_address)
    
    def get_device_connections(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Récupère les connexions d'un équipement réseau.
        
        Args:
            ip_address: Adresse IP de l'équipement
            
        Returns:
            Liste des connexions de l'équipement
            
        Raises:
            DiscoveryException: Si la récupération échoue
        """
        all_connections = []
        
        # Essayer de récupérer les voisins LLDP
        try:
            lldp_connections = self.lldp_strategy.get_device_connections(ip_address)
            all_connections.extend(lldp_connections)
        except:
            # Ignorer les erreurs
            pass
        
        # Essayer de récupérer les voisins CDP
        try:
            cdp_connections = self.cdp_strategy.get_device_connections(ip_address)
            all_connections.extend(cdp_connections)
        except:
            # Ignorer les erreurs
            pass
        
        return all_connections 