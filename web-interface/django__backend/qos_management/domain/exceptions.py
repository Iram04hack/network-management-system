"""
Exceptions du domaine pour le module qos_management.

Ce fichier contient les exceptions spécifiques au domaine qos_management
qui permettent de transmettre des erreurs du domaine vers les couches supérieures.
"""

from typing import Dict, Any, Optional, List

class QoSException(Exception):
    """Exception de base pour les erreurs QoS."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class QoSValidationException(QoSException):
    """Exception levée lorsque la validation d'une politique QoS échoue."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        self.errors = errors or {}
        super().__init__(message)


class QoSLowLatencyValidationException(QoSValidationException):
    """Exception levée lorsqu'une politique ne respecte pas les contraintes LLQ."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)


class QoSConfigurationException(QoSException):
    """Exception levée lorsque la configuration QoS ne peut pas être appliquée."""
    
    def __init__(self, message: str, reason: str = "unknown"):
        self.reason = reason
        super().__init__(message)


class NetworkDeviceNotFoundException(QoSException):
    """Exception levée lorsqu'un appareil réseau n'est pas trouvé."""
    
    def __init__(self, message: str):
        super().__init__(message)


class QoSDomainException(Exception):
    """Exception de base pour toutes les exceptions du domaine qos_management."""
    pass


class QoSMonitoringException(QoSException):
    """Exception levée lorsqu'une opération de monitoring QoS échoue."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        super().__init__(message)


class QoSPolicyNotFoundException(QoSDomainException):
    """Exception levée lorsqu'une politique QoS n'est pas trouvée."""
    
    def __init__(self, policy_id: int):
        self.policy_id = policy_id
        super().__init__(f"Politique QoS avec l'ID {policy_id} non trouvée")


class TrafficClassNotFoundException(QoSDomainException):
    """Exception levée lorsqu'une classe de trafic n'est pas trouvée."""
    
    def __init__(self, class_id: int):
        self.class_id = class_id
        super().__init__(f"Classe de trafic avec l'ID {class_id} non trouvée")


class TrafficClassifierNotFoundException(QoSDomainException):
    """Exception levée lorsqu'un classificateur de trafic n'est pas trouvé."""
    
    def __init__(self, classifier_id: int):
        self.classifier_id = classifier_id
        super().__init__(f"Classificateur de trafic avec l'ID {classifier_id} non trouvé")


class InterfaceQoSPolicyNotFoundException(QoSDomainException):
    """Exception levée lorsqu'aucune politique QoS n'est trouvée pour une interface."""
    
    def __init__(self, interface_id: int):
        self.interface_id = interface_id
        super().__init__(f"Aucune politique QoS appliquée à l'interface {interface_id}")


class QoSPolicyApplicationException(QoSDomainException):
    """Exception levée lorsque l'application d'une politique QoS échoue."""
    
    def __init__(self, message: Optional[str] = None, policy_id: Optional[int] = None, 
               interface_id: Optional[int] = None, reason: str = "unknown"):
        self.policy_id = policy_id
        self.interface_id = interface_id
        self.reason = reason
        
        if not message:
            if policy_id and interface_id:
                message = f"Impossible d'appliquer la politique QoS {policy_id} à l'interface {interface_id}: {reason}"
            elif interface_id:
                message = f"Impossible d'appliquer une politique QoS à l'interface {interface_id}: {reason}"
            else:
                message = f"Impossible d'appliquer la politique QoS: {reason}"
                
        super().__init__(message)


class TrafficControlException(QoSDomainException):
    """Exception levée lorsqu'une opération de contrôle de trafic échoue."""
    
    def __init__(self, operation: str, reason: str = "unknown"):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Opération de contrôle de trafic échouée ({operation}): {reason}")


class BandwidthLimitExceededException(QoSDomainException):
    """Exception levée lorsqu'une limite de bande passante est dépassée."""
    
    def __init__(self, policy_id=None, interface_id=None, bandwidth=None, available=None, message=None):
        self.policy_id = policy_id
        self.interface_id = interface_id
        self.bandwidth = bandwidth
        self.available = available
        
        if message:
            self.message = message
        elif bandwidth and available:
            self.message = f"Limite de bande passante dépassée: demandé {bandwidth}, disponible {available}"
        else:
            self.message = "Limite de bande passante dépassée"
            
        super().__init__(self.message)


class SLAComplianceException(QoSException):
    """Exception levée lorsque l'analyse de conformité SLA échoue."""
    
    def __init__(self, message: str, device_id: Optional[int] = None):
        self.device_id = device_id
        msg = message
        if device_id:
            msg = f"{message} pour l'équipement {device_id}"
        super().__init__(msg) 