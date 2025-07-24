"""
Exceptions du domaine pour le module Network Management.

Ce module définit les exceptions spécifiques au domaine 
pour la gestion des erreurs selon les principes de l'architecture hexagonale.
"""

class NetworkDomainException(Exception):
    """Exception de base pour toutes les erreurs du domaine."""
    pass


class ResourceNotFoundException(NetworkDomainException):
    """Exception levée lorsqu'une ressource n'est pas trouvée."""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        message = f"{resource_type} avec identifiant {resource_id} non trouvé."
        super().__init__(message)


class NetworkDeviceNotFoundException(NetworkDomainException):
    """Exception levée lorsqu'un équipement réseau n'est pas trouvé."""
    def __init__(self, device_id: str):
        self.device_id = device_id
        message = f"Équipement réseau avec identifiant {device_id} non trouvé."
        super().__init__(message)


class NetworkInterfaceNotFoundException(NetworkDomainException):
    """Exception levée lorsqu'une interface réseau n'est pas trouvée."""
    def __init__(self, interface_id: str):
        self.interface_id = interface_id
        message = f"Interface réseau avec identifiant {interface_id} non trouvée."
        super().__init__(message)


class NetworkConnectionNotFoundException(NetworkDomainException):
    """Exception levée lorsqu'une connexion réseau n'est pas trouvée."""
    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        message = f"Connexion réseau avec identifiant {connection_id} non trouvée."
        super().__init__(message)


class DeviceConfigurationNotFoundException(NetworkDomainException):
    """Exception levée lorsqu'une configuration d'équipement n'est pas trouvée."""
    def __init__(self, config_id: str):
        self.config_id = config_id
        message = f"Configuration avec identifiant {config_id} non trouvée."
        super().__init__(message)


class NetworkValidationException(NetworkDomainException):
    """Exception levée lorsqu'une validation échoue."""
    def __init__(self, message: str, errors=None):
        self.errors = errors or {}
        super().__init__(message)


class ValidationException(NetworkDomainException):
    """Exception levée lorsqu'une validation échoue."""
    def __init__(self, message: str, errors=None):
        self.errors = errors or {}
        super().__init__(message)


class BusinessRuleViolationException(NetworkDomainException):
    """Exception levée lorsqu'une règle métier est violée."""
    pass


class TopologyException(NetworkDomainException):
    """Exception spécifique aux opérations de topologie."""
    pass


class NetworkConnectionException(NetworkDomainException):
    """Exception levée lors d'un problème de connexion à un équipement."""
    pass


class ConnectionException(NetworkDomainException):
    """Exception levée lors d'un problème de connexion à un équipement."""
    pass


class CommandException(NetworkDomainException):
    """Exception levée lors de l'exécution d'une commande sur un équipement."""
    pass


class ConfigurationException(NetworkDomainException):
    """Exception liée aux opérations de configuration."""
    pass


class SimulationException(NetworkDomainException):
    """Exception levée lors d'une erreur de simulation de configuration."""
    pass


class SNMPException(NetworkDomainException):
    """Exception levée lors d'une erreur SNMP."""
    def __init__(self, message: str, oid: str = None, ip_address: str = None):
        self.oid = oid
        self.ip_address = ip_address
        extra_info = ""
        if ip_address:
            extra_info += f" Équipement: {ip_address}."
        if oid:
            extra_info += f" OID: {oid}."
        super().__init__(f"{message}{extra_info}")


class SSHException(NetworkDomainException):
    """Exception levée lors d'une erreur SSH."""
    def __init__(self, message: str, ip_address: str = None, command: str = None):
        self.ip_address = ip_address
        self.command = command
        extra_info = ""
        if ip_address:
            extra_info += f" Équipement: {ip_address}."
        if command:
            extra_info += f" Commande: {command}."
        super().__init__(f"{message}{extra_info}")


class DiscoveryException(NetworkDomainException):
    """Exception levée lors d'une erreur de découverte réseau."""
    pass


class CircuitOpenException(NetworkDomainException):
    """Exception levée lorsqu'un circuit breaker est ouvert."""
    def __init__(self, service_name: str):
        self.service_name = service_name
        message = f"Circuit breaker ouvert pour le service {service_name}."
        super().__init__(message)


class MaxRetriesExceededException(NetworkDomainException):
    """Exception levée lorsque le nombre maximal de tentatives est atteint."""
    def __init__(self, operation: str, attempts: int):
        self.operation = operation
        self.attempts = attempts
        message = f"Nombre maximal de tentatives atteint ({attempts}) pour l'opération {operation}."
        super().__init__(message)


class TemplateException(NetworkDomainException):
    """Exception liée aux templates de configuration."""
    pass


class ComplianceException(NetworkDomainException):
    """Exception liée à la vérification de conformité."""
    pass 