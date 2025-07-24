"""
Cas d'utilisation pour valider et appliquer une configuration QoS complète.

Ce cas d'utilisation permet de valider une configuration QoS complète
et de l'appliquer à une interface réseau si elle est valide.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..domain.interfaces import (
    QoSPolicyRepository,
    InterfaceQoSPolicyRepository,
    TrafficControlService
)
from ..domain.entities import QoSPolicy, InterfaceQoSPolicy

logger = logging.getLogger(__name__)


class ValidateAndApplyQoSConfigUseCase:
    """
    Cas d'utilisation pour valider et appliquer une configuration QoS complète.
    
    Ce cas d'utilisation combine la validation d'une politique QoS et son
    application à une interface réseau, en utilisant l'architecture hexagonale.
    """
    
    def __init__(
        self,
        qos_policy_repository: QoSPolicyRepository,
        interface_qos_repository: InterfaceQoSPolicyRepository,
        traffic_control_service: TrafficControlService
    ):
        """
        Initialise le cas d'utilisation avec les dépendances nécessaires.
        
        Args:
            qos_policy_repository: Repository pour les politiques QoS
            interface_qos_repository: Repository pour les associations interface/politique
            traffic_control_service: Service de contrôle de trafic
        """
        self._qos_policy_repository = qos_policy_repository
        self._interface_qos_repository = interface_qos_repository
        self._traffic_control_service = traffic_control_service
    
    def execute(
        self,
        policy_id: int,
        interface_name: str,
        direction: str = "egress",
        reapply_if_exists: bool = False
    ) -> Dict[str, Any]:
        """
        Valide et applique une politique QoS à une interface réseau.
        
        Args:
            policy_id: ID de la politique QoS à appliquer
            interface_name: Nom de l'interface réseau
            direction: Direction du trafic (ingress/egress)
            reapply_if_exists: Si True, réapplique la politique même si elle existe déjà
            
        Returns:
            Résultat de l'opération
        """
        try:
            # 1. Récupérer la politique QoS
            policy_data = self._qos_policy_repository.get_policy(policy_id)
            if not policy_data:
                return {
                    "success": False,
                    "message": f"Politique QoS avec ID {policy_id} non trouvée",
                    "policy_id": policy_id,
                    "interface": interface_name
                }
            
            # 2. Vérifier si une politique est déjà appliquée à cette interface
            existing_policies = self._interface_qos_repository.list_interface_policies({
                "interface_name": interface_name
            })
            
            if existing_policies and not reapply_if_exists:
                return {
                    "success": False,
                    "message": f"Une politique QoS est déjà appliquée à l'interface {interface_name}",
                    "policy_id": policy_id,
                    "interface": interface_name,
                    "existing_policy": existing_policies[0]
                }
            
            # 3. Ajouter la direction à la politique pour le service
            policy_data["direction"] = direction
            
            # 4. Valider la politique pour cette interface
            validation_result = self._traffic_control_service.validate_policy(
                policy_data=policy_data,
                interface_name=interface_name
            )
            
            if not validation_result.get("success", False):
                return {
                    "success": False,
                    "message": "La politique QoS n'est pas valide pour cette interface",
                    "policy_id": policy_id,
                    "interface": interface_name,
                    "validation_errors": validation_result.get("errors", [])
                }
            
            # 5. Supprimer la configuration existante si nécessaire
            if existing_policies:
                self._traffic_control_service.remove_policy(interface_name)
                # Suppression de l'association en base de données
                for existing_policy in existing_policies:
                    self._interface_qos_repository.remove_policy_from_interface(
                        interface_id=existing_policy.get("interface_id")
                    )
            
            # 6. Appliquer la politique à l'interface
            apply_result = self._traffic_control_service.apply_policy(
                policy_data=policy_data,
                interface_name=interface_name
            )
            
            if not apply_result.get("success", False):
                return {
                    "success": False,
                    "message": f"Échec de l'application de la politique QoS: {apply_result.get('message', '')}",
                    "policy_id": policy_id,
                    "interface": interface_name,
                    "details": apply_result
                }
            
            # 7. Enregistrer l'association en base de données
            association_data = {
                "interface_name": interface_name,
                "policy_id": policy_id,
                "policy_name": policy_data.get("name", ""),
                "direction": direction,
                "is_active": True,
                "applied_at": datetime.now().isoformat()
            }
            
            self._interface_qos_repository.apply_policy_to_interface(
                policy_id=policy_id,
                interface_id=0,  # ID fictif, sera remplacé par l'interface_name
                parameters=association_data
            )
            
            # 8. Retourner le résultat
            return {
                "success": True,
                "message": f"Politique QoS '{policy_data.get('name')}' appliquée avec succès à l'interface {interface_name}",
                "policy_id": policy_id,
                "interface": interface_name,
                "direction": direction,
                "applied_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "policy_id": policy_id,
                "interface": interface_name
            } 