"""
Définition des événements spécifiques au module de gestion QoS.
Ces événements permettent de découpler les différents composants du système.
"""
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Classes de base pour les événements
class EntityEvent:
    """Classe de base pour tous les événements liés aux entités."""
    def __init__(self, entity_type, entity_id):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.timestamp = datetime.now()

class EntityCreatedEvent(EntityEvent):
    """Événement émis lorsqu'une entité est créée."""
    def __init__(self, entity_type, entity_id):
        super().__init__(entity_type, entity_id)

class EntityUpdatedEvent(EntityEvent):
    """Événement émis lorsqu'une entité est mise à jour."""
    def __init__(self, entity_type, entity_id, changes):
        super().__init__(entity_type, entity_id)
        self.changes = changes

class EntityDeletedEvent(EntityEvent):
    """Événement émis lorsqu'une entité est supprimée."""
    def __init__(self, entity_type, entity_id):
        super().__init__(entity_type, entity_id)

# Bus d'événements
class EventBus:
    """
    Bus d'événements simplifié pour la communication entre composants.
    """
    _subscribers = {}
    
    @classmethod
    def publish(cls, event: Any) -> bool:
        """
        Publie un événement de manière synchrone.
        
        Args:
            event: L'événement à publier
            
        Returns:
            True si la publication a réussi
        """
        event_type = type(event).__name__
        if event_type in cls._subscribers:
            for handler in cls._subscribers[event_type]:
                handler(event)
        return True
    
    @classmethod
    def publish_async(cls, event: Any) -> bool:
        """
        Publie un événement de manière asynchrone.
        Dans cette implémentation simplifiée, c'est identique à publish.
        
        Args:
            event: L'événement à publier
            
        Returns:
            True si la publication a été mise en file d'attente
        """
        return cls.publish(event)
    
    @classmethod
    def subscribe(cls, event_type: str, handler: Callable[[Any], None]) -> str:
        """
        Souscrit à un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction de traitement
            
        Returns:
            ID de souscription
        """
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        
        cls._subscribers[event_type].append(handler)
        return f"{event_type}_{len(cls._subscribers[event_type])}"
    
    @classmethod
    def unsubscribe(cls, subscription_id: str) -> bool:
        """
        Annule une souscription.
        
        Args:
            subscription_id: ID de souscription
            
        Returns:
            True si la désinscription a réussi
        """
        if '_' not in subscription_id:
            return False
        
        event_type, index = subscription_id.split('_', 1)
        if event_type in cls._subscribers and index.isdigit():
            index = int(index) - 1
            if 0 <= index < len(cls._subscribers[event_type]):
                cls._subscribers[event_type].pop(index)
                return True
        
        return False

# Événements pour les politiques QoS

class QoSPolicyEvent(EntityEvent):
    """Classe de base pour les événements liés aux politiques QoS."""
    def __init__(self, policy_id=None, name=None, details=None):
        super().__init__("qos_policy", policy_id)
        self.name = name
        self.details = details or {}

class QoSPolicyCreatedEvent(QoSPolicyEvent, EntityCreatedEvent):
    """Événement émis lorsqu'une politique QoS est créée."""
    def __init__(self, policy_id, name=None, created_by=None, details=None):
        super().__init__(policy_id, name, details)
        self.created_by = created_by

class QoSPolicyUpdatedEvent(QoSPolicyEvent, EntityUpdatedEvent):
    """Événement émis lorsqu'une politique QoS est mise à jour."""
    def __init__(self, policy_id, changes, name=None, updated_by=None, details=None):
        QoSPolicyEvent.__init__(self, policy_id, name, details)
        EntityUpdatedEvent.__init__(self, "qos_policy", policy_id, changes)
        self.updated_by = updated_by

class QoSPolicyDeletedEvent(QoSPolicyEvent, EntityDeletedEvent):
    """Événement émis lorsqu'une politique QoS est supprimée."""
    def __init__(self, policy_id, name=None, deleted_by=None, details=None):
        super().__init__(policy_id, name, details)
        self.deleted_by = deleted_by

class QoSPolicyAppliedEvent(QoSPolicyEvent):
    """Événement émis lorsqu'une politique QoS est appliquée à une interface."""
    def __init__(self, entity_id, policy_id, interface_id, direction, details=None):
        super().__init__(policy_id, details=details)
        self.entity_id = entity_id
        self.interface_id = interface_id
        self.direction = direction

class QoSPolicyRemovedEvent(QoSPolicyEvent):
    """Événement émis lorsqu'une politique QoS est retirée d'une interface."""
    def __init__(self, entity_id, policy_id, interface_id, direction, details=None):
        super().__init__(policy_id, details=details)
        self.entity_id = entity_id
        self.interface_id = interface_id
        self.direction = direction

# Événements pour les classes de trafic

class TrafficClassEvent(EntityEvent):
    """Classe de base pour les événements liés aux classes de trafic."""
    def __init__(self, traffic_class_id=None, policy_id=None, name=None, details=None):
        super().__init__("traffic_class", traffic_class_id)
        self.policy_id = policy_id
        self.name = name
        self.details = details or {}

class TrafficClassCreatedEvent(TrafficClassEvent, EntityCreatedEvent):
    """Événement émis lorsqu'une classe de trafic est créée."""
    pass

class TrafficClassUpdatedEvent(TrafficClassEvent, EntityUpdatedEvent):
    """Événement émis lorsqu'une classe de trafic est mise à jour."""
    def __init__(self, traffic_class_id, changes, policy_id=None, name=None, details=None):
        TrafficClassEvent.__init__(self, traffic_class_id, policy_id, name, details)
        EntityUpdatedEvent.__init__(self, "traffic_class", traffic_class_id, changes)

class TrafficClassDeletedEvent(TrafficClassEvent, EntityDeletedEvent):
    """Événement émis lorsqu'une classe de trafic est supprimée."""
    pass

# Événements pour les classificateurs de trafic

class TrafficClassifierEvent(EntityEvent):
    """Classe de base pour les événements liés aux classificateurs de trafic."""
    def __init__(self, classifier_id=None, traffic_class_id=None, name=None, details=None):
        super().__init__("traffic_classifier", classifier_id)
        self.traffic_class_id = traffic_class_id
        self.name = name
        self.details = details or {}

class TrafficClassifierCreatedEvent(TrafficClassifierEvent, EntityCreatedEvent):
    """Événement émis lorsqu'un classificateur de trafic est créé."""
    pass

class TrafficClassifierUpdatedEvent(TrafficClassifierEvent, EntityUpdatedEvent):
    """Événement émis lorsqu'un classificateur de trafic est mis à jour."""
    def __init__(self, classifier_id, changes, traffic_class_id=None, name=None, details=None):
        TrafficClassifierEvent.__init__(self, classifier_id, traffic_class_id, name, details)
        EntityUpdatedEvent.__init__(self, "traffic_classifier", classifier_id, changes)

class TrafficClassifierDeletedEvent(TrafficClassifierEvent, EntityDeletedEvent):
    """Événement émis lorsqu'un classificateur de trafic est supprimé."""
    pass

class TrafficClassifiedEvent(EntityEvent):
    """Événement émis lorsqu'un paquet est classifié."""
    def __init__(self, packet_id, classifier_id, traffic_class_id, matched=True, details=None):
        super().__init__("packet", packet_id)
        self.classifier_id = classifier_id
        self.traffic_class_id = traffic_class_id
        self.matched = matched
        self.details = details or {}

# Événements pour les applications QoS sur interfaces

class InterfaceQoSEvent(EntityEvent):
    """Classe de base pour les événements liés aux applications QoS sur interfaces."""
    def __init__(self, interface_qos_id=None, interface_id=None, policy_id=None, details=None):
        super().__init__("interface_qos", interface_qos_id)
        self.interface_id = interface_id
        self.policy_id = policy_id
        self.details = details or {}

class InterfaceQoSCreatedEvent(InterfaceQoSEvent, EntityCreatedEvent):
    """Événement émis lorsqu'une application QoS sur interface est créée."""
    pass

class InterfaceQoSUpdatedEvent(InterfaceQoSEvent, EntityUpdatedEvent):
    """Événement émis lorsqu'une application QoS sur interface est mise à jour."""
    def __init__(self, interface_qos_id, changes, interface_id=None, policy_id=None, details=None):
        InterfaceQoSEvent.__init__(self, interface_qos_id, interface_id, policy_id, details)
        EntityUpdatedEvent.__init__(self, "interface_qos", interface_qos_id, changes)

class InterfaceQoSDeletedEvent(InterfaceQoSEvent, EntityDeletedEvent):
    """Événement émis lorsqu'une application QoS sur interface est supprimée."""
    pass

class InterfaceQoSStatusChangedEvent(InterfaceQoSEvent):
    """Événement émis lorsque le statut d'une application QoS sur interface change."""
    def __init__(self, interface_qos_id, old_status, new_status, interface_id=None, policy_id=None, details=None):
        super().__init__(interface_qos_id, interface_id, policy_id, details)
        self.old_status = old_status
        self.new_status = new_status 