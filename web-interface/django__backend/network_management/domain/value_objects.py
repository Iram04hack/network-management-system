"""
Value Objects et DTOs pour le module Network Management.

Ce module définit les Value Objects et Data Transfer Objects (DTOs)
pour standardiser les échanges de données selon l'architecture hexagonale.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar, Union, Optional, List, Dict, Any
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')


class ResultStatus(Enum):
    """États possibles d'un résultat d'opération."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """
    Pattern Result pour encapsuler les retours d'opérations.
    
    Permet de gérer les succès et erreurs de manière type-safe.
    """
    
    status: ResultStatus
    data: Optional[T] = None
    error: Optional[E] = None
    message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
    
    @classmethod
    def success(cls, data: T, message: Optional[str] = None) -> 'Result[T, E]':
        """Crée un résultat de succès."""
        return cls(status=ResultStatus.SUCCESS, data=data, message=message)
    
    @classmethod
    def error(cls, error: E, message: Optional[str] = None) -> 'Result[T, E]':
        """Crée un résultat d'erreur."""
        return cls(status=ResultStatus.ERROR, error=error, message=message)
    
    @classmethod
    def warning(cls, data: T, warnings: List[str], message: Optional[str] = None) -> 'Result[T, E]':
        """Crée un résultat avec avertissements."""
        return cls(status=ResultStatus.WARNING, data=data, warnings=warnings, message=message)
    
    def is_success(self) -> bool:
        """Vérifie si l'opération a réussi."""
        return self.status == ResultStatus.SUCCESS
    
    def is_error(self) -> bool:
        """Vérifie si l'opération a échoué."""
        return self.status == ResultStatus.ERROR
    
    def is_warning(self) -> bool:
        """Vérifie si l'opération a des avertissements."""
        return self.status == ResultStatus.WARNING
    
    def unwrap(self) -> T:
        """Récupère les données ou lève une exception."""
        if self.is_error():
            raise ValueError(f"Cannot unwrap error result: {self.error}")
        return self.data
    
    def unwrap_or(self, default: T) -> T:
        """Récupère les données ou retourne la valeur par défaut."""
        if self.is_error():
            return default
        return self.data


@dataclass(frozen=True)
class DeviceDiscoveryRequest:
    """DTO pour les requêtes de découverte d'équipements."""
    
    ip_range: str
    snmp_community: str = "public"
    snmp_version: str = "v2c"
    snmp_port: int = 161
    timeout: int = 1
    retries: int = 2
    protocols: List[str] = None
    
    def __post_init__(self):
        if self.protocols is None:
            object.__setattr__(self, 'protocols', ["snmp"])


@dataclass(frozen=True)
class DeviceDiscoveryResponse:
    """DTO pour les réponses de découverte d'équipements."""
    
    discovered_count: int
    failed_count: int
    saved_count: int
    devices: List[Dict[str, Any]]
    failed_addresses: List[str]
    execution_time: float
    timestamp: str


@dataclass(frozen=True)
class ConfigurationDeploymentRequest:
    """DTO pour les requêtes de déploiement de configuration."""
    
    device_ids: List[int]
    config_version_id: int
    scheduled_at: Optional[str] = None
    backup_before: bool = True
    validate_before: bool = True
    rollback_on_error: bool = True


@dataclass(frozen=True)
class ConfigurationDeploymentResponse:
    """DTO pour les réponses de déploiement de configuration."""
    
    deployment_id: int
    status: str
    device_results: List[Dict[str, Any]]
    started_at: str
    completed_at: Optional[str] = None
    summary: Dict[str, int] = None


@dataclass(frozen=True)
class TopologySimulationRequest:
    """DTO pour les requêtes de simulation de topologie."""
    
    topology_id: int
    changes: List[Dict[str, Any]]
    simulation_type: str  # "add_device", "remove_device", "add_link", "remove_link"
    analyze_impact: bool = True
    generate_recommendations: bool = True


@dataclass(frozen=True)
class TopologySimulationResponse:
    """DTO pour les réponses de simulation de topologie."""
    
    simulation_id: str
    original_topology: Dict[str, Any]
    simulated_topology: Dict[str, Any]
    impact_analysis: Dict[str, Any]
    recommendations: List[str]
    execution_time: float


@dataclass(frozen=True)
class NetworkDiagnosticRequest:
    """DTO pour les requêtes de diagnostic réseau."""
    
    source_device_id: int
    target_device_id: Optional[int] = None
    target_ip: Optional[str] = None
    diagnostic_type: str = "ping"  # "ping", "traceroute", "bandwidth_test"
    parameters: Dict[str, Any] = None


@dataclass(frozen=True)
class NetworkDiagnosticResponse:
    """DTO pour les réponses de diagnostic réseau."""
    
    diagnostic_id: str
    diagnostic_type: str
    source: Dict[str, Any]
    target: Dict[str, Any]
    results: Dict[str, Any]
    success: bool
    execution_time: float
    timestamp: str


@dataclass(frozen=True)
class CredentialRequest:
    """DTO pour les requêtes de gestion des credentials."""
    
    device_id: int
    protocol: str
    username: Optional[str] = None
    password: Optional[str] = None
    enable_password: Optional[str] = None
    community: Optional[str] = None
    private_key: Optional[str] = None
    api_key: Optional[str] = None


@dataclass(frozen=True)
class DeviceConnectionRequest:
    """DTO pour les requêtes de connexion aux équipements."""
    
    device_id: int
    protocol: str = "ssh"
    timeout: int = 30
    retries: int = 3
    use_cached_credentials: bool = True


@dataclass(frozen=True)
class DeviceConnectionResponse:
    """DTO pour les réponses de connexion aux équipements."""
    
    device_id: int
    connected: bool
    protocol_used: str
    connection_time: float
    error_message: Optional[str] = None
    capabilities: List[str] = None


@dataclass(frozen=True)
class ConfigurationValidationRequest:
    """DTO pour les requêtes de validation de configuration."""
    
    device_id: int
    configuration_content: str
    validation_rules: List[str] = None
    strict_mode: bool = False


@dataclass(frozen=True)
class ConfigurationValidationResponse:
    """DTO pour les réponses de validation de configuration."""
    
    valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    suggestions: List[str]
    compliance_score: float
    validation_time: float


@dataclass(frozen=True)
class WorkflowRequest:
    """DTO pour les requêtes de workflow."""
    
    workflow_name: str
    parameters: Dict[str, Any]
    scheduled_at: Optional[str] = None
    priority: str = "normal"  # "low", "normal", "high", "critical"


@dataclass(frozen=True)
class WorkflowResponse:
    """DTO pour les réponses de workflow."""
    
    workflow_id: str
    status: str
    steps: List[Dict[str, Any]]
    started_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


# Value Objects pour les concepts métier

@dataclass(frozen=True)
class IPAddress:
    """Value Object pour les adresses IP."""
    
    address: str
    
    def __post_init__(self):
        import ipaddress
        try:
            ipaddress.ip_address(self.address)
        except ValueError:
            raise ValueError(f"Invalid IP address: {self.address}")


@dataclass(frozen=True)
class IPRange:
    """Value Object pour les plages d'adresses IP."""
    
    cidr: str
    
    def __post_init__(self):
        import ipaddress
        try:
            ipaddress.ip_network(self.cidr, strict=False)
        except ValueError:
            raise ValueError(f"Invalid IP range: {self.cidr}")
    
    def contains(self, ip: IPAddress) -> bool:
        """Vérifie si une IP est dans la plage."""
        import ipaddress
        network = ipaddress.ip_network(self.cidr, strict=False)
        return ipaddress.ip_address(ip.address) in network


@dataclass(frozen=True)
class MACAddress:
    """Value Object pour les adresses MAC."""
    
    address: str
    
    def __post_init__(self):
        import re
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        if not mac_pattern.match(self.address):
            raise ValueError(f"Invalid MAC address: {self.address}")


@dataclass(frozen=True)
class Version:
    """Value Object pour les versions."""
    
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'Version') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __eq__(self, other: 'Version') -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """Crée une version à partir d'une chaîne."""
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
        
        try:
            major, minor, patch = map(int, parts)
            return cls(major=major, minor=minor, patch=patch)
        except ValueError:
            raise ValueError(f"Invalid version format: {version_str}")


@dataclass(frozen=True)
class Bandwidth:
    """Value Object pour la bande passante."""
    
    value: float
    unit: str  # "bps", "kbps", "mbps", "gbps"
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Bandwidth cannot be negative")
        
        valid_units = ["bps", "kbps", "mbps", "gbps"]
        if self.unit.lower() not in valid_units:
            raise ValueError(f"Invalid bandwidth unit: {self.unit}")
    
    def to_bps(self) -> float:
        """Convertit en bits par seconde."""
        multipliers = {
            "bps": 1,
            "kbps": 1000,
            "mbps": 1000000,
            "gbps": 1000000000
        }
        return self.value * multipliers[self.unit.lower()]
    
    def __str__(self) -> str:
        return f"{self.value} {self.unit}" 