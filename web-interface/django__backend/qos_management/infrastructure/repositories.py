"""
Implémentations concrètes des repositories pour la gestion QoS basées sur Django ORM.

Ce module implémente les interfaces de repository définies dans le domaine
en utilisant Django ORM pour accéder à la base de données.
"""

from typing import Dict, List, Any, Optional
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from ..domain.interfaces import (
    QoSPolicyRepository, 
    TrafficClassRepository, 
    TrafficClassifierRepository,
    InterfaceQoSPolicyRepository
)
from ..domain.exceptions import (
    QoSPolicyNotFoundException,
    TrafficClassNotFoundException,
    TrafficClassifierNotFoundException,
    InterfaceQoSPolicyNotFoundException
)

from ..models import (
    QoSPolicy as QoSPolicyModel,
    TrafficClass as TrafficClassModel,
    TrafficClassifier as TrafficClassifierModel,
    InterfaceQoSPolicy as InterfaceQoSPolicyModel
)
from network_management.models import NetworkInterface

from .mappers import (
    map_qos_policy_to_dict,
    map_traffic_class_to_dict,
    map_traffic_classifier_to_dict,
    map_interface_qos_policy_to_dict
)


class DjangoQoSPolicyRepository(QoSPolicyRepository):
    """
    Implémentation Django du repository pour les politiques QoS.
    """
    
    def get_policy(self, policy_id: int) -> Dict[str, Any]:
        """
        Récupère une politique QoS par son identifiant.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            La politique QoS sous forme de dictionnaire
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        try:
            policy = QoSPolicyModel.objects.get(pk=policy_id)
            return map_qos_policy_to_dict(policy)
        except QoSPolicyModel.DoesNotExist:
            raise QoSPolicyNotFoundException(policy_id)
    
    def list_policies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les politiques QoS selon des filtres optionnels.
        
        Args:
            filters: Filtres optionnels
            
        Returns:
            Liste des politiques QoS
        """
        filters = filters or {}
        queryset = QoSPolicyModel.objects.all()
        
        # Appliquer les filtres
        if 'is_active' in filters:
            queryset = queryset.filter(is_active=filters['is_active'])
        if 'name' in filters:
            queryset = queryset.filter(name__icontains=filters['name'])
        if 'policy_type' in filters:
            queryset = queryset.filter(policy_type=filters['policy_type'])
        
        # Convertir en dictionnaires
        return [map_qos_policy_to_dict(policy) for policy in queryset]
    
    def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle politique QoS.
        
        Args:
            policy_data: Données de la politique
            
        Returns:
            La politique QoS créée
        """
        # Extraire les champs valides pour le modèle
        valid_fields = [
            'name', 'description', 'bandwidth_limit', 'is_active', 
            'policy_type', 'priority'
        ]
        model_data = {k: v for k, v in policy_data.items() if k in valid_fields}
        
        # Créer la politique
        with transaction.atomic():
            policy = QoSPolicyModel.objects.create(**model_data)
            return map_qos_policy_to_dict(policy)
    
    def update_policy(self, policy_id: int, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une politique QoS.
        
        Args:
            policy_id: ID de la politique à mettre à jour
            policy_data: Nouvelles données
            
        Returns:
            La politique QoS mise à jour
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        try:
            policy = QoSPolicyModel.objects.get(pk=policy_id)
            
            # Mettre à jour les champs valides
            valid_fields = [
                'name', 'description', 'bandwidth_limit', 'is_active',
                'policy_type', 'priority'
            ]
            for field in valid_fields:
                if field in policy_data:
                    setattr(policy, field, policy_data[field])
            
            policy.save()
            return map_qos_policy_to_dict(policy)
        except QoSPolicyModel.DoesNotExist:
            raise QoSPolicyNotFoundException(policy_id)
    
    def delete_policy(self, policy_id: int) -> bool:
        """
        Supprime une politique QoS.
        
        Args:
            policy_id: ID de la politique à supprimer
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        try:
            policy = QoSPolicyModel.objects.get(pk=policy_id)
            policy.delete()
            return True
        except QoSPolicyModel.DoesNotExist:
            raise QoSPolicyNotFoundException(policy_id)


class DjangoTrafficClassRepository(TrafficClassRepository):
    """
    Implémentation Django du repository pour les classes de trafic.
    """
    
    def get_traffic_class(self, class_id: int) -> Dict[str, Any]:
        """
        Récupère une classe de trafic par son identifiant.
        
        Args:
            class_id: ID de la classe de trafic
            
        Returns:
            La classe de trafic sous forme de dictionnaire
            
        Raises:
            TrafficClassNotFoundException: Si la classe de trafic n'existe pas
        """
        try:
            traffic_class = TrafficClassModel.objects.get(pk=class_id)
            return map_traffic_class_to_dict(traffic_class)
        except TrafficClassModel.DoesNotExist:
            raise TrafficClassNotFoundException(class_id)
    
    def list_traffic_classes(self, policy_id: Optional[int] = None, 
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les classes de trafic, optionnellement filtrées par politique.
        
        Args:
            policy_id: ID de la politique (optionnel)
            filters: Filtres supplémentaires (optionnel)
            
        Returns:
            Liste des classes de trafic
        """
        queryset = TrafficClassModel.objects.all()
        filters = filters or {}
        
        if policy_id is not None:
            queryset = queryset.filter(policy_id=policy_id)
            
        # Appliquer les filtres additionnels
        if 'priority' in filters:
            queryset = queryset.filter(priority=filters['priority'])
            
        if 'dscp' in filters:
            queryset = queryset.filter(dscp=filters['dscp'])
        
        return [map_traffic_class_to_dict(traffic_class) for traffic_class in queryset]
    
    def create_traffic_class(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle classe de trafic.
        
        Args:
            class_data: Données de la classe de trafic
            
        Returns:
            La classe de trafic créée
        """
        # Valider que policy_id est fourni
        if 'policy_id' not in class_data:
            raise ValueError("policy_id est requis pour créer une classe de trafic")
        
        # Extraire les champs valides pour le modèle
        valid_fields = [
            'name', 'description', 'priority', 'min_bandwidth', 'max_bandwidth',
            'dscp', 'burst', 'policy_id', 'queue_discipline'
        ]
        model_data = {k: v for k, v in class_data.items() if k in valid_fields}
        
        # Créer la classe de trafic
        with transaction.atomic():
            traffic_class = TrafficClassModel.objects.create(**model_data)
            
            # Créer les classificateurs si présents
            classifiers_data = class_data.get('classifiers', [])
            for classifier_data in classifiers_data:
                classifier_data['traffic_class_id'] = traffic_class.id
                self._create_classifier(classifier_data)
            
            return map_traffic_class_to_dict(traffic_class)
    
    def update_traffic_class(self, class_id: int, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une classe de trafic.
        
        Args:
            class_id: ID de la classe de trafic à mettre à jour
            class_data: Nouvelles données
            
        Returns:
            La classe de trafic mise à jour
            
        Raises:
            TrafficClassNotFoundException: Si la classe de trafic n'existe pas
        """
        try:
            traffic_class = TrafficClassModel.objects.get(pk=class_id)
            
            # Mettre à jour les champs valides
            valid_fields = [
                'name', 'description', 'priority', 'min_bandwidth', 'max_bandwidth',
                'dscp', 'burst', 'queue_discipline'
            ]
            for field in valid_fields:
                if field in class_data:
                    setattr(traffic_class, field, class_data[field])
            
            traffic_class.save()
            return map_traffic_class_to_dict(traffic_class)
        except TrafficClassModel.DoesNotExist:
            raise TrafficClassNotFoundException(class_id)
    
    def delete_traffic_class(self, class_id: int) -> bool:
        """
        Supprime une classe de trafic.
        
        Args:
            class_id: ID de la classe de trafic à supprimer
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            TrafficClassNotFoundException: Si la classe de trafic n'existe pas
        """
        try:
            traffic_class = TrafficClassModel.objects.get(pk=class_id)
            traffic_class.delete()
            return True
        except TrafficClassModel.DoesNotExist:
            raise TrafficClassNotFoundException(class_id)
    
    def _create_classifier(self, classifier_data: Dict[str, Any]) -> TrafficClassifierModel:
        """
        Méthode utilitaire pour créer un classificateur de trafic.
        
        Args:
            classifier_data: Données du classificateur
            
        Returns:
            Le classificateur créé
        """
        valid_fields = [
            'name', 'description', 'source_ip', 'destination_ip', 'protocol',
            'source_port_start', 'source_port_end', 'destination_port_start',
            'destination_port_end', 'dscp_marking', 'vlan', 'traffic_class_id'
        ]
        model_data = {k: v for k, v in classifier_data.items() if k in valid_fields}
        
        return TrafficClassifierModel.objects.create(**model_data)


class DjangoTrafficClassifierRepository(TrafficClassifierRepository):
    """
    Implémentation Django du repository pour les classificateurs de trafic.
    """
    
    def get_classifier(self, classifier_id: int) -> Dict[str, Any]:
        """
        Récupère un classificateur de trafic par son identifiant.
        
        Args:
            classifier_id: ID du classificateur
            
        Returns:
            Le classificateur sous forme de dictionnaire
            
        Raises:
            TrafficClassifierNotFoundException: Si le classificateur n'existe pas
        """
        try:
            classifier = TrafficClassifierModel.objects.get(pk=classifier_id)
            return map_traffic_classifier_to_dict(classifier)
        except TrafficClassifierModel.DoesNotExist:
            raise TrafficClassifierNotFoundException(classifier_id)
    
    def list_classifiers(self, traffic_class_id: Optional[int] = None, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les classificateurs de trafic, optionnellement filtrés par classe de trafic.
        
        Args:
            traffic_class_id: ID de la classe de trafic (optionnel)
            filters: Filtres supplémentaires (optionnel)
            
        Returns:
            Liste des classificateurs de trafic
        """
        queryset = TrafficClassifierModel.objects.all()
        filters = filters or {}
        
        if traffic_class_id is not None:
            queryset = queryset.filter(traffic_class_id=traffic_class_id)
            
        # Appliquer les filtres additionnels
        if 'protocol' in filters:
            queryset = queryset.filter(protocol=filters['protocol'])
        
        return [map_traffic_classifier_to_dict(classifier) for classifier in queryset]
    
    def create_classifier(self, classifier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau classificateur de trafic.
        
        Args:
            classifier_data: Données du classificateur
            
        Returns:
            Le classificateur créé
        """
        # Valider que traffic_class_id est fourni
        if 'traffic_class_id' not in classifier_data:
            raise ValueError("traffic_class_id est requis pour créer un classificateur")
        
        # Extraire les champs valides pour le modèle
        valid_fields = [
            'name', 'description', 'source_ip', 'destination_ip', 'protocol',
            'source_port_start', 'source_port_end', 'destination_port_start',
            'destination_port_end', 'dscp_marking', 'vlan', 'traffic_class_id'
        ]
        model_data = {k: v for k, v in classifier_data.items() if k in valid_fields}
        
        # Créer le classificateur
        classifier = TrafficClassifierModel.objects.create(**model_data)
        return map_traffic_classifier_to_dict(classifier)
    
    def update_classifier(self, classifier_id: int, classifier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un classificateur de trafic.
        
        Args:
            classifier_id: ID du classificateur à mettre à jour
            classifier_data: Nouvelles données
            
        Returns:
            Le classificateur mis à jour
            
        Raises:
            TrafficClassifierNotFoundException: Si le classificateur n'existe pas
        """
        try:
            classifier = TrafficClassifierModel.objects.get(pk=classifier_id)
            
            # Mettre à jour les champs valides
            valid_fields = [
                'name', 'description', 'source_ip', 'destination_ip', 'protocol',
                'source_port_start', 'source_port_end', 'destination_port_start',
                'destination_port_end', 'dscp_marking', 'vlan'
            ]
            for field in valid_fields:
                if field in classifier_data:
                    setattr(classifier, field, classifier_data[field])
            
            classifier.save()
            return map_traffic_classifier_to_dict(classifier)
        except TrafficClassifierModel.DoesNotExist:
            raise TrafficClassifierNotFoundException(classifier_id)
    
    def delete_classifier(self, classifier_id: int) -> bool:
        """
        Supprime un classificateur de trafic.
        
        Args:
            classifier_id: ID du classificateur à supprimer
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            TrafficClassifierNotFoundException: Si le classificateur n'existe pas
        """
        try:
            classifier = TrafficClassifierModel.objects.get(pk=classifier_id)
            classifier.delete()
            return True
        except TrafficClassifierModel.DoesNotExist:
            raise TrafficClassifierNotFoundException(classifier_id)


class DjangoInterfaceQoSPolicyRepository(InterfaceQoSPolicyRepository):
    """
    Implémentation Django du repository pour les associations interface-politique QoS.
    """
    
    def get_interface_policy(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère l'association politique-interface par ID d'interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            L'association sous forme de dictionnaire
            
        Raises:
            InterfaceQoSPolicyNotFoundException: Si aucune association n'existe pour cette interface
        """
        try:
            interface_policy = InterfaceQoSPolicyModel.objects.get(interface_id=interface_id)
            return map_interface_qos_policy_to_dict(interface_policy)
        except InterfaceQoSPolicyModel.DoesNotExist:
            raise InterfaceQoSPolicyNotFoundException(interface_id=interface_id)
    
    def list_interface_policies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les associations interface-politique selon des filtres optionnels.
        
        Args:
            filters: Filtres optionnels
            
        Returns:
            Liste des associations interface-politique
        """
        queryset = InterfaceQoSPolicyModel.objects.all()
        filters = filters or {}
        
        if 'interface_id' in filters:
            queryset = queryset.filter(interface_id=filters['interface_id'])
            
        if 'policy_id' in filters:
            queryset = queryset.filter(policy_id=filters['policy_id'])
            
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])
        
        return [map_interface_qos_policy_to_dict(policy) for policy in queryset]
    
    def apply_policy_to_interface(self, policy_id: int, interface_id: int, 
                                parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Applique une politique QoS à une interface réseau.
        
        Args:
            policy_id: ID de la politique QoS
            interface_id: ID de l'interface réseau
            parameters: Paramètres supplémentaires (optionnel)
            
        Returns:
            L'association créée ou mise à jour
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        # Vérifier que la politique et l'interface existent
        try:
            policy = QoSPolicyModel.objects.get(pk=policy_id)
        except QoSPolicyModel.DoesNotExist:
            raise QoSPolicyNotFoundException(policy_id)
            
        try:
            interface = NetworkInterface.objects.get(pk=interface_id)
        except NetworkInterface.DoesNotExist:
            raise ValueError(f"Interface with ID {interface_id} not found")
            
        # Vérifier si une association existe déjà
        interface_policy = None
        try:
            interface_policy = InterfaceQoSPolicyModel.objects.get(interface_id=interface_id)
            
            # Mettre à jour l'association existante
            interface_policy.policy = policy
            interface_policy.parameters = parameters or {}
            interface_policy.status = 'applied'
            interface_policy.save()
            
        except InterfaceQoSPolicyModel.DoesNotExist:
            # Créer une nouvelle association
            interface_policy = InterfaceQoSPolicyModel.objects.create(
                interface=interface,
                policy=policy,
                parameters=parameters or {},
                status='applied'
            )
            
        return map_interface_qos_policy_to_dict(interface_policy)
    
    def remove_policy_from_interface(self, interface_id: int) -> bool:
        """
        Retire la politique QoS d'une interface réseau.
        
        Args:
            interface_id: ID de l'interface réseau
            
        Returns:
            True si le retrait a réussi
            
        Raises:
            InterfaceQoSPolicyNotFoundException: Si aucune politique n'est appliquée à cette interface
        """
        try:
            interface_policy = InterfaceQoSPolicyModel.objects.get(interface_id=interface_id)
            interface_policy.delete()
            return True
        except InterfaceQoSPolicyModel.DoesNotExist:
            raise InterfaceQoSPolicyNotFoundException(interface_id=interface_id) 