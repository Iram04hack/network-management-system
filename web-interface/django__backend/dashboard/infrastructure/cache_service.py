"""
Service de cache basé sur Redis pour le module Dashboard.

Ce service implémente l'interface ICacheService pour fournir
une mise en cache performante des données du tableau de bord.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
import redis
from django.core.cache import cache
from django.conf import settings

from ..domain.interfaces import ICacheService
from ..conf import get_cache_ttl

logger = logging.getLogger(__name__)


class RedisCacheService(ICacheService):
    """
    Implémentation du service de cache utilisant Redis.
    
    Cette classe implémente l'interface ICacheService en utilisant
    Redis comme backend de cache.
    """
    
    def __init__(self):
        """Initialise le service de cache avec la configuration Redis."""
        self.default_ttl = get_cache_ttl()
        self.redis_available = False
        
        # Essai de connexion à Redis
        try:
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = int(getattr(settings, 'REDIS_PORT', 6379))
            redis_password = getattr(settings, 'REDIS_PASSWORD', None) or None
            redis_db = int(getattr(settings, 'REDIS_DB_CACHE', 2))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True
            )
            
            # Test de connexion
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Service de cache Redis initialisé avec succès")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Impossible de se connecter à Redis: {e}. Utilisation du cache Django par défaut.")
        except Exception as e:
            logger.warning(f"Erreur d'initialisation Redis: {e}. Utilisation du cache Django par défaut.")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de la valeur à récupérer
            
        Returns:
            Valeur mise en cache ou None si absente
        """
        try:
            # Préfixer la clé pour isolation
            prefixed_key = f"dashboard:{key}"
            
            if self.redis_available:
                result = self.redis_client.get(prefixed_key)
                if result:
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return result
                return None
            else:
                # Fallback sur le cache Django
                return cache.get(prefixed_key)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache pour {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Définit une valeur dans le cache.
        
        Args:
            key: Clé de la valeur à stocker
            value: Valeur à stocker
            ttl: Durée de vie en secondes (utilise la valeur par défaut si None)
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            # Préfixer la clé pour isolation
            prefixed_key = f"dashboard:{key}"
            
            # Utiliser le TTL par défaut si non spécifié
            ttl = ttl if ttl is not None else self.default_ttl
            
            # Sérialiser la valeur si nécessaire
            if not isinstance(value, (str, int, float, bool)) and value is not None:
                value = json.dumps(value)
            
            if self.redis_available:
                return bool(self.redis_client.setex(prefixed_key, ttl, value))
            else:
                # Fallback sur le cache Django
                cache.set(prefixed_key, value, timeout=ttl)
                return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache pour {key}: {e}")
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalide les entrées de cache correspondant à un motif.
        
        Args:
            pattern: Motif de clés à invalider
            
        Returns:
            Nombre d'entrées invalidées
        """
        try:
            # Préfixer le motif pour isolation
            prefixed_pattern = f"dashboard:{pattern}"
            
            if self.redis_available:
                # Rechercher les clés correspondantes
                keys = self.redis_client.keys(prefixed_pattern)
                
                if not keys:
                    return 0
                
                # Supprimer les clés
                deleted = self.redis_client.delete(*keys)
                logger.debug(f"Cache invalidé: {deleted} clés pour le motif {pattern}")
                return deleted
            else:
                # Pas d'opération équivalente dans le cache Django standard
                # Cette fonctionnalité n'est disponible qu'avec Redis
                logger.warning("L'invalidation par motif nécessite Redis")
                return 0
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache pour {pattern}: {e}")
            return 0
            
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """
        Récupère les clés correspondant à un motif.
        
        Args:
            pattern: Motif de clés à rechercher
            
        Returns:
            Liste des clés correspondantes
        """
        try:
            # Préfixer le motif pour isolation
            prefixed_pattern = f"dashboard:{pattern}"
            
            if self.redis_available:
                keys = self.redis_client.keys(prefixed_pattern)
                # Enlever le préfixe pour les clés retournées
                return [key.replace("dashboard:", "", 1) for key in keys]
            else:
                logger.warning("La récupération de clés par motif nécessite Redis")
                return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des clés pour {pattern}: {e}")
            return [] 