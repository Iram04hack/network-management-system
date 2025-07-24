"""
Cas d'utilisation pour la gestion des vérifications de service.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class ServiceCheckUseCase:
    """Cas d'utilisation pour la gestion des vérifications de service."""
    
    def __init__(self, service_check_repository):
        self.service_check_repository = service_check_repository
    
    def list_service_checks(self, filters=None):
        """Liste toutes les vérifications de service avec filtres optionnels."""
        if filters is None:
            filters = {}
            
        if 'category' in filters:
            return self.service_check_repository().get_by_category(filters['category'])
        elif 'check_type' in filters:
            return self.service_check_repository().get_by_check_type(filters['check_type'])
        else:
            return self.service_check_repository().list_all()
    
    def get_service_check(self, service_check_id):
        """Récupère une vérification de service par son ID."""
        service_check = self.service_check_repository.get_by_id(service_check_id)
        if service_check is None:
            raise ValueError(f"ServiceCheck with ID {service_check_id} not found")
        return service_check
    
    def create_service_check(self, name, check_type, check_config, description=None, 
                            category=None, compatible_device_types=None, enabled=True):
        """Crée une nouvelle vérification de service."""
        return self.service_check_repository.create_service_check(
            name=name,
            description=description,
            check_type=check_type,
            check_config=check_config,
            category=category,
            compatible_device_types=compatible_device_types,
            enabled=enabled
        )
    
    def update_check_config(self, service_check_id, new_config):
        """Met à jour la configuration d'une vérification de service."""
        service_check = self.get_service_check(service_check_id)
        return self.service_check_repository.update_check_config(service_check_id, new_config)


class DeviceServiceCheckUseCase:
    """Cas d'utilisation pour la gestion des vérifications de service d'équipement."""
    
    def __init__(self, device_service_check_repository, service_check_repository):
        self.device_service_check_repository = device_service_check_repository
        self.service_check_repository = service_check_repository
    
    def list_device_checks(self, device_id=None):
        """Liste les vérifications de service d'un équipement ou toutes les vérifications."""
        if device_id is not None:
            return self.device_service_check_repository().get_by_device(device_id)
        else:
            return self.device_service_check_repository().list_all()
    
    def get_device_check(self, device_check_id):
        """Récupère une vérification de service d'équipement par son ID."""
        device_check = self.device_service_check_repository.get_by_id(device_check_id)
        if device_check is None:
            raise ValueError(f"DeviceServiceCheck with ID {device_check_id} not found")
        return device_check
    
    def create_device_check(self, device_id, service_check_id, name=None, 
                           specific_config=None, check_interval=300, is_active=True):
        """Crée une nouvelle vérification de service d'équipement."""
        # Vérifier que la vérification de service existe
        service_check = self.service_check_repository.get_by_id(service_check_id)
        if service_check is None:
            raise ValueError(f"ServiceCheck with ID {service_check_id} not found")
        
        # Utiliser le nom de la vérification de service si aucun nom n'est fourni
        if name is None:
            name = service_check.name
        
        return self.device_service_check_repository.create_device_service_check(
            device_id=device_id,
            service_check_id=service_check_id,
            name=name,
            specific_config=specific_config,
            check_interval=check_interval,
            is_active=is_active
        )
    
    def update_check_status(self, device_check_id, last_status, message=None):
        """Met à jour le statut d'une vérification de service d'équipement."""
        device_check = self.get_device_check(device_check_id)
        return self.device_service_check_repository.update_check_status(
            device_check_id,
            last_status=last_status,
            message=message
        )


class CheckResultUseCase:
    """Cas d'utilisation pour la gestion des résultats de vérification."""
    
    def __init__(self, check_result_repository, device_service_check_repository, alert_service):
        self.check_result_repository = check_result_repository
        self.device_service_check_repository = device_service_check_repository
        self.alert_service = alert_service
    
    def get_check_results(self, device_check_id, start_time=None, end_time=None, limit=None):
        """Récupère les résultats d'une vérification de service d'équipement."""
        # Vérifier que la vérification de service d'équipement existe
        device_check = self.device_service_check_repository.get_by_id(device_check_id)
        if device_check is None:
            raise ValueError(f"DeviceServiceCheck with ID {device_check_id} not found")
        
        # Si aucune date de début n'est fournie, utiliser une date par défaut (24 heures)
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        
        return self.check_result_repository.get_results_for_device_check(
            device_check_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    
    def get_latest_result(self, device_check_id):
        """Récupère le dernier résultat d'une vérification de service d'équipement."""
        # Vérifier que la vérification de service d'équipement existe
        device_check = self.device_service_check_repository.get_by_id(device_check_id)
        if device_check is None:
            raise ValueError(f"DeviceServiceCheck with ID {device_check_id} not found")
        
        return self.check_result_repository.get_latest_result(device_check_id)
    
    def create_check_result(self, device_check_id, status, execution_time, 
                           message=None, details=None):
        """Crée un nouveau résultat de vérification."""
        # Vérifier que la vérification de service d'équipement existe
        device_check = self.device_service_check_repository.get_by_id(device_check_id)
        if device_check is None:
            raise ValueError(f"DeviceServiceCheck with ID {device_check_id} not found")
        
        # Créer le résultat de vérification
        check_result = self.check_result_repository.create_check_result(
            device_service_check_id=device_check_id,
            status=status,
            execution_time=execution_time,
            message=message,
            details=details
        )
        
        # Mettre à jour le statut de la vérification de service d'équipement
        self.device_service_check_repository.update_check_status(
            device_check_id,
            last_status=status,
            message=message
        )
        
        # Créer une alerte si le statut est warning ou critical
        if status in ["warning", "critical"]:
            self.alert_service.create_service_check_alert(
                device_check_id=device_check_id,
                status=status,
                message=message,
                details=details
            )
        
        return check_result 