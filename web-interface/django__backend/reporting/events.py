"""
Définition des événements spécifiques au module de reporting.
Ces événements permettent de découpler les différents composants du système.
"""

# Classes de base pour les événements (indépendantes de services.event_bus)
class BaseEvent:
    """Classe de base pour tous les événements."""
    def __init__(self, entity_type, entity_id):
        self.entity_type = entity_type
        self.entity_id = entity_id

class EntityEvent(BaseEvent):
    """Classe de base pour les événements liés aux entités."""
    pass

class EntityCreatedEvent(EntityEvent):
    """Événement émis lorsqu'une entité est créée."""
    pass

class EntityUpdatedEvent(EntityEvent):
    """Événement émis lorsqu'une entité est mise à jour."""
    def __init__(self, entity_type, entity_id, changes):
        super().__init__(entity_type, entity_id)
        self.changes = changes

class EntityDeletedEvent(EntityEvent):
    """Événement émis lorsqu'une entité est supprimée."""
    pass

# Événements pour les rapports

class ReportEvent(EntityEvent):
    """Classe de base pour les événements liés aux rapports."""
    def __init__(self, entity_id=None, title=None, report_type=None, details=None):
        super().__init__("report", entity_id)
        self.title = title
        self.report_type = report_type
        self.details = details or {}

class ReportGeneratedEvent(ReportEvent):
    """Événement émis lorsqu'un rapport est généré."""
    def __init__(self, entity_id, template_id=None, template_name=None, report_type=None, details=None):
        super().__init__(entity_id, template_name, report_type, details)
        self.template_id = template_id

class ReportDeliveredEvent(ReportEvent):
    """Événement émis lorsqu'un rapport est envoyé."""
    def __init__(self, entity_id, recipients=None, format_type=None, details=None):
        super().__init__(entity_id, details=details)
        self.recipients = recipients or []
        self.format_type = format_type

class ReportDownloadedEvent(ReportEvent):
    """Événement émis lorsqu'un rapport est téléchargé."""
    def __init__(self, entity_id, format_type=None, downloaded_by=None, details=None):
        super().__init__(entity_id, details=details)
        self.format_type = format_type
        self.downloaded_by = downloaded_by

# Événements pour les templates de rapports

class ReportTemplateEvent(EntityEvent):
    """Classe de base pour les événements liés aux templates de rapports."""
    def __init__(self, entity_id=None, name=None, report_type=None, details=None):
        super().__init__("report_template", entity_id)
        self.name = name
        self.report_type = report_type
        self.details = details or {}

class ReportTemplateCreatedEvent(ReportTemplateEvent, EntityCreatedEvent):
    """Événement émis lorsqu'un template de rapport est créé."""
    pass

class ReportTemplateUpdatedEvent(ReportTemplateEvent, EntityUpdatedEvent):
    """Événement émis lorsqu'un template de rapport est mis à jour."""
    def __init__(self, entity_id, changes, name=None, report_type=None, details=None):
        ReportTemplateEvent.__init__(self, entity_id, name, report_type, details)
        EntityUpdatedEvent.__init__(self, "report_template", entity_id, changes)

class ReportTemplateDeletedEvent(ReportTemplateEvent, EntityDeletedEvent):
    """Événement émis lorsqu'un template de rapport est supprimé."""
    pass

# Événements pour les planifications de rapports

class ReportScheduleEvent(EntityEvent):
    """Classe de base pour les événements liés aux planifications de rapports."""
    def __init__(self, entity_id=None, template_id=None, template_name=None, schedule_type=None, details=None):
        super().__init__("report_schedule", entity_id)
        self.template_id = template_id
        self.template_name = template_name
        self.schedule_type = schedule_type
        self.details = details or {}

class ReportScheduledEvent(ReportScheduleEvent, EntityCreatedEvent):
    """Événement émis lorsqu'un rapport est planifié."""
    pass

class ReportScheduleUpdatedEvent(ReportScheduleEvent, EntityUpdatedEvent):
    """Événement émis lorsqu'une planification de rapport est mise à jour."""
    def __init__(self, entity_id, changes, template_id=None, template_name=None, schedule_type=None, details=None):
        ReportScheduleEvent.__init__(self, entity_id, template_id, template_name, schedule_type, details)
        EntityUpdatedEvent.__init__(self, "report_schedule", entity_id, changes)

class ReportScheduleDeletedEvent(ReportScheduleEvent, EntityDeletedEvent):
    """Événement émis lorsqu'une planification de rapport est supprimée."""
    pass

class ReportScheduleExecutedEvent(ReportScheduleEvent):
    """Événement émis lorsqu'une planification de rapport est exécutée."""
    def __init__(self, entity_id, report_id=None, template_id=None, template_name=None, schedule_type=None, details=None):
        super().__init__(entity_id, template_id, template_name, schedule_type, details)
        self.report_id = report_id 