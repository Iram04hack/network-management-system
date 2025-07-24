"""
Adaptateur pour le service legacy de reporting.

Ce module fournit un adaptateur pour intégrer le service legacy de reporting
avec le nouveau module reporting basé sur l'architecture hexagonale.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import logging

from django.utils import timezone

from reporting.domain.entities import (
    Report, ReportTemplate, ScheduledReport,
    ReportFormat, ReportType, ReportStatus, Frequency
)
from reporting.domain.exceptions import (
    ReportNotFoundError, ReportGenerationError, 
    ReportValidationError
)

# Configuration du logger
logger = logging.getLogger(__name__)

# Import du service legacy - utilisation d'un mock pour les tests
logger.info("Utilisation d'un service mock pour les tests dans l'adaptateur.")

# Utiliser le même mock que dans services.py
from reporting.infrastructure.services import LegacyReportService

class LegacyReportServiceAdapter:
    """
    Adaptateur pour le service legacy de reporting.
    
    Cette classe adapte l'interface du service legacy pour qu'elle soit
    compatible avec le nouveau module reporting.
    """
    
    @classmethod
    def generate_report(cls, template_id: int, parameters: Dict[str, Any], user_id: int) -> Report:
        """
        Génère un rapport en utilisant le service legacy.
        
        Args:
            template_id: ID du template à utiliser
            parameters: Paramètres pour la génération
            user_id: ID de l'utilisateur qui génère le rapport
            
        Returns:
            Report: Le rapport généré
            
        Raises:
            ReportNotFoundError: Si le template n'existe pas
            ReportValidationError: Si les paramètres sont invalides
            ReportGenerationError: Si la génération échoue
        """
        try:
            # Utiliser le service legacy pour générer le rapport
            legacy_report = LegacyReportService.generate_report(
                template_id=template_id,
                parameters=parameters,
                title=parameters.get('title')
            )
            
            # Récupérer les données JSON du rapport
            data_json = {}
            if legacy_report.data_json:
                try:
                    data_json = json.loads(legacy_report.data_json.read().decode('utf-8'))
                except Exception as e:
                    logger.warning(f"Erreur lors de la lecture des données JSON du rapport: {str(e)}")
            
            # Déterminer le type de rapport
            report_type = ReportType.CUSTOM  # Utiliser CUSTOM comme valeur par défaut
            if hasattr(legacy_report, 'template') and legacy_report.template:
                if legacy_report.template.report_type == 'network_inventory':
                    report_type = ReportType.NETWORK
                elif legacy_report.template.report_type == 'security_alerts':
                    report_type = ReportType.SECURITY
                elif legacy_report.template.report_type == 'performance_metrics':
                    report_type = ReportType.PERFORMANCE
            
            # Convertir en entité du domaine
            report = Report(
                id=legacy_report.id,
                title=legacy_report.title,
                description="",  # À remplir si nécessaire
                report_type=report_type,
                content=data_json,
                status=ReportStatus.COMPLETED,
                created_by=user_id,
                created_at=legacy_report.generated_at
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}", exc_info=True)
            raise ReportGenerationError(f"Erreur lors de la génération du rapport: {str(e)}")
    
    @classmethod
    def schedule_report(cls, template_id: int, schedule_type: str, 
                      parameters: Dict[str, Any], recipients: List[str]) -> ScheduledReport:
        """
        Planifie un rapport en utilisant le service legacy.
        
        Args:
            template_id: ID du template à utiliser
            schedule_type: Type de planification (daily, weekly, monthly)
            parameters: Paramètres pour la génération
            recipients: Liste des destinataires
            
        Returns:
            ScheduledReport: Le rapport planifié
            
        Raises:
            ReportNotFoundError: Si le template n'existe pas
            ReportValidationError: Si les paramètres sont invalides
        """
        try:
            # Convertir le type de planification
            frequency_map = {
                'daily': Frequency.DAILY,
                'weekly': Frequency.WEEKLY,
                'monthly': Frequency.MONTHLY
            }
            frequency = frequency_map.get(schedule_type, Frequency.DAILY)
            
            # Utiliser le service legacy pour planifier le rapport
            legacy_scheduled = LegacyReportService.schedule_report(
                template_id=template_id,
                schedule_type=schedule_type,
                parameters=parameters,
                title=parameters.get('title'),
                recipients=recipients
            )
            
            # Convertir en entité du domaine
            scheduled_report = ScheduledReport(
                id=legacy_scheduled.id,
                frequency=frequency,
                is_active=legacy_scheduled.is_active,
                template_id=template_id,
                report_id=None,  # Sera rempli lors de la génération
                last_run=legacy_scheduled.last_run,
                next_run=legacy_scheduled.next_run,
                recipients=[int(r) for r in legacy_scheduled.recipients if r.isdigit()]
            )
            
            return scheduled_report
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification du rapport: {str(e)}", exc_info=True)
            raise ReportValidationError(f"Erreur lors de la planification du rapport: {str(e)}")
    
    @classmethod
    def deliver_report(cls, report_id: int, recipients: List[str], format_type: str = 'pdf') -> bool:
        """
        Distribue un rapport en utilisant le service legacy.
        
        Args:
            report_id: ID du rapport à distribuer
            recipients: Liste des destinataires
            format_type: Format du rapport (pdf, xlsx, etc.)
            
        Returns:
            bool: True si la distribution a réussi
        """
        try:
            # Utiliser le service legacy pour distribuer le rapport
            result = LegacyReportService.deliver_report(
                report_id=report_id,
                recipients=recipients,
                format_type=format_type
            )
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Erreur lors de la distribution du rapport: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def execute_scheduled_reports(cls) -> Dict[str, Any]:
        """
        Exécute les rapports planifiés en utilisant le service legacy.
        
        Returns:
            Dict[str, Any]: Résultat de l'exécution
        """
        try:
            # Utiliser le service legacy pour exécuter les rapports planifiés
            result = LegacyReportService.execute_scheduled_reports()
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution des rapports planifiés: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)} 