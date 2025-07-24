"""
Implémentation des repositories pour les politiques QoS.

Ce module fournit des implémentations Django pour les interfaces
de repositories des politiques QoS.
"""

from typing import Dict, List, Any, Optional
from django.db import transaction
from django.db.models import Q, Count, F, Value, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta

from ..domain.repository_interfaces import (
    QoSPolicyReader,
    QoSPolicyWriter,
    QoSPolicyQueryService,
    QoSPolicyRepository
)
from ..domain.exceptions import (
    QoSPolicyNotFoundException
)
from ..models import (
    QoSPolicy as QoSPolicyModel,
    InterfaceQoSPolicy,
    TrafficClass
)
from network_management.models import NetworkInterface, NetworkDevice

from .mappers import map_qos_policy_to_dict


class DjangoQoSPolicyReader(QoSPolicyReader):
    """
    Implémentation Django du repository pour la lecture des politiques QoS.
    """
    
    def get_by_id(self, policy_id: int) -> Dict[str, Any]:
        """
        Récupère une politique QoS par son ID.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Données de la politique QoS
            
        Raises:
            QoSPolicyNotFoundException: Si la politique n'existe pas
        """
        try:
            policy = QoSPolicyModel.objects.get(pk=policy_id)
            return map_qos_policy_to_dict(policy)
        except QoSPolicyModel.DoesNotExist:
            raise QoSPolicyNotFoundException(policy_id)
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère toutes les politiques QoS correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer
            
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
        if 'priority_min' in filters:
            queryset = queryset.filter(priority__gte=filters['priority_min'])
        if 'priority_max' in filters:
            queryset = queryset.filter(priority__lte=filters['priority_max'])
        
        # Convertir en dictionnaires
        return [map_qos_policy_to_dict(policy) for policy in queryset]


class DjangoQoSPolicyWriter(QoSPolicyWriter):
    """
    Implémentation Django du repository pour l'écriture des politiques QoS.
    """
    
    def create(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle politique QoS.
        
        Args:
            policy_data: Données de la politique
            
        Returns:
            Politique QoS créée
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
    
    def update(self, policy_id: int, policy_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def delete(self, policy_id: int) -> bool:
        """
        Supprime une politique QoS.
        
        Args:
            policy_id: ID de la politique
            
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


class DjangoQoSPolicyQueryService(QoSPolicyQueryService):
    """
    Implémentation Django du service de requêtes spécialisées pour les politiques QoS.
    """
    
    def get_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les politiques QoS associées à un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des politiques QoS
        """
        # Récupérer les interfaces de l'équipement
        interfaces = NetworkInterface.objects.filter(device_id=device_id).values_list('id', flat=True)
        
        # Récupérer les politiques appliquées à ces interfaces
        applied_policies = InterfaceQoSPolicy.objects.filter(interface_id__in=interfaces)
        policy_ids = applied_policies.values_list('policy_id', flat=True).distinct()
        
        # Récupérer les détails des politiques
        policies = QoSPolicyModel.objects.filter(id__in=policy_ids)
        return [map_qos_policy_to_dict(policy) for policy in policies]
    
    def get_by_interface(self, interface_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les politiques QoS associées à une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Liste des politiques QoS
        """
        # Récupérer les politiques appliquées à cette interface
        applied_policies = InterfaceQoSPolicy.objects.filter(interface_id=interface_id)
        policy_ids = applied_policies.values_list('policy_id', flat=True).distinct()
        
        # Récupérer les détails des politiques
        policies = QoSPolicyModel.objects.filter(id__in=policy_ids)
        return [map_qos_policy_to_dict(policy) for policy in policies]
    
    def search_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recherche des politiques QoS selon des critères spécifiques.
        
        Args:
            criteria: Critères de recherche avancés
                - name: Nom de la politique (recherche partielle)
                - description: Description de la politique (recherche partielle)
                - policy_types: Liste des types de politique
                - priority_range: Tuple (min, max) pour la priorité
                - is_active: État d'activation
                - application_status: 'applied' ou 'not_applied'
                - created_after: Date de création minimum (YYYY-MM-DD)
                - created_before: Date de création maximum (YYYY-MM-DD)
                - bandwidth_range: Tuple (min, max) pour la bande passante
                - traffic_class_count: Nombre minimum de classes de trafic
                - sort_by: Champ de tri ('name', 'priority', 'created_at')
                - sort_order: Ordre de tri ('asc' ou 'desc')
                - keyword: Mot-clé à rechercher dans tous les champs texte
            
        Returns:
            Liste des politiques QoS correspondantes
        """
        query = QoSPolicyModel.objects.all()
        
        # Recherche textuelle
        name_query = Q()
        description_query = Q()
        
        # Recherche par nom
        if 'name' in criteria and criteria['name']:
            name_query |= Q(name__icontains=criteria['name'])
        
        # Recherche par description
        if 'description' in criteria and criteria['description']:
            description_query |= Q(description__icontains=criteria['description'])
        
        # Recherche par mot-clé dans tous les champs texte
        if 'keyword' in criteria and criteria['keyword']:
            keyword = criteria['keyword']
            name_query |= Q(name__icontains=keyword)
            description_query |= Q(description__icontains=keyword)
        
        # Combiner les requêtes textuelles
        text_query = name_query | description_query
        if text_query:
            query = query.filter(text_query)
        
        # Filtres par type de politique
        if 'policy_types' in criteria and criteria['policy_types']:
            query = query.filter(policy_type__in=criteria['policy_types'])
            
        # Filtres par plage de priorité
        if 'priority_range' in criteria:
            p_min, p_max = criteria['priority_range']
            query = query.filter(priority__gte=p_min, priority__lte=p_max)
            
        # Filtres par état d'activation
        if 'is_active' in criteria:
            query = query.filter(is_active=criteria['is_active'])
            
        # Filtres par statut d'application
        if 'application_status' in criteria:
            status = criteria['application_status']
            applied_policy_ids = InterfaceQoSPolicy.objects.values_list('policy_id', flat=True).distinct()
            
            if status == 'applied':
                query = query.filter(id__in=applied_policy_ids)
            elif status == 'not_applied':
                query = query.exclude(id__in=applied_policy_ids)
        
        # Filtres par date de création
        if 'created_after' in criteria and criteria['created_after']:
            try:
                date_after = datetime.strptime(criteria['created_after'], '%Y-%m-%d')
                query = query.filter(created_at__gte=date_after)
            except (ValueError, TypeError):
                pass  # Ignorer les dates invalides
                
        if 'created_before' in criteria and criteria['created_before']:
            try:
                date_before = datetime.strptime(criteria['created_before'], '%Y-%m-%d')
                date_before = date_before + timedelta(days=1)  # Inclure le jour spécifié
                query = query.filter(created_at__lt=date_before)
            except (ValueError, TypeError):
                pass  # Ignorer les dates invalides
        
        # Filtres par plage de bande passante
        if 'bandwidth_range' in criteria:
            bw_min, bw_max = criteria['bandwidth_range']
            query = query.filter(bandwidth_limit__gte=bw_min, bandwidth_limit__lte=bw_max)
            
        # Filtres par nombre de classes de trafic
        if 'traffic_class_count' in criteria:
            min_count = criteria['traffic_class_count']
            # Annoter chaque politique avec le nombre de classes de trafic associées
            query = query.annotate(class_count=Count('trafficclass'))
            query = query.filter(class_count__gte=min_count)
        
        # Trier les résultats
        sort_field = criteria.get('sort_by', 'name')
        sort_order = criteria.get('sort_order', 'asc')
        
        valid_sort_fields = {
            'name': 'name',
            'priority': 'priority',
            'created_at': 'created_at',
            'bandwidth': 'bandwidth_limit'
        }
        
        if sort_field in valid_sort_fields:
            order_prefix = '' if sort_order == 'asc' else '-'
            query = query.order_by(f'{order_prefix}{valid_sort_fields[sort_field]}')
        
        # Limiter le nombre de résultats si spécifié
        if 'limit' in criteria:
            try:
                limit = int(criteria['limit'])
                query = query[:limit]
            except (ValueError, TypeError):
                pass  # Ignorer les limites invalides
        
        # Convertir en dictionnaires
        return [map_qos_policy_to_dict(policy) for policy in query]


class DjangoQoSPolicyRepository(QoSPolicyRepository, DjangoQoSPolicyReader, DjangoQoSPolicyWriter, DjangoQoSPolicyQueryService):
    """
    Implémentation complète du repository pour les politiques QoS.
    
    Cette classe combine toutes les interfaces spécialisées pour fournir
    une implémentation complète du repository.
    """
    pass