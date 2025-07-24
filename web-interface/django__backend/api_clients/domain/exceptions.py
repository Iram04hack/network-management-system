"""
Exceptions du domaine pour les clients API.

Ce module définit les exceptions spécifiques au domaine des clients API.
"""

class APIClientException(Exception):
    """Exception de base pour les erreurs de client API."""
    
    def __init__(self, message: str = "Erreur de client API", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message


class APIConnectionException(APIClientException):
    """Exception levée lors d'une erreur de connexion au service distant."""
    
    def __init__(self, message: str = "Erreur de connexion au service distant", 
                 service_name: str = None, *args, **kwargs):
        if service_name:
            message = f"Erreur de connexion au service {service_name}: {message}"
        super().__init__(message, *args, **kwargs)
        self.service_name = service_name


class APIRequestException(APIClientException):
    """Exception levée lors d'une erreur de requête API."""
    
    def __init__(self, message: str = "Erreur de requête API", 
                 status_code: int = None, endpoint: str = None, *args, **kwargs):
        if status_code and endpoint:
            message = f"Erreur de requête API ({status_code}) sur {endpoint}: {message}"
        elif status_code:
            message = f"Erreur de requête API ({status_code}): {message}"
        elif endpoint:
            message = f"Erreur de requête API sur {endpoint}: {message}"
        super().__init__(message, *args, **kwargs)
        self.status_code = status_code
        self.endpoint = endpoint


class APIResponseException(APIClientException):
    """Exception levée lors d'une erreur de traitement de réponse API."""
    
    def __init__(self, message: str = "Erreur de traitement de réponse API", 
                 status_code: int = None, response_content: str = None, *args, **kwargs):
        if status_code:
            message = f"Erreur de traitement de réponse API ({status_code}): {message}"
        super().__init__(message, *args, **kwargs)
        self.status_code = status_code
        self.response_content = response_content


class APITimeoutException(APIClientException):
    """Exception levée lors d'un timeout de requête API."""
    
    def __init__(self, message: str = "Timeout de requête API", 
                 timeout_duration: float = None, endpoint: str = None, *args, **kwargs):
        if timeout_duration and endpoint:
            message = f"Timeout de requête API ({timeout_duration}s) sur {endpoint}: {message}"
        elif timeout_duration:
            message = f"Timeout de requête API ({timeout_duration}s): {message}"
        elif endpoint:
            message = f"Timeout de requête API sur {endpoint}: {message}"
        super().__init__(message, *args, **kwargs)
        self.timeout_duration = timeout_duration
        self.endpoint = endpoint


class AuthenticationException(APIClientException):
    """Exception levée lors d'une erreur d'authentification."""
    
    def __init__(self, message: str = "Erreur d'authentification", 
                 service_name: str = None, *args, **kwargs):
        if service_name:
            message = f"Erreur d'authentification pour le service {service_name}: {message}"
        super().__init__(message, *args, **kwargs)
        self.service_name = service_name


class APIClientDataException(APIClientException):
    """Exception levée lors d'une erreur de données (parsing, validation, etc.)."""
    
    def __init__(self, message: str = "Erreur de données API", 
                 data_type: str = None, *args, **kwargs):
        if data_type:
            message = f"Erreur de données API ({data_type}): {message}"
        super().__init__(message, *args, **kwargs)
        self.data_type = data_type


class CircuitBreakerOpenException(APIClientException):
    """Exception levée quand le circuit breaker est ouvert."""
    
    def __init__(self, message: str = "Circuit breaker ouvert", 
                 service_name: str = None, retry_after: float = None, *args, **kwargs):
        if service_name and retry_after:
            message = f"Circuit breaker ouvert pour {service_name}. Retry dans {retry_after}s"
        elif service_name:
            message = f"Circuit breaker ouvert pour {service_name}"
        super().__init__(message, *args, **kwargs)
        self.service_name = service_name
        self.retry_after = retry_after


class CircuitBreakerException(APIClientException):
    """Exception de base pour les erreurs de circuit breaker."""
    pass


class RetryExhaustedException(APIClientException):
    """Exception levée quand le nombre maximum de tentatives est atteint."""
    
    def __init__(self, message: str = "Nombre maximum de tentatives atteint", 
                 max_retries: int = None, last_exception: Exception = None, *args, **kwargs):
        if max_retries:
            message = f"Nombre maximum de tentatives atteint ({max_retries}): {message}"
        super().__init__(message, *args, **kwargs)
        self.max_retries = max_retries
        self.last_exception = last_exception


class ValidationException(APIClientException):
    """Exception levée lors d'une erreur de validation des données d'entrée."""
    
    def __init__(self, message: str = "Erreur de validation", 
                 field_name: str = None, field_value: str = None, *args, **kwargs):
        if field_name and field_value:
            message = f"Erreur de validation pour le champ '{field_name}' avec la valeur '{field_value}': {message}"
        elif field_name:
            message = f"Erreur de validation pour le champ '{field_name}': {message}"
        super().__init__(message, *args, **kwargs)
        self.field_name = field_name
        self.field_value = field_value


class CacheException(APIClientException):
    """Exception levée lors d'une erreur de cache."""
    
    def __init__(self, message: str = "Erreur de cache", 
                 cache_key: str = None, *args, **kwargs):
        if cache_key:
            message = f"Erreur de cache pour la clé '{cache_key}': {message}"
        super().__init__(message, *args, **kwargs)
        self.cache_key = cache_key


class ConfigurationException(APIClientException):
    """Exception levée lors d'une erreur de configuration."""
    
    def __init__(self, message: str = "Erreur de configuration", 
                 config_key: str = None, *args, **kwargs):
        if config_key:
            message = f"Erreur de configuration pour '{config_key}': {message}"
        super().__init__(message, *args, **kwargs)
        self.config_key = config_key 