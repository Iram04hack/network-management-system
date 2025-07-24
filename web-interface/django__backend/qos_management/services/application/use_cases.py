from typing import Dict, Optional
from ..domain.interfaces import QoSPolicyRepository, InterfaceQoSPolicyRepository, TrafficControlService, QoSVisualizationService, QoSConfigurerService
from ..domain.entities import QoSPolicy, InterfaceQoSPolicy, QoSVisualizationData, QoSRecommendation
# from security_management.domain.interfaces import AuditLogRepository  # TODO: Corriger l'import

class ApplyQoSPolicyUseCase:
    def __init__(self, 
                 policy_repository: QoSPolicyRepository,
                 interface_policy_repository: InterfaceQoSPolicyRepository,
                 traffic_control_service: TrafficControlService,
                 audit_log_repository: AuditLogRepository):
        self.policy_repository = policy_repository
        self.interface_policy_repository = interface_policy_repository
        self.traffic_control_service = traffic_control_service
        self.audit_log_repository = audit_log_repository
    
    def execute(self, policy_id: int, interface_id: int, direction: str, user_id: int = None) -> Dict:
        """
        Applique une politique QoS à une interface réseau
        
        Args:
            policy_id: ID de la politique QoS
            interface_id: ID de l'interface réseau
            direction: Direction du trafic (ingress/egress)
            user_id: ID de l'utilisateur effectuant l'action (optionnel)
            
        Returns:
            Dict contenant le statut et les détails de l'opération
            
        Raises:
            ValueError: Si l'interface n'existe pas ou si les paramètres sont invalides
        """
        # Récupérer la politique
        policy = self.policy_repository.get_by_id(policy_id)
        if not policy:
            self._log_audit("ERROR", f"Tentative d'application de politique inexistante: {policy_id}", user_id)
            raise ValueError(f"La politique QoS avec l'ID {policy_id} n'existe pas")
            
        # Vérifier si une politique est déjà appliquée
        existing = self.interface_policy_repository.get_by_interface_and_direction(
            interface_id, direction)
            
        if existing:
            if existing.policy.id == policy_id:
                self._log_audit("INFO", f"Politique {policy.name} déjà appliquée à l'interface {interface_id}", user_id)
                return {
                    'status': 'unchanged',
                    'message': 'Cette politique est déjà appliquée à cette interface'
                }
            else:
                # Supprimer l'ancienne politique
                self._log_audit("INFO", f"Remplacement de politique sur l'interface {interface_id}: {existing.policy.name} -> {policy.name}", user_id)
                self._remove_policy_from_interface(existing)
                
        # Créer la nouvelle association
        interface_policy = InterfaceQoSPolicy(
            id=None,  # Sera généré par le repository
            interface_id=interface_id,
            interface_name=f"interface_{interface_id}",  # À remplacer par le vrai nom
            policy=policy,
            direction=direction,
            is_active=True
        )
        
        # Sauvegarder l'association
        saved_policy = self.interface_policy_repository.save(interface_policy)
        
        # Appliquer la politique via Traffic Control
        if not self.traffic_control_service.test_connection():
            saved_policy.is_active = False
            self.interface_policy_repository.save(saved_policy)
            self._log_audit("ERROR", "Échec de connexion au service Traffic Control", user_id)
            return {
                'status': 'error',
                'message': 'Impossible de se connecter au service Traffic Control'
            }
            
        success = self.traffic_control_service.configure_interface(
            interface_name=saved_policy.interface_name,
            direction=direction,
            bandwidth_limit=policy.bandwidth_limit,
            traffic_classes=policy.traffic_classes
        )
        
        if not success:
            saved_policy.is_active = False
            self.interface_policy_repository.save(saved_policy)
            self._log_audit("ERROR", f"Échec d'application de la politique {policy.name} à l'interface {interface_id}", user_id)
            return {
                'status': 'error',
                'message': 'Échec de l\'application de la politique QoS via Traffic Control'
            }
        
        self._log_audit("SUCCESS", f"Politique {policy.name} appliquée à l'interface {interface_id}", user_id)    
        return {
            'status': 'success',
            'message': 'Politique QoS appliquée avec succès',
            'interface_policy': {
                'id': saved_policy.id,
                'interface': saved_policy.interface_name,
                'policy': policy.name,
                'direction': direction,
                'is_active': True
            }
        }
        
    def _remove_policy_from_interface(self, interface_policy: InterfaceQoSPolicy) -> bool:
        """Supprime une politique QoS d'une interface"""
        try:
            # Nettoyer l'interface via Traffic Control
            self.traffic_control_service.clear_interface(interface_policy.interface_name)
            
            # Supprimer l'association
            return self.interface_policy_repository.delete(interface_policy.id)
            
        except Exception as e:
            self._log_audit("ERROR", f"Erreur lors de la suppression de politique: {str(e)}")
            return False
            
    def _log_audit(self, level: str, message: str, user_id: int = None):
        """Enregistre une entrée dans le journal d'audit"""
        try:
            self.audit_log_repository.add_log_entry(
                component="QOS",
                level=level,
                message=message,
                user_id=user_id
            )
        except Exception as e:
            # En cas d'erreur d'audit, on continue l'exécution mais on journalise l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Échec de journalisation d'audit: {str(e)}")

class GetQoSVisualizationUseCase:
    def __init__(self, 
                 policy_repository: QoSPolicyRepository,
                 visualization_service: QoSVisualizationService):
        self.policy_repository = policy_repository
        self.visualization_service = visualization_service
    
    def execute(self, policy_id: int) -> QoSVisualizationData:
        """
        Récupère les données de visualisation pour une politique QoS
        
        Args:
            policy_id: ID de la politique QoS
            
        Returns:
            QoSVisualizationData contenant les données de visualisation
            
        Raises:
            ValueError: Si la politique n'existe pas
        """
        # Vérifier que la politique existe
        policy = self.policy_repository.get_by_id(policy_id)
        if not policy:
            raise ValueError(f"La politique QoS avec l'ID {policy_id} n'existe pas")
        
        # Récupérer les données de visualisation
        return self.visualization_service.get_policy_visualization(policy_id)

class GetQoSRecommendationsUseCase:
    def __init__(self, configurer_service: QoSConfigurerService):
        self.configurer_service = configurer_service
    
    def execute(self, traffic_type: str, network_size: str) -> QoSRecommendation:
        """
        Récupère des recommandations de politique QoS basées sur le type de trafic et la taille du réseau
        
        Args:
            traffic_type: Type de trafic (general, voice, streaming, etc.)
            network_size: Taille du réseau (small, medium, large)
            
        Returns:
            QoSRecommendation contenant les recommandations
        """
        return self.configurer_service.generate_recommendations(traffic_type, network_size) 