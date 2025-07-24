"""
Cas d'utilisation pour le module de reporting.

Ce module contient les cas d'utilisation qui implémentent la logique métier
du domaine de reporting indépendamment de l'infrastructure technique.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..domain.interfaces import ReportRepository, ReportGenerationService, ReportStorageService

class GenerateReportUseCase:
    """Cas d'utilisation pour générer un rapport."""
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 report_generator: ReportGenerationService,
                 report_storage: ReportStorageService):
        self.report_repository = report_repository
        self.report_generator = report_generator
        self.report_storage = report_storage
    
    def execute(self, report_type: str, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Génère un rapport selon les paramètres fournis.
        
        Args:
            report_type: Type de rapport à générer
            parameters: Paramètres du rapport
            user_id: ID de l'utilisateur qui demande le rapport
            
        Returns:
            Informations sur le rapport généré, y compris son URL
            
        Raises:
            ValueError: Si le type de rapport est invalide ou les paramètres incomplets
        """
        # Vérification des paramètres
        if not report_type:
            raise ValueError("Le type de rapport est requis")
        
        # Génération du rapport
        report_data = self.report_generator.generate_report(report_type, parameters)
        
        # Stockage du rapport
        file_path = self.report_storage.store(
            report_data,
            report_type=report_type,
            file_format=parameters.get('format', 'pdf')
        )
        
        # Création de l'entrée dans la base de données
        report_info = {
            'title': parameters.get('title', f'Rapport {report_type}'),
            'description': parameters.get('description', ''),
            'report_type': report_type,
            'parameters': parameters,
            'file_path': file_path,
            'created_by': user_id
        }
        
        report = self.report_repository.create(report_info)
        return report

class GetReportUseCase:
    """Cas d'utilisation pour récupérer un rapport existant."""
    
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository
    
    def execute(self, report_id: int) -> Dict[str, Any]:
        """
        Récupère les informations d'un rapport par son ID.
        
        Args:
            report_id: ID du rapport
            
        Returns:
            Informations sur le rapport
            
        Raises:
            ValueError: Si le rapport n'existe pas
        """
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapport avec ID {report_id} introuvable")
        return report

class ListReportsUseCase:
    """Cas d'utilisation pour lister les rapports."""
    
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository
    
    def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les rapports selon les filtres fournis.
        
        Args:
            filters: Filtres à appliquer (type, utilisateur, période...)
            
        Returns:
            Liste des rapports
        """
        return self.report_repository.list(filters)

class ScheduleReportUseCase:
    """Cas d'utilisation pour planifier un rapport périodique."""
    
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository
    
    def execute(self, schedule_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Planifie un rapport périodique.
        
        Args:
            schedule_data: Données de planification
            user_id: ID de l'utilisateur
            
        Returns:
            Informations sur le rapport planifié
            
        Raises:
            ValueError: Si les données sont invalides
        """
        # Vérification des données
        if not schedule_data.get('report_type'):
            raise ValueError("Le type de rapport est requis")
        
        if not schedule_data.get('schedule'):
            raise ValueError("La fréquence de planification est requise")
        
        # Création de la planification
        scheduled_report = self.report_repository.schedule_report(
            report_type=schedule_data.get('report_type'),
            parameters=schedule_data.get('parameters', {}),
            schedule=schedule_data.get('schedule'),
            user_id=user_id,
            recipients=schedule_data.get('recipients', []),
            title=schedule_data.get('title', f'Rapport périodique {schedule_data.get("report_type")}'),
            description=schedule_data.get('description', '')
        )
        
        return scheduled_report

class DeleteReportUseCase:
    """Cas d'utilisation pour supprimer un rapport."""
    
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository
    
    def execute(self, report_id: int) -> bool:
        """
        Supprime un rapport.
        
        Args:
            report_id: ID du rapport à supprimer
            
        Returns:
            True si la suppression a réussi
            
        Raises:
            ValueError: Si le rapport n'existe pas
        """
        # Vérifier si le rapport existe
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapport avec ID {report_id} introuvable")
        
        # Supprimer le rapport
        return self.report_repository.delete(report_id) 