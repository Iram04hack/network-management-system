"""
Cas d'utilisation pour la gestion des politiques de qualité de service (QoS).

Ce module implémente les cas d'utilisation liés aux politiques QoS
selon les principes de l'architecture hexagonale.
"""

import logging
from typing import Dict, Any, List, Optional

from ..domain.interfaces import QoSPolicyRepository, QoSConfigurationService
from ..domain.exceptions import (
    QoSPolicyNotFoundException,
    QoSValidationException,
    QoSConfigurationException
)
from ..domain.repository_interfaces import (
    QoSPolicyReader,
    QoSPolicyWriter,
    QoSPolicyQueryService
)
from network_management.models import NetworkInterface, NetworkDevice

logger = logging.getLogger(__name__)

# Types de politiques QoS valides
VALID_POLICY_TYPES = ["htb", "hfsc", "cbq", "fq_codel"]

# Paramètres requis par type de politique
REQUIRED_PARAMS_BY_TYPE = {
    "htb": ["bandwidth_limit", "priority"],
    "hfsc": ["bandwidth_limit", "priority", "latency"],
    "cbq": ["bandwidth_limit", "priority", "borrowing"],
    "fq_codel": ["queue_limit", "quantum"]
}

# Bornes de validation pour certains paramètres
VALIDATION_BOUNDS = {
    "bandwidth_limit": {"min": 0, "max": 10000000},  # 0-10 Gbps
    "priority": {"min": 0, "max": 7},
    "latency": {"min": 0, "max": 1000},  # 0-1000 ms
    "queue_limit": {"min": 0, "max": 10000},
    "quantum": {"min": 0, "max": 65535}
}


class GetQoSPolicyUseCase:
    """
    Cas d'utilisation pour récupérer une politique QoS.
    
    Ce cas d'utilisation permet de récupérer les détails d'une politique QoS existante.
    """
    
    def __init__(self, policy_reader: QoSPolicyReader):
        """
        Initialise le cas d'utilisation avec les dépendances requises.
        
        Args:
            policy_reader: Repository pour la lecture des politiques QoS
        """
        self.policy_reader = policy_reader
    
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
        try:
            return self.policy_reader.get_by_id(policy_id)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la politique QoS {policy_id}: {str(e)}", exc_info=True)
            raise


class ListQoSPoliciesUseCase:
    """
    Cas d'utilisation pour lister les politiques QoS.
    
    Ce cas d'utilisation permet de récupérer la liste des politiques QoS
    avec possibilité de filtrage.
    """
    
    def __init__(self, policy_reader: QoSPolicyReader, policy_query_service: QoSPolicyQueryService):
        """
        Initialise le cas d'utilisation avec les dépendances requises.
        
        Args:
            policy_reader: Repository pour la lecture des politiques QoS
            policy_query_service: Service pour les requêtes spécialisées
        """
        self.policy_reader = policy_reader
        self.policy_query_service = policy_query_service
    
    def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les politiques QoS selon des filtres optionnels.
        
        Args:
            filters: Filtres optionnels
            
        Returns:
            Liste des politiques QoS
        """
        try:
            # Vérifier si des filtres avancés nécessitent le service de requête
            if filters and any(k in filters for k in ['device_id', 'interface_id', 'search']):
                # Construire les critères de recherche
                criteria = {}
                if 'search' in filters:
                    criteria['name'] = filters['search']
                    criteria['description'] = filters['search']
                
                # Gérer les requêtes spéciales
                if 'device_id' in filters:
                    return self.policy_query_service.get_by_device(filters['device_id'])
                elif 'interface_id' in filters:
                    return self.policy_query_service.get_by_interface(filters['interface_id'])
                else:
                    return self.policy_query_service.search_by_criteria(criteria)
            else:
                # Utiliser la méthode standard
                return self.policy_reader.get_all(filters)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des politiques QoS: {str(e)}", exc_info=True)
            raise


class CreateQoSPolicyUseCase:
    """
    Cas d'utilisation pour créer une politique QoS.
    
    Ce cas d'utilisation permet de créer une nouvelle politique QoS
    avec les paramètres spécifiés.
    """
    
    def __init__(self, policy_writer: QoSPolicyWriter):
        """
        Initialise le cas d'utilisation avec les dépendances requises.
        
        Args:
            policy_writer: Repository pour l'écriture des politiques QoS
        """
        self.policy_writer = policy_writer
    
    def execute(self, policy_data: Dict[str, Any], validate_only: bool = False) -> Dict[str, Any]:
        """
        Crée une nouvelle politique QoS.
        
        Args:
            policy_data: Données de la politique
            validate_only: Si True, valide uniquement sans créer
            
        Returns:
            Politique QoS créée
            
        Raises:
            QoSValidationException: Si les données sont invalides
        """
        try:
            # Validation de la politique
            self._validate_policy(policy_data)
            
            # Si validation uniquement, retourner sans créer
            if validate_only:
                return {"valid": True}
            
            # Créer la politique
            return self.policy_writer.create(policy_data)
        except QoSValidationException as e:
            logger.error(f"Erreur de validation lors de la création de la politique QoS: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création de la politique QoS: {str(e)}", exc_info=True)
            raise
    
    def _validate_policy(self, policy_data: Dict[str, Any]) -> None:
        """
        Valide les données d'une politique QoS.
        
        Args:
            policy_data: Données à valider
            
        Raises:
            QoSValidationException: Si les données sont invalides
        """
        errors = {}
        
        # Vérifier les champs obligatoires communs
        required_fields = ["name", "policy_type"]
        for field in required_fields:
            if field not in policy_data:
                errors[field] = f"Le champ '{field}' est obligatoire"
        
        # Vérifier que le nom n'est pas vide
        if policy_data.get("name", "") == "":
            errors["name"] = "Le nom de la politique ne peut pas être vide"
        
        # Vérifier que le type est valide
        policy_type = policy_data.get("policy_type")
        if policy_type and policy_type not in VALID_POLICY_TYPES:
            errors["policy_type"] = f"Type de politique invalide. Valeurs acceptées: {', '.join(VALID_POLICY_TYPES)}"
        
        # Vérifier les paramètres spécifiques au type
        if policy_type and policy_type in REQUIRED_PARAMS_BY_TYPE:
            required_params = REQUIRED_PARAMS_BY_TYPE[policy_type]
            params = policy_data.get("parameters", {})
            
            for param in required_params:
                if param not in policy_data and param not in params:
                    if "parameters_errors" not in errors:
                        errors["parameters_errors"] = {}
                    errors["parameters_errors"][param] = f"Le paramètre '{param}' est requis pour le type '{policy_type}'"
        
        # Vérifier les bornes des paramètres
        for param_name, bounds in VALIDATION_BOUNDS.items():
            param_value = policy_data.get(param_name, policy_data.get("parameters", {}).get(param_name))
            if param_value is not None:
                try:
                    param_value = float(param_value)
                    if param_value < bounds["min"] or param_value > bounds["max"]:
                        if "parameters_errors" not in errors:
                            errors["parameters_errors"] = {}
                        errors["parameters_errors"][param_name] = (
                            f"La valeur de '{param_name}' doit être entre {bounds['min']} et {bounds['max']}"
                        )
                except (ValueError, TypeError):
                    if "parameters_errors" not in errors:
                        errors["parameters_errors"] = {}
                    errors["parameters_errors"][param_name] = f"La valeur de '{param_name}' doit être un nombre"
        
        # Vérifier la priorité
        priority = policy_data.get("priority")
        if priority is not None:
            try:
                priority = int(priority)
                if priority < 0 or priority > 7:
                    errors["priority"] = "La priorité doit être un entier entre 0 et 7"
            except (ValueError, TypeError):
                errors["priority"] = "La priorité doit être un entier"
        
        # Lancer une exception s'il y a des erreurs
        if errors:
            raise QoSValidationException("Validation de la politique QoS échouée", errors)


class UpdateQoSPolicyUseCase:
    """
    Cas d'utilisation pour mettre à jour une politique QoS.
    
    Ce cas d'utilisation permet de modifier une politique QoS existante.
    """
    
    def __init__(self, policy_reader: QoSPolicyReader, policy_writer: QoSPolicyWriter):
        """
        Initialise le cas d'utilisation avec les dépendances requises.
        
        Args:
            policy_reader: Repository pour la lecture des politiques QoS
            policy_writer: Repository pour l'écriture des politiques QoS
        """
        self.policy_reader = policy_reader
        self.policy_writer = policy_writer
    
    def execute(self, policy_id: int, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une politique QoS.
        
        Args:
            policy_id: ID de la politique
            policy_data: Nouvelles données
            
        Returns:
            Politique QoS mise à jour
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        try:
            # Vérifier l'existence de la politique
            self.policy_reader.get_by_id(policy_id)
            
            # Mettre à jour la politique
            return self.policy_writer.update(policy_id, policy_data)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la politique QoS {policy_id}: {str(e)}", exc_info=True)
            raise


class DeleteQoSPolicyUseCase:
    """
    Cas d'utilisation pour supprimer une politique QoS.
    
    Ce cas d'utilisation permet de supprimer une politique QoS existante.
    """
    
    def __init__(self, policy_reader: QoSPolicyReader, policy_writer: QoSPolicyWriter, policy_query_service: QoSPolicyQueryService):
        """
        Initialise le cas d'utilisation avec les dépendances requises.
        
        Args:
            policy_reader: Repository pour la lecture des politiques QoS
            policy_writer: Repository pour l'écriture des politiques QoS
            policy_query_service: Service pour les requêtes spécialisées
        """
        self.policy_reader = policy_reader
        self.policy_writer = policy_writer
        self.policy_query_service = policy_query_service
        
    def execute(self, policy_id: int, force: bool = False) -> bool:
        """
        Supprime une politique QoS.
        
        Args:
            policy_id: ID de la politique
            force: Si True, supprime même si des références existent
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
            QoSConfigurationException: Si la politique est utilisée et force=False
        """
        try:
            # Vérifier l'existence de la politique
            policy = self.policy_reader.get_by_id(policy_id)
            
            # Vérifier si la politique est utilisée actuellement
            if not force:
                # Rechercher les équipements utilisant cette politique
                devices_using_policy = self._find_devices_using_policy(policy_id)
                interfaces_using_policy = self._find_interfaces_using_policy(policy_id)
                
                if devices_using_policy or interfaces_using_policy:
                    error_message = "La politique QoS est actuellement utilisée et ne peut pas être supprimée."
                    details = {}
                    
                    if devices_using_policy:
                        details["devices"] = devices_using_policy
                        
                    if interfaces_using_policy:
                        details["interfaces"] = interfaces_using_policy
                        
                    details["solution"] = "Utilisez force=True pour forcer la suppression, ou retirez d'abord la politique des équipements et interfaces."
                    
                    raise QoSConfigurationException(error_message, "policy_in_use", details)
            
            # Supprimer la politique
            return self.policy_writer.delete(policy_id)
        except (QoSPolicyNotFoundException, QoSConfigurationException):
            # Ne pas logger ces exceptions attendues, juste les propager
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique QoS {policy_id}: {str(e)}", exc_info=True)
            raise
    
    def _find_devices_using_policy(self, policy_id: int) -> List[Dict[str, Any]]:
        """
        Trouve tous les équipements utilisant la politique.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Liste des équipements utilisant la politique
        """
        # Cette méthode utiliserait normalement un repository spécifique pour
        # les équipements, mais pour simplifier, nous allons utiliser une approche
        # basée sur le policy_query_service
        
        # Pour l'implémentation réelle, on devrait appeler un service approprié
        # En attendant, on retourne une liste vide
        
        # Liste simulée des équipements
        from ..models import InterfaceQoSPolicy
        from network_management.models import NetworkInterface, NetworkDevice
        
        devices = []
        try:
            # Trouver toutes les interfaces utilisant cette politique
            applied_policies = InterfaceQoSPolicy.objects.filter(policy_id=policy_id)
            interface_ids = applied_policies.values_list('interface_id', flat=True)
            
            # Trouver les équipements associés à ces interfaces
            if interface_ids:
                interfaces = NetworkInterface.objects.filter(id__in=interface_ids)
                device_ids = interfaces.values_list('device_id', flat=True).distinct()
                
                # Récupérer les informations des équipements
                device_objects = NetworkDevice.objects.filter(id__in=device_ids)
                
                for device in device_objects:
                    devices.append({
                        "id": device.id,
                        "name": device.name,
                        "type": device.device_type
                    })
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche des équipements utilisant la politique {policy_id}: {str(e)}")
            # En cas d'erreur, on ignore et on continue
            
        return devices
    
    def _find_interfaces_using_policy(self, policy_id: int) -> List[Dict[str, Any]]:
        """
        Trouve toutes les interfaces utilisant la politique.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Liste des interfaces utilisant la politique
        """
        from ..models import InterfaceQoSPolicy
        from network_management.models import NetworkInterface
        
        interfaces = []
        try:
            # Trouver toutes les associations interface-politique pour cette politique
            applied_policies = InterfaceQoSPolicy.objects.filter(policy_id=policy_id)
            interface_ids = applied_policies.values_list('interface_id', flat=True)
            
            # Récupérer les informations des interfaces
            if interface_ids:
                interface_objects = NetworkInterface.objects.filter(id__in=interface_ids)
                
                for interface in interface_objects:
                    interfaces.append({
                        "id": interface.id,
                        "name": interface.name,
                        "device_id": interface.device_id,
                        "device_name": interface.device.name if hasattr(interface, 'device') else "Unknown"
                    })
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche des interfaces utilisant la politique {policy_id}: {str(e)}")
            # En cas d'erreur, on ignore et on continue
            
        return interfaces


class ApplyQoSPolicyUseCase:
    """
    Cas d'utilisation pour appliquer une politique QoS.
    
    Ce cas d'utilisation permet d'appliquer une politique QoS à une interface.
    """
    
    def __init__(self, 
                policy_repository: QoSPolicyRepository,
                configuration_service: QoSConfigurationService):
        """
        Initialise le cas d'utilisation.
        
        Args:
            policy_repository: Repository pour les politiques QoS
            configuration_service: Service de configuration QoS
        """
        self.policy_repository = policy_repository
        self.configuration_service = configuration_service
    
    def execute(self, device_id: int, interface_id: int, policy_id: int) -> Dict[str, Any]:
        """
        Applique une politique QoS à une interface.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface
            policy_id: ID de la politique à appliquer
            
        Returns:
            Résultat de l'opération
        """
        try:
            # Vérifier que la politique existe
            policy = self.policy_repository.get_by_id(policy_id)
            
            # Appliquer la politique
            success = self.configuration_service.apply_policy(device_id, interface_id, policy_id)
            
            return {
                "success": success,
                "device_id": device_id,
                "interface_id": interface_id,
                "policy_id": policy_id,
                "policy_name": policy.get("name", "")
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS {policy_id}: {str(e)}", exc_info=True)
            raise 