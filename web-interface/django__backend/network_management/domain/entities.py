"""
Entités du domaine pour le module Network Management.

Ce module définit les classes de base du domaine, qui représentent
les concepts métier dans la gestion des réseaux.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union, Any


class DeviceType(Enum):
    """Types d'équipements réseau supportés."""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    ACCESS_POINT = "access_point"
    SERVER = "server"
    UNKNOWN = "unknown"


class DeviceStatus(Enum):
    """États possibles d'un équipement réseau."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class InterfaceType(Enum):
    """Types d'interfaces réseau supportés."""
    ETHERNET = "ethernet"
    FASTETHERNET = "fastethernet"
    GIGABITETHERNET = "gigabitethernet"
    TENGIGABITETHERNET = "tengigabitethernet"
    SERIAL = "serial"
    LOOPBACK = "loopback"
    TUNNEL = "tunnel"
    VLAN = "vlan"
    PORTCHANNEL = "portchannel"
    VIRTUAL = "virtual"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    OTHER = "other"
    UNKNOWN = "unknown"


class InterfaceStatus(Enum):
    """États possibles d'une interface réseau."""
    UP = "up"
    DOWN = "down"
    TESTING = "testing"
    UNKNOWN = "unknown"
    DORMANT = "dormant"
    NOT_PRESENT = "not_present"
    LOWER_LAYER_DOWN = "lower_layer_down"


class ProtocolType(Enum):
    """Types de protocoles supportés pour les connexions."""
    SSH = "ssh"
    TELNET = "telnet"
    SNMP = "snmp"
    HTTP = "http"
    HTTPS = "https"
    NETCONF = "netconf"
    REST = "rest"
    UNKNOWN = "unknown"


class ConfigurationType(Enum):
    """Types de configurations d'équipements."""
    RUNNING = "running"
    STARTUP = "startup"
    CANDIDATE = "candidate"
    BACKUP = "backup"


@dataclass
class Credentials:
    """
    Informations d'authentification pour les équipements réseau.
    
    Cette classe encapsule les différents types d'informations d'authentification
    nécessaires pour se connecter aux équipements réseau.
    """
    
    protocol: ProtocolType
    username: Optional[str] = None
    password: Optional[str] = None
    enable_password: Optional[str] = None
    community: Optional[str] = None  # Pour SNMP
    private_key: Optional[str] = None  # Pour SSH avec clé
    api_key: Optional[str] = None  # Pour REST
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "protocol": self.protocol.value,
            "username": self.username,
            "password": self.password,
            "enable_password": self.enable_password,
            "community": self.community,
            "private_key": self.private_key,
            "api_key": self.api_key,
        }


@dataclass
class DeviceStatusEntity:
    """
    Entité représentant le statut opérationnel d'un équipement réseau.
    
    Cette classe encapsule toutes les informations liées
    au statut opérationnel d'un équipement réseau.
    """
    
    status: DeviceStatus = DeviceStatus.UNKNOWN
    last_seen: Optional[datetime] = None
    uptime: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    temperature: Optional[float] = None
    alerts: List[str] = field(default_factory=list)
    
    def update(self, new_status: DeviceStatus) -> None:
        """
        Met à jour le statut de l'équipement.
        
        Args:
            new_status: Nouveau statut
        """
        self.status = new_status
        self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "uptime": self.uptime,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "temperature": self.temperature,
            "alerts": self.alerts,
        }


@dataclass
class NetworkInterfaceEntity:
    """
    Entité représentant une interface réseau.
    
    Cette entité contient toutes les informations d'une interface réseau
    et est liée à un équipement réseau.
    """
    
    name: str
    interface_type: InterfaceType
    status: InterfaceStatus = InterfaceStatus.UNKNOWN
    id: Optional[int] = None
    description: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    speed: Optional[int] = None
    mtu: Optional[int] = None
    vlan: Optional[int] = None
    device_id: Optional[int] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: InterfaceStatus) -> None:
        """
        Met à jour le statut de l'interface.
        
        Args:
            new_status: Nouveau statut
        """
        self.status = new_status
    
    def set_ip_configuration(self, ip_address: str, subnet_mask: str) -> None:
        """
        Configure l'adresse IP et le masque de sous-réseau.
        
        Args:
            ip_address: Adresse IP
            subnet_mask: Masque de sous-réseau
        """
        self.ip_address = ip_address
        self.subnet_mask = subnet_mask
    
    def update_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Met à jour les statistiques de l'interface.
        
        Args:
            stats: Nouvelles statistiques
        """
        self.statistics.update(stats)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "id": self.id,
            "name": self.name,
            "interface_type": self.interface_type.value,
            "status": self.status.value,
            "description": self.description,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "subnet_mask": self.subnet_mask,
            "speed": self.speed,
            "mtu": self.mtu,
            "vlan": self.vlan,
            "device_id": self.device_id,
            "statistics": self.statistics,
        }


@dataclass
class DeviceIdentityEntity:
    """
    Entité représentant l'identité d'un équipement réseau.
    
    Cette entité encapsule les informations d'identification
    d'un équipement réseau.
    """
    
    name: str
    ip_address: str
    device_type: DeviceType
    id: Optional[int] = None
    description: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "id": self.id,
            "name": self.name,
            "ip_address": self.ip_address,
            "device_type": self.device_type.value,
            "description": self.description,
            "model": self.model,
            "manufacturer": self.manufacturer,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "location": self.location,
            "contact": self.contact,
        }


@dataclass
class DeviceCredentialsEntity:
    """
    Entité représentant les informations d'authentification d'un équipement réseau.
    
    Cette entité encapsule les différentes informations d'authentification
    pour chaque protocole supporté par l'équipement.
    """
    
    device_id: Optional[int] = None
    credentials: Dict[ProtocolType, Credentials] = field(default_factory=dict)
    
    def add_credentials(self, credentials: Credentials) -> None:
        """
        Ajoute des informations d'authentification pour un protocole.
        
        Args:
            credentials: Informations d'authentification
        """
        self.credentials[credentials.protocol] = credentials
    
    def get_credentials(self, protocol: ProtocolType) -> Optional[Credentials]:
        """
        Récupère les informations d'authentification pour un protocole.
        
        Args:
            protocol: Type de protocole
            
        Returns:
            Informations d'authentification ou None si non trouvées
        """
        return self.credentials.get(protocol)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "device_id": self.device_id,
            "credentials": {protocol.value: cred.to_dict() for protocol, cred in self.credentials.items()},
        }


@dataclass
class NetworkDeviceEntity:
    """
    Entité représentant un équipement réseau.
    
    Cette entité agrège les différentes composantes d'un équipement réseau
    et constitue le cœur du modèle de domaine.
    """
    
    identity: DeviceIdentityEntity
    id: Optional[int] = None
    status: DeviceStatusEntity = field(default_factory=DeviceStatusEntity)
    interfaces: List[NetworkInterfaceEntity] = field(default_factory=list)
    credentials: DeviceCredentialsEntity = field(default_factory=DeviceCredentialsEntity)
    
    def __post_init__(self):
        """Initialisation après création."""
        # Synchroniser l'ID entre l'entité principale et ses composantes
        if self.id is not None:
            self.identity.id = self.id
            self.credentials.device_id = self.id
    
    @property
    def name(self) -> str:
        """Nom de l'équipement."""
        return self.identity.name
    
    @property
    def ip_address(self) -> str:
        """Adresse IP de l'équipement."""
        return self.identity.ip_address
    
    @property
    def device_type(self) -> DeviceType:
        """Type de l'équipement."""
        return self.identity.device_type
    
    def add_interface(self, interface: NetworkInterfaceEntity) -> None:
        """
        Ajoute une interface à l'équipement.
        
        Args:
            interface: Interface à ajouter
        """
        interface.device_id = self.id
        self.interfaces.append(interface)
    
    def remove_interface(self, interface_id: int) -> bool:
        """
        Supprime une interface de l'équipement.
        
        Args:
            interface_id: ID de l'interface à supprimer
            
        Returns:
            True si l'interface a été supprimée
        """
        for i, interface in enumerate(self.interfaces):
            if interface.id == interface_id:
                self.interfaces.pop(i)
                return True
        return False
    
    def get_interface(self, interface_id: int) -> Optional[NetworkInterfaceEntity]:
        """
        Récupère une interface par son ID.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Interface ou None si non trouvée
        """
        for interface in self.interfaces:
            if interface.id == interface_id:
                return interface
        return None
    
    def get_interface_by_name(self, name: str) -> Optional[NetworkInterfaceEntity]:
        """
        Récupère une interface par son nom.
        
        Args:
            name: Nom de l'interface
            
        Returns:
            Interface ou None si non trouvée
        """
        for interface in self.interfaces:
            if interface.name == name:
                return interface
        return None
    
    def update_status(self, new_status: DeviceStatus) -> None:
        """
        Met à jour le statut de l'équipement.
        
        Args:
            new_status: Nouveau statut
        """
        self.status.update(new_status)
    
    def add_credentials(self, credentials: Credentials) -> None:
        """
        Ajoute des informations d'authentification pour un protocole.
        
        Args:
            credentials: Informations d'authentification
        """
        self.credentials.add_credentials(credentials)
    
    def get_credentials(self, protocol: ProtocolType) -> Optional[Credentials]:
        """
        Récupère les informations d'authentification pour un protocole.
        
        Args:
            protocol: Type de protocole
            
        Returns:
            Informations d'authentification ou None si non trouvées
        """
        return self.credentials.get_credentials(protocol)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        identity_dict = self.identity.to_dict()
        identity_dict.pop("id", None)  # Éviter la duplication de l'ID
        
        return {
            "id": self.id,
            **identity_dict,
            "status": self.status.to_dict(),
            "interfaces": [interface.to_dict() for interface in self.interfaces],
            "credentials": {protocol.value: cred.to_dict() for protocol, cred in self.credentials.credentials.items()},
        }


@dataclass
class ConfigurationChangeEntity:
    """
    Entité représentant un changement dans une configuration.
    
    Cette entité enregistre les informations sur un changement de configuration.
    """
    
    change_type: str
    description: str
    created_at: datetime
    created_by: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialisation après création."""
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "change_type": self.change_type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "details": self.details,
        }


@dataclass
class DeviceConfigurationEntity:
    """
    Entité représentant une configuration d'équipement.
    
    Cette entité contient le contenu d'une configuration et ses métadonnées.
    """
    
    device_id: int
    content: str
    config_type: ConfigurationType
    id: Optional[int] = None
    version: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    description: Optional[str] = None
    history: List[ConfigurationChangeEntity] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialisation après création."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def add_change(self, change: ConfigurationChangeEntity) -> None:
        """
        Ajoute un changement à l'historique.
        
        Args:
            change: Changement à ajouter
        """
        self.history.append(change)
    
    def get_section(self, section_name: str) -> Optional[str]:
        """
        Récupère une section de la configuration.
        
        Args:
            section_name: Nom de la section
            
        Returns:
            Contenu de la section ou None si non trouvée
        """
        # Implémentation simplifiée, à adapter selon le format de configuration
        start_marker = f"!{section_name}"
        end_marker = "!"
        
        if start_marker not in self.content:
            return None
        
        start_index = self.content.find(start_marker)
        end_index = self.content.find(end_marker, start_index + len(start_marker))
        
        if end_index == -1:
            end_index = len(self.content)
        
        return self.content[start_index:end_index].strip()
    
    def diff(self, other: 'DeviceConfigurationEntity') -> Dict[str, Any]:
        """
        Compare cette configuration avec une autre.
        
        Args:
            other: Autre configuration
            
        Returns:
            Différences entre les configurations
        """
        # Implémentation simplifiée, à adapter selon le format de configuration
        from difflib import unified_diff
        
        diff = list(unified_diff(
            self.content.splitlines(),
            other.content.splitlines(),
            fromfile=f"version_{self.version}",
            tofile=f"version_{other.version}",
            n=3
        ))
        
        return {
            "diff_lines": diff,
            "additions": len([line for line in diff if line.startswith('+')]),
            "deletions": len([line for line in diff if line.startswith('-')]),
            "changes": len(diff),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "id": self.id,
            "device_id": self.device_id,
            "content": self.content,
            "config_type": self.config_type.value,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "description": self.description,
            "history": [change.to_dict() for change in self.history],
        }


@dataclass
class ConnectionEntity:
    """
    Entité représentant une connexion entre deux interfaces réseau.
    
    Cette entité permet de modéliser les liens physiques ou logiques
    entre équipements réseau.
    """
    
    source_interface_id: int
    target_interface_id: int
    id: Optional[int] = None
    connection_type: str = "physical"
    description: Optional[str] = None
    bandwidth: Optional[int] = None
    latency: Optional[int] = None
    status: str = "active"
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Met à jour les métriques de la connexion.
        
        Args:
            metrics: Nouvelles métriques
        """
        self.metrics.update(metrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "id": self.id,
            "source_interface_id": self.source_interface_id,
            "target_interface_id": self.target_interface_id,
            "connection_type": self.connection_type,
            "description": self.description,
            "bandwidth": self.bandwidth,
            "latency": self.latency,
            "status": self.status,
            "metrics": self.metrics,
        }


@dataclass
class TopologyEntity:
    """
    Entité représentant une topologie réseau.
    
    Cette entité contient la définition d'une topologie réseau,
    y compris les équipements et leurs connexions.
    """
    
    name: str
    devices: List[NetworkDeviceEntity] = field(default_factory=list)
    connections: List[ConnectionEntity] = field(default_factory=list)
    id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialisation après création."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def add_device(self, device: NetworkDeviceEntity) -> None:
        """
        Ajoute un équipement à la topologie.
        
        Args:
            device: Équipement à ajouter
        """
        self.devices.append(device)
        self.updated_at = datetime.now()
    
    def remove_device(self, device_id: int) -> bool:
        """
        Supprime un équipement de la topologie.
        
        Args:
            device_id: ID de l'équipement à supprimer
            
        Returns:
            True si l'équipement a été supprimé
        """
        for i, device in enumerate(self.devices):
            if device.id == device_id:
                self.devices.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def add_connection(self, connection: ConnectionEntity) -> None:
        """
        Ajoute une connexion à la topologie.
        
        Args:
            connection: Connexion à ajouter
        """
        self.connections.append(connection)
        self.updated_at = datetime.now()
    
    def remove_connection(self, connection_id: int) -> bool:
        """
        Supprime une connexion de la topologie.
        
        Args:
            connection_id: ID de la connexion à supprimer
            
        Returns:
            True si la connexion a été supprimée
        """
        for i, connection in enumerate(self.connections):
            if connection.id == connection_id:
                self.connections.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def calculate_path(self, source_device_id: int, target_device_id: int) -> List[List[int]]:
        """
        Calcule tous les chemins possibles entre deux équipements.
        
        Args:
            source_device_id: ID de l'équipement source
            target_device_id: ID de l'équipement cible
            
        Returns:
            Liste des chemins possibles (liste d'IDs d'équipements)
            
        Raises:
            TopologyException: Si le calcul échoue
        """
        # Créer un graphe des connexions
        graph = {}
        
        # Ajouter tous les équipements
        for device in self.devices:
            if device.id:
                graph[device.id] = []
        
        # Ajouter les connexions
        for connection in self.connections:
            # Trouver les équipements correspondants
            source_device_id = None
            target_device_id = None
            
            for device in self.devices:
                for interface in device.interfaces:
                    if interface.id == connection.source_interface_id:
                        source_device_id = device.id
                    if interface.id == connection.target_interface_id:
                        target_device_id = device.id
            
            if source_device_id and target_device_id:
                if source_device_id in graph:
                    graph[source_device_id].append(target_device_id)
                if target_device_id in graph:
                    graph[target_device_id].append(source_device_id)
        
        # Recherche en profondeur pour trouver tous les chemins
        def find_paths(graph, start, end, path=None):
            if path is None:
                path = []
            
            path = path + [start]
            
            if start == end:
                return [path]
            
            if start not in graph:
                return []
            
            paths = []
            
            for node in graph[start]:
                if node not in path:
                    new_paths = find_paths(graph, node, end, path)
                    for new_path in new_paths:
                        paths.append(new_path)
            
            return paths
        
        return find_paths(graph, source_device_id, target_device_id)
    
    def detect_loops(self) -> List[List[int]]:
        """
        Détecte les boucles dans la topologie.
        
        Returns:
            Liste des boucles détectées (liste de chemins)
        """
        # Créer un graphe des connexions
        graph = {}
        
        # Ajouter tous les équipements
        for device in self.devices:
            if device.id:
                graph[device.id] = []
        
        # Ajouter les connexions
        for connection in self.connections:
            # Trouver les équipements correspondants
            source_device_id = None
            target_device_id = None
            
            for device in self.devices:
                for interface in device.interfaces:
                    if interface.id == connection.source_interface_id:
                        source_device_id = device.id
                    if interface.id == connection.target_interface_id:
                        target_device_id = device.id
            
            if source_device_id and target_device_id:
                if source_device_id in graph:
                    graph[source_device_id].append(target_device_id)
                if target_device_id in graph:
                    graph[target_device_id].append(source_device_id)
        
        # Détection de cycles par DFS
        loops = []
        visited = set()
        
        def detect_cycle(node, parent, path, visited_in_path):
            visited.add(node)
            visited_in_path.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor == parent:
                    continue
                
                if neighbor in visited_in_path:
                    # Cycle détecté
                    cycle_start = path.index(neighbor)
                    loops.append(path[cycle_start:] + [neighbor])
                elif neighbor not in visited:
                    detect_cycle(neighbor, node, path, visited_in_path)
            
            path.pop()
            visited_in_path.remove(node)
        
        for node in graph:
            if node not in visited:
                detect_cycle(node, None, [], set())
        
        return loops
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Représentation sous forme de dictionnaire
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "devices": [device.to_dict() for device in self.devices],
            "connections": [connection.to_dict() for connection in self.connections],
        }

# Alias pour compatibilité
NetworkTopologyEntity = TopologyEntity 