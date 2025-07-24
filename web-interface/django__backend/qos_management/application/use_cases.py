"""
Cas d'utilisation pour le module qos_management.

Ce module implémente la logique métier du domaine qos_management
indépendamment de l'infrastructure technique ou de l'interface utilisateur.
"""

from typing import Dict, Any, List, Optional
import logging

from ..domain.interfaces import (
    QoSPolicyRepository,
    TrafficClassRepository,
    TrafficClassifierRepository,
    InterfaceQoSPolicyRepository,
    TrafficControlService
)
from ..domain.exceptions import (
    QoSPolicyNotFoundException,
    TrafficClassNotFoundException,
    TrafficClassifierNotFoundException,
    InterfaceQoSPolicyNotFoundException,
    QoSValidationException,
    QoSPolicyApplicationException,
    TrafficControlException,
    BandwidthLimitExceededException,
    QoSConfigurationException
)
from ..domain.entities import QoSRecommendations, QoSVisualizationData

logger = logging.getLogger(__name__)


class GetQoSPolicyUseCase:
    """
    Cas d'utilisation pour récupérer une politique QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository):
        self.qos_policy_repository = qos_policy_repository
    
    def execute(self, policy_id: int) -> Dict[str, Any]:
        """
        Récupère une politique QoS par son ID.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Politique QoS
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        policy = self.qos_policy_repository.get_policy(policy_id)
        
        if not policy:
            raise QoSPolicyNotFoundException(policy_id)
            
        return policy


class ListQoSPoliciesUseCase:
    """
    Cas d'utilisation pour lister les politiques QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository):
        self.qos_policy_repository = qos_policy_repository
    
    def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les politiques QoS selon des filtres optionnels.
        
        Args:
            filters: Filtres optionnels (type, statut, etc.)
            
        Returns:
            Liste des politiques QoS
        """
        return self.qos_policy_repository.list_policies(filters)


class CreateQoSPolicyUseCase:
    """
    Cas d'utilisation pour créer une politique QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository,
                traffic_control_service: Optional[TrafficControlService] = None):
        self.qos_policy_repository = qos_policy_repository
        self.traffic_control_service = traffic_control_service
    
    def execute(self, policy_data: Dict[str, Any], validate_only: bool = False) -> Dict[str, Any]:
        """
        Crée une nouvelle politique QoS.
        
        Args:
            policy_data: Données de la politique à créer
            validate_only: Si True, valide seulement sans créer la politique
            
        Returns:
            Politique QoS créée (ou résultat de validation si validate_only=True)
            
        Raises:
            QoSValidationException: Si les données de la politique sont invalides
        """
        # Validation des données
        errors = self._validate_policy_data(policy_data)
        
        if errors:
            raise QoSValidationException("QoSPolicy", errors=errors)
        
        # Validation avec le service de contrôle de trafic si disponible
        if self.traffic_control_service:
            try:
                validation_result = self.traffic_control_service.validate_policy(policy_data)
                if not validation_result.get("valid", False):
                    validation_errors = validation_result.get("errors", [])
                    raise QoSValidationException(
                        "QoSPolicy", 
                        errors=validation_errors or {"policy": ["Politique QoS invalide pour Traffic Control"]}
                    )
            except TrafficControlException as e:
                raise QoSValidationException(
                    "QoSPolicy", 
                    errors={"policy": [str(e)]}
                )
        
        # Si validation uniquement, retourner le résultat sans créer la politique
        if validate_only:
            return {"valid": True, "data": policy_data}
        
        # Création de la politique
        return self.qos_policy_repository.create_policy(policy_data)
    
    def _validate_policy_data(self, policy_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les données d'une politique QoS.
        
        Args:
            policy_data: Données de la politique à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not policy_data.get("name"):
            errors["name"] = ["Le nom est obligatoire"]
        
        if "bandwidth" in policy_data:
            try:
                bandwidth = int(policy_data["bandwidth"])
                if bandwidth <= 0:
                    errors["bandwidth"] = ["La bande passante doit être positive"]
            except (ValueError, TypeError):
                errors["bandwidth"] = ["La bande passante doit être un nombre entier"]
        
        if "policy_type" in policy_data:
            policy_type = policy_data["policy_type"]
            valid_types = ["htb", "hfsc", "cbq", "fq_codel"]
            if policy_type not in valid_types:
                errors["policy_type"] = [f"Type de politique non valide. Types valides: {', '.join(valid_types)}"]
        
        return errors


class UpdateQoSPolicyUseCase:
    """
    Cas d'utilisation pour mettre à jour une politique QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository,
                traffic_control_service: Optional[TrafficControlService] = None,
                interface_qos_repository: Optional[InterfaceQoSPolicyRepository] = None):
        self.qos_policy_repository = qos_policy_repository
        self.traffic_control_service = traffic_control_service
        self.interface_qos_repository = interface_qos_repository
    
    def execute(self, policy_id: int, policy_data: Dict[str, Any], 
               validate_only: bool = False) -> Dict[str, Any]:
        """
        Met à jour une politique QoS existante.
        
        Args:
            policy_id: ID de la politique à mettre à jour
            policy_data: Nouvelles données de la politique
            validate_only: Si True, valide seulement sans mettre à jour la politique
            
        Returns:
            Politique QoS mise à jour (ou résultat de validation si validate_only=True)
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
            QoSValidationException: Si les données de la politique sont invalides
        """
        # Vérifier que la politique existe
        existing_policy = self.qos_policy_repository.get_policy(policy_id)
        if not existing_policy:
            raise QoSPolicyNotFoundException(policy_id)
        
        # Validation des données
        errors = self._validate_policy_data(policy_data)
        
        if errors:
            raise QoSValidationException("QoSPolicy", errors=errors)
        
        # Préparer les données combinées pour validation
        updated_policy = {**existing_policy, **policy_data}
        
        # Validation avec le service de contrôle de trafic si disponible
        if self.traffic_control_service:
            try:
                validation_result = self.traffic_control_service.validate_policy(updated_policy)
                if not validation_result.get("valid", False):
                    validation_errors = validation_result.get("errors", [])
                    raise QoSValidationException(
                        "QoSPolicy", 
                        errors=validation_errors or {"policy": ["Politique QoS invalide pour Traffic Control"]}
                    )
            except TrafficControlException as e:
                raise QoSValidationException(
                    "QoSPolicy", 
                    errors={"policy": [str(e)]}
                )
        
        # Si validation uniquement, retourner le résultat sans mettre à jour la politique
        if validate_only:
            return {"valid": True, "data": updated_policy}
        
        # Mise à jour de la politique
        updated_policy = self.qos_policy_repository.update_policy(policy_id, policy_data)
        
        # Si la politique est appliquée à des interfaces, mettre à jour les applications
        if self.interface_qos_repository:
            try:
                # Obtenir la liste des interfaces où cette politique est appliquée
                interfaces = self.interface_qos_repository.list_interface_policies(
                    {"policy_id": policy_id}
                )
                
                # Mettre à jour chaque application
                for interface in interfaces:
                    interface_id = interface.get("interface_id")
                    if interface_id and self.traffic_control_service:
                        # Reappliquer la politique
                        try:
                            self.interface_qos_repository.apply_policy_to_interface(
                                policy_id, 
                                interface_id
                            )
                        except Exception as e:
                            logger.error(f"Erreur lors de la réapplication de la politique QoS {policy_id} "
                                         f"sur l'interface {interface_id}: {e}")
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour des applications de la politique QoS {policy_id}: {e}")
        
        return updated_policy
    
    def _validate_policy_data(self, policy_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les données d'une politique QoS pour la mise à jour.
        
        Args:
            policy_data: Données de la politique à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if "name" in policy_data and not policy_data["name"]:
            errors["name"] = ["Le nom est obligatoire"]
        
        if "bandwidth" in policy_data:
            try:
                bandwidth = int(policy_data["bandwidth"])
                if bandwidth <= 0:
                    errors["bandwidth"] = ["La bande passante doit être positive"]
            except (ValueError, TypeError):
                errors["bandwidth"] = ["La bande passante doit être un nombre entier"]
        
        if "policy_type" in policy_data:
            policy_type = policy_data["policy_type"]
            valid_types = ["htb", "hfsc", "cbq", "fq_codel"]
            if policy_type not in valid_types:
                errors["policy_type"] = [f"Type de politique non valide. Types valides: {', '.join(valid_types)}"]
        
        return errors


class DeleteQoSPolicyUseCase:
    """
    Cas d'utilisation pour supprimer une politique QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository,
                interface_qos_repository: Optional[InterfaceQoSPolicyRepository] = None):
        self.qos_policy_repository = qos_policy_repository
        self.interface_qos_repository = interface_qos_repository
    
    def execute(self, policy_id: int, force: bool = False) -> bool:
        """
        Supprime une politique QoS.
        
        Args:
            policy_id: ID de la politique à supprimer
            force: Si True, force la suppression même si la politique est utilisée
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
            QoSConfigurationException: Si la politique est utilisée et force=False
        """
        # Vérifier que la politique existe
        existing_policy = self.qos_policy_repository.get_policy(policy_id)
        if not existing_policy:
            raise QoSPolicyNotFoundException(policy_id)
        
        # Vérifier si la politique est utilisée
        if self.interface_qos_repository:
            interfaces = self.interface_qos_repository.list_interface_policies(
                {"policy_id": policy_id}
            )
            
            if interfaces and not force:
                interfaces_count = len(interfaces)
                raise QoSConfigurationException(
                    policy_id=policy_id,
                    reason=f"La politique est utilisée par {interfaces_count} interface(s)"
                )
            
            # Si force=True, retirer la politique de toutes les interfaces
            if interfaces and force:
                for interface in interfaces:
                    interface_id = interface.get("interface_id")
                    if interface_id:
                        try:
                            self.interface_qos_repository.remove_policy_from_interface(interface_id)
                        except Exception as e:
                            logger.error(f"Erreur lors du retrait de la politique QoS {policy_id} "
                                         f"de l'interface {interface_id}: {e}")
        
        # Suppression de la politique
        return self.qos_policy_repository.delete_policy(policy_id)


class GetTrafficClassUseCase:
    """
    Cas d'utilisation pour récupérer une classe de trafic.
    """
    
    def __init__(self, traffic_class_repository: TrafficClassRepository):
        self.traffic_class_repository = traffic_class_repository
    
    def execute(self, class_id: int) -> Dict[str, Any]:
        """
        Récupère une classe de trafic par son ID.
        
        Args:
            class_id: ID de la classe de trafic
            
        Returns:
            Classe de trafic
            
        Raises:
            TrafficClassNotFoundException: Si la classe de trafic n'existe pas
        """
        traffic_class = self.traffic_class_repository.get_traffic_class(class_id)
        
        if not traffic_class:
            raise TrafficClassNotFoundException(class_id)
            
        return traffic_class


class ListTrafficClassesUseCase:
    """
    Cas d'utilisation pour lister les classes de trafic.
    """
    
    def __init__(self, traffic_class_repository: TrafficClassRepository):
        self.traffic_class_repository = traffic_class_repository
    
    def execute(self, policy_id: Optional[int] = None, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les classes de trafic selon des filtres optionnels.
        
        Args:
            policy_id: ID de la politique QoS (optionnel)
            filters: Filtres optionnels (priorité, etc.)
            
        Returns:
            Liste des classes de trafic
        """
        combined_filters = filters or {}
        if policy_id:
            combined_filters["policy_id"] = policy_id
            
        return self.traffic_class_repository.list_traffic_classes(policy_id, combined_filters)


class CreateTrafficClassUseCase:
    """
    Cas d'utilisation pour créer une classe de trafic.
    """
    
    def __init__(self, traffic_class_repository: TrafficClassRepository,
                qos_policy_repository: QoSPolicyRepository):
        self.traffic_class_repository = traffic_class_repository
        self.qos_policy_repository = qos_policy_repository
    
    def execute(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle classe de trafic.
        
        Args:
            class_data: Données de la classe de trafic à créer
            
        Returns:
            Classe de trafic créée
            
        Raises:
            QoSPolicyNotFoundException: Si la politique associée n'existe pas
            QoSValidationException: Si les données de la classe sont invalides
            BandwidthLimitExceededException: Si la bande passante demandée dépasse celle disponible
        """
        # Validation des données
        errors = self._validate_class_data(class_data)
        
        if errors:
            raise QoSValidationException("TrafficClass", errors=errors)
        
        # Vérifier que la politique existe
        policy_id = class_data.get("policy_id")
        if policy_id:
            policy = self.qos_policy_repository.get_policy(policy_id)
            if not policy:
                raise QoSPolicyNotFoundException(policy_id)
            
            # Vérifier les limites de bande passante
            if "bandwidth" in class_data and "bandwidth" in policy:
                class_bandwidth = int(class_data["bandwidth"])
                policy_bandwidth = int(policy["bandwidth"])
                
                # Obtenir la somme des bandes passantes des classes existantes
                existing_classes = self.traffic_class_repository.list_traffic_classes(policy_id)
                existing_bandwidth = sum(int(c.get("bandwidth", 0)) for c in existing_classes)
                
                # Vérifier si l'ajout dépasse la limite
                if existing_bandwidth + class_bandwidth > policy_bandwidth:
                    available = policy_bandwidth - existing_bandwidth
                    raise BandwidthLimitExceededException(
                        policy_id=policy_id,
                        bandwidth=class_bandwidth,
                        available=available
                    )
        
        # Création de la classe de trafic
        return self.traffic_class_repository.create_traffic_class(class_data)
    
    def _validate_class_data(self, class_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les données d'une classe de trafic.
        
        Args:
            class_data: Données de la classe à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not class_data.get("name"):
            errors["name"] = ["Le nom est obligatoire"]
        
        if not class_data.get("policy_id"):
            errors["policy_id"] = ["La politique associée est obligatoire"]
        
        if "priority" in class_data:
            try:
                priority = int(class_data["priority"])
                if priority < 0:
                    errors["priority"] = ["La priorité doit être positive ou nulle"]
            except (ValueError, TypeError):
                errors["priority"] = ["La priorité doit être un nombre entier"]
        
        if "bandwidth" in class_data:
            try:
                bandwidth = int(class_data["bandwidth"])
                if bandwidth <= 0:
                    errors["bandwidth"] = ["La bande passante doit être positive"]
            except (ValueError, TypeError):
                errors["bandwidth"] = ["La bande passante doit être un nombre entier"]
        
        return errors


class ApplyPolicyToInterfaceUseCase:
    """
    Cas d'utilisation pour appliquer une politique QoS à une interface réseau.
    """
    
    def __init__(self, interface_qos_repository: InterfaceQoSPolicyRepository,
                qos_policy_repository: QoSPolicyRepository,
                traffic_control_service: TrafficControlService):
        self.interface_qos_repository = interface_qos_repository
        self.qos_policy_repository = qos_policy_repository
        self.traffic_control_service = traffic_control_service
    
    def execute(self, policy_id: int, interface_id: int, 
               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Applique une politique QoS à une interface réseau.
        
        Args:
            policy_id: ID de la politique QoS
            interface_id: ID de l'interface réseau
            parameters: Paramètres supplémentaires (optionnel)
            
        Returns:
            Résultat de l'application
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
            QoSPolicyApplicationException: Si l'application échoue
        """
        # Vérifier que la politique existe
        policy = self.qos_policy_repository.get_policy(policy_id)
        if not policy:
            raise QoSPolicyNotFoundException(policy_id)
        
        try:
            # Appliquer la politique à l'interface
            result = self.interface_qos_repository.apply_policy_to_interface(
                policy_id, 
                interface_id, 
                parameters
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'application de la politique QoS {policy_id} "
                           f"sur l'interface {interface_id}: {e}")
            raise QoSPolicyApplicationException(
            policy_id=policy_id,
            interface_id=interface_id,
                reason=str(e)
        )
        

class RemovePolicyFromInterfaceUseCase:
    """
    Cas d'utilisation pour retirer une politique QoS d'une interface réseau.
    """
    
    def __init__(self, interface_qos_repository: InterfaceQoSPolicyRepository):
        self.interface_qos_repository = interface_qos_repository
    
    def execute(self, interface_id: int) -> bool:
        """
        Retire la politique QoS d'une interface réseau.
        
        Args:
            interface_id: ID de l'interface réseau
            
        Returns:
            True si le retrait a réussi
            
        Raises:
            InterfaceQoSPolicyNotFoundException: Si aucune politique n'est appliquée à l'interface
            QoSPolicyApplicationException: Si le retrait échoue
        """
        try:
            # Vérifier si une politique est appliquée à l'interface
            interface_policy = self.interface_qos_repository.get_interface_policy(interface_id)
            if not interface_policy:
                raise InterfaceQoSPolicyNotFoundException(interface_id=interface_id)
            
        # Retirer la politique de l'interface
            return self.interface_qos_repository.remove_policy_from_interface(interface_id)
            
        except InterfaceQoSPolicyNotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Erreur lors du retrait de la politique QoS de l'interface {interface_id}: {e}")
            raise QoSPolicyApplicationException(
            interface_id=interface_id,
                reason=str(e)
            )


class GetQoSStatisticsUseCase:
    """
    Cas d'utilisation pour obtenir les statistiques QoS d'une interface réseau.
    """
    
    def __init__(self, interface_qos_repository: InterfaceQoSPolicyRepository,
                traffic_control_service: TrafficControlService):
        self.interface_qos_repository = interface_qos_repository
        self.traffic_control_service = traffic_control_service
    
    def execute(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère les statistiques QoS pour une interface réseau.
        
        Args:
            interface_id: ID de l'interface réseau
            
        Returns:
            Statistiques QoS
            
        Raises:
            InterfaceQoSPolicyNotFoundException: Si aucune politique n'est appliquée à l'interface
            TrafficControlException: Si la récupération des statistiques échoue
        """
        # Vérifier si une politique est appliquée à l'interface
        interface_policy = self.interface_qos_repository.get_interface_policy(interface_id)
        if not interface_policy:
            raise InterfaceQoSPolicyNotFoundException(interface_id=interface_id)
        
        # Récupérer le nom de l'interface
        interface_name = interface_policy.get("interface_name")
        if not interface_name:
            raise TrafficControlException(
                operation="get_statistics",
                reason="Nom d'interface manquant"
            )
        
        # Récupérer les statistiques
        return self.traffic_control_service.get_statistics(interface_name)


class ListTrafficClassifiersUseCase:
    """
    Cas d'utilisation pour lister les classificateurs d'une classe de trafic.
    """
    
    def __init__(self, traffic_classifier_repository: TrafficClassifierRepository,
                traffic_class_repository: TrafficClassRepository):
        self.traffic_classifier_repository = traffic_classifier_repository
        self.traffic_class_repository = traffic_class_repository
    
    def execute(self, class_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les classificateurs de trafic associés à une classe de trafic.
        
        Args:
            class_id: ID de la classe de trafic
            filters: Filtres optionnels
            
        Returns:
            Liste des classificateurs de trafic
            
        Raises:
            TrafficClassNotFoundException: Si la classe de trafic n'existe pas
        """
        # Vérifier que la classe de trafic existe
        traffic_class = self.traffic_class_repository.get_traffic_class(class_id)
        if not traffic_class:
            raise TrafficClassNotFoundException(class_id)
        
        # Obtenir les classificateurs de trafic
        return self.traffic_classifier_repository.list_classifiers(class_id, filters)


class CreateTrafficClassifierUseCase:
    """
    Cas d'utilisation pour créer un classificateur de trafic.
    """
    
    def __init__(self, traffic_classifier_repository: TrafficClassifierRepository,
                traffic_class_repository: TrafficClassRepository):
        self.traffic_classifier_repository = traffic_classifier_repository
        self.traffic_class_repository = traffic_class_repository
    
    def execute(self, classifier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau classificateur de trafic.
        
        Args:
            classifier_data: Données du classificateur à créer
            
        Returns:
            Classificateur de trafic créé
            
        Raises:
            TrafficClassNotFoundException: Si la classe de trafic associée n'existe pas
            QoSValidationException: Si les données du classificateur sont invalides
        """
        # Validation des données
        errors = self._validate_classifier_data(classifier_data)
        
        if errors:
            raise QoSValidationException("TrafficClassifier", errors=errors)
        
        # Vérifier que la classe de trafic existe
        class_id = classifier_data.get("traffic_class_id")
        if class_id:
            traffic_class = self.traffic_class_repository.get_traffic_class(class_id)
        if not traffic_class:
                raise TrafficClassNotFoundException(class_id)
        
        # Création du classificateur
        return self.traffic_classifier_repository.create_classifier(classifier_data)
    
    def _validate_classifier_data(self, classifier_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les données d'un classificateur de trafic.
        
        Args:
            classifier_data: Données du classificateur à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        
        if not classifier_data.get("name"):
            errors["name"] = ["Le nom est obligatoire"]
        
        if not classifier_data.get("traffic_class_id"):
            errors["traffic_class_id"] = ["La classe de trafic associée est obligatoire"]
        
        # Validation des ports
        source_port_start = classifier_data.get("source_port_start")
        source_port_end = classifier_data.get("source_port_end")
        dest_port_start = classifier_data.get("destination_port_start")
        dest_port_end = classifier_data.get("destination_port_end")
        
        if source_port_start is not None:
            try:
                source_port_start = int(source_port_start)
                if not (0 <= source_port_start <= 65535):
                    errors["source_port_start"] = ["Le port source doit être entre 0 et 65535"]
            except (ValueError, TypeError):
                errors["source_port_start"] = ["Le port source doit être un nombre entier"]
        
        if source_port_end is not None:
            try:
                source_port_end = int(source_port_end)
                if not (0 <= source_port_end <= 65535):
                    errors["source_port_end"] = ["Le port source de fin doit être entre 0 et 65535"]
                elif source_port_start is not None and source_port_end < source_port_start:
                    errors["source_port_end"] = ["Le port source de fin doit être supérieur au port source de début"]
            except (ValueError, TypeError):
                errors["source_port_end"] = ["Le port source de fin doit être un nombre entier"]
        
        if dest_port_start is not None:
            try:
                dest_port_start = int(dest_port_start)
                if not (0 <= dest_port_start <= 65535):
                    errors["destination_port_start"] = ["Le port destination doit être entre 0 et 65535"]
            except (ValueError, TypeError):
                errors["destination_port_start"] = ["Le port destination doit être un nombre entier"]
        
        if dest_port_end is not None:
            try:
                dest_port_end = int(dest_port_end)
                if not (0 <= dest_port_end <= 65535):
                    errors["destination_port_end"] = ["Le port destination de fin doit être entre 0 et 65535"]
                elif dest_port_start is not None and dest_port_end < dest_port_start:
                    errors["destination_port_end"] = ["Le port destination de fin doit être supérieur au port destination de début"]
            except (ValueError, TypeError):
                errors["destination_port_end"] = ["Le port destination de fin doit être un nombre entier"]
        
        # Validation du protocole
        if "protocol" in classifier_data:
            protocol = classifier_data["protocol"]
            valid_protocols = ["any", "tcp", "udp", "icmp", "sctp", "gre"]
            if protocol not in valid_protocols:
                errors["protocol"] = [f"Protocole non valide. Protocoles valides: {', '.join(valid_protocols)}"]
        
        return errors


class GetQoSVisualizationUseCase:
    """
    Cas d'utilisation pour obtenir les données de visualisation QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository, 
                 interface_qos_repository: InterfaceQoSPolicyRepository,
                 traffic_control_service: TrafficControlService):
        self.qos_policy_repository = qos_policy_repository
        self.interface_qos_repository = interface_qos_repository
        self.traffic_control_service = traffic_control_service
    
    def execute(self, policy_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données de visualisation QoS.
        
        Args:
            policy_id: ID de la politique (optionnel)
            
        Returns:
            Données de visualisation QoS
        """
        try:
            if policy_id:
                # Visualisation d'une politique spécifique
                policy = self.qos_policy_repository.get_policy(policy_id)
                if not policy:
                    raise QoSPolicyNotFoundException(policy_id)
                
                # Récupérer les interfaces où cette politique est appliquée
                interfaces = self.interface_qos_repository.get_interfaces_by_policy(policy_id)
                
                # Récupérer les statistiques pour chaque interface
                interface_stats = []
                for interface in interfaces:
                    try:
                        stats = self.traffic_control_service.get_statistics(
                            interface.get("interface_name", "")
                        )
                        interface_stats.append({
                            "interface": interface,
                            "statistics": stats
                        })
                    except Exception as e:
                        logger.warning(f"Impossible de récupérer les statistiques pour l'interface {interface.get('interface_name')}: {e}")
                        interface_stats.append({
                            "interface": interface,
                            "statistics": {"error": str(e)}
                        })
                
                return {
                    "policy": policy,
                    "interfaces": interface_stats,
                    "summary": {
                        "total_interfaces": len(interfaces),
                        "active_interfaces": len([i for i in interface_stats if "error" not in i["statistics"]])
                    }
                }
            else:
                # Vue d'ensemble de toutes les politiques
                policies = self.qos_policy_repository.list_policies()
                
                policy_summaries = []
                for policy in policies:
                    interfaces = self.interface_qos_repository.get_interfaces_by_policy(policy["id"])
                    policy_summaries.append({
                        "policy": policy,
                        "interface_count": len(interfaces),
                        "is_active": policy.get("is_active", False)
                    })
                
                return {
                    "policies": policy_summaries,
                    "summary": {
                        "total_policies": len(policies),
                        "active_policies": len([p for p in policies if p.get("is_active", False)]),
                        "total_applied_interfaces": sum(p["interface_count"] for p in policy_summaries)
                    }
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de visualisation QoS: {e}")
            raise


class GetQoSRecommendationsUseCase:
    """
    Cas d'utilisation pour obtenir des recommandations de configuration QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository,
                 interface_qos_repository: InterfaceQoSPolicyRepository,
                 traffic_control_service: TrafficControlService):
        self.qos_policy_repository = qos_policy_repository
        self.interface_qos_repository = interface_qos_repository
        self.traffic_control_service = traffic_control_service
    
    def execute(self, device_id: Optional[int] = None, 
                interface_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Génère des recommandations de configuration QoS.
        
        Args:
            device_id: ID de l'équipement (optionnel)
            interface_id: ID de l'interface (optionnel)
            
        Returns:
            Recommandations de configuration QoS
        """
        try:
            from datetime import datetime
            
            logger.info("Génération de recommandations QoS")
            recommendations = {
                "timestamp": datetime.now().isoformat(),
                "device_id": device_id,
                "interface_id": interface_id,
                "recommendations": []
            }
            
            if interface_id:
                # Recommandations pour une interface spécifique
                current_policy = self.interface_qos_repository.get_interface_policy(interface_id)
                
                if not current_policy:
                    recommendations["recommendations"].append({
                        "type": "policy_application",
                        "priority": "high",
                        "title": "Aucune politique QoS appliquée",
                        "description": "Cette interface n'a pas de politique QoS. Considérez appliquer une politique appropriée.",
                        "suggested_action": "apply_default_policy"
                    })
                else:
                    # Analyser la politique actuelle
                    policy_analysis = self._analyze_current_policy(current_policy)
                    recommendations["recommendations"].extend(policy_analysis)
                    
            elif device_id:
                # Recommandations pour un équipement
                device_analysis = self._analyze_device_qos(device_id)
                recommendations["recommendations"].extend(device_analysis)
            else:
                # Recommandations générales
                general_analysis = self._get_general_recommendations()
                recommendations["recommendations"].extend(general_analysis)
            
            # Prioriser les recommandations
            recommendations["recommendations"] = sorted(
                recommendations["recommendations"],
                key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("priority", "low"), 3)
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de recommandations QoS: {e}")
            raise
    
    def _analyze_current_policy(self, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyse une politique QoS actuelle et génère des recommandations."""
        recommendations = []
        
        # Vérifier la limite de bande passante
        bandwidth_limit = policy.get("bandwidth_limit", 0)
        if bandwidth_limit <= 0:
            recommendations.append({
                "type": "bandwidth_configuration",
                "priority": "medium",
                "title": "Limite de bande passante non définie",
                "description": "La politique n'a pas de limite de bande passante définie.",
                "suggested_action": "configure_bandwidth_limit"
            })
        
        return recommendations
    
    def _analyze_device_qos(self, device_id: int) -> List[Dict[str, Any]]:
        """Analyse la configuration QoS d'un équipement."""
        recommendations = []
        
        # Récupérer les politiques appliquées sur cet équipement
        policies = self.qos_policy_repository.get_policies_by_device(device_id)
        
        if not policies:
            recommendations.append({
                "type": "device_configuration",
                "priority": "high",
                "title": "Aucune politique QoS sur l'équipement",
                "description": "Cet équipement n'a aucune politique QoS configurée.",
                "suggested_action": "configure_device_qos"
            })
        
        return recommendations
    
    def _get_general_recommendations(self) -> List[Dict[str, Any]]:
        """Génère des recommandations générales."""
        recommendations = []
        
        # Analyser toutes les politiques
        all_policies = self.qos_policy_repository.list_policies()
        inactive_policies = [p for p in all_policies if not p.get("is_active", False)]
        
        if inactive_policies:
            recommendations.append({
                "type": "policy_optimization",
                "priority": "low",
                "title": f"{len(inactive_policies)} politique(s) inactive(s)",
                "description": "Certaines politiques QoS sont inactives et pourraient être nettoyées.",
                "suggested_action": "review_inactive_policies"
            })
        
        return recommendations


class GetQoSRecommendationsUseCase:
    """
    Cas d'utilisation pour obtenir les recommandations de configuration QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository):
        self.qos_policy_repository = qos_policy_repository
    
    def execute(self, traffic_type: str = 'general', network_size: str = 'medium') -> QoSRecommendations:
        """
        Génère des recommandations de configuration QoS.
        
        Args:
            traffic_type: Type de trafic (voip, video, data, gaming, general)
            network_size: Taille du réseau (small, medium, large)
            
        Returns:
            QoSRecommendations: Recommandations de configuration
        """
        # Configuration par défaut selon le type de trafic
        traffic_configs = {
            'voip': {
                'policy_name': 'VoIP-Optimized',
                'description': 'Configuration optimisée pour la VoIP avec latence minimale',
                'traffic_classes': [
                    {'name': 'Voice', 'priority': 1, 'min_bandwidth': 64, 'max_bandwidth': 256, 'dscp': 46},
                    {'name': 'Video', 'priority': 2, 'min_bandwidth': 256, 'max_bandwidth': 2048, 'dscp': 34},
                    {'name': 'Data', 'priority': 3, 'min_bandwidth': 128, 'max_bandwidth': 1024, 'dscp': 0}
                ]
            },
            'video': {
                'policy_name': 'Video-Optimized',
                'description': 'Configuration optimisée pour les applications vidéo',
                'traffic_classes': [
                    {'name': 'Video', 'priority': 1, 'min_bandwidth': 1024, 'max_bandwidth': 8192, 'dscp': 34},
                    {'name': 'Voice', 'priority': 2, 'min_bandwidth': 64, 'max_bandwidth': 256, 'dscp': 46},
                    {'name': 'Data', 'priority': 3, 'min_bandwidth': 256, 'max_bandwidth': 2048, 'dscp': 0}
                ]
            },
            'general': {
                'policy_name': 'Balanced-QoS',
                'description': 'Configuration équilibrée pour usage général',
                'traffic_classes': [
                    {'name': 'Critical', 'priority': 1, 'min_bandwidth': 256, 'max_bandwidth': 1024, 'dscp': 46},
                    {'name': 'Business', 'priority': 2, 'min_bandwidth': 512, 'max_bandwidth': 2048, 'dscp': 34},
                    {'name': 'Standard', 'priority': 3, 'min_bandwidth': 128, 'max_bandwidth': 1024, 'dscp': 0}
                ]
            }
        }
        
        config = traffic_configs.get(traffic_type, traffic_configs['general'])
        
        return QoSRecommendations(
            policy_name=config['policy_name'],
            description=config['description'],
            traffic_classes=config['traffic_classes']
        )


class GetQoSVisualizationUseCase:
    """
    Cas d'utilisation pour obtenir les données de visualisation QoS.
    """
    
    def __init__(self, qos_policy_repository: QoSPolicyRepository):
        self.qos_policy_repository = qos_policy_repository
    
    def execute(self, policy_id: Optional[int] = None) -> QoSVisualizationData:
        """
        Obtient les données de visualisation pour une politique QoS.
        
        Args:
            policy_id: ID de la politique (optionnel)
            
        Returns:
            QoSVisualizationData: Données de visualisation
        """
        if policy_id:
            policy = self.qos_policy_repository.get_policy(policy_id)
            if not policy:
                raise QoSPolicyNotFoundException(policy_id)
            
            return QoSVisualizationData(
                policy_id=policy_id,
                policy_name=policy.get('name', ''),
                bandwidth_limit=policy.get('bandwidth_limit', 0),
                traffic_classes=policy.get('traffic_classes', []),
                traffic_data={
                    'current_usage': 0,
                    'peak_usage': 0,
                    'average_usage': 0
                }
            )
        
        # Données générales de visualisation
        return QoSVisualizationData(
            policy_id=0,
            policy_name='Global QoS Status',
            bandwidth_limit=10000,
            traffic_classes=[],
            traffic_data={
                'active_policies': len(self.qos_policy_repository.list_policies()),
                'total_bandwidth': 10000,
                'utilization': 45.2
            }
        )