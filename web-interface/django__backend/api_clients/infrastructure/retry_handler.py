"""
Gestionnaire de retry avec backoff exponentiel pour les clients API.

Ce module fournit une implémentation robuste du pattern Retry
avec backoff exponentiel et jitter pour améliorer la résilience.
"""

import time
import random
import logging
from typing import Callable, Any, Optional, Union, List, Type
from abc import ABC, abstractmethod
from functools import wraps

from ..domain.exceptions import (
    APIClientException,
    RetryExhaustedException,
    APIConnectionException,
    APITimeoutException,
    ConfigurationException
)

logger = logging.getLogger(__name__)

class BackoffStrategy(ABC):
    """Interface abstraite pour les stratégies de backoff."""
    
    @abstractmethod
    def calculate_delay(self, attempt: int, base_delay: float) -> float:
        """
        Calcule le délai d'attente pour une tentative donnée.
        
        Args:
            attempt: Numéro de la tentative (commence à 1)
            base_delay: Délai de base en secondes
            
        Returns:
            Délai d'attente calculé en secondes
        """
        pass

class ExponentialBackoffStrategy(BackoffStrategy):
    """Stratégie de backoff exponentiel avec jitter optionnel."""
    
    def __init__(self, max_delay: float = 300.0, jitter: bool = True, 
                 jitter_factor: float = 0.1):
        """
        Initialise la stratégie de backoff exponentiel.
        
        Args:
            max_delay: Délai maximum en secondes
            jitter: Activer le jitter pour éviter le thundering herd
            jitter_factor: Facteur de jitter (pourcentage du délai)
        """
        self.max_delay = max_delay
        self.jitter = jitter
        self.jitter_factor = jitter_factor
    
    def calculate_delay(self, attempt: int, base_delay: float) -> float:
        """Calcule le délai avec backoff exponentiel et jitter."""
        # Backoff exponentiel: base_delay * (2 ^ (attempt - 1))
        delay = base_delay * (2 ** (attempt - 1))
        
        # Limiter au délai maximum
        delay = min(delay, self.max_delay)
        
        # Ajouter du jitter si activé
        if self.jitter:
            jitter_amount = delay * self.jitter_factor
            jitter_offset = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter_offset)
        
        return delay

class LinearBackoffStrategy(BackoffStrategy):
    """Stratégie de backoff linéaire."""
    
    def __init__(self, max_delay: float = 60.0):
        """
        Initialise la stratégie de backoff linéaire.
        
        Args:
            max_delay: Délai maximum en secondes
        """
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int, base_delay: float) -> float:
        """Calcule le délai avec backoff linéaire."""
        delay = base_delay * attempt
        return min(delay, self.max_delay)

class FixedBackoffStrategy(BackoffStrategy):
    """Stratégie de backoff fixe."""
    
    def calculate_delay(self, attempt: int, base_delay: float) -> float:
        """Retourne toujours le délai de base."""
        return base_delay

class RetryConfig:
    """Configuration pour le gestionnaire de retry."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        backoff_strategy: Optional[BackoffStrategy] = None,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
        retry_on_status_codes: Optional[List[int]] = None,
        no_retry_on_status_codes: Optional[List[int]] = None
    ):
        """
        Initialise la configuration de retry.
        
        Args:
            max_retries: Nombre maximum de tentatives
            base_delay: Délai de base entre les tentatives (secondes)
            backoff_strategy: Stratégie de backoff à utiliser
            retryable_exceptions: Types d'exceptions à retry
            non_retryable_exceptions: Types d'exceptions à ne pas retry
            retry_on_status_codes: Codes de statut HTTP à retry
            no_retry_on_status_codes: Codes de statut HTTP à ne pas retry
        """
        if max_retries < 0:
            raise ConfigurationException("max_retries doit être >= 0")
        if base_delay <= 0:
            raise ConfigurationException("base_delay doit être > 0")
        
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_strategy = backoff_strategy or ExponentialBackoffStrategy()
        
        # Exceptions par défaut à retry
        self.retryable_exceptions = retryable_exceptions or [
            APIConnectionException,
            APITimeoutException,
            ConnectionError,
            TimeoutError
        ]
        
        # Exceptions à ne jamais retry
        self.non_retryable_exceptions = non_retryable_exceptions or [
            ValueError,
            TypeError,
            AttributeError
        ]
        
        # Codes de statut HTTP à retry (erreurs serveur temporaires)
        self.retry_on_status_codes = retry_on_status_codes or [
            408,  # Request Timeout
            429,  # Too Many Requests
            502,  # Bad Gateway
            503,  # Service Unavailable
            504   # Gateway Timeout
        ]
        
        # Codes de statut à ne pas retry (erreurs client)
        self.no_retry_on_status_codes = no_retry_on_status_codes or [
            400,  # Bad Request
            401,  # Unauthorized
            403,  # Forbidden
            404,  # Not Found
            422   # Unprocessable Entity
        ]

class RetryHandler:
    """
    Gestionnaire de retry avec backoff exponentiel et configuration flexible.
    
    Cette classe implémente le pattern Retry avec diverses stratégies de backoff
    et une configuration flexible pour différents types d'erreurs.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialise le gestionnaire de retry.
        
        Args:
            config: Configuration optionnelle du retry
        """
        self.config = config or RetryConfig()
        
        logger.debug(f"Gestionnaire de retry initialisé avec configuration: "
                    f"max_retries={self.config.max_retries}, "
                    f"base_delay={self.config.base_delay}s, "
                    f"strategy={type(self.config.backoff_strategy).__name__}")
    
    def execute_with_retry(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Exécute une fonction avec retry automatique en cas d'échec.
        
        Args:
            func: Fonction à exécuter
            *args: Arguments positionnels pour la fonction
            **kwargs: Arguments nommés pour la fonction
            
        Returns:
            Résultat de la fonction
            
        Raises:
            RetryExhaustedException: Si le nombre maximum de tentatives est atteint
            Exception: Toute exception non-retryable de la fonction
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_retries + 2):  # +1 pour la tentative initiale
            try:
                if attempt > 1:
                    logger.info(f"Tentative {attempt}/{self.config.max_retries + 1} pour {func.__name__}")
                
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"Succès à la tentative {attempt} pour {func.__name__}")
                
                return result
            
            except Exception as e:
                last_exception = e
                
                # Vérifier si l'exception est retryable
                if not self._should_retry(e, attempt):
                    logger.debug(f"Exception non-retryable ou max tentatives atteint: {type(e).__name__}")
                    raise
                
                # Calculer le délai d'attente
                if attempt <= self.config.max_retries:
                    delay = self.config.backoff_strategy.calculate_delay(
                        attempt, self.config.base_delay
                    )
                    
                    logger.warning(
                        f"Tentative {attempt} échouée pour {func.__name__}: {type(e).__name__}: {e}. "
                        f"Nouvelle tentative dans {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
        
        # Si on arrive ici, toutes les tentatives ont échoué
        raise RetryExhaustedException(
            f"Échec après {self.config.max_retries + 1} tentatives",
            max_retries=self.config.max_retries,
            last_exception=last_exception
        )
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Détermine si une exception doit déclencher un retry.
        
        Args:
            exception: Exception levée
            attempt: Numéro de la tentative actuelle
            
        Returns:
            True si un retry doit être effectué
        """
        # Ne pas retry si on a atteint le maximum de tentatives
        if attempt > self.config.max_retries:
            return False
        
        # Vérifier les exceptions explicitement non-retryables
        for non_retryable in self.config.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                logger.debug(f"Exception non-retryable: {type(exception).__name__}")
                return False
        
        # Vérifier les exceptions explicitement retryables
        for retryable in self.config.retryable_exceptions:
            if isinstance(exception, retryable):
                logger.debug(f"Exception retryable: {type(exception).__name__}")
                return True
        
        # Vérifier les codes de statut HTTP si applicable
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
            
            # Codes de statut explicitement non-retryables
            if status_code in self.config.no_retry_on_status_codes:
                logger.debug(f"Code de statut non-retryable: {status_code}")
                return False
            
            # Codes de statut explicitement retryables
            if status_code in self.config.retry_on_status_codes:
                logger.debug(f"Code de statut retryable: {status_code}")
                return True
        
        # Par défaut, ne pas retry les exceptions inconnues
        logger.debug(f"Exception inconnue, pas de retry: {type(exception).__name__}")
        return False
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques de configuration du retry handler.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            'max_retries': self.config.max_retries,
            'base_delay': self.config.base_delay,
            'backoff_strategy': type(self.config.backoff_strategy).__name__,
            'retryable_exceptions': [exc.__name__ for exc in self.config.retryable_exceptions],
            'non_retryable_exceptions': [exc.__name__ for exc in self.config.non_retryable_exceptions],
            'retry_on_status_codes': self.config.retry_on_status_codes,
            'no_retry_on_status_codes': self.config.no_retry_on_status_codes
        }

def retry_on_failure(config: Optional[RetryConfig] = None):
    """
    Décorateur pour ajouter automatiquement le retry à une fonction.
    
    Args:
        config: Configuration optionnelle du retry
        
    Returns:
        Décorateur configuré
    """
    def decorator(func: Callable) -> Callable:
        retry_handler = RetryHandler(config)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_handler.execute_with_retry(func, *args, **kwargs)
        
        return wrapper
    
    return decorator

# Instances pré-configurées pour les cas d'usage courants
DEFAULT_RETRY_HANDLER = RetryHandler()

AGGRESSIVE_RETRY_HANDLER = RetryHandler(RetryConfig(
    max_retries=5,
    base_delay=0.5,
    backoff_strategy=ExponentialBackoffStrategy(max_delay=60.0)
))

CONSERVATIVE_RETRY_HANDLER = RetryHandler(RetryConfig(
    max_retries=2,
    base_delay=2.0,
    backoff_strategy=LinearBackoffStrategy(max_delay=30.0)
)) 