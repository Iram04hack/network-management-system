"""
Décorateurs pour les vues API Clients.

Ce module contient des fonctions pour appliquer automatiquement
les décorateurs Swagger aux vues du module api_clients.
"""

import inspect
from functools import wraps
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

def decorate_all_views(module):
    """
    Applique les décorateurs Swagger à toutes les vues d'un module.
    
    Cette fonction est utilisée pour appliquer automatiquement les
    décorateurs Swagger aux vues du module api_clients.
    
    Args:
        module: Le module contenant les vues à décorer
    """
    # Désactivé temporairement pour résoudre les problèmes de syntaxe
    print("Décorateurs Swagger temporairement désactivés pour résoudre les problèmes de syntaxe")
    return
    
    # Code original commenté
    """
    # Trouver toutes les classes de ViewSet dans le module
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, viewsets.ViewSet) and obj != viewsets.ViewSet:
            # Parcourir toutes les méthodes du ViewSet
            for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                if method_name in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
                    # Vérifier si la méthode a déjà un décorateur swagger_auto_schema
                    if not hasattr(method, '_swagger_auto_schema'):
                        # Appliquer le décorateur par défaut
                        setattr(obj, method_name, swagger_auto_schema(
                            operation_description=f"Opération {method_name} pour {name}",
                            tags=['clients']
                        )(method))
    """
