"""
Module contenant les repositories pour les politiques de conformité et les vérifications de conformité.
"""

from typing import List, Optional, Type, Dict, Any

from django.db.models import QuerySet, Q

from ..models import CompliancePolicy, ComplianceCheck, NetworkDevice, DeviceConfiguration
from .base_repository import BaseRepository


class CompliancePolicyRepository(BaseRepository[CompliancePolicy]):
    """
    Repository pour les politiques de conformité.
    
    Cette classe fournit des méthodes pour accéder aux données
    des politiques de conformité dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[CompliancePolicy]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[CompliancePolicy]: La classe du modèle CompliancePolicy.
        """
        return CompliancePolicy
    
    def get_by_name(self, name: str) -> Optional[CompliancePolicy]:
        """
        Récupère une politique de conformité par son nom.
        
        Args:
            name (str): Le nom de la politique de conformité à récupérer.
            
        Returns:
            Optional[CompliancePolicy]: La politique de conformité trouvée ou None si aucune politique n'a été trouvée.
        """
        try:
            return self.model_class.objects.get(name=name)
        except self.model_class.DoesNotExist:
            return None
    
    def search(self, query: str) -> QuerySet[CompliancePolicy]:
        """
        Recherche des politiques de conformité par nom, description ou type d'équipement.
        
        Args:
            query (str): Le terme de recherche.
            
        Returns:
            QuerySet[CompliancePolicy]: Un QuerySet contenant les politiques de conformité trouvées.
        """
        return self.model_class.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(device_type__icontains=query)
        )
    
    def get_by_device_type(self, device_type: str) -> QuerySet[CompliancePolicy]:
        """
        Récupère des politiques de conformité par type d'équipement.
        
        Args:
            device_type (str): Le type d'équipement.
            
        Returns:
            QuerySet[CompliancePolicy]: Un QuerySet contenant les politiques de conformité pour le type d'équipement spécifié.
        """
        return self.model_class.objects.filter(device_type=device_type)
    
    def get_by_vendor(self, vendor: str) -> QuerySet[CompliancePolicy]:
        """
        Récupère des politiques de conformité par fabricant.
        
        Args:
            vendor (str): Le fabricant des équipements.
            
        Returns:
            QuerySet[CompliancePolicy]: Un QuerySet contenant les politiques de conformité pour le fabricant spécifié.
        """
        return self.model_class.objects.filter(vendor=vendor)
    
    def get_by_severity(self, severity: str) -> QuerySet[CompliancePolicy]:
        """
        Récupère des politiques de conformité par sévérité.
        
        Args:
            severity (str): La sévérité des politiques.
            
        Returns:
            QuerySet[CompliancePolicy]: Un QuerySet contenant les politiques de conformité avec la sévérité spécifiée.
        """
        return self.model_class.objects.filter(severity=severity)
    
    def get_by_created_by(self, created_by: str) -> QuerySet[CompliancePolicy]:
        """
        Récupère des politiques de conformité par créateur.
        
        Args:
            created_by (str): Le créateur des politiques de conformité.
            
        Returns:
            QuerySet[CompliancePolicy]: Un QuerySet contenant les politiques de conformité créées par le créateur spécifié.
        """
        return self.model_class.objects.filter(created_by=created_by)
    
    def get_applicable_to_device(self, device_type: str, vendor: str = None) -> QuerySet[CompliancePolicy]:
        """
        Récupère des politiques de conformité applicables à un équipement.
        
        Args:
            device_type (str): Le type d'équipement.
            vendor (str, optional): Le fabricant de l'équipement. Defaults to None.
            
        Returns:
            QuerySet[CompliancePolicy]: Un QuerySet contenant les politiques de conformité applicables.
        """
        query = Q(device_type='') | Q(device_type=device_type)
        
        if vendor:
            query &= (Q(vendor='') | Q(vendor=vendor))
        
        return self.model_class.objects.filter(query)


class ComplianceCheckRepository(BaseRepository[ComplianceCheck]):
    """
    Repository pour les vérifications de conformité.
    
    Cette classe fournit des méthodes pour accéder aux données
    des vérifications de conformité dans la base de données.
    """
    
    @property
    def model_class(self) -> Type[ComplianceCheck]:
        """
        Retourne la classe du modèle géré par ce repository.
        
        Returns:
            Type[ComplianceCheck]: La classe du modèle ComplianceCheck.
        """
        return ComplianceCheck
    
    def get_by_device(self, device: NetworkDevice) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité d'un équipement.
        
        Args:
            device (NetworkDevice): L'équipement dont on veut récupérer les vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité de l'équipement.
        """
        return self.model_class.objects.filter(device=device)
    
    def get_by_device_id(self, device_id: int) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité d'un équipement par son ID.
        
        Args:
            device_id (int): L'ID de l'équipement dont on veut récupérer les vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité de l'équipement.
        """
        return self.model_class.objects.filter(device_id=device_id)
    
    def get_by_policy(self, policy: CompliancePolicy) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité d'une politique.
        
        Args:
            policy (CompliancePolicy): La politique dont on veut récupérer les vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité de la politique.
        """
        return self.model_class.objects.filter(policy=policy)
    
    def get_by_policy_id(self, policy_id: int) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité d'une politique par son ID.
        
        Args:
            policy_id (int): L'ID de la politique dont on veut récupérer les vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité de la politique.
        """
        return self.model_class.objects.filter(policy_id=policy_id)
    
    def get_by_configuration(self, configuration: DeviceConfiguration) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité d'une configuration.
        
        Args:
            configuration (DeviceConfiguration): La configuration dont on veut récupérer les vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité de la configuration.
        """
        return self.model_class.objects.filter(configuration=configuration)
    
    def get_by_configuration_id(self, configuration_id: int) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité d'une configuration par son ID.
        
        Args:
            configuration_id (int): L'ID de la configuration dont on veut récupérer les vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité de la configuration.
        """
        return self.model_class.objects.filter(configuration_id=configuration_id)
    
    def get_non_compliant(self) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité non conformes.
        
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité non conformes.
        """
        return self.model_class.objects.filter(is_compliant=False)
    
    def get_compliant(self) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité conformes.
        
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité conformes.
        """
        return self.model_class.objects.filter(is_compliant=True)
    
    def get_by_checked_by(self, checked_by: str) -> QuerySet[ComplianceCheck]:
        """
        Récupère les vérifications de conformité par vérificateur.
        
        Args:
            checked_by (str): Le vérificateur des vérifications de conformité.
            
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité vérifiées par le vérificateur spécifié.
        """
        return self.model_class.objects.filter(checked_by=checked_by)
    
    def get_with_related(self) -> QuerySet[ComplianceCheck]:
        """
        Récupère toutes les vérifications de conformité avec leurs relations préchargées.
        
        Returns:
            QuerySet[ComplianceCheck]: Un QuerySet contenant les vérifications de conformité avec leurs relations.
        """
        return self.model_class.objects.select_related('device', 'policy', 'configuration')


# Alias pour la compatibilité avec le reste du code
ComplianceRepository = CompliancePolicyRepository 