"""
Cache de réponses avec TTL et stratégies d'éviction pour les clients API.

Ce module fournit une implémentation robuste du cache avec TTL (Time To Live)
et éviction LRU pour améliorer les performances des clients API.
"""

import time
import threading
import hashlib
import json
import logging
from typing import Any, Optional, Dict, Union, Callable
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass

from ..domain.exceptions import CacheException

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Entrée du cache avec métadonnées."""
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: Optional[float] = None
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si l'entrée a expiré."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    @property
    def age(self) -> float:
        """Retourne l'âge de l'entrée en secondes."""
        return time.time() - self.created_at
    
    def touch(self):
        """Met à jour le temps d'accès et incrémente le compteur."""
        self.last_accessed = time.time()
        self.access_count += 1

class EvictionStrategy(ABC):
    """Interface abstraite pour les stratégies d'éviction."""
    
    @abstractmethod
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """
        Détermine si une entrée doit être évincée.
        
        Args:
            entry: Entrée du cache à évaluer
            cache_size: Taille actuelle du cache
            max_size: Taille maximum du cache
            
        Returns:
            True si l'entrée doit être évincée
        """
        pass
    
    @abstractmethod
    def select_for_eviction(self, entries: Dict[str, CacheEntry]) -> str:
        """
        Sélectionne une clé pour l'éviction.
        
        Args:
            entries: Dictionnaire des entrées du cache
            
        Returns:
            Clé de l'entrée à évincer
        """
        pass

class LRUEvictionStrategy(EvictionStrategy):
    """Stratégie d'éviction LRU (Least Recently Used)."""
    
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """L'éviction se base uniquement sur la taille du cache."""
        return cache_size >= max_size
    
    def select_for_eviction(self, entries: Dict[str, CacheEntry]) -> str:
        """Sélectionne l'entrée la moins récemment utilisée."""
        if not entries:
            raise CacheException("Aucune entrée à évincer")
        
        oldest_key = min(entries.keys(), 
                        key=lambda k: entries[k].last_accessed)
        return oldest_key

class LFUEvictionStrategy(EvictionStrategy):
    """Stratégie d'éviction LFU (Least Frequently Used)."""
    
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """L'éviction se base uniquement sur la taille du cache."""
        return cache_size >= max_size
    
    def select_for_eviction(self, entries: Dict[str, CacheEntry]) -> str:
        """Sélectionne l'entrée la moins fréquemment utilisée."""
        if not entries:
            raise CacheException("Aucune entrée à évincer")
        
        least_used_key = min(entries.keys(), 
                           key=lambda k: entries[k].access_count)
        return least_used_key

class TTLEvictionStrategy(EvictionStrategy):
    """Stratégie d'éviction basée sur TTL."""
    
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Évince si l'entrée a expiré ou si le cache est plein."""
        return entry.is_expired or cache_size >= max_size
    
    def select_for_eviction(self, entries: Dict[str, CacheEntry]) -> str:
        """Sélectionne la plus ancienne entrée expirée, ou la plus ancienne."""
        if not entries:
            raise CacheException("Aucune entrée à évincer")
        
        # D'abord, chercher les entrées expirées
        expired_entries = {k: v for k, v in entries.items() if v.is_expired}
        if expired_entries:
            # Prendre la plus ancienne entrée expirée
            oldest_expired = min(expired_entries.keys(),
                               key=lambda k: expired_entries[k].created_at)
            return oldest_expired
        
        # Sinon, prendre la plus ancienne entrée
        oldest_key = min(entries.keys(),
                        key=lambda k: entries[k].created_at)
        return oldest_key

class CacheConfig:
    """Configuration pour le cache de réponses."""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = 300.0,  # 5 minutes
        eviction_strategy: Optional[EvictionStrategy] = None,
        cleanup_interval: float = 60.0,  # 1 minute
        enable_stats: bool = True
    ):
        """
        Initialise la configuration du cache.
        
        Args:
            max_size: Taille maximum du cache (nombre d'entrées)
            default_ttl: TTL par défaut en secondes (None = pas d'expiration)
            eviction_strategy: Stratégie d'éviction à utiliser
            cleanup_interval: Intervalle de nettoyage automatique (secondes)
            enable_stats: Activer la collecte de statistiques
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.eviction_strategy = eviction_strategy or LRUEvictionStrategy()
        self.cleanup_interval = cleanup_interval
        self.enable_stats = enable_stats

class CacheStats:
    """Statistiques thread-safe pour le cache."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expired_entries = 0
        self.total_requests = 0
    
    def record_hit(self):
        """Enregistre un cache hit."""
        with self._lock:
            self.hits += 1
            self.total_requests += 1
    
    def record_miss(self):
        """Enregistre un cache miss."""
        with self._lock:
            self.misses += 1
            self.total_requests += 1
    
    def record_eviction(self):
        """Enregistre une éviction."""
        with self._lock:
            self.evictions += 1
    
    def record_expiration(self):
        """Enregistre une expiration."""
        with self._lock:
            self.expired_entries += 1
    
    @property
    def hit_rate(self) -> float:
        """Calcule le taux de cache hit."""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calcule le taux de cache miss."""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les statistiques en dictionnaire."""
        with self._lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'expired_entries': self.expired_entries,
                'total_requests': self.total_requests,
                'hit_rate': self.hit_rate,
                'miss_rate': self.miss_rate
            }

class ResponseCache:
    """
    Cache de réponses avec TTL et éviction thread-safe.
    
    Cette classe implémente un cache haute performance avec TTL,
    éviction LRU/LFU et nettoyage automatique des entrées expirées.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialise le cache de réponses.
        
        Args:
            config: Configuration optionnelle du cache
        """
        self.config = config or CacheConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._cleanup_timer: Optional[threading.Timer] = None
        self.stats = CacheStats() if self.config.enable_stats else None
        
        # Démarrer le nettoyage automatique si configuré
        if self.config.cleanup_interval > 0:
            self._schedule_cleanup()
        
        logger.debug(f"Cache initialisé avec configuration: "
                    f"max_size={self.config.max_size}, "
                    f"default_ttl={self.config.default_ttl}s, "
                    f"strategy={type(self.config.eviction_strategy).__name__}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de l'entrée à récupérer
            
        Returns:
            Valeur stockée ou None si non trouvée/expirée
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._record_miss()
                return None
            
            # Vérifier l'expiration
            if entry.is_expired:
                self._remove_entry(key)
                self._record_miss()
                if self.stats:
                    self.stats.record_expiration()
                return None
            
            # Mettre à jour les métadonnées d'accès
            entry.touch()
            self._record_hit()
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Ajoute ou met à jour une valeur dans le cache.
        
        Args:
            key: Clé de l'entrée
            value: Valeur à stocker
            ttl: TTL spécifique (utilise default_ttl si None)
        """
        with self._lock:
            # Utiliser le TTL par défaut si aucun spécifié
            effective_ttl = ttl if ttl is not None else self.config.default_ttl
            
            # Créer la nouvelle entrée
            now = time.time()
            entry = CacheEntry(
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=1,
                ttl=effective_ttl
            )
            
            # Vérifier si l'éviction est nécessaire
            if (len(self._cache) >= self.config.max_size and 
                key not in self._cache):
                self._evict_entries()
            
            # Stocker l'entrée
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            key: Clé de l'entrée à supprimer
            
        Returns:
            True si l'entrée a été supprimée, False si non trouvée
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self) -> None:
        """Vide complètement le cache."""
        with self._lock:
            self._cache.clear()
            logger.debug("Cache vidé")
    
    def cleanup_expired(self) -> int:
        """
        Nettoie les entrées expirées.
        
        Returns:
            Nombre d'entrées supprimées
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
                if self.stats:
                    self.stats.record_expiration()
            
            if expired_keys:
                logger.debug(f"Nettoyage: {len(expired_keys)} entrées expirées supprimées")
            
            return len(expired_keys)
    
    def _evict_entries(self) -> None:
        """Évince les entrées selon la stratégie configurée."""
        while len(self._cache) >= self.config.max_size:
            try:
                key_to_evict = self.config.eviction_strategy.select_for_eviction(
                    self._cache
                )
                self._remove_entry(key_to_evict)
                if self.stats:
                    self.stats.record_eviction()
                
                logger.debug(f"Entrée évincée: {key_to_evict}")
            except CacheException:
                # Plus d'entrées à évincer
                break
    
    def _remove_entry(self, key: str) -> None:
        """Supprime une entrée du cache."""
        self._cache.pop(key, None)
    
    def _record_hit(self) -> None:
        """Enregistre un cache hit."""
        if self.stats:
            self.stats.record_hit()
    
    def _record_miss(self) -> None:
        """Enregistre un cache miss."""
        if self.stats:
            self.stats.record_miss()
    
    def _schedule_cleanup(self) -> None:
        """Programme le prochain nettoyage automatique."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        
        self._cleanup_timer = threading.Timer(
            self.config.cleanup_interval,
            self._periodic_cleanup
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def _periodic_cleanup(self) -> None:
        """Nettoyage périodique des entrées expirées."""
        try:
            self.cleanup_expired()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage périodique: {e}")
        finally:
            # Programmer le prochain nettoyage
            if self.config.cleanup_interval > 0:
                self._schedule_cleanup()
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur l'état du cache.
        
        Returns:
            Dictionnaire avec les informations du cache
        """
        with self._lock:
            info = {
                'size': len(self._cache),
                'max_size': self.config.max_size,
                'config': {
                    'default_ttl': self.config.default_ttl,
                    'cleanup_interval': self.config.cleanup_interval,
                    'eviction_strategy': type(self.config.eviction_strategy).__name__
                }
            }
            
            if self.stats:
                info['stats'] = self.stats.to_dict()
            
            return info
    
    def __del__(self):
        """Nettoyage lors de la destruction."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()

def generate_cache_key(*args, **kwargs) -> str:
    """
    Génère une clé de cache unique basée sur les arguments.
    
    Args:
        *args: Arguments positionnels
        **kwargs: Arguments nommés
        
    Returns:
        Clé de cache hexadécimale
    """
    # Créer une représentation déterministe des arguments
    cache_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    # Sérialiser en JSON (ordonné) puis hasher
    json_str = json.dumps(cache_data, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    return hash_obj.hexdigest()

def cached_response(
    cache: ResponseCache,
    ttl: Optional[float] = None,
    key_func: Optional[Callable] = None
):
    """
    Décorateur pour mettre en cache automatiquement les réponses de fonction.
    
    Args:
        cache: Instance du cache à utiliser
        ttl: TTL spécifique pour cette fonction
        key_func: Fonction personnalisée pour générer la clé de cache
        
    Returns:
        Décorateur configuré
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la fonction et mettre en cache le résultat
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator

# Instances pré-configurées pour les cas d'usage courants
DEFAULT_CACHE = ResponseCache()

LONG_LIVED_CACHE = ResponseCache(CacheConfig(
    max_size=5000,
    default_ttl=3600.0,  # 1 heure
    eviction_strategy=LRUEvictionStrategy()
))

SHORT_LIVED_CACHE = ResponseCache(CacheConfig(
    max_size=100,
    default_ttl=60.0,  # 1 minute
    eviction_strategy=TTLEvictionStrategy()
)) 