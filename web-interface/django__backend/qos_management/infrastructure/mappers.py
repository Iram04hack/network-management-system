"""
Mappers pour la conversion entre modèles Django et objets du domaine pour le module QoS Management.

Ce module contient les fonctions de conversion entre les modèles Django (infrastructure)
et les entités du domaine, respectant ainsi la séparation des couches de l'architecture hexagonale.
"""

from typing import Dict, Any, List
from ..models import (
    QoSPolicy as QoSPolicyModel,
    TrafficClass as TrafficClassModel,
    TrafficClassifier as TrafficClassifierModel,
    InterfaceQoSPolicy as InterfaceQoSPolicyModel
)


def map_qos_policy_to_dict(model: QoSPolicyModel) -> Dict[str, Any]:
    """
    Convertit un modèle de politique QoS en dictionnaire représentant l'entité du domaine.
    
    Args:
        model: Instance du modèle Django QoSPolicy
        
    Returns:
        Dictionnaire représentant l'entité du domaine QoSPolicy
    """
    return {
        'id': model.id,
        'name': model.name,
        'description': model.description,
        'bandwidth_limit': model.bandwidth_limit,
        'status': model.status,
        'policy_type': model.policy_type,
        'priority': model.priority,
        'configuration': model.configuration,
        'created_at': model.created_at.isoformat() if model.created_at else None,
        'updated_at': model.updated_at.isoformat() if model.updated_at else None
    }


def map_traffic_class_to_dict(model: TrafficClassModel) -> Dict[str, Any]:
    """
    Convertit un modèle de classe de trafic en dictionnaire représentant l'entité du domaine.
    
    Args:
        model: Instance du modèle Django TrafficClass
        
    Returns:
        Dictionnaire représentant l'entité du domaine TrafficClass
    """
    return {
        'id': model.id,
        'name': model.name,
        'description': model.description,
        'priority': model.priority,
        'bandwidth': model.bandwidth,
        'bandwidth_percent': model.bandwidth_percent,
        'dscp': model.dscp,
        'queue_limit': model.queue_limit,
        'policy_id': model.policy_id,
        'parameters': model.parameters,
        'created_at': model.created_at.isoformat() if model.created_at else None,
        'updated_at': model.updated_at.isoformat() if model.updated_at else None
    }


def map_traffic_classifier_to_dict(model: TrafficClassifierModel) -> Dict[str, Any]:
    """
    Convertit un modèle de classificateur de trafic en dictionnaire représentant l'entité du domaine.
    
    Args:
        model: Instance du modèle Django TrafficClassifier
        
    Returns:
        Dictionnaire représentant l'entité du domaine TrafficClassifier
    """
    return {
        'id': model.id,
        'description': model.description,
        'source_ip': model.source_ip,
        'destination_ip': model.destination_ip,
        'protocol': model.protocol,
        'source_port_start': model.source_port_start,
        'source_port_end': model.source_port_end,
        'destination_port_start': model.destination_port_start,
        'destination_port_end': model.destination_port_end,
        'dscp': model.dscp,
        'vlan_id': model.vlan_id,
        'traffic_class_id': model.traffic_class_id,
        'created_at': model.created_at.isoformat() if model.created_at else None,
        'updated_at': model.updated_at.isoformat() if model.updated_at else None
    }


def map_interface_qos_policy_to_dict(model: InterfaceQoSPolicyModel) -> Dict[str, Any]:
    """
    Convertit un modèle d'association interface-politique QoS en dictionnaire représentant l'entité du domaine.
    
    Args:
        model: Instance du modèle Django InterfaceQoSPolicy
        
    Returns:
        Dictionnaire représentant l'entité du domaine InterfaceQoSPolicy
    """
    return {
        'id': model.id,
        'device_id': model.device_id,
        'interface_id': model.interface_id,
        'interface_name': model.interface_name,
        'policy_id': model.policy_id,
        'direction': model.direction,
        'parameters': model.parameters,
        'applied_at': model.applied_at.isoformat() if model.applied_at else None,
        'updated_at': model.updated_at.isoformat() if model.updated_at else None
    }


def map_dict_to_qos_policy(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit un dictionnaire en données pour créer un modèle QoSPolicy.
    
    Args:
        data: Dictionnaire contenant les données de la politique
        
    Returns:
        Dictionnaire formaté pour créer un modèle Django
    """
    return {
        'name': data.get('name'),
        'description': data.get('description', ''),
        'policy_type': data.get('policy_type', 'htb'),
        'priority': data.get('priority', 0),
        'bandwidth_limit': data.get('bandwidth_limit'),
        'status': data.get('status', 'inactive'),
        'configuration': data.get('configuration', {})
    }


def map_dict_to_traffic_class(data: Dict[str, Any], policy_id: int) -> Dict[str, Any]:
    """
    Convertit un dictionnaire en données pour créer un modèle TrafficClass.
    
    Args:
        data: Dictionnaire contenant les données de la classe de trafic
        policy_id: ID de la politique parente
        
    Returns:
        Dictionnaire formaté pour créer un modèle Django
    """
    return {
        'policy_id': policy_id,
        'name': data.get('name'),
        'description': data.get('description', ''),
        'priority': data.get('priority', 0),
        'dscp': data.get('dscp'),
        'bandwidth': data.get('bandwidth', 0),
        'bandwidth_percent': data.get('bandwidth_percent', 0.0),
        'queue_limit': data.get('queue_limit', 64),
        'parameters': data.get('parameters', {})
    }


def map_dict_to_traffic_classifier(data: Dict[str, Any], traffic_class_id: int) -> Dict[str, Any]:
    """
    Convertit un dictionnaire en données pour créer un modèle TrafficClassifier.
    
    Args:
        data: Dictionnaire contenant les données du classificateur
        traffic_class_id: ID de la classe de trafic parente
        
    Returns:
        Dictionnaire formaté pour créer un modèle Django
    """
    return {
        'traffic_class_id': traffic_class_id,
        'description': data.get('description', ''),
        'protocol': data.get('protocol'),
        'source_ip': data.get('source_ip'),
        'destination_ip': data.get('destination_ip'),
        'source_port_start': data.get('source_port_start'),
        'source_port_end': data.get('source_port_end'),
        'destination_port_start': data.get('destination_port_start'),
        'destination_port_end': data.get('destination_port_end'),
        'dscp': data.get('dscp'),
        'vlan_id': data.get('vlan_id')
    }