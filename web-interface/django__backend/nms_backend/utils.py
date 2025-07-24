# nms_backend/utils.py
import hashlib
import logging
import time
import traceback
from datetime import datetime
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import Http404
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import (
    APIException, AuthenticationFailed, NotAuthenticated, PermissionDenied,
    ValidationError
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('django')

def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé qui :
    1. Enregistre l'erreur dans les logs
    2. Renvoie une réponse JSON formatée de manière cohérente
    3. Masque les détails techniques en production
    """
    # Appel du gestionnaire d'erreurs par défaut de DRF
    response = exception_handler(exc, context)

    # Si le gestionnaire par défaut ne renvoie pas de réponse, créer une réponse personnalisée
    if response is None:
        # Pour les erreurs 404
        if isinstance(exc, Http404):
            response = Response(
                {'detail': _('Ressource non trouvée')},
                status=status.HTTP_404_NOT_FOUND
            )
        # Pour les erreurs internes
        else:
            # Journaliser l'erreur
            logger.error(
                f"Exception non gérée: {str(exc)}\n"
                f"Context: {context}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # En production, masquer les détails d'erreur
            if not settings.DEBUG:
                response = Response(
                    {'detail': _('Une erreur interne est survenue.')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                # En mode DEBUG, inclure plus de détails
                response = Response(
                    {
                        'detail': _('Une erreur interne est survenue.'),
                        'exception': str(exc),
                        'traceback': traceback.format_exc().splitlines()
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    # Ajouter des informations communes à toutes les réponses d'erreur
    if response is not None:
        if not hasattr(response, 'data') or not isinstance(response.data, dict):
            response.data = {'detail': str(response.data) if response.data else 'Erreur'}
            
        response.data['status_code'] = response.status_code
        response.data['timestamp'] = datetime.now().isoformat()
        
        # Si on a un utilisateur authentifié, ajouter son ID
        if hasattr(context['request'], 'user') and context['request'].user.is_authenticated:
            response.data['user_id'] = context['request'].user.id
            
        # Ajouter le type d'erreur
        if isinstance(exc, ValidationError):
            response.data['error_type'] = 'validation_error'
        elif isinstance(exc, AuthenticationFailed) or isinstance(exc, NotAuthenticated):
            response.data['error_type'] = 'authentication_error'
        elif isinstance(exc, PermissionDenied):
            response.data['error_type'] = 'permission_error'
        elif isinstance(exc, Http404):
            response.data['error_type'] = 'not_found'
        elif isinstance(exc, APIException):
            response.data['error_type'] = 'api_error'
        else:
            response.data['error_type'] = 'server_error'
            
        # Log l'erreur pour le monitoring
        if response.status_code >= 500:
            logger.error(f"API Error [{response.status_code}]: {response.data.get('detail')}")
        elif response.status_code >= 400:
            logger.warning(f"API Warning [{response.status_code}]: {response.data.get('detail')}")
    
    return response

def make_key(key, key_prefix, version):
    """
    Fonction personnalisée pour générer les clés de cache.
    Cette fonction utilise hashlib pour garantir que les clés de cache ne dépassent pas
    la limite de taille et sont uniformes.
    """
    return ':'.join([
        key_prefix,
        str(version),
        hashlib.md5(force_bytes(key)).hexdigest()
    ])

def cache_response(timeout=None, cache_alias='default', key_prefix='view'):
    """
    Décorateur pour mettre en cache les réponses des fonctions de vue,
    adapté pour les vues de l'API REST Framework.
    
    Usage:
        @cache_response(timeout=60 * 15)  # Cache pour 15 minutes
        def my_view_method(self, request, *args, **kwargs):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Générer une clé unique basée sur la vue, la méthode HTTP, et les paramètres
            cache_key = f"{key_prefix}:{request.path}:{request.method}:{hashlib.md5(force_bytes(request.query_params.urlencode())).hexdigest()}"
            
            # Si l'utilisateur est authentifié, ajouter son ID à la clé pour éviter de servir des contenus en cache d'un utilisateur à un autre
            if hasattr(request, 'user') and request.user.is_authenticated:
                cache_key = f"{cache_key}:user_{request.user.id}"
            
            # Vérifier si la réponse est déjà en cache
            response = cache.get(cache_key)
            if response is not None:
                return response
            
            # Si pas en cache, exécuter la vue
            response = view_func(self, request, *args, **kwargs)
            
            # Mettre en cache uniquement les réponses réussies (2xx)
            if 200 <= response.status_code < 300:
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator

def query_debugger(func):
    """
    Décorateur pour mesurer et journaliser le nombre de requêtes SQL
    et le temps d'exécution d'une fonction.
    
    Usage:
        @query_debugger
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        query_count = len(connection.queries)
        query_time = sum(float(q['time']) for q in connection.queries)
        
        slow_query_threshold = getattr(settings, 'PERFORMANCE', {}).get('SLOW_QUERY_THRESHOLD_MS', 500) / 1000
        
        if query_time > slow_query_threshold:
            logger.warning(
                f"Fonction {func.__name__} a exécuté {query_count} requêtes en {query_time:.3f}s "
                f"(durée totale: {end - start:.3f}s) - PERFORMANCE LENTE DÉTECTÉE"
            )
            
            # Log des requêtes individuelles lentes
            for i, query in enumerate(connection.queries):
                if float(query['time']) > slow_query_threshold / 10:  # Requêtes 10x plus lentes que le seuil divisé par 10
                    logger.warning(f"Requête lente #{i}: {query['sql']} - {query['time']}s")
        else:
            logger.debug(
                f"Fonction {func.__name__} a exécuté {query_count} requêtes en {query_time:.3f}s "
                f"(durée totale: {end - start:.3f}s)"
            )
            
        return result
    return wrapper

def reset_queries():
    """Réinitialise les requêtes SQL enregistrées"""
    if hasattr(connection, 'queries'):
        connection.queries_log.clear()
        
def format_duration(seconds):
    """Formate une durée en secondes en format lisible"""
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} μs"  # Microsecondes
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"  # Millisecondes
    else:
        return f"{seconds:.2f} s"  # Secondes 