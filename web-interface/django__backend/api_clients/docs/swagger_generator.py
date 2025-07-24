"""
Générateur de documentation Swagger pour les clients API.

Ce module fournit des décorateurs et des utilitaires pour générer
automatiquement une documentation Swagger/OpenAPI pour les clients API.
"""

import inspect
import json
import os
from functools import wraps
from typing import Any, Dict, List, Optional, Callable, Type, Union

# Chemin du répertoire de sortie pour les fichiers de documentation
SWAGGER_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "swagger_output")

# Assurez-vous que le répertoire existe
if not os.path.exists(SWAGGER_OUTPUT_DIR):
    try:
        os.makedirs(SWAGGER_OUTPUT_DIR)
        print(f"Répertoire créé : {SWAGGER_OUTPUT_DIR}")
    except Exception as e:
        print(f"Erreur lors de la création du répertoire : {e}")
        # Utiliser un répertoire temporaire si celui-ci ne peut pas être créé
        import tempfile
        SWAGGER_OUTPUT_DIR = tempfile.gettempdir()
        print(f"Utilisation du répertoire temporaire : {SWAGGER_OUTPUT_DIR}")

class SwaggerEndpoint:
    """
    Représente un point de terminaison API pour la documentation Swagger.
    """
    def __init__(
        self,
        path: str,
        method: str,
        summary: str,
        description: str,
        tags: List[str],
        parameters: List[Dict[str, Any]],
        responses: Dict[str, Dict[str, Any]],
        request_body: Optional[Dict[str, Any]] = None
    ):
        self.path = path
        self.method = method.lower()
        self.summary = summary
        self.description = description
        self.tags = tags
        self.parameters = parameters
        self.responses = responses
        self.request_body = request_body

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'endpoint en dictionnaire pour Swagger.
        """
        result = {
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "responses": self.responses,
        }

        if self.parameters:
            result["parameters"] = self.parameters

        if self.request_body:
            result["requestBody"] = self.request_body

        return result

class SwaggerSpec:
    """
    Générateur de spécification Swagger/OpenAPI.
    """
    def __init__(
        self,
        title: str,
        description: str,
        version: str = "1.0.0"
    ):
        self.title = title
        self.description = description
        self.version = version
        self.endpoints: Dict[str, Dict[str, SwaggerEndpoint]] = {}

    def add_endpoint(self, endpoint: SwaggerEndpoint) -> None:
        """
        Ajoute un endpoint à la spécification.
        """
        if endpoint.path not in self.endpoints:
            self.endpoints[endpoint.path] = {}
        
        self.endpoints[endpoint.path][endpoint.method] = endpoint

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit la spécification en dictionnaire pour Swagger.
        """
        paths = {}
        for path, methods in self.endpoints.items():
            paths[path] = {}
            for method, endpoint in methods.items():
                paths[path][method] = endpoint.to_dict()

        return {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "description": self.description,
                "version": self.version
            },
            "paths": paths
        }

    def save(self, filename: str) -> None:
        """
        Sauvegarde la spécification dans un fichier JSON.
        """
        output_path = os.path.join(SWAGGER_OUTPUT_DIR, filename)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

def swagger_doc(
    path: str,
    method: str,
    summary: str,
    description: str,
    tags: List[str],
    parameters: Optional[List[Dict[str, Any]]] = None,
    responses: Optional[Dict[str, Dict[str, Any]]] = None,
    request_body: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    Décorateur pour documenter une méthode API.
    
    Args:
        path: Chemin de l'endpoint
        method: Méthode HTTP (GET, POST, etc.)
        summary: Résumé court de l'endpoint
        description: Description détaillée de l'endpoint
        tags: Tags de catégorisation
        parameters: Paramètres de l'endpoint
        responses: Réponses possibles
        request_body: Corps de la requête si applicable
        
    Returns:
        La fonction décorée
    """
    if parameters is None:
        parameters = []
    if responses is None:
        responses = {
            "200": {
                "description": "Opération réussie"
            },
            "400": {
                "description": "Requête invalide"
            },
            "500": {
                "description": "Erreur serveur"
            }
        }

    def decorator(func):
        # Stocker les métadonnées Swagger sur la fonction
        func._swagger_metadata = {
            "endpoint": SwaggerEndpoint(
                path=path,
                method=method,
                summary=summary,
                description=description,
                tags=tags,
                parameters=parameters,
                responses=responses,
                request_body=request_body
            )
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def generate_swagger_for_class(
    client_class: Type,
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: str = "1.0.0",
    output_filename: Optional[str] = None
) -> SwaggerSpec:
    """
    Génère une spécification Swagger pour une classe de client API.
    
    Args:
        client_class: Classe du client API
        title: Titre de la documentation
        description: Description de l'API
        version: Version de l'API
        output_filename: Nom du fichier de sortie
        
    Returns:
        La spécification Swagger générée
    """
    if title is None:
        title = f"API {client_class.__name__}"
    
    if description is None:
        description = client_class.__doc__ or f"Documentation API pour {client_class.__name__}"
    
    if output_filename is None:
        output_filename = f"{client_class.__name__.lower()}_swagger.json"
    
    swagger = SwaggerSpec(title=title, description=description, version=version)
    
    # Parcourir toutes les méthodes de la classe
    for name, method in inspect.getmembers(client_class, predicate=inspect.isfunction):
        if hasattr(method, '_swagger_metadata'):
            endpoint = method._swagger_metadata['endpoint']
            swagger.add_endpoint(endpoint)
    
    # Sauvegarder la spécification dans un fichier
    swagger.save(output_filename)
    
    return swagger 