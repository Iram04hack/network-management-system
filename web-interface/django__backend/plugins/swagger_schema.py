"""
Schéma Swagger pour l'API du module plugins.

Ce module fournit les définitions de schéma nécessaires pour la
génération automatique de la documentation de l'API avec Swagger.
"""
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.urls import path
from rest_framework import permissions

# Création du schéma Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Plugins API",
        default_version='v1',
        description="API pour le système de plugins extensible",
        terms_of_service="https://www.network-management-system.com/terms/",
        contact=openapi.Contact(email="contact@network-management-system.com"),
        license=openapi.License(name="Licence propriétaire"),
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)

# Définition des modèles pour la documentation
plugin_metadata_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_STRING, description='Identifiant unique du plugin'),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom lisible du plugin'),
        'version': openapi.Schema(type=openapi.TYPE_STRING, description='Version du plugin'),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description du plugin'),
        'author': openapi.Schema(type=openapi.TYPE_STRING, description='Auteur du plugin'),
        'dependencies': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description='Liste des identifiants des plugins dont dépend ce plugin'
        ),
        'provides': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description='Liste des fonctionnalités fournies par ce plugin'
        ),
    }
)

alert_handler_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indique si le traitement a réussi'),
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Message d\'erreur en cas d\'échec'),
        'recipients': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de destinataires (pour les notifications)'),
        'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='Code de statut HTTP (pour les webhooks)'),
    }
)

plugin_list_response_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=plugin_metadata_schema
)

# URLs pour la documentation Swagger
swagger_urls = [
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Définitions des opérations pour l'API REST
plugin_operations = {
    'list': {
        'operation_id': 'listPlugins',
        'responses': {
            200: openapi.Response(
                description='Liste des plugins disponibles',
                schema=plugin_list_response_schema
            )
        },
        'parameters': [
            openapi.Parameter(
                'plugin_type',
                openapi.IN_QUERY,
                description='Filtre par type de plugin (ex: alert_handlers)',
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        'tags': ['plugins']
    },
    'retrieve': {
        'operation_id': 'retrievePlugin',
        'responses': {
            200: openapi.Response(
                description='Détails du plugin',
                schema=plugin_metadata_schema
            ),
            404: openapi.Response(
                description='Plugin non trouvé'
            )
        },
        'parameters': [
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description='Identifiant du plugin',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        'tags': ['plugins']
    },
    'handle_alert': {
        'operation_id': 'handleAlert',
        'responses': {
            200: openapi.Response(
                description='Résultat du traitement de l\'alerte',
                schema=alert_handler_response_schema
            ),
            400: openapi.Response(
                description='Requête invalide'
            )
        },
        'parameters': [
            openapi.Parameter(
                'alert_data',
                openapi.IN_BODY,
                description='Données de l\'alerte',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'alert_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Identifiant de l\'alerte'),
                        'alert_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type d\'alerte (security ou monitoring)'),
                    },
                    required=['alert_id', 'alert_type']
                )
            )
        ],
        'tags': ['alerts']
    }
} 