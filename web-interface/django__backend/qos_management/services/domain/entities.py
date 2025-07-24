from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class TrafficClassifierEntity:
    protocol: str
    source_ip: Optional[str]
    destination_ip: Optional[str]
    source_port_start: Optional[int]
    source_port_end: Optional[int]
    destination_port_start: Optional[int]
    destination_port_end: Optional[int]
    dscp_marking: Optional[str]
    vlan: Optional[int]

@dataclass
class TrafficClassEntity:
    id: int
    priority: int
    min_bandwidth: int
    max_bandwidth: int
    dscp: Optional[str]
    burst: Optional[int]
    classifiers: List[TrafficClassifierEntity]

@dataclass
class QoSPolicyEntity:
    id: int
    name: str
    description: str
    bandwidth_limit: int
    traffic_classes: List[TrafficClassEntity]
    is_active: bool

@dataclass
class InterfaceQoSPolicyEntity:
    id: int
    interface_id: int
    interface_name: str
    policy: QoSPolicyEntity
    direction: str
    is_active: bool

@dataclass
class QoSVisualizationData:
    """Données de visualisation pour une politique QoS"""
    policy_id: int
    policy_name: str
    bandwidth_limit: int
    traffic_classes: List[Dict[str, Any]]
    traffic_data: Dict[str, Any]

@dataclass
class RecommendedTrafficClass:
    """Classe de trafic recommandée pour une politique QoS"""
    name: str
    description: str
    dscp: str
    priority: int
    min_bandwidth: int
    max_bandwidth: int

@dataclass
class QoSRecommendation:
    """Recommandation de politique QoS"""
    policy_name: str
    description: str
    traffic_classes: List[RecommendedTrafficClass] 