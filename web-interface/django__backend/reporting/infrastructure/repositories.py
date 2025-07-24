"""
Implémentations des repositories pour le module de reporting.

Ce module fournit les implémentations concrètes des interfaces
de repository définies dans le domaine, en utilisant Django ORM.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.models import User

from ..domain.interfaces import ReportRepository, ReportTemplateRepository, ScheduledReportRepository
from ..domain.entities import Report as ReportEntity, ReportTemplate as TemplateEntity, ScheduledReport as ScheduledEntity
from ..domain.entities import ReportType, ReportStatus, Frequency
from reporting.models import Report, ReportTemplate, ScheduledReport
from .api_adapters import ReportApiAdapter, ReportTemplateApiAdapter, ScheduledReportApiAdapter

class DjangoReportRepository(ReportRepository):
    """
    Implémentation Django du repository des rapports.
    """
    
    def __init__(self):
        """Initialise le repository avec l'adaptateur API."""
        self.adapter = ReportApiAdapter()
    
    def get_by_id(self, report_id: int) -> Optional[ReportEntity]:
        """
        Récupère un rapport par son ID.
        
        Args:
            report_id: ID du rapport à récupérer
            
        Returns:
            Le rapport correspondant ou None s'il n'existe pas
        """
        try:
            report = Report.objects.get(pk=report_id)
            return self.adapter.to_domain_entity(report)
        except Report.DoesNotExist:
            return None
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[ReportEntity]:
        """
        Liste les rapports selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres (report_type, status, created_by...)
            
        Returns:
            Liste des rapports correspondants
        """
        queryset = Report.objects.all()
        
        if filters:
            if 'report_type' in filters:
                report_type = filters['report_type']
                if isinstance(report_type, ReportType):
                    report_type = report_type.value
                queryset = queryset.filter(report_type=report_type)
                
            if 'status' in filters:
                status = filters['status']
                if isinstance(status, ReportStatus):
                    status = status.value
                queryset = queryset.filter(status=status)
                
            if 'created_by' in filters:
                queryset = queryset.filter(created_by_id=filters['created_by'])
                
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) | 
                    Q(description__icontains=search_term)
                )
        
        return [self.adapter.to_domain_entity(report) for report in queryset]
    
    def create(self, report: ReportEntity) -> ReportEntity:
        """
        Crée un nouveau rapport.
        
        Args:
            report: Entité du rapport à créer
            
        Returns:
            Le rapport créé avec son ID généré
        """
        # Convertir le type de rapport et le statut en valeurs de chaîne
        report_type = report.report_type.value if isinstance(report.report_type, ReportType) else report.report_type
        status = report.status.value if isinstance(report.status, ReportStatus) else report.status
        
        # Récupérer le template si nécessaire
        template = None
        if report.template_id:
            try:
                template = ReportTemplate.objects.get(pk=report.template_id)
            except ReportTemplate.DoesNotExist:
                pass
                
        # Créer le rapport
        django_report = Report.objects.create(
            title=report.title,
            description=report.description,
            report_type=report_type,
            created_by_id=report.created_by,
            template=template,
            content=report.content,
            parameters=report.parameters,
            status=status,
            file_path=report.file_path
        )
        
        # Retourner l'entité du domaine
        return self.adapter.to_domain_entity(django_report)
    
    def update(self, report: ReportEntity) -> ReportEntity:
        """
        Met à jour un rapport existant.
        
        Args:
            report: Entité du rapport avec les modifications
            
        Returns:
            Le rapport mis à jour
        """
        try:
            django_report = Report.objects.get(pk=report.id)
            
            # Mettre à jour les champs
            django_report.title = report.title
            django_report.description = report.description
            
            # Convertir le type de rapport et le statut en valeurs de chaîne
            django_report.report_type = report.report_type.value if isinstance(report.report_type, ReportType) else report.report_type
            django_report.status = report.status.value if isinstance(report.status, ReportStatus) else report.status
            
            django_report.content = report.content
            django_report.parameters = report.parameters
            django_report.file_path = report.file_path
            
            # Mettre à jour le template si nécessaire
            if report.template_id:
                try:
                    template = ReportTemplate.objects.get(pk=report.template_id)
                    django_report.template = template
                except ReportTemplate.DoesNotExist:
                    pass
            
            django_report.save()
            return self.adapter.to_domain_entity(django_report)
        except Report.DoesNotExist:
            raise ValueError(f"Rapport avec ID {report.id} non trouvé")
    
    def update_status(self, report_id: int, status: ReportStatus) -> ReportEntity:
        """
        Met à jour le statut d'un rapport.
        
        Args:
            report_id: ID du rapport
            status: Nouveau statut
            
        Returns:
            Le rapport mis à jour
        """
        try:
            django_report = Report.objects.get(pk=report_id)
            django_report.status = status.value if isinstance(status, ReportStatus) else status
            django_report.save()
            return self.adapter.to_domain_entity(django_report)
        except Report.DoesNotExist:
            raise ValueError(f"Rapport avec ID {report_id} non trouvé")
    
    def update_content(self, report_id: int, content: Dict[str, Any]) -> ReportEntity:
        """
        Met à jour le contenu d'un rapport.
        
        Args:
            report_id: ID du rapport
            content: Nouveau contenu
            
        Returns:
            Le rapport mis à jour
        """
        try:
            django_report = Report.objects.get(pk=report_id)
            django_report.content = content
            django_report.save()
            return self.adapter.to_domain_entity(django_report)
        except Report.DoesNotExist:
            raise ValueError(f"Rapport avec ID {report_id} non trouvé")
    
    def delete(self, report_id: int) -> bool:
        """
        Supprime un rapport.
        
        Args:
            report_id: ID du rapport à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            django_report = Report.objects.get(pk=report_id)
            django_report.delete()
            return True
        except Report.DoesNotExist:
            return False
    

class DjangoReportTemplateRepository(ReportTemplateRepository):
    """
    Implémentation Django du repository des templates de rapport.
    """
    
    def __init__(self):
        """Initialise le repository avec l'adaptateur API."""
        self.adapter = ReportTemplateApiAdapter()
    
    def get_by_id(self, template_id: int) -> Optional[TemplateEntity]:
        """
        Récupère un template par son ID.
        
        Args:
            template_id: ID du template à récupérer
            
        Returns:
            Le template correspondant ou None s'il n'existe pas
        """
        try:
            template = ReportTemplate.objects.get(pk=template_id)
            return self.adapter.to_domain_entity(template)
        except ReportTemplate.DoesNotExist:
            return None
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[TemplateEntity]:
        """
        Liste les templates selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres (template_type, is_active, created_by...)
            
        Returns:
            Liste des templates correspondants
        """
        queryset = ReportTemplate.objects.all()
        
        if filters:
            if 'template_type' in filters:
                queryset = queryset.filter(template_type=filters['template_type'])
                
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
                
            if 'created_by' in filters:
                queryset = queryset.filter(created_by_id=filters['created_by'])
                
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) | 
                    Q(description__icontains=search_term)
                )
        
        return [self.adapter.to_domain_entity(template) for template in queryset]
    
    def create(self, template: TemplateEntity) -> TemplateEntity:
        """
        Crée un nouveau template.
        
        Args:
            template: Entité du template à créer
            
        Returns:
            Le template créé avec son ID généré
        """
        # Créer le template
        django_template = ReportTemplate.objects.create(
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            created_by_id=template.created_by,
            content=template.content,
            is_active=template.is_active,
            metadata=template.metadata
        )
        
        # Retourner l'entité du domaine
        return self.adapter.to_domain_entity(django_template)
    
    def update(self, template: TemplateEntity) -> TemplateEntity:
        """
        Met à jour un template existant.
        
        Args:
            template: Entité du template avec les modifications
            
        Returns:
            Le template mis à jour
        """
        try:
            django_template = ReportTemplate.objects.get(pk=template.id)
            
            # Mettre à jour les champs
            django_template.name = template.name
            django_template.description = template.description
            django_template.template_type = template.template_type
            django_template.content = template.content
            django_template.is_active = template.is_active
            django_template.metadata = template.metadata
            
            django_template.save()
            return self.adapter.to_domain_entity(django_template)
        except ReportTemplate.DoesNotExist:
            raise ValueError(f"Template avec ID {template.id} non trouvé")
    
    def delete(self, template_id: int) -> bool:
        """
        Supprime un template.
        
        Args:
            template_id: ID du template à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            django_template = ReportTemplate.objects.get(pk=template_id)
            django_template.delete()
            return True
        except ReportTemplate.DoesNotExist:
            return False


class DjangoScheduledReportRepository(ScheduledReportRepository):
    """
    Implémentation Django du repository des rapports planifiés.
    """
    
    def __init__(self):
        """Initialise le repository avec l'adaptateur API."""
        self.adapter = ScheduledReportApiAdapter()
    
    def get_by_id(self, scheduled_report_id: int) -> Optional[ScheduledEntity]:
        """
        Récupère un rapport planifié par son ID.
        
        Args:
            scheduled_report_id: ID du rapport planifié à récupérer
            
        Returns:
            Le rapport planifié correspondant ou None s'il n'existe pas
        """
        try:
            scheduled = ScheduledReport.objects.get(pk=scheduled_report_id)
            return self.adapter.to_domain_entity(scheduled)
        except ScheduledReport.DoesNotExist:
            return None
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[ScheduledEntity]:
        """
        Liste les rapports planifiés selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres (frequency, is_active, report_id...)
            
        Returns:
            Liste des rapports planifiés correspondants
        """
        queryset = ScheduledReport.objects.all()
        
        if filters:
            if 'frequency' in filters:
                frequency = filters['frequency']
                if isinstance(frequency, Frequency):
                    frequency = frequency.value
                queryset = queryset.filter(frequency=frequency)
                
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
                
            if 'report_id' in filters:
                queryset = queryset.filter(report_id=filters['report_id'])
                
            if 'template_id' in filters:
                queryset = queryset.filter(template_id=filters['template_id'])
                
            if 'recipient_id' in filters:
                queryset = queryset.filter(recipients__id=filters['recipient_id'])
        
        return [self.adapter.to_domain_entity(scheduled) for scheduled in queryset]
    
    def create(self, scheduled_report: ScheduledEntity) -> ScheduledEntity:
        """
        Crée un nouveau rapport planifié.
        
        Args:
            scheduled_report: Entité du rapport planifié à créer
            
        Returns:
            Le rapport planifié créé avec son ID généré
        """
        # Convertir la fréquence en valeur de chaîne
        frequency = scheduled_report.frequency.value if isinstance(scheduled_report.frequency, Frequency) else scheduled_report.frequency
        
        # Créer le rapport planifié
        django_scheduled = ScheduledReport.objects.create(
            report_id=scheduled_report.report_id,
            template_id=scheduled_report.template_id,
            frequency=frequency,
            is_active=scheduled_report.is_active,
            next_run=scheduled_report.next_run,
            last_run=scheduled_report.last_run,
            start_date=scheduled_report.start_date,
            parameters=scheduled_report.parameters
        )
        
        # Ajouter les destinataires
        if scheduled_report.recipients:
            users = User.objects.filter(id__in=scheduled_report.recipients)
            django_scheduled.recipients.add(*users)
        
        # Retourner l'entité du domaine
        return self.adapter.to_domain_entity(django_scheduled)
    
    def update(self, scheduled_report: ScheduledEntity) -> ScheduledEntity:
        """
        Met à jour un rapport planifié existant.
        
        Args:
            scheduled_report: Entité du rapport planifié avec les modifications
            
        Returns:
            Le rapport planifié mis à jour
        """
        try:
            django_scheduled = ScheduledReport.objects.get(pk=scheduled_report.id)
            
            # Mettre à jour les champs
            if scheduled_report.report_id:
                django_scheduled.report_id = scheduled_report.report_id
                
            if scheduled_report.template_id:
                django_scheduled.template_id = scheduled_report.template_id
            
            # Convertir la fréquence en valeur de chaîne
            django_scheduled.frequency = scheduled_report.frequency.value if isinstance(scheduled_report.frequency, Frequency) else scheduled_report.frequency
            
            django_scheduled.is_active = scheduled_report.is_active
            django_scheduled.next_run = scheduled_report.next_run
            django_scheduled.last_run = scheduled_report.last_run
            django_scheduled.start_date = scheduled_report.start_date
            django_scheduled.parameters = scheduled_report.parameters
            
            django_scheduled.save()
            
            # Mettre à jour les destinataires si nécessaire
            if scheduled_report.recipients is not None:
                django_scheduled.recipients.clear()
                users = User.objects.filter(id__in=scheduled_report.recipients)
                django_scheduled.recipients.add(*users)
            
            return self.adapter.to_domain_entity(django_scheduled)
        except ScheduledReport.DoesNotExist:
            raise ValueError(f"Rapport planifié avec ID {scheduled_report.id} non trouvé")
    
    def delete(self, scheduled_report_id: int) -> bool:
        """
        Supprime un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            django_scheduled = ScheduledReport.objects.get(pk=scheduled_report_id)
            django_scheduled.delete()
            return True
        except ScheduledReport.DoesNotExist:
            return False
    
    def add_recipient(self, scheduled_report_id: int, user_id: int) -> bool:
        """
        Ajoute un destinataire à un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            user_id: ID de l'utilisateur à ajouter
            
        Returns:
            True si l'ajout a réussi
        """
        try:
            scheduled = ScheduledReport.objects.get(pk=scheduled_report_id)
            user = User.objects.get(pk=user_id)
            
            if user not in scheduled.recipients.all():
                
                scheduled.recipients.add(user)
                return True
            return False
        except (ScheduledReport.DoesNotExist, User.DoesNotExist):
            return False
    
    def remove_recipient(self, scheduled_report_id: int, user_id: int) -> bool:
        """
        Supprime un destinataire d'un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            user_id: ID de l'utilisateur à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            scheduled = ScheduledReport.objects.get(pk=scheduled_report_id)
            user = User.objects.get(pk=user_id)
            
            if user in scheduled.recipients.all():
                scheduled.recipients.remove(user)
                return True
            return False
        except (ScheduledReport.DoesNotExist, User.DoesNotExist):
            return False