"""
Adaptateurs API pour le module reporting.

Ce module contient les adaptateurs qui convertissent entre les entités du domaine
et les représentations API.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..domain.entities import (
    Report, ReportTemplate, ScheduledReport,
    ReportType, ReportStatus, Frequency, ReportFormat
)
from ..models import Report as ReportModel
from ..models import ReportTemplate as TemplateModel
from ..models import ScheduledReport as ScheduledModel


class ReportApiAdapter:
    """Adaptateur pour convertir entre les entités Report et les représentations API."""
    
    def to_domain_entity(self, model: ReportModel) -> Report:
        """
        Convertit un modèle Django en entité du domaine.
        
        Args:
            model: Le modèle Django
            
        Returns:
            L'entité du domaine correspondante
        """
        report_type = ReportType.NETWORK
        if model.report_type == 'security':
            report_type = ReportType.SECURITY
        elif model.report_type == 'performance':
            report_type = ReportType.PERFORMANCE
        elif model.report_type == 'audit':
            report_type = ReportType.AUDIT
        elif model.report_type == 'custom':
            report_type = ReportType.CUSTOM
        
        status = ReportStatus.DRAFT
        if model.status == 'processing':
            status = ReportStatus.PROCESSING
        elif model.status == 'completed':
            status = ReportStatus.COMPLETED
        elif model.status == 'failed':
            status = ReportStatus.FAILED
        
        return Report(
            id=model.id,
            title=model.title,
            description=model.description,
            report_type=report_type,
            created_by=model.created_by.id if model.created_by else None,
            created_at=model.created_at,
            status=status,
            content=model.content or {},
            parameters=model.parameters or {},
            file_path=model.file_path,
            template_id=model.template.id if model.template else None
        )
    
    def to_api_representation(self, entity: Report) -> Dict[str, Any]:
        """
        Convertit une entité du domaine en représentation API.
        
        Args:
            entity: L'entité du domaine
            
        Returns:
            La représentation API correspondante
        """
        report_type_str = 'network'
        if entity.report_type == ReportType.SECURITY:
            report_type_str = 'security'
        elif entity.report_type == ReportType.PERFORMANCE:
            report_type_str = 'performance'
        elif entity.report_type == ReportType.AUDIT:
            report_type_str = 'audit'
        elif entity.report_type == ReportType.CUSTOM:
            report_type_str = 'custom'
        
        status_str = 'draft'
        if entity.status == ReportStatus.PROCESSING:
            status_str = 'processing'
        elif entity.status == ReportStatus.COMPLETED:
            status_str = 'completed'
        elif entity.status == ReportStatus.FAILED:
            status_str = 'failed'
        
        return {
            'id': entity.id,
            'title': entity.title,
            'description': entity.description,
            'report_type': report_type_str,
            'created_by': entity.created_by,
            'created_at': entity.created_at.isoformat() if entity.created_at else None,
            'status': status_str,
            'content': entity.content,
            'parameters': entity.parameters,
            'file_path': entity.file_path,
            'template_id': entity.template_id
        }
    
    def from_api_representation(self, data: Dict[str, Any]) -> Report:
        """
        Convertit une représentation API en entité du domaine.
        
        Args:
            data: La représentation API
            
        Returns:
            L'entité du domaine correspondante
        """
        report_type = ReportType.NETWORK
        if data.get('report_type') == 'security':
            report_type = ReportType.SECURITY
        elif data.get('report_type') == 'performance':
            report_type = ReportType.PERFORMANCE
        elif data.get('report_type') == 'audit':
            report_type = ReportType.AUDIT
        elif data.get('report_type') == 'custom':
            report_type = ReportType.CUSTOM
        
        status = ReportStatus.DRAFT
        if data.get('status') == 'processing':
            status = ReportStatus.PROCESSING
        elif data.get('status') == 'completed':
            status = ReportStatus.COMPLETED
        elif data.get('status') == 'failed':
            status = ReportStatus.FAILED
        
        return Report(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            report_type=report_type,
            created_by=data.get('created_by'),
            created_at=None,  # Sera défini par le repository
            status=status,
            content=data.get('content', {}),
            parameters=data.get('parameters', {}),
            file_path=data.get('file_path'),
            template_id=data.get('template_id')
        )


class ReportTemplateApiAdapter:
    """Adaptateur pour convertir entre les entités ReportTemplate et les représentations API."""
    
    def to_domain_entity(self, model: TemplateModel) -> ReportTemplate:
        """
        Convertit un modèle Django en entité du domaine.
        
        Args:
            model: Le modèle Django
            
        Returns:
            L'entité du domaine correspondante
        """
        return ReportTemplate(
            id=model.id,
            name=model.name,
            description=model.description,
            template_type=model.template_type,
            created_by=model.created_by.id if model.created_by else None,
            created_at=model.created_at,
            content=model.content or {},
            is_active=model.is_active,
            metadata=model.metadata or {}
        )
    
    def to_api_representation(self, entity: ReportTemplate) -> Dict[str, Any]:
        """
        Convertit une entité du domaine en représentation API.
        
        Args:
            entity: L'entité du domaine
            
        Returns:
            La représentation API correspondante
        """
        return {
            'id': entity.id,
            'name': entity.name,
            'description': entity.description,
            'template_type': entity.template_type,
            'created_by': entity.created_by,
            'created_at': entity.created_at.isoformat() if entity.created_at else None,
            'content': entity.content,
            'is_active': entity.is_active,
            'metadata': entity.metadata
        }
    
    def from_api_representation(self, data: Dict[str, Any]) -> ReportTemplate:
        """
        Convertit une représentation API en entité du domaine.
        
        Args:
            data: La représentation API
            
        Returns:
            L'entité du domaine correspondante
        """
        return ReportTemplate(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            template_type=data.get('template_type', ''),
            created_by=data.get('created_by'),
            created_at=None,  # Sera défini par le repository
            content=data.get('content', {}),
            is_active=data.get('is_active', True),
            metadata=data.get('metadata', {})
        )


class ScheduledReportApiAdapter:
    """Adaptateur pour convertir entre les entités ScheduledReport et les représentations API."""
    
    def to_domain_entity(self, model: ScheduledModel) -> ScheduledReport:
        """
        Convertit un modèle Django en entité du domaine.
        
        Args:
            model: Le modèle Django
            
        Returns:
            L'entité du domaine correspondante
        """
        frequency = Frequency.DAILY
        if model.frequency == 'weekly':
            frequency = Frequency.WEEKLY
        elif model.frequency == 'monthly':
            frequency = Frequency.MONTHLY
        elif model.frequency == 'quarterly':
            frequency = Frequency.QUARTERLY
        
        format_type = ReportFormat.PDF
        if model.format == 'json':
            format_type = ReportFormat.JSON
        elif model.format == 'xlsx':
            format_type = ReportFormat.XLSX
        elif model.format == 'csv':
            format_type = ReportFormat.CSV
        elif model.format == 'html':
            format_type = ReportFormat.HTML
        
        return ScheduledReport(
            id=model.id,
            report_id=model.report.id if model.report else None,
            template_id=model.template.id if model.template else None,
            frequency=frequency,
            is_active=model.is_active,
            next_run=model.next_run,
            last_run=model.last_run,
            start_date=model.start_date,
            recipients=[recipient.id for recipient in model.recipients.all()],
            parameters=model.parameters or {}
        )
    
    def to_api_representation(self, entity: ScheduledReport) -> Dict[str, Any]:
        """
        Convertit une entité du domaine en représentation API.
        
        Args:
            entity: L'entité du domaine
            
        Returns:
            La représentation API correspondante
        """
        frequency_str = 'daily'
        if entity.frequency == Frequency.WEEKLY:
            frequency_str = 'weekly'
        elif entity.frequency == Frequency.MONTHLY:
            frequency_str = 'monthly'
        elif entity.frequency == Frequency.QUARTERLY:
            frequency_str = 'quarterly'
        
        return {
            'id': entity.id,
            'report_id': entity.report_id,
            'template_id': entity.template_id,
            'frequency': frequency_str,
            'is_active': entity.is_active,
            'next_run': entity.next_run.isoformat() if entity.next_run else None,
            'last_run': entity.last_run.isoformat() if entity.last_run else None,
            'start_date': entity.start_date.isoformat() if entity.start_date else None,
            'recipients': entity.recipients,
            'parameters': entity.parameters
        }
    
    def from_api_representation(self, data: Dict[str, Any]) -> ScheduledReport:
        """
        Convertit une représentation API en entité du domaine.
        
        Args:
            data: La représentation API
            
        Returns:
            L'entité du domaine correspondante
        """
        frequency = Frequency.DAILY
        if data.get('frequency') == 'weekly':
            frequency = Frequency.WEEKLY
        elif data.get('frequency') == 'monthly':
            frequency = Frequency.MONTHLY
        elif data.get('frequency') == 'quarterly':
            frequency = Frequency.QUARTERLY
        
        return ScheduledReport(
            id=data.get('id'),
            report_id=data.get('report_id'),
            template_id=data.get('template_id'),
            frequency=frequency,
            is_active=data.get('is_active', True),
            next_run=None,  # Sera calculé par le service
            last_run=None,  # Sera mis à jour par le service
            start_date=None,  # Sera défini par le repository
            recipients=data.get('recipients', []),
            parameters=data.get('parameters', {})
        ) 