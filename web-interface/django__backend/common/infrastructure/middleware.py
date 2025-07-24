"""
Middlewares Django pour la sécurité, la gestion d'erreurs et l'audit.

Ce module fournit des middlewares pour:
- Ajouter des en-têtes de sécurité HTTP appropriés
- Intercepter et convertir les exceptions en réponses JSON cohérentes
- Journaliser les actions importantes des utilisateurs
"""
import json
import logging
import traceback
from typing import Dict, Any, Optional, Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from common.domain.exceptions import (
    NMSException, ServiceException, ValidationException,
    PermissionException, ResourceException, NetworkException,
    SecurityException, NotFoundException, ServiceUnavailableException,
    UnauthorizedException, ConflictException, RateLimitedException, TimeoutException
)
from common.infrastructure.models import AuditLogEntry

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware pour ajouter des en-têtes de sécurité HTTP.
    
    Ajoute systématiquement les en-têtes de sécurité recommandés
    pour protéger contre les attaques XSS, le clickjacking, le MIME-sniffing, 
    et autres vulnérabilités web courantes.
    
    En mode production, des en-têtes supplémentaires sont ajoutés
    pour renforcer la sécurité (HSTS, CSP).
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Ajoute les en-têtes de sécurité à chaque réponse HTTP.
        
        Args:
            request: Requête HTTP entrante
            response: Réponse HTTP sortante
            
        Returns:
            HttpResponse: Réponse avec les en-têtes de sécurité ajoutés
        """
        # Protection contre le MIME-sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Protection contre le clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Protection contre les attaques XSS
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Politique de référence pour contrôler les informations de provenance
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # En mode production, ajouter des en-têtes supplémentaires
        if not settings.DEBUG:
            # Strict-Transport-Security pour forcer HTTPS
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # Content-Security-Policy pour limiter les sources de contenu
            csp_policies = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "form-action 'self'",
                "base-uri 'self'",
                "object-src 'none'"
            ]
            response.headers['Content-Security-Policy'] = "; ".join(csp_policies)
            
            # Feature-Policy pour limiter les fonctionnalités du navigateur
            response.headers['Permissions-Policy'] = (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), accelerometer=(), gyroscope=()"
            )
            
        return response


class ExceptionHandlerMiddleware:
    """
    Middleware pour intercepter et gérer les exceptions du système NMS.
    Fournit une réponse JSON cohérente pour toutes les erreurs.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        return self.get_response(request)
        
    def process_exception(self, request, exception):
        """
        Traite l'exception et renvoie une réponse JSON appropriée.
        
        Args:
            request: La requête HTTP
            exception: L'exception levée
            
        Returns:
            JsonResponse avec les détails de l'erreur
        """
        if isinstance(exception, NMSException):
            # Journaliser l'exception avec un niveau approprié
            if isinstance(exception, (ValidationException, NotFoundException)):
                logger.info(f"{exception.__class__.__name__}: {exception.message}")
            else:
                logger.error(f"{exception.__class__.__name__}: {exception.message}")
                
            return JsonResponse({
                'error': True,
                'code': exception.code,
                'message': exception.message,
                'details': exception.details
            }, status=self._get_status_code(exception))
            
        # Exception non gérée, journaliser avec le stack trace complet
        logger.exception("Exception non gérée")
        
        # En production, ne pas exposer les détails internes
        return JsonResponse({
            'error': True,
            'code': 'server_error',
            'message': 'Une erreur interne est survenue.'
        }, status=500)
    
    def _get_status_code(self, exception):
        """
        Détermine le code de statut HTTP approprié pour l'exception.
        
        Args:
            exception: L'exception NMS
            
        Returns:
            Code de statut HTTP (int)
        """
        exception_to_status = {
            ValidationException: 400,
            NotFoundException: 404,
            UnauthorizedException: 401,
            PermissionException: 403,
            ServiceUnavailableException: 503,
            ConflictException: 409,
            RateLimitedException: 429,
            TimeoutException: 504
        }
        
        for exc_class, status in exception_to_status.items():
            if isinstance(exception, exc_class):
                return status
                
        return 500  # Cas par défaut


class AuditMiddleware:
    """
    Middleware pour journaliser les actions importantes des utilisateurs.
    
    Enregistre les opérations de modification (POST, PUT, PATCH, DELETE)
    effectuées par les utilisateurs authentifiés pour maintenir une piste
    d'audit complète.
    """
    
    def __init__(self, get_response: Callable):
        """
        Initialise le middleware.
        
        Args:
            get_response: Fonction pour obtenir la réponse
        """
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Méthode principale appelée pour chaque requête.
        
        Args:
            request: Requête HTTP entrante
            
        Returns:
            HttpResponse: Réponse HTTP
        """
        return self.get_response(request)
    
    def process_view(self, request: HttpRequest, view_func: Callable, view_args: list, view_kwargs: dict) -> None:
        """
        Journalise les informations sur les vues accédées.
        
        Args:
            request: Requête HTTP
            view_func: Fonction de vue à appeler
            view_args: Arguments positionnels pour la vue
            view_kwargs: Arguments nommés pour la vue
            
        Returns:
            None: Ne modifie pas la chaîne de traitement
        """
        # Ne pas journaliser les requêtes statiques ou les requêtes anonymes
        if (request.path.startswith('/static/') or request.path.startswith('/media/')
                or not request.user.is_authenticated):
            return None
            
        # Journaliser uniquement les requêtes de modification (POST, PUT, PATCH, DELETE)
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return None
            
        # Extraire les informations pertinentes
        user = request.user
        method = request.method
        path = request.path
        
        # Déterminer le type d'action
        action_map = {
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        action = action_map.get(method, 'other')
        
        # Essayer d'extraire le type d'objet et l'ID de l'URL
        object_type = view_func.__module__ if hasattr(view_func, '__module__') else ''
        if hasattr(view_func, '__name__'):
            object_type += '.' + view_func.__name__
        
        object_id = ''
        if 'pk' in view_kwargs:
            object_id = str(view_kwargs['pk'])
        elif 'id' in view_kwargs:
            object_id = str(view_kwargs['id'])
            
        # Préparer les détails
        details = {
            'method': method,
            'path': path,
            'view': object_type
        }
        
        # Ajouter des données POST/PUT filtrées (sans mots de passe)
        if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'data'):
            # Pour DRF
            data_copy = request.data.copy() if hasattr(request.data, 'copy') else {}
            # Filtrer les données sensibles
            for key in list(data_copy.keys()):
                if 'password' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                    data_copy[key] = '***FILTERED***'
            details['data'] = data_copy
        
        # Journaliser l'action
        logger.info(
            f"Audit: {user.username} a effectué une requête {method} sur {path}",
            extra={
                "user": user.username,
                "user_id": user.id,
                "method": method,
                "path": path,
                "object_type": object_type,
                "object_id": object_id,
                "ip": self._get_client_ip(request)
            }
        )
        
        # Enregistrer dans la base de données
        try:
            AuditLogEntry.objects.create(
                user=user,
                action=action,
                object_type=object_type,
                object_id=object_id,
                details=details,
                ip_address=self._get_client_ip(request),
                created_by=user,
                updated_by=user
            )
        except Exception as e:
            # Ne pas laisser une erreur d'audit bloquer l'application
            logger.error(f"Erreur d'enregistrement d'audit: {str(e)}", exc_info=True)
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> Optional[str]:
        """
        Extrait l'adresse IP du client en tenant compte des proxys.
        
        Args:
            request: Requête HTTP
            
        Returns:
            str: Adresse IP du client, ou None si non déterminée
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Prendre la première adresse IP (celle du client d'origine)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 