"""
Cas d'utilisation pour la configuration LLQ sur les appareils réseau.

Ce module contient le cas d'utilisation permettant de configurer l'algorithme 
Low Latency Queuing sur un appareil réseau.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..domain.entities import QoSPolicy, InterfaceQoSPolicy
from ..domain.algorithms import QueueAlgorithmType, QueueConfiguration, AlgorithmFactory
from ..domain.exceptions import (
    QoSConfigurationException,
    QoSValidationException, 
    NetworkDeviceNotFoundException,
    QoSLowLatencyValidationException
)
from ..domain.interfaces import (
    QoSPolicyRepository,
    NetworkDeviceRepository,
    QoSConfigurationService
)
from ..domain.entities import QoSConfigurationResult


@dataclass
class LLQConfiguration:
    """Résultat de la configuration LLQ."""
    policy_id: int
    device_id: int
    interface_name: str
    queue_configurations: List[QueueConfiguration]
    priority_classes_count: int
    standard_classes_count: int
    commands_generated: List[str]
    success: bool
    message: str


class ConfigureLLQUseCase:
    """
    Cas d'utilisation pour configurer LLQ sur un appareil réseau.
    
    Cette classe orchestre le processus de configuration de l'algorithme
    Low Latency Queuing sur une interface d'un appareil réseau.
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
        direction: str = 'egress',
        validate_priority_allocation: bool = True
    ) -> LLQConfiguration:
        """
        Configure LLQ sur une interface d'un appareil réseau.
        
        Args:
            policy_id: ID de la politique QoS à appliquer
            device_id: ID de l'appareil réseau
            interface_name: Nom de l'interface réseau
            direction: Direction du trafic ('ingress' ou 'egress')
            validate_priority_allocation: Valider que les allocations prioritaires respectent les limites
            
        Returns:
            Configuration LLQ appliquée
            
        Raises:
            QoSValidationException: Si la politique n'est pas valide
            QoSLowLatencyValidationException: Si la politique ne respecte pas les contraintes LLQ
            QoSConfigurationException: Si la configuration échoue
            NetworkDeviceNotFoundException: Si l'appareil n'est pas trouvé
        """
        # 1. Récupérer la politique QoS
        policy = self.policy_repository.get_policy_by_id(policy_id)
        if not policy:
            raise QoSValidationException(f"Politique QoS avec ID {policy_id} non trouvée")

        # 2. Vérifier si la politique a des classes prioritaires
        priority_classes = [tc for tc in policy.traffic_classes if tc.priority >= 5]
        if not priority_classes:
            raise QoSLowLatencyValidationException(
                "La politique ne contient pas de classe à priorité élevée (>=5). "
                "Utilisez CBWFQ au lieu de LLQ pour cette politique."
            )

        # 3. Vérifier que l'appareil existe
        device = self.device_repository.get_device_by_id(device_id)
        if not device:
            raise NetworkDeviceNotFoundException(f"Appareil réseau avec ID {device_id} non trouvé")
        
        # 4. Vérifier que l'interface existe sur l'appareil
        if not self.device_repository.has_interface(device_id, interface_name):
            raise QoSConfigurationException(
                f"Interface '{interface_name}' non trouvée sur l'appareil ID {device_id}",
                reason="interface_not_found"
            )
        
        # 5. Vérifier que l'appareil supporte LLQ
        if not device.supports_advanced_qos:
            raise QoSConfigurationException(
                f"L'appareil ID {device_id} ne supporte pas les algorithmes QoS avancés comme LLQ",
                reason="device_not_supported"
            )
        
        # 6. Calculer les configurations LLQ pour la politique
        algorithm = AlgorithmFactory.create_algorithm(QueueAlgorithmType.LLQ)
        try:
            queue_configs = algorithm.calculate_parameters(policy)
        except ValueError as e:
            if validate_priority_allocation:
                raise QoSLowLatencyValidationException(
                    f"La politique ne respecte pas les contraintes LLQ: {str(e)}"
                )
            # Si validation désactivée, on continue avec un warning
        
        # 7. Générer la configuration pour l'appareil
        configuration = {
            'policy_id': policy_id,
            'policy_name': policy.name,
            'interface_name': interface_name,
            'direction': direction,
            'queue_configurations': queue_configs,
            'algorithm': 'low_latency_queuing'
        }
        
        # 8. Appliquer la configuration à l'appareil
        result = self.qos_configuration_service.apply_llq_configuration(
            device_id,
            interface_name,
            configuration
        )
        
        # 9. Enregistrer l'association politique-interface si succès
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
        
        # 10. Retourner le résultat
        return LLQConfiguration(
            policy_id=policy_id,
            device_id=device_id,
            interface_name=interface_name,
            queue_configurations=queue_configs,
            priority_classes_count=len(priority_classes),
            standard_classes_count=len(policy.traffic_classes) - len(priority_classes),
            commands_generated=result.commands or [],
            success=result.success,
            message=result.message
        )


class ValidateLLQPolicyUseCase:
    """
    Cas d'utilisation pour valider qu'une politique QoS est compatible avec LLQ.
    
    Cette classe analyse une politique QoS pour vérifier sa compatibilité
    avec l'algorithme Low Latency Queuing.
    """
    
    def __init__(self, policy_repository: QoSPolicyRepository):
        """
        Initialise le cas d'utilisation avec ses dépendances.
        
        Args:
            policy_repository: Repository pour accéder aux politiques QoS
        """
        self.policy_repository = policy_repository
    
    def execute(self, policy_id: int) -> Dict[str, Any]:
        """
        Valide qu'une politique est compatible avec LLQ.
        
        Args:
            policy_id: ID de la politique à valider
            
        Returns:
            Résultat de validation avec les détails
            
        Raises:
            QoSValidationException: Si la politique n'est pas trouvée
        """
        # 1. Récupérer la politique QoS
        policy = self.policy_repository.get_policy_by_id(policy_id)
        if not policy:
            raise QoSValidationException(f"Politique QoS avec ID {policy_id} non trouvée")
        
        # 2. Analyser la politique
        priority_classes = [tc for tc in policy.traffic_classes if tc.priority >= 5]
        standard_classes = [tc for tc in policy.traffic_classes if tc.priority < 5]
        
        total_bandwidth = policy.bandwidth_limit
        priority_bandwidth = sum(tc.min_bandwidth for tc in priority_classes)
        priority_percent = (priority_bandwidth / total_bandwidth * 100) if total_bandwidth > 0 else 0
        
        # 3. Effectuer les validations
        validation_results = {
            "valid": True,
            "policy_id": policy_id,
            "policy_name": policy.name,
            "total_classes": len(policy.traffic_classes),
            "priority_classes": len(priority_classes),
            "standard_classes": len(standard_classes),
            "total_bandwidth": total_bandwidth,
            "priority_bandwidth": priority_bandwidth,
            "priority_bandwidth_percent": priority_percent,
            "issues": []
        }
        
        # Validation 1: Au moins une classe prioritaire
        if not priority_classes:
            validation_results["valid"] = False
            validation_results["issues"].append({
                "severity": "critical",
                "message": "La politique ne contient pas de classe à priorité élevée (>=5)",
                "recommendation": "Ajouter au moins une classe avec priorité >= 5 pour utiliser LLQ"
            })
        
        # Validation 2: Pas trop de bande passante pour les classes prioritaires
        max_percent = 33  # LowLatencyQueueingAlgorithm.MAX_PRIORITY_BANDWIDTH_PERCENT
        if priority_percent > max_percent:
            validation_results["valid"] = False
            validation_results["issues"].append({
                "severity": "critical",
                "message": (f"La bande passante prioritaire ({priority_percent:.1f}%) "
                           f"dépasse la limite recommandée ({max_percent}%)"),
                "recommendation": "Réduire la bande passante réservée aux classes prioritaires"
            })
        
        # Validation 3: Suffisamment de bande passante pour les classes standard
        standard_bandwidth = sum(tc.min_bandwidth for tc in standard_classes)
        remaining_bandwidth = total_bandwidth - priority_bandwidth
        
        if standard_bandwidth > remaining_bandwidth:
            validation_results["valid"] = False
            validation_results["issues"].append({
                "severity": "critical",
                "message": (f"La bande passante garantie pour les classes standard ({standard_bandwidth} kbps) "
                           f"dépasse la bande passante disponible ({remaining_bandwidth} kbps)"),
                "recommendation": "Réduire les garanties de bande passante minimale des classes standard"
            })
        
        # Validation 4: Vérifier que le DSCP est correctement configuré
        for tc in priority_classes:
            if tc.dscp == 'default':
                validation_results["issues"].append({
                    "severity": "warning",
                    "message": f"La classe prioritaire '{tc.name}' n'a pas de marquage DSCP défini",
                    "recommendation": "Définir un marquage DSCP approprié (ex: ef pour la voix)"
                })
        
        return validation_results 