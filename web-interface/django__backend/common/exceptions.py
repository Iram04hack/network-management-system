"""
Exceptions communes pour le système NMS.

Ce module définit les exceptions de base utilisées dans tout le système.
"""


class BaseException(Exception):
    """
    Exception de base pour toutes les exceptions du système.
    """
    def __init__(self, message: str = "", details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundException(BaseException):
    """
    Exception levée lorsqu'une ressource n'est pas trouvée.
    """
    pass


class ValidationException(BaseException):
    """
    Exception levée lorsqu'une validation échoue.
    """
    pass


class AuthorizationException(BaseException):
    """
    Exception levée lorsqu'un utilisateur n'a pas les permissions nécessaires.
    """
    pass


class ServiceUnavailableException(BaseException):
    """
    Exception levée lorsqu'un service externe n'est pas disponible.
    """
    pass


class ConfigurationException(BaseException):
    """
    Exception levée lorsqu'une configuration est invalide.
    """
    pass


class BusinessRuleException(BaseException):
    """
    Exception levée lorsqu'une règle métier est violée.
    """
    pass 