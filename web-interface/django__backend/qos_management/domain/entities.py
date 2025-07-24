"""
Entités du domaine pour la gestion de la qualité de service (QoS).

Ce module définit les entités métier principales du domaine QoS,
indépendamment de toute infrastructure technique.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .strategies import CompositeMatchStrategy, create_composite_strategy_from_classifier

@dataclass
class QoSVisualizationData:
    """
    Données de visualisation pour une politique QoS.
    """
    policy_id: int
    policy_name: str
    bandwidth_limit: int
    traffic_classes: List[Dict[str, Any]]
    traffic_data: Dict[str, Any]

@dataclass
class TrafficClassifier:
    """
    Classificateur de trafic pour identifier les flux réseau.
    """
    id: Optional[int] = None
    protocol: str = 'any'
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port_start: Optional[int] = None
    source_port_end: Optional[int] = None
    destination_port_start: Optional[int] = None
    destination_port_end: Optional[int] = None
    dscp_marking: Optional[str] = None
    vlan: Optional[int] = None
    name: str = ''
    description: str = ''

    def matches(self, packet_data: Dict[str, Any]) -> bool:
        """
        Vérifie si un paquet correspond à ce classificateur.
        
        Args:
            packet_data: Données du paquet à vérifier
            
        Returns:
            True si le paquet correspond au classificateur
        """
        # Utilisation du pattern Strategy avec CompositeMatchStrategy
        strategy = create_composite_strategy_from_classifier({
            'protocol': self.protocol,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'source_port_start': self.source_port_start,
            'source_port_end': self.source_port_end,
            'destination_port_start': self.destination_port_start,
            'destination_port_end': self.destination_port_end,
            'dscp_marking': self.dscp_marking,
            'vlan': self.vlan
        })
        
        return strategy.matches(packet_data)

@dataclass
class TrafficClass:
    """
    Classe de trafic pour regrouper et prioriser les flux réseau.
    """
    id: Optional[int] = None
    name: str = ''
    description: str = ''
    priority: int = 0
    min_bandwidth: int = 0  # En kbps
    max_bandwidth: int = 0  # En kbps
    dscp: str = 'default'
    burst: int = 0  # En kb
    classifiers: List[TrafficClassifier] = None
    
    def __post_init__(self):
        if self.classifiers is None:
            self.classifiers = []

@dataclass
class QoSPolicy:
    """
    Politique de qualité de service regroupant plusieurs classes de trafic.
    """
    id: Optional[int] = None
    name: str = ''
    description: str = ''
    bandwidth_limit: int = 0  # En kbps
    is_active: bool = True
    priority: int = 0
    traffic_classes: List[TrafficClass] = None
    
    def __post_init__(self):
        if self.traffic_classes is None:
            self.traffic_classes = []
    
    def add_traffic_class(self, traffic_class: TrafficClass) -> None:
        """
        Ajoute une classe de trafic à cette politique.
        
        Args:
            traffic_class: Classe de trafic à ajouter
        """
        self.traffic_classes.append(traffic_class)
    
    def remove_traffic_class(self, class_id: int) -> bool:
        """
        Supprime une classe de trafic de cette politique.
        
        Args:
            class_id: ID de la classe à supprimer
            
        Returns:
            True si la classe a été supprimée
        """
        for i, tc in enumerate(self.traffic_classes):
            if tc.id == class_id:
                self.traffic_classes.pop(i)
                return True
        return False

@dataclass
class QoSPolicyEntity:
    """
    Entité de domaine représentant une politique QoS.
    Cette entité est utilisée dans le domaine métier pour les cas d'utilisation.
    """
    id: Optional[int] = None
    name: str = ''
    description: str = ''
    bandwidth_limit: int = 0  # En kbps
    is_active: bool = True
    priority: int = 0
    algorithm: str = 'HTB'
    congestion_control: str = 'CODEL'
    traffic_classes: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.traffic_classes is None:
            self.traffic_classes = []
    
    @classmethod
    def from_policy(cls, policy: QoSPolicy) -> 'QoSPolicyEntity':
        """
        Crée une entité QoSPolicyEntity à partir d'une QoSPolicy.
        
        Args:
            policy: Objet QoSPolicy source
            
        Returns:
            Nouvelle instance de QoSPolicyEntity
        """
        traffic_classes = []
        for tc in policy.traffic_classes:
            traffic_classes.append({
                'id': tc.id,
                'name': tc.name,
                'priority': tc.priority,
                'min_bandwidth': tc.min_bandwidth,
                'max_bandwidth': tc.max_bandwidth,
                'dscp': tc.dscp
            })
        
        return cls(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            bandwidth_limit=policy.bandwidth_limit,
            is_active=policy.is_active,
            priority=policy.priority,
            traffic_classes=traffic_classes
        )

@dataclass
class QoSRuleEntity:
    """
    Entité de domaine représentant une règle QoS.
    """
    id: Optional[int] = None
    policy_id: int = 0
    name: str = ''
    description: str = ''
    match_criteria: Dict[str, Any] = None
    action: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.match_criteria is None:
            self.match_criteria = {}
        if self.action is None:
            self.action = {}

@dataclass
class TrafficClassEntity:
    """
    Entité de domaine représentant une classe de trafic.
    """
    id: Optional[int] = None
    name: str = ''
    description: str = ''
    priority: int = 0
    min_bandwidth: int = 0
    max_bandwidth: int = 0
    dscp: str = 'default'
    classifiers: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.classifiers is None:
            self.classifiers = []

@dataclass
class InterfaceQoSPolicy:
    """
    Association entre une politique QoS et une interface réseau.
    """
    id: Optional[int] = None
    interface_id: int = 0
    interface_name: str = ''
    policy_id: int = 0
    policy_name: str = ''
    direction: str = 'egress'  # 'ingress' ou 'egress'
    is_active: bool = True
    applied_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class QoSConfigurationResult:
    """
    Résultat d'une opération de configuration QoS.
    """
    success: bool = False
    message: str = ''
    device_id: Optional[int] = None
    interface_id: Optional[int] = None
    policy_id: Optional[int] = None
    errors: List[str] = None
    warnings: List[str] = None
    applied_commands: List[str] = None
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.applied_commands is None:
            self.applied_commands = []


@dataclass
class QoSRecommendations:
    """
    Entité représentant les recommandations de configuration QoS.
    """
    policy_name: str = ''
    description: str = ''
    traffic_classes: List[Dict[str, Any]] = None
    bandwidth_allocation: Dict[str, Any] = None
    priority_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.traffic_classes is None:
            self.traffic_classes = []
        if self.bandwidth_allocation is None:
            self.bandwidth_allocation = {}
        if self.priority_settings is None:
            self.priority_settings = {}


@dataclass 
class QoSVisualizationData:
    """
    Entité représentant les données de visualisation QoS.
    """
    policy_id: int
    policy_name: str = ''
    bandwidth_limit: int = 0
    traffic_classes: List[Dict[str, Any]] = None
    traffic_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.traffic_classes is None:
            self.traffic_classes = []
        if self.traffic_data is None:
            self.traffic_data = {}