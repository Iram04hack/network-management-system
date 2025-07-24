"""
Entités du domaine pour le module de reporting.

Ce fichier définit les entités métier avec leur logique et validation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

class ReportType(Enum):
    """Types de rapports supportés."""
    NETWORK = "network"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    CUSTOM = "custom"

class ReportStatus(Enum):
    """Statuts des rapports."""
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportFormat(Enum):
    """Formats de rapports supportés."""
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"
    HTML = "html"

class Frequency(Enum):
    """Fréquences de planification."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

@dataclass
class Report:
    """
    Entité représentant un rapport.
    """
    title: str
    report_type: ReportType
    created_by: Optional[int] = None
    id: Optional[int] = None
    description: str = ""
    status: ReportStatus = ReportStatus.DRAFT
    content: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    template_id: Optional[int] = None
    
    def __post_init__(self):
        """Validation post-initialisation."""
        self.validate()
    
    def validate(self) -> None:
        """Valide les données de l'entité."""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Le titre du rapport est requis")
        
        if len(self.title) > 255:
            raise ValueError("Le titre ne peut pas dépasser 255 caractères")
        
        if not isinstance(self.report_type, ReportType):
            raise ValueError(f"Type de rapport invalide: {self.report_type}")
        
        if not isinstance(self.status, ReportStatus):
            raise ValueError(f"Statut de rapport invalide: {self.status}")
    
    def mark_as_processing(self) -> None:
        """Marque le rapport comme en cours de traitement."""
        self.status = ReportStatus.PROCESSING
    
    def mark_as_completed(self, file_path: str) -> None:
        """Marque le rapport comme terminé."""
        self.status = ReportStatus.COMPLETED
        self.file_path = file_path
    
    def mark_as_failed(self, error_message: str = "") -> None:
        """Marque le rapport comme échoué."""
        self.status = ReportStatus.FAILED
        if error_message:
            self.content["error_message"] = error_message
    
    def is_completed(self) -> bool:
        """Vérifie si le rapport est terminé."""
        return self.status == ReportStatus.COMPLETED
    
    def can_be_regenerated(self) -> bool:
        """Vérifie si le rapport peut être régénéré."""
        return self.status in [ReportStatus.COMPLETED, ReportStatus.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type.value if isinstance(self.report_type, ReportType) else self.report_type,
            'status': self.status.value if isinstance(self.status, ReportStatus) else self.status,
            'content': self.content,
            'parameters': self.parameters,
            'file_path': self.file_path,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'template_id': self.template_id
        }

@dataclass
class ReportTemplate:
    """
    Entité représentant un template de rapport.
    """
    name: str
    template_type: str
    content: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
    description: str = ""
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation post-initialisation."""
        self.validate()
    
    def validate(self) -> None:
        """Valide les données du template."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Le nom du template est requis")
        
        if len(self.name) > 255:
            raise ValueError("Le nom ne peut pas dépasser 255 caractères")
        
        if not self.template_type:
            raise ValueError("Le type de template est requis")
    
    def activate(self) -> None:
        """Active le template."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Désactive le template."""
        self.is_active = False
    
    def update_content(self, content: Dict[str, Any]) -> None:
        """Met à jour le contenu du template."""
        if not isinstance(content, dict):
            raise ValueError("Le contenu doit être un dictionnaire")
        self.content = content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'content': self.content,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'metadata': self.metadata
        }

@dataclass
class ScheduledReport:
    """
    Entité représentant un rapport planifié.
    """
    frequency: Frequency
    is_active: bool = True
    id: Optional[int] = None
    report_id: Optional[int] = None
    template_id: Optional[int] = None
    recipients: List[int] = field(default_factory=list)
    start_date: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation post-initialisation."""
        self.validate()
    
    def validate(self) -> None:
        """Valide les données du rapport planifié."""
        if not isinstance(self.frequency, Frequency):
            raise ValueError(f"Fréquence invalide: {self.frequency}")
        
        if not self.report_id and not self.template_id:
            raise ValueError("Un rapport ou un template doit être associé")
        
        if self.report_id and self.template_id:
            raise ValueError("Un seul rapport OU template peut être associé")
    
    def activate(self) -> None:
        """Active la planification."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Désactive la planification."""
        self.is_active = False
    
    def add_recipient(self, user_id: int) -> None:
        """Ajoute un destinataire."""
        if user_id not in self.recipients:
            self.recipients.append(user_id)
    
    def remove_recipient(self, user_id: int) -> None:
        """Supprime un destinataire."""
        if user_id in self.recipients:
            self.recipients.remove(user_id)
    
    def update_last_run(self, timestamp: datetime) -> None:
        """Met à jour la dernière exécution."""
        self.last_run = timestamp
    
    def should_run(self, reference_date: datetime) -> bool:
        """Vérifie si le rapport doit être exécuté."""
        if not self.is_active:
            return False
        
        if self.start_date and reference_date < self.start_date:
            return False
        
        if not self.next_run:
            return True
        
        return reference_date >= self.next_run
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            'id': self.id,
            'report_id': self.report_id,
            'template_id': self.template_id,
            'frequency': self.frequency.value if isinstance(self.frequency, Frequency) else self.frequency,
            'is_active': self.is_active,
            'recipients': self.recipients,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'parameters': self.parameters
        }

__all__ = [
    'Report',
    'ReportTemplate', 
    'ScheduledReport',
    'ReportType',
    'ReportStatus',
    'ReportFormat',
    'Frequency'
] 