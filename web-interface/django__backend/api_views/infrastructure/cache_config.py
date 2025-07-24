"""
Configuration du cache Redis pour les vues API.

Ce module contient les configurations et décorateurs pour utiliser Redis
comme système de cache distribué pour les réponses des vues API.
"""

from functools import wraps
from django.core.cache import cache
from django.conf import settings
import hashlib
import json
import time


# Configuration des durées de cache par défaut (en secondes)
DEFAULT_CACHE_TTL = 60 * 5  # 5 minutes
DASHBOARD_CACHE_TTL = 60 * 2  # 2 minutes
TOPOLOGY_CACHE_TTL = 60 * 10  # 10 minutes
SEARCH_CACHE_TTL = 60 * 5  # 5 minutes
DEVICE_CACHE_TTL = 60 * 15  # 15 minutes
MONITORING_CACHE_TTL = 60  # 1 minute
CONFIG_CACHE_TTL = 60 * 60 * 24  # 1 jour


def get_cache_key(view_instance, request, *args, **kwargs):
    """Génère une clé de cache basée sur la vue, l'URL et les paramètres."""
    # Construire un identifiant unique pour cette requête
    view_name = view_instance.__class__.__name__
    url = request.build_absolute_uri()
    method = request.method
    
    # Inclure les données POST pour les requêtes non GET
    if method != "GET":
        body = request.body.decode('utf-8') if request.body else ""
        params_str = f"{url}:{method}:{body}"
    else:
        params_str = f"{url}:{method}"
    
    # Utiliser l'ID utilisateur s'il est authentifié
    user_id = request.user.id if request.user.is_authenticated else "anonymous"
    
    # Construire et retourner la clé de cache
    key_base = f"api_views:{view_name}:{user_id}:{params_str}"
    return hashlib.md5(key_base.encode()).hexdigest()


def api_cache(timeout=DEFAULT_CACHE_TTL, key_prefix=''):
    """
    Décorateur pour mettre en cache les réponses d'API.
    
    Args:
        timeout (int): Durée de validité du cache en secondes
        key_prefix (str): Préfixe optionnel pour la clé de cache
        
    Returns:
        function: Décorateur configuré
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view_instance, request, *args, **kwargs):
            # Ne pas utiliser le cache pour les méthodes non GET
            if request.method != 'GET':
                return view_func(view_instance, request, *args, **kwargs)
                
            # En mode DEBUG, utiliser un cache avec timeout réduit pour les tests
            cache_timeout = timeout if not settings.DEBUG else min(timeout, 60)
                
            # Générer la clé de cache
            cache_key = f"{key_prefix}:{get_cache_key(view_instance, request, *args, **kwargs)}"
            
            # Vérifier si la réponse est dans le cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response
                
            # Exécuter la vue si la réponse n'est pas en cache
            response = view_func(view_instance, request, *args, **kwargs)
            
            # Mettre en cache la réponse si elle est valide
            if response.status_code == 200:
                cache.set(cache_key, response, cache_timeout)
                
            return response
        return _wrapped_view
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalide toutes les clés de cache correspondant au motif.
    
    Args:
        pattern (str): Le motif de clés à invalider (ex: "api_views:Dashboard*")
    """
    # Note: Cette fonction est un placeholder car Django n'expose pas directement
    # la fonctionnalité de recherche par motif dans son API de cache.
    # En production, cela nécessiterait l'utilisation directe du client Redis
    pass


def monitor_cache_hit_rate(view_func):
    """
    Décorateur pour surveiller le taux de succès du cache.
    Utilisé pour fins de monitoring et optimisation.
    
    Args:
        view_func (function): La vue à monitorer
        
    Returns:
        function: Vue décorée
    """
    @wraps(view_func)
    def _wrapped_view(view_instance, request, *args, **kwargs):
        start_time = time.time()
        cache_key = get_cache_key(view_instance, request, *args, **kwargs)
        is_cached = cache.get(cache_key) is not None
        
        response = view_func(view_instance, request, *args, **kwargs)
        
        # Ajouter des en-têtes de diagnostic
        response['X-Cache'] = 'HIT' if is_cached else 'MISS'
        response['X-Cache-Lookup'] = 'HIT' if is_cached else 'MISS'
        response['X-Response-Time'] = str(round((time.time() - start_time) * 1000, 2)) + 'ms'
        
        return response
    return _wrapped_view


# Configuration des décorateurs de cache pour différents types de vues
def cache_dashboard_view():
    """Cache pour les vues de tableau de bord."""
    return api_cache(timeout=DASHBOARD_CACHE_TTL, key_prefix='dashboard')


def cache_topology_view():
    """Cache pour les vues de topologie."""
    return api_cache(timeout=TOPOLOGY_CACHE_TTL, key_prefix='topology')
    

def cache_search_view():
    """Cache pour les vues de recherche."""
    return api_cache(timeout=SEARCH_CACHE_TTL, key_prefix='search')


def cache_search_results():
    """Cache pour les résultats de recherche."""
    return api_cache(timeout=SEARCH_CACHE_TTL, key_prefix='search_results')


def cache_device_view():
    """Cache pour les vues d'équipements."""
    return api_cache(timeout=DEVICE_CACHE_TTL, key_prefix='device')


def cache_monitoring_view():
    """Cache pour les vues de monitoring."""
    return api_cache(timeout=MONITORING_CACHE_TTL, key_prefix='monitoring')