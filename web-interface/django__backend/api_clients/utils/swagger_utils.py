"""
Utilitaires pour la génération automatique de la documentation Swagger.

Ce module fournit des fonctions et décorateurs pour générer automatiquement
la documentation Swagger/OpenAPI pour les vues et ViewSets.
"""

import inspect
from functools import wraps
from typing import Type, Dict, Any, Callable, List, Optional, Union

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, action
from rest_framework.serializers import Serializer
from rest_framework.views import APIView


def apply_swagger_auto_schema(view_class: Type) -> Type:
    """
    Applique automatiquement des décorateurs swagger_auto_schema à une classe de vue.

    Cette fonction parcourt toutes les méthodes d'un ViewSet ou d'une APIView 
    et leur applique des décorateurs swagger_auto_schema avec des configurations 
    basées sur les serializers et docstrings.

    Args:
        view_class (Type): Classe de vue (ViewSet ou APIView) à décorer

    Returns:
        Type: La classe décorée
    """
    if not (issubclass(view_class, viewsets.ViewSet) or issubclass(view_class, APIView)):
        return view_class
    
    # Chercher les serializers définis dans la classe
    request_serializer = getattr(view_class, 'serializer_class', None)
    
    # Traitement des méthodes standard des ViewSets
    viewset_actions = {
        'list': {'method': 'GET', 'suffix': ''},
        'retrieve': {'method': 'GET', 'suffix': '{id}/'},
        'create': {'method': 'POST', 'suffix': ''},
        'update': {'method': 'PUT', 'suffix': '{id}/'},
        'partial_update': {'method': 'PATCH', 'suffix': '{id}/'},
        'destroy': {'method': 'DELETE', 'suffix': '{id}/'},
    }
    
    # Pour les ViewSets, traiter les méthodes standard (list, retrieve, create, etc.)
    if issubclass(view_class, viewsets.ViewSet):
        for action_name, action_info in viewset_actions.items():
            if hasattr(view_class, action_name):
                method = getattr(view_class, action_name)
                
                # Vérifier si la méthode a déjà un décorateur swagger_auto_schema
                if not hasattr(method, '_swagger_auto_schema'):
                    # Préparer des paramètres pour swagger_auto_schema
                    operation_summary = f"{action_info['method']} {view_class.__name__}"
                    operation_description = method.__doc__ or f"Endpoint {action_name}"
                    
                    # Appliquer le décorateur
                    decorated_method = swagger_auto_schema(
                        operation_summary=operation_summary,
                        operation_description=operation_description,
                        request_body=request_serializer,
                        responses={
                            200: openapi.Response(description="Succès"),
                            400: openapi.Response(description="Requête invalide"),
                            500: openapi.Response(description="Erreur serveur"),
                        },
                        tags=['API Clients']
                    )(method)
                    
                    # Remplacer la méthode d'origine par la méthode décorée
                    setattr(view_class, action_name, decorated_method)
    
    # Traiter les méthodes @action personnalisées
    for name, method in inspect.getmembers(view_class, inspect.isfunction):
        # Vérifier si c'est une méthode @action et si elle n'a pas encore de décorateur swagger
        if hasattr(method, 'mapping') and not hasattr(method, '_swagger_auto_schema'):
            http_methods = list(getattr(method, 'mapping', {}).keys())
            if http_methods:
                http_method = http_methods[0].upper()
                
                # Préparer des paramètres pour swagger_auto_schema
                operation_summary = f"{http_method} {name.replace('_', ' ').title()}"
                operation_description = method.__doc__ or f"Action personnalisée {name}"
                
                # Appliquer le décorateur
                decorated_method = swagger_auto_schema(
                    operation_summary=operation_summary,
                    operation_description=operation_description,
                    responses={
                        200: openapi.Response(description="Succès"),
                        400: openapi.Response(description="Requête invalide"),
                        500: openapi.Response(description="Erreur serveur"),
                    },
                    tags=['API Clients']
                )(method)
                
                # Remplacer la méthode d'origine par la méthode décorée
                setattr(view_class, name, decorated_method)
    
    return view_class


def auto_schema_viewset(cls):
    """
    Décorateur de classe pour appliquer automatiquement swagger_auto_schema à un ViewSet.
    
    Exemple d'utilisation:
        @auto_schema_viewset
        class MyViewSet(viewsets.ModelViewSet):
            ...
    
    Args:
        cls: La classe ViewSet à décorer
        
    Returns:
        La classe décorée
    """
    return apply_swagger_auto_schema(cls)


def generate_schema_for_all_views(views_module):
    """
    Décore automatiquement toutes les vues et ViewSets dans un module.
    
    Args:
        views_module: Module contenant des vues et ViewSets
        
    Returns:
        None
    """
    for name, obj in inspect.getmembers(views_module):
        # Vérifier si l'objet est une classe de type ViewSet ou APIView
        if inspect.isclass(obj) and (
            issubclass(obj, viewsets.ViewSet) or 
            issubclass(obj, APIView)
        ) and obj not in (viewsets.ViewSet, APIView):
            # Appliquer le décorateur
            apply_swagger_auto_schema(obj) 