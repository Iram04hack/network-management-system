"""
Implémentation thread-safe du Circuit Breaker pour les clients API.

Ce module fournit une implémentation robuste du pattern Circuit Breaker
conforme aux principes SOLID et à l'architecture hexagonale.
"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict
from abc import ABC, abstractmethod
import random

from ..domain.interfaces import CircuitBreakerInterface
from ..domain.exceptions import (
    APIClientException,
    CircuitBreakerOpenException,
    CircuitBreakerException
)

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """États possibles du Circuit Breaker."""
    CLOSED = "closed"      # Circuit fermé, requêtes autorisées
    OPEN = "open"          # Circuit ouvert, requêtes bloquées
    HALF_OPEN = "half_open"  # Circuit semi-ouvert, test de rétablissement

class CircuitBreakerConfig:
    """Configuration pour le Circuit Breaker."""
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_success_threshold: int = 3,
        half_open_max_calls: int = 5,
        expected_exception: type = Exception
    ):
        """
        Initialise la configuration du Circuit Breaker.
        
        Args:
            failure_threshold: Nombre d'échecs consécutifs avant ouverture
            reset_timeout: Délai avant tentative de rétablissement (secondes)
            half_open_success_threshold: Succès requis pour fermer le circuit
            half_open_max_calls: Appels max autorisés en mode semi-ouvert
            expected_exception: Type d'exception considérée comme échec
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_success_threshold = half_open_success_threshold
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception

class CircuitBreakerMetrics:
    """Métriques thread-safe pour le Circuit Breaker."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.failure_count = 0
        self.success_count = 0
        self.total_calls = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.state_transitions = []
    
    def record_success(self):
        """Enregistre un succès de manière thread-safe."""
        with self._lock:
            self.success_count += 1
            self.total_calls += 1
            self.last_success_time = time.time()
    
    def record_failure(self):
        """Enregistre un échec de manière thread-safe."""
        with self._lock:
            self.failure_count += 1
            self.total_calls += 1
            self.last_failure_time = time.time()
    
    def reset_counts(self):
        """Remet à zéro les compteurs."""
        with self._lock:
            self.failure_count = 0
            self.success_count = 0
    
    def record_state_transition(self, from_state: CircuitState, to_state: CircuitState):
        """Enregistre une transition d'état."""
        with self._lock:
            transition = {
                'timestamp': time.time(),
                'from_state': from_state.value,
                'to_state': to_state.value
            }
            self.state_transitions.append(transition)
            
            # Garder seulement les 100 dernières transitions
            if len(self.state_transitions) > 100:
                self.state_transitions.pop(0)

class DefaultCircuitBreaker(CircuitBreakerInterface):
    """
    Implémentation thread-safe du Circuit Breaker.
    
    Implémente le pattern Circuit Breaker avec gestion thread-safe des états
    et protection contre les appels simultanés.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialise le Circuit Breaker.
        
        Args:
            config: Configuration optionnelle du circuit breaker
        """
        self.config = config or CircuitBreakerConfig()
        self.metrics = CircuitBreakerMetrics()
        self._state = CircuitState.CLOSED
        self._state_lock = threading.RLock()
        self._half_open_lock = threading.Semaphore(self.config.half_open_max_calls)
        
        logger.info(f"Circuit Breaker initialisé avec configuration: {self._config_to_dict()}")
    
    @property
    def state(self) -> CircuitState:
        """Retourne l'état actuel du circuit (thread-safe)."""
        with self._state_lock:
            return self._state
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire pour le logging."""
        return {
            'failure_threshold': self.config.failure_threshold,
            'reset_timeout': self.config.reset_timeout,
            'half_open_success_threshold': self.config.half_open_success_threshold,
            'half_open_max_calls': self.config.half_open_max_calls
        }
    
    def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Exécute une fonction avec protection du Circuit Breaker.
        
        Args:
            func: Fonction à exécuter
            *args: Arguments positionnels pour la fonction
            **kwargs: Arguments nommés pour la fonction
            
        Returns:
            Résultat de la fonction
            
        Raises:
            CircuitBreakerOpenException: Si le circuit est ouvert
            Exception: Toute exception levée par la fonction
        """
        self._check_and_update_state()
        
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenException(
                f"Circuit breaker ouvert. Prochaine tentative dans "
                f"{self._time_to_next_attempt():.1f} secondes"
            )
        
        if current_state == CircuitState.HALF_OPEN:
            # Limiter le nombre d'appels en mode semi-ouvert
            if not self._half_open_lock.acquire(blocking=False):
                raise CircuitBreakerOpenException(
                    "Circuit breaker en mode semi-ouvert avec limite d'appels atteinte"
                )
        
        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        
        except self.config.expected_exception as e:
            self._handle_failure()
            raise
        
        except Exception as e:
            # Les exceptions non attendues ne comptent pas comme des échecs
            logger.warning(f"Exception non attendue dans Circuit Breaker: {type(e).__name__}: {e}")
            raise
        
        finally:
            if current_state == CircuitState.HALF_OPEN:
                self._half_open_lock.release()
    
    def _check_and_update_state(self):
        """Vérifie et met à jour l'état du circuit si nécessaire."""
        with self._state_lock:
            current_time = time.time()
            
            if (self._state == CircuitState.OPEN and 
                self.metrics.last_failure_time and
                current_time - self.metrics.last_failure_time >= self.config.reset_timeout):
                
                old_state = self._state
                self._state = CircuitState.HALF_OPEN
                self.metrics.reset_counts()
                self.metrics.record_state_transition(old_state, self._state)
                
                logger.info("Circuit breaker passé de OPEN à HALF_OPEN")
    
    def _handle_success(self):
        """Gère un succès d'exécution."""
        self.metrics.record_success()
        
        with self._state_lock:
            if self._state == CircuitState.HALF_OPEN:
                if self.metrics.success_count >= self.config.half_open_success_threshold:
                    old_state = self._state
                    self._state = CircuitState.CLOSED
                    self.metrics.reset_counts()
                    self.metrics.record_state_transition(old_state, self._state)
                    
                    logger.info("Circuit breaker fermé après succès en mode semi-ouvert")
    
    def _handle_failure(self):
        """Gère un échec d'exécution."""
        self.metrics.record_failure()
        
        with self._state_lock:
            if self._state == CircuitState.CLOSED:
                if self.metrics.failure_count >= self.config.failure_threshold:
                    old_state = self._state
                    self._state = CircuitState.OPEN
                    self.metrics.record_state_transition(old_state, self._state)
                    
                    logger.warning(
                        f"Circuit breaker ouvert après {self.metrics.failure_count} échecs"
                    )
            
            elif self._state == CircuitState.HALF_OPEN:
                # Un échec en mode semi-ouvert rouvre immédiatement le circuit
                old_state = self._state
                self._state = CircuitState.OPEN
                self.metrics.reset_counts()
                self.metrics.record_state_transition(old_state, self._state)
                
                logger.warning("Circuit breaker rouvert après échec en mode semi-ouvert")
    
    def _time_to_next_attempt(self) -> float:
        """Calcule le temps restant avant la prochaine tentative."""
        if not self.metrics.last_failure_time:
            return 0.0
        
        elapsed = time.time() - self.metrics.last_failure_time
        return max(0.0, self.config.reset_timeout - elapsed)
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Retourne les informations détaillées sur l'état du circuit.
        
        Returns:
            Dictionnaire avec les informations d'état
        """
        with self._state_lock:
            return {
                'state': self._state.value,
                'failure_count': self.metrics.failure_count,
                'success_count': self.metrics.success_count,
                'total_calls': self.metrics.total_calls,
                'last_failure_time': self.metrics.last_failure_time,
                'last_success_time': self.metrics.last_success_time,
                'time_to_next_attempt': self._time_to_next_attempt(),
                'recent_transitions': self.metrics.state_transitions[-10:],  # 10 dernières
                'config': self._config_to_dict()
            }
    
    def execute(self, func, *args, **kwargs):
        """
        Exécute une fonction avec protection par circuit breaker.

        Args:
            func: Fonction à exécuter
            *args: Arguments de la fonction
            **kwargs: Arguments nommés de la fonction

        Returns:
            Résultat de la fonction

        Raises:
            CircuitBreakerOpenException: Si le circuit est ouvert
            Exception: Autres exceptions propagées depuis la fonction
        """
        return self.call(func, *args, **kwargs)

    def get_state(self) -> str:
        """
        Retourne l'état actuel du circuit breaker.

        Returns:
            État du circuit ("OPEN", "CLOSED", "HALF_OPEN")
        """
        return self.state.value.upper().replace("_", "-")

    def reset(self):
        """Remet à zéro le circuit breaker."""
        with self._state_lock:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self.metrics.reset_counts()
            self.metrics.record_state_transition(old_state, self._state)

            logger.info("Circuit breaker réinitialisé manuellement")

class CircuitBreakerOpenException(APIClientException):
    """Exception levée quand le circuit breaker est ouvert."""
    
    def __init__(self, message: str = "Circuit breaker ouvert"):
        super().__init__(message)

class CircuitBreakerException(APIClientException):
    """Exception de base pour les erreurs de circuit breaker."""
    pass 