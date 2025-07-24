"""
Implémentation concrète du repository pour les vérifications de service.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

from django.db.models import Q, Count, Max, F
from django.db import transaction

from ...domain.interfaces.repositories import (
    ServiceCheckRepository as IServiceCheckRepository,
    DeviceServiceCheckRepository as IDeviceServiceCheckRepository,
    CheckResultRepository as ICheckResultRepository
)
from ...models import ServiceCheck, DeviceServiceCheck, CheckResult
from .base_repository import BaseRepository

# Configuration du logger
logger = logging.getLogger(__name__)


class ServiceCheckRepository(BaseRepository[ServiceCheck], IServiceCheckRepository):
    """
    Repository pour les vérifications de service.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle ServiceCheck.
        """
        super().__init__(ServiceCheck)
    
    def create_service_check(self, name: str, description: str, 
                            check_type: str, check_config: Dict[str, Any] = None,
                            category: str = None, 
                            compatible_device_types: List[str] = None,
                            enabled: bool = True) -> ServiceCheck:
        """
        Crée une nouvelle vérification de service.
        
        Args:
            name: Nom de la vérification
            description: Description de la vérification
            check_type: Type de vérification ('ping', 'http', 'snmp', etc.)
            check_config: Configuration spécifique pour la vérification (optionnel)
            category: Catégorie de la vérification (optionnel)
            compatible_device_types: Types d'équipements compatibles (optionnel)
            enabled: Si la vérification est activée globalement
            
        Returns:
            La vérification de service créée
        """
        try:
            service_check = ServiceCheck(
                name=name,
                description=description,
                check_type=check_type,
                check_config=check_config or {},
                category=category,
                compatible_device_types=compatible_device_types,
                enabled=enabled
            )
            
            service_check.save()
            logger.info(f"Vérification de service créée: {service_check.id} - {name}")
            return service_check
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une vérification de service: {e}")
            raise
    
    def get_by_check_type(self, check_type: str, enabled_only: bool = True) -> List[ServiceCheck]:
        """
        Récupère les vérifications de service par type.
        
        Args:
            check_type: Type de vérification à filtrer
            enabled_only: Si on ne récupère que les vérifications activées
            
        Returns:
            Liste des vérifications de service
        """
        query = Q(check_type=check_type)
        
        if enabled_only:
            query &= Q(enabled=True)
            
        return list(ServiceCheck.objects.filter(query))
    
    def get_by_category(self, category: str, enabled_only: bool = True) -> List[ServiceCheck]:
        """
        Récupère les vérifications de service par catégorie.
        
        Args:
            category: Catégorie à filtrer
            enabled_only: Si on ne récupère que les vérifications activées
            
        Returns:
            Liste des vérifications de service
        """
        query = Q(category=category)
        
        if enabled_only:
            query &= Q(enabled=True)
            
        return list(ServiceCheck.objects.filter(query))
    
    def get_compatible_with_device_type(self, device_type: str, 
                                       enabled_only: bool = True) -> List[ServiceCheck]:
        """
        Récupère les vérifications de service compatibles avec un type d'équipement.
        
        Args:
            device_type: Type d'équipement
            enabled_only: Si on ne récupère que les vérifications activées
            
        Returns:
            Liste des vérifications de service compatibles
        """
        # Vérifications compatibles avec tous les types ou avec ce type spécifique
        query = Q(compatible_device_types__isnull=True) | Q(compatible_device_types__contains=[device_type])
        
        if enabled_only:
            query &= Q(enabled=True)
            
        return list(ServiceCheck.objects.filter(query))
    
    def update_check_config(self, service_check_id: int, 
                           check_config: Dict[str, Any]) -> Optional[ServiceCheck]:
        """
        Met à jour la configuration d'une vérification de service.
        
        Args:
            service_check_id: ID de la vérification de service
            check_config: Nouvelle configuration de vérification
            
        Returns:
            La vérification de service mise à jour ou None si elle n'existe pas
        """
        service_check = self.get_by_id(service_check_id)
        if not service_check:
            return None
        
        try:
            # Fusionner avec la configuration existante
            if service_check.check_config:
                service_check.check_config.update(check_config)
            else:
                service_check.check_config = check_config
                
            service_check.save()
            logger.info(f"Configuration mise à jour pour la vérification de service {service_check_id}")
            return service_check
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration pour la vérification de service {service_check_id}: {e}")
            raise

    def list_all(self) -> List[Dict[str, Any]]:
        """Liste toutes les vérifications de service."""
        service_checks = ServiceCheck.objects.all()
        return [
            {
                'id': check.id,
                'name': check.name,
                'description': check.description,
                'check_type': check.check_type,
                'check_command': check.check_command,
                'check_parameters': check.check_parameters,
                'warning_threshold': check.warning_threshold,
                'critical_threshold': check.critical_threshold,
                'is_active': check.is_active,
                'template_id': check.template.id if check.template else None,
                'created_at': check.created_at.isoformat() if check.created_at else None,
                'updated_at': check.updated_at.isoformat() if check.updated_at else None,
            }
            for check in service_checks
        ]

    def list_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """Liste les vérifications de service pour un équipement spécifique."""
        # Pour les service checks, cette méthode retourne les checks actifs
        service_checks = ServiceCheck.objects.filter(is_active=True)
        return [
            {
                'id': check.id,
                'name': check.name,
                'description': check.description,
                'check_type': check.check_type,
                'check_command': check.check_command,
                'check_parameters': check.check_parameters,
                'warning_threshold': check.warning_threshold,
                'critical_threshold': check.critical_threshold,
                'is_active': check.is_active,
                'template_id': check.template.id if check.template else None,
                'created_at': check.created_at.isoformat() if check.created_at else None,
                'updated_at': check.updated_at.isoformat() if check.updated_at else None,
            }
            for check in service_checks
        ]


class DeviceServiceCheckRepository(BaseRepository[DeviceServiceCheck], IDeviceServiceCheckRepository):
    """
    Repository pour les vérifications de service d'équipement.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle DeviceServiceCheck.
        """
        super().__init__(DeviceServiceCheck)
    
    def create_device_service_check(self, device_id: int, service_check_id: int, 
                                   name: Optional[str] = None,
                                   specific_config: Dict[str, Any] = None,
                                   check_interval: int = 300,
                                   is_active: bool = True) -> DeviceServiceCheck:
        """
        Crée une nouvelle vérification de service d'équipement.
        
        Args:
            device_id: ID de l'équipement
            service_check_id: ID de la vérification de service
            name: Nom personnalisé pour cette instance (optionnel)
            specific_config: Configuration spécifique pour cette instance (optionnel)
            check_interval: Intervalle de vérification en secondes
            is_active: Si la vérification est active
            
        Returns:
            La vérification de service d'équipement créée
        """
        try:
            # Si aucun nom n'est fourni, utiliser le nom de la vérification de service
            if not name:
                service_check = ServiceCheck.objects.get(id=service_check_id)
                name = service_check.name
                
            device_check = DeviceServiceCheck(
                device_id=device_id,
                service_check_id=service_check_id,
                name=name,
                specific_config=specific_config or {},
                check_interval=check_interval,
                is_active=is_active
            )
            
            device_check.save()
            logger.info(f"Vérification de service d'équipement créée: {device_check.id} - {name} pour l'équipement {device_id}")
            return device_check
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une vérification de service d'équipement: {e}")
            raise
    
    def get_by_device(self, device_id: int, active_only: bool = True) -> List[DeviceServiceCheck]:
        """
        Récupère les vérifications pour un équipement donné.
        
        Args:
            device_id: ID de l'équipement
            active_only: Si on ne récupère que les vérifications actives
            
        Returns:
            Liste des vérifications de service d'équipement
        """
        query = Q(device_id=device_id)
        
        if active_only:
            query &= Q(is_active=True)
            
        return list(DeviceServiceCheck.objects.filter(query))
    
    def get_by_check_type(self, check_type: str, active_only: bool = True) -> List[DeviceServiceCheck]:
        """
        Récupère les vérifications d'équipement par type de vérification.
        
        Args:
            check_type: Type de vérification à filtrer
            active_only: Si on ne récupère que les vérifications actives
            
        Returns:
            Liste des vérifications de service d'équipement
        """
        query = Q(service_check__check_type=check_type)
        
        if active_only:
            query &= Q(is_active=True)
            
        return list(DeviceServiceCheck.objects.filter(query))
    
    def update_check_status(self, device_check_id: int, 
                           last_status: str, 
                           message: Optional[str] = None) -> Optional[DeviceServiceCheck]:
        """
        Met à jour le statut de vérification d'une vérification de service d'équipement.
        
        Args:
            device_check_id: ID de la vérification de service d'équipement
            last_status: Dernier statut ('ok', 'warning', 'critical', 'unknown')
            message: Message associé à la vérification (optionnel)
            
        Returns:
            La vérification de service d'équipement mise à jour ou None si elle n'existe pas
        """
        device_check = self.get_by_id(device_check_id)
        if not device_check:
            return None
        
        try:
            device_check.last_check = datetime.now(timezone.utc)
            device_check.last_status = last_status
            
            if message:
                device_check.last_message = message
                
            device_check.save()
            logger.info(f"Statut de vérification mis à jour pour la vérification de service d'équipement {device_check_id}")
            return device_check
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut de vérification pour la vérification de service d'équipement {device_check_id}: {e}")
            raise
    
    def get_checks_to_execute(self, limit: int = 100) -> List[DeviceServiceCheck]:
        """
        Récupère les vérifications de service d'équipement à exécuter.
        
        Args:
            limit: Nombre maximum de vérifications à récupérer
            
        Returns:
            Liste des vérifications de service d'équipement à exécuter
        """
        # Récupérer les vérifications actives qui n'ont jamais été exécutées
        # ou dont l'intervalle de vérification est dépassé
        now = datetime.now(timezone.utc)
        
        never_checked = Q(last_check__isnull=True)
        
        # Vérifications dont l'intervalle est dépassé
        interval_due = Q(last_check__lt=now - F('check_interval') * timedelta(seconds=1))
        
        query = Q(is_active=True) & Q(service_check__enabled=True) & (never_checked | interval_due)
        
        return list(DeviceServiceCheck.objects.filter(query).order_by('last_check')[:limit])

    def list_all(self) -> List[Dict[str, Any]]:
        """Liste toutes les vérifications de service d'équipement."""
        device_checks = DeviceServiceCheck.objects.all()
        return [
            {
                'id': check.id,
                'device_id': check.device_id,
                'service_check_id': check.service_check_id,
                'name': check.name,
                'specific_config': check.specific_config,
                'check_interval': check.check_interval,
                'is_active': check.is_active,
                'last_check': check.last_check.isoformat() if check.last_check else None,
                'last_status': check.last_status,
                'last_message': check.last_message,
                'created_at': check.created_at.isoformat() if check.created_at else None,
                'updated_at': check.updated_at.isoformat() if check.updated_at else None,
            }
            for check in device_checks
        ]


class CheckResultRepository(BaseRepository[CheckResult], ICheckResultRepository):
    """
    Repository pour les résultats de vérification.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle CheckResult.
        """
        super().__init__(CheckResult)
    
    def create_check_result(self, device_service_check_id: int, status: str, 
                           execution_time: float = 0.0,
                           message: Optional[str] = None,
                           details: Dict[str, Any] = None,
                           timestamp: Optional[datetime] = None) -> CheckResult:
        """
        Crée un nouveau résultat de vérification.
        
        Args:
            device_service_check_id: ID de la vérification de service d'équipement
            status: Statut du résultat ('ok', 'warning', 'critical', 'unknown')
            execution_time: Temps d'exécution en secondes
            message: Message du résultat (optionnel)
            details: Détails supplémentaires du résultat (optionnel)
            timestamp: Horodatage du résultat (optionnel, utilise l'heure actuelle par défaut)
            
        Returns:
            Le résultat de vérification créé
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
                
            check_result = CheckResult(
                device_service_check_id=device_service_check_id,
                status=status,
                execution_time=execution_time,
                message=message,
                details=details or {},
                timestamp=timestamp
            )
            
            check_result.save()
            
            # Mettre à jour le statut de la vérification de service d'équipement
            device_check = DeviceServiceCheck.objects.get(id=device_service_check_id)
            device_check.last_check = timestamp
            device_check.last_status = status
            device_check.last_message = message
            device_check.save()
            
            return check_result
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un résultat de vérification: {e}")
            raise
    
    def get_results_for_device_check(self, device_service_check_id: int, 
                                    start_time: Optional[datetime] = None,
                                    end_time: Optional[datetime] = None,
                                    limit: int = 100) -> List[CheckResult]:
        """
        Récupère les résultats pour une vérification de service d'équipement.
        
        Args:
            device_service_check_id: ID de la vérification de service d'équipement
            start_time: Heure de début (optionnel)
            end_time: Heure de fin (optionnel)
            limit: Nombre maximum de résultats à récupérer
            
        Returns:
            Liste des résultats de vérification
        """
        query = Q(device_service_check_id=device_service_check_id)
        
        if start_time:
            query &= Q(timestamp__gte=start_time)
            
        if end_time:
            query &= Q(timestamp__lte=end_time)
            
        return list(CheckResult.objects.filter(query).order_by('-timestamp')[:limit])
    
    def get_latest_result(self, device_service_check_id: int) -> Optional[CheckResult]:
        """
        Récupère le dernier résultat pour une vérification de service d'équipement.
        
        Args:
            device_service_check_id: ID de la vérification de service d'équipement
            
        Returns:
            Le dernier résultat ou None si aucun résultat n'existe
        """
        try:
            return CheckResult.objects.filter(device_service_check_id=device_service_check_id).latest('timestamp')
        except CheckResult.DoesNotExist:
            return None
    
    def get_results_by_status(self, status: str, 
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             limit: int = 100) -> List[CheckResult]:
        """
        Récupère les résultats par statut.
        
        Args:
            status: Statut à filtrer
            start_time: Heure de début (optionnel)
            end_time: Heure de fin (optionnel)
            limit: Nombre maximum de résultats à récupérer
            
        Returns:
            Liste des résultats de vérification
        """
        query = Q(status=status)
        
        if start_time:
            query &= Q(timestamp__gte=start_time)
            
        if end_time:
            query &= Q(timestamp__lte=end_time)
            
        return list(CheckResult.objects.filter(query).order_by('-timestamp')[:limit])
    
    def get_results_for_device(self, device_id: int, 
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              limit: int = 100) -> List[CheckResult]:
        """
        Récupère les résultats pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            start_time: Heure de début (optionnel)
            end_time: Heure de fin (optionnel)
            limit: Nombre maximum de résultats à récupérer
            
        Returns:
            Liste des résultats de vérification
        """
        query = Q(device_service_check__device_id=device_id)
        
        if start_time:
            query &= Q(timestamp__gte=start_time)
            
        if end_time:
            query &= Q(timestamp__lte=end_time)
            
        return list(CheckResult.objects.filter(query).order_by('-timestamp')[:limit])
    
    def clean_old_results(self, device_service_check_id: int, 
                         retention_days: int = 30) -> int:
        """
        Supprime les anciens résultats pour une vérification de service d'équipement.
        
        Args:
            device_service_check_id: ID de la vérification de service d'équipement
            retention_days: Nombre de jours de rétention
            
        Returns:
            Nombre de résultats supprimés
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            # Compter les résultats à supprimer
            count = CheckResult.objects.filter(
                device_service_check_id=device_service_check_id,
                timestamp__lt=cutoff_date
            ).count()
            
            # Supprimer les résultats
            CheckResult.objects.filter(
                device_service_check_id=device_service_check_id,
                timestamp__lt=cutoff_date
            ).delete()
            
            logger.info(f"Suppression de {count} anciens résultats pour la vérification de service d'équipement {device_service_check_id}")
            return count
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des anciens résultats pour la vérification de service d'équipement {device_service_check_id}: {e}")
            raise 