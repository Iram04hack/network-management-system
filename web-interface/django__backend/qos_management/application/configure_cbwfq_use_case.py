"""
Cas d'utilisation pour la configuration CBWFQ sur les appareils réseau.

Ce module contient le cas d'utilisation permettant de configurer l'algorithme 
Class-Based Weighted Fair Queuing sur un appareil réseau.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..domain.entities import QoSPolicy, InterfaceQoSPolicy
from ..domain.algorithms import QueueAlgorithmType, QueueConfiguration, AlgorithmFactory
from ..domain.exceptions import (
    QoSConfigurationException, 
    QoSValidationException,
    NetworkDeviceNotFoundException
)
from ..domain.interfaces import (
    QoSPolicyRepository,
    NetworkDeviceRepository,
    QoSConfigurationService
)
from ..domain.entities import QoSConfigurationResult


@dataclass
class CBWFQConfiguration:
    """Résultat de la configuration CBWFQ."""
    policy_id: int
    device_id: int
    interface_name: str
    queue_configurations: List[QueueConfiguration]
    commands_generated: List[str]
    success: bool
    message: str


class ConfigureCBWFQUseCase:
    """
    Cas d'utilisation pour configurer CBWFQ sur un appareil réseau.
    
    Cette classe orchestre le processus de configuration de l'algorithme
    Class-Based Weighted Fair Queuing sur une interface d'un appareil réseau.
    """
    
    def __init__(
        self,
        policy_repository: QoSPolicyRepository,
        device_repository: NetworkDeviceRepository,
        qos_configuration_service: QoSConfigurationService
    ):
        """
        Initialise le cas d'utilisation avec ses dépendances.
        
        Args:
            policy_repository: Repository pour accéder aux politiques QoS
            device_repository: Repository pour accéder aux appareils réseau
            qos_configuration_service: Service pour configurer la QoS sur les appareils
        """
        self.policy_repository = policy_repository
        self.device_repository = device_repository
        self.qos_configuration_service = qos_configuration_service
    
    def execute(
        self,
        policy_id: int,
        device_id: int,
        interface_name: str,
        direction: str = 'egress'
    ) -> CBWFQConfiguration:
        """
        Configure CBWFQ sur une interface d'un appareil réseau.
        
        Args:
            policy_id: ID de la politique QoS à appliquer
            device_id: ID de l'appareil réseau
            interface_name: Nom de l'interface réseau
            direction: Direction du trafic ('ingress' ou 'egress')
            
        Returns:
            Configuration CBWFQ appliquée
            
        Raises:
            QoSValidationException: Si la politique n'est pas valide
            QoSConfigurationException: Si la configuration échoue
            NetworkDeviceNotFoundException: Si l'appareil n'est pas trouvé
        """
        # 1. Récupérer la politique QoS
        policy = self.policy_repository.get_policy_by_id(policy_id)
        if not policy:
            raise QoSValidationException(f"Politique QoS avec ID {policy_id} non trouvée")
        
        # 2. Vérifier que l'appareil existe
        device = self.device_repository.get_device_by_id(device_id)
        if not device:
            raise NetworkDeviceNotFoundException(f"Appareil réseau avec ID {device_id} non trouvé")
        
        # 3. Vérifier que l'interface existe sur l'appareil
        if not self.device_repository.has_interface(device_id, interface_name):
            raise QoSConfigurationException(
                f"Interface '{interface_name}' non trouvée sur l'appareil ID {device_id}",
                reason="interface_not_found"
            )
        
        # 4. Calculer les configurations CBWFQ pour la politique
        algorithm = AlgorithmFactory.create_algorithm(QueueAlgorithmType.CBWFQ)
        queue_configs = algorithm.calculate_parameters(policy)
        
        # 5. Générer la configuration pour l'appareil
        configuration = {
            'policy_id': policy_id,
            'policy_name': policy.name,
            'interface_name': interface_name,
            'direction': direction,
            'queue_configurations': queue_configs
        }
        
        # 6. Appliquer la configuration à l'appareil
        result = self.qos_configuration_service.apply_cbwfq_configuration(
            device_id,
            interface_name,
            configuration
        )
        
        # 7. Enregistrer l'association politique-interface si succès
        if result.success:
            interface_policy = InterfaceQoSPolicy(
                interface_id=0,  # Sera défini par le repository
                interface_name=interface_name,
                policy_id=policy_id,
                policy_name=policy.name,
                direction=direction,
                is_active=True
            )
            self.policy_repository.save_interface_policy(interface_policy)
        
        # 8. Retourner le résultat
        return CBWFQConfiguration(
            policy_id=policy_id,
            device_id=device_id,
            interface_name=interface_name,
            queue_configurations=queue_configs,
            commands_generated=result.commands or [],
            success=result.success,
            message=result.message
        )


class CalculateBandwidthAllocationUseCase:
    """
    Cas d'utilisation pour calculer l'allocation de bande passante selon CBWFQ.
    
    Cette classe offre un moyen de simuler l'allocation de bande passante
    selon l'algorithme CBWFQ sans appliquer la configuration à un appareil.
    """
    
    def __init__(self, policy_repository: QoSPolicyRepository):
        """
        Initialise le cas d'utilisation avec ses dépendances.
        
        Args:
            policy_repository: Repository pour accéder aux politiques QoS
        """
        self.policy_repository = policy_repository
    
    def execute(self, policy_id: int) -> List[Dict[str, Any]]:
        """
        Calcule l'allocation de bande passante pour une politique QoS.
        
        Args:
            policy_id: ID de la politique QoS
            
        Returns:
            Liste d'allocations de bande passante par classe de trafic
            
        Raises:
            QoSValidationException: Si la politique n'est pas valide
        """
        # 1. Récupérer la politique QoS
        policy = self.policy_repository.get_policy_by_id(policy_id)
        if not policy:
            raise QoSValidationException(f"Politique QoS avec ID {policy_id} non trouvée")
        
        # 2. Calculer les paramètres CBWFQ
        algorithm = AlgorithmFactory.create_algorithm(QueueAlgorithmType.CBWFQ)
        queue_configs = algorithm.calculate_parameters(policy)
        
        # 3. Préparer le résultat
        allocations = []
        total_bandwidth = policy.bandwidth_limit
        total_min_bandwidth = sum(tc.min_bandwidth for tc in policy.traffic_classes)
        remaining_bandwidth = max(0, total_bandwidth - total_min_bandwidth)
        
        # Calculer la somme des poids pour la distribution du reste
        total_weight = sum(config.queue_params.weight for config in queue_configs)
        
        # Préparer les allocations par classe
        for config in queue_configs:
            traffic_class = config.traffic_class
            queue_params = config.queue_params
            
            # Calculer la part du reste en fonction du poids
            share_of_remaining = 0
            if total_weight > 0 and remaining_bandwidth > 0:
                share_of_remaining = (queue_params.weight / total_weight) * remaining_bandwidth
            
            # Calculer l'allocation totale
            total_allocation = traffic_class.min_bandwidth + share_of_remaining
            
            allocations.append({
                'class_id': traffic_class.id,
                'class_name': traffic_class.name,
                'priority': traffic_class.priority,
                'min_bandwidth_kbps': traffic_class.min_bandwidth,
                'weight': queue_params.weight,
                'remaining_share_kbps': share_of_remaining,
                'total_allocation_kbps': total_allocation,
                'bandwidth_percent': (total_allocation / total_bandwidth * 100) if total_bandwidth > 0 else 0,
                'queue_limit': queue_params.queue_limit,
                'buffer_size': queue_params.buffer_size
            })
        
        return allocations 