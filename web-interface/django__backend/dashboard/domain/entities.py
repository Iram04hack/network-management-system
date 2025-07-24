"""
Entités du domaine pour le module de tableau de bord.

Ce fichier définit les entités métier utilisées dans le domaine du tableau de bord.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

__all__ = [
    'DashboardOverview',
    'NetworkOverview', 
    'TopologyView',
    'DeviceStatus',
    'ConnectionStatus',
    'SystemHealthMetrics',
    'AlertInfo',
    'DeviceInfo',
    'AlertSeverity'
]

class DeviceStatus(str, Enum):
    """Statuts possibles d'un équipement"""
    HEALTHY = 'healthy'
    WARNING = 'warning'
    CRITICAL = 'critical'
    INACTIVE = 'inactive'
    UNKNOWN = 'unknown'
    
class ConnectionStatus(str, Enum):
    """Statuts possibles d'une connexion"""
    HEALTHY = 'healthy'
    WARNING = 'warning'
    CRITICAL = 'critical'
    UNKNOWN = 'unknown'

class AlertSeverity(str, Enum):
    """Niveaux de sévérité des alertes"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

@dataclass
class AlertInfo:
    """Information sur une alerte système ou sécurité"""
    id: int
    message: str
    severity: AlertSeverity
    timestamp: datetime
    status: str
    source: Optional[str] = None
    metric_name: Optional[str] = None
    affected_devices: List[int] = field(default_factory=list)
    
    def is_critical(self) -> bool:
        """Vérifie si l'alerte est critique"""
        return self.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'alerte en dictionnaire pour sérialisation"""
        return {
            'id': self.id,
            'message': self.message,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'source': self.source,
            'metric_name': self.metric_name,
            'affected_devices': self.affected_devices
        }

@dataclass
class DeviceInfo:
    """Information sur un équipement réseau"""
    id: int
    name: str
    device_type: str
    status: DeviceStatus
    ip_address: Optional[str] = None
    last_seen: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def is_operational(self) -> bool:
        """Vérifie si l'équipement est opérationnel"""
        return self.status in [DeviceStatus.HEALTHY, DeviceStatus.WARNING]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'info d'équipement en dictionnaire pour sérialisation"""
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'status': self.status,
            'ip_address': self.ip_address,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'metrics': self.metrics,
            'is_operational': self.is_operational()
        }

@dataclass
class SystemHealthMetrics:
    """Métriques de santé du système"""
    system_health: float
    network_health: float
    security_health: float
    
    def __post_init__(self):
        """Validation des valeurs après initialisation"""
        for attr in ['system_health', 'network_health', 'security_health']:
            value = getattr(self, attr)
            if not 0 <= value <= 1:
                raise ValueError(f"{attr} doit être entre 0 et 1, reçu: {value}")
    
    def get_overall_status(self) -> DeviceStatus:
        """Détermine le statut global basé sur les métriques"""
        avg_health = (self.system_health + self.network_health + self.security_health) / 3
        
        if avg_health >= 0.8:
            return DeviceStatus.HEALTHY
        elif avg_health >= 0.6:
            return DeviceStatus.WARNING
        else:
            return DeviceStatus.CRITICAL
            
    def to_dict(self) -> Dict[str, Union[float, str]]:
        """Convertit les métriques de santé en dictionnaire pour sérialisation"""
        return {
            'system_health': self.system_health,
            'network_health': self.network_health,
            'security_health': self.security_health,
            'overall_health': (self.system_health + self.network_health + self.security_health) / 3,
            'status': self.get_overall_status()
        }

@dataclass
class DashboardOverview:
    """Vue d'ensemble principale du tableau de bord"""
    devices: Dict[str, Any]  # Statistiques des équipements
    security_alerts: List[AlertInfo]  # Alertes de sécurité récentes
    system_alerts: List[AlertInfo]  # Alertes système récentes
    performance: Dict[str, Any]  # Métriques de performance
    health_metrics: SystemHealthMetrics  # Indicateurs de santé du système
    timestamp: datetime
    
    def get_critical_alerts_count(self) -> int:
        """Compte le nombre d'alertes critiques"""
        critical_security = sum(1 for alert in self.security_alerts if alert.is_critical())
        critical_system = sum(1 for alert in self.system_alerts if alert.is_critical())
        return critical_security + critical_system
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la vue d'ensemble en dictionnaire pour sérialisation"""
        return {
            'devices': self.devices,
            'security_alerts': [alert.to_dict() for alert in self.security_alerts],
            'system_alerts': [alert.to_dict() for alert in self.system_alerts],
            'performance': self.performance,
            'health_metrics': self.health_metrics.to_dict(),
            'timestamp': self.timestamp.isoformat(),
            'critical_alerts_count': self.get_critical_alerts_count()
        }

@dataclass
class NetworkOverview:
    """Vue d'ensemble du réseau"""
    devices: Dict[str, Any]  # Statistiques des équipements réseau
    interfaces: Dict[str, Any]  # Statistiques des interfaces réseau
    qos: Dict[str, Any]  # Informations sur les politiques QoS
    alerts: List[AlertInfo]  # Alertes réseau
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la vue d'ensemble réseau en dictionnaire pour sérialisation"""
        return {
            'devices': self.devices,
            'interfaces': self.interfaces,
            'qos': self.qos,
            'alerts': [alert.to_dict() for alert in self.alerts],
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class TopologyView:
    """Vue d'une topologie réseau"""
    topology_id: int
    name: str
    nodes: List[Dict[str, Any]]  # Noeuds de la topologie (équipements)
    connections: List[Dict[str, Any]]  # Connexions entre les équipements
    health_summary: Dict[str, int]  # Résumé de la santé de la topologie
    last_updated: datetime
    
    def get_total_devices(self) -> int:
        """Retourne le nombre total d'équipements dans la topologie"""
        return len(self.nodes)
    
    def get_critical_devices_count(self) -> int:
        """Compte les équipements en état critique"""
        return self.health_summary.get('critical', 0)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la vue de topologie en dictionnaire pour sérialisation"""
        return {
            'topology_id': self.topology_id,
            'name': self.name,
            'nodes': self.nodes,
            'connections': self.connections,
            'health_summary': self.health_summary,
            'last_updated': self.last_updated.isoformat(),
            'total_devices': self.get_total_devices(),
            'critical_devices_count': self.get_critical_devices_count()
        } 