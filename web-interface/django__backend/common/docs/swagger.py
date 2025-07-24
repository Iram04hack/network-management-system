"""
Configuration Swagger pour la documentation de l'API du module Common.

Ce module définit les métadonnées, schémas et configurations utilisés
par drf-yasg (Yet Another Swagger Generator) pour générer la documentation
OpenAPI/Swagger du module Common.
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Définition des tags Swagger pour le module Common
# Ces tags permettent de regrouper les endpoints par fonctionnalité dans la documentation
COMMON_TAGS = [
    'Audit',
    'Utilitaires',
    'Configuration'
]

# Métadonnées pour la documentation du module
COMMON_API_INFO = {
    'title': 'API Common',
    'description': (
        'Cette API fournit des fonctionnalités communes et transversales '
        'utilisées par tous les modules du système. Elle inclut notamment '
        'des endpoints pour accéder aux logs d\'audit, aux configurations '
        'globales et à diverses utilitaires partagés.'
    ),
    'version': '1.0.0',
    'contact': {
        'name': 'Équipe NMS',
        'email': 'support@nms.example.com'
    }
}

# Modèles de réponses communs pour la documentation Swagger
COMMON_RESPONSES = {
    'NotFound': openapi.Response(
        description='Ressource non trouvée',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                'code': openapi.Schema(type=openapi.TYPE_STRING, default='not_found'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default='La ressource demandée n\'a pas été trouvée.'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, default='NotFoundException')
            }
        )
    ),
    'ValidationError': openapi.Response(
        description='Erreur de validation',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                'code': openapi.Schema(type=openapi.TYPE_STRING, default='validation_error'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default='Erreur de validation.'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, default='ValidationException'),
                'details': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                )
            }
        )
    ),
    'ServerError': openapi.Response(
        description='Erreur serveur',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                'code': openapi.Schema(type=openapi.TYPE_STRING, default='server_error'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default='Une erreur inattendue s\'est produite.'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, default='NMSException')
            }
        )
    ),
    'PermissionDenied': openapi.Response(
        description='Permission refusée',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                'code': openapi.Schema(type=openapi.TYPE_STRING, default='permission_denied'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default='Vous n\'avez pas la permission d\'effectuer cette action.'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, default='PermissionException')
            }
        )
    )
}

# Décorateur pour simplifier la documentation des vues
def common_swagger_auto_schema(method='get', operation_summary=None, operation_description=None, tags=None,
                             request_body=None, query_serializer=None, responses=None, manual_parameters=None,
                             deprecated=False):
    """
    Décorateur pour simplifier la documentation des vues du module common.
    
    Args:
        method: Méthode HTTP concernée ('get', 'post', 'put', 'patch', 'delete')
        operation_summary: Résumé court de l'opération
        operation_description: Description détaillée de l'opération
        tags: Tags Swagger pour cette opération
        request_body: Schéma du corps de la requête
        query_serializer: Serializer pour les paramètres de requête
        responses: Dictionnaire des réponses possibles
        manual_parameters: Paramètres manuels supplémentaires
        deprecated: Si l'endpoint est déprécié
        
    Returns:
        Décorateur swagger_auto_schema pré-configuré
    """
    # Ajouter le tag Common par défaut si aucun tag n'est spécifié
    if tags is None:
        tags = ['Common']
        
    # Fusionner les réponses spécifiques avec les réponses communes
    all_responses = {
        '404': COMMON_RESPONSES['NotFound'],
        '400': COMMON_RESPONSES['ValidationError'],
        '403': COMMON_RESPONSES['PermissionDenied'],
        '500': COMMON_RESPONSES['ServerError']
    }
    
    # Ajouter les réponses spécifiques
    if responses:
        all_responses.update(responses)
        
    return swagger_auto_schema(
        method=method,
        operation_summary=operation_summary,
        operation_description=operation_description,
        tags=tags,
        request_body=request_body,
        query_serializer=query_serializer,
        responses=all_responses,
        manual_parameters=manual_parameters,
        deprecated=deprecated
    )


# Définitions de schémas pour les exceptions communes
exception_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
        'code': openapi.Schema(type=openapi.TYPE_STRING),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'type': openapi.Schema(type=openapi.TYPE_STRING),
        'details': openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True)
    },
    required=['error', 'code', 'message']
)

# Paramètres de requête communs
pagination_parameters = [
    openapi.Parameter(
        'page', openapi.IN_QUERY, 
        description="Numéro de page", 
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'page_size', openapi.IN_QUERY, 
        description="Nombre d'éléments par page", 
        type=openapi.TYPE_INTEGER
    )
]

ordering_parameters = [
    openapi.Parameter(
        'ordering', openapi.IN_QUERY,
        description="Champ(s) de tri (préfixer par '-' pour ordre décroissant, ex: '-created_at')",
        type=openapi.TYPE_STRING
    )
]

search_parameters = [
    openapi.Parameter(
        'search', openapi.IN_QUERY,
        description="Terme de recherche global",
        type=openapi.TYPE_STRING
    )
]

# Combinaisons de paramètres courantes pour les vues de liste
list_parameters = pagination_parameters + ordering_parameters + search_parameters 