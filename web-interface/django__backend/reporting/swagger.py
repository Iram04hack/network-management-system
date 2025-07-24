"""
Configuration Swagger pour la documentation d'API du module reporting.

Ce module configure la documentation OpenAPI/Swagger pour l'API de reporting
en utilisant drf-yasg.
"""

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path

# Métadonnées de la documentation
schema_view = get_schema_view(
    openapi.Info(
        title="API de Reporting",
        default_version='v1',
        description="API pour la gestion des rapports et des analyses du système de gestion de réseau",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)

# Endpoints Swagger
urlpatterns = [
    path('swagger<str:format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Schémas de reports
report_schema = {
    "Report": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Identifiant unique du rapport"
            },
            "title": {
                "type": "string",
                "description": "Titre du rapport"
            },
            "description": {
                "type": "string",
                "description": "Description détaillée du rapport"
            },
            "report_type": {
                "type": "string",
                "enum": ["network", "security", "performance", "audit", "custom"],
                "description": "Type de rapport"
            },
            "status": {
                "type": "string",
                "enum": ["draft", "processing", "completed", "failed"],
                "description": "Statut du rapport"
            },
            "content": {
                "type": "object",
                "description": "Contenu du rapport"
            },
            "file_path": {
                "type": "string",
                "description": "Chemin du fichier généré"
            },
            "created_by": {
                "type": "integer",
                "description": "ID de l'utilisateur qui a créé le rapport"
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "Date de création du rapport"
            },
            "template_id": {
                "type": "integer",
                "description": "ID du template utilisé (optionnel)"
            }
        },
        "required": ["title", "report_type"]
    }
}

# Documentation des endpoints spécifiques
report_list_schema = {
    "operation_id": "report_list",
    "responses": {
        "200": {
            "description": "Liste des rapports",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Report"}
                    }
                }
            }
        }
    },
    "parameters": [
        {
            "name": "report_type",
            "in": "query",
            "description": "Filtrer par type de rapport",
            "required": False,
            "schema": {"type": "string"}
        },
        {
            "name": "status",
            "in": "query",
            "description": "Filtrer par statut",
            "required": False,
            "schema": {"type": "string"}
        },
        {
            "name": "search",
            "in": "query",
            "description": "Recherche textuelle",
            "required": False,
            "schema": {"type": "string"}
        }
    ],
    "tags": ["reports"]
}

# Documentation pour la création de rapport
report_create_schema = {
    "operation_id": "report_create",
    "responses": {
        "201": {
            "description": "Rapport créé avec succès",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Report"}
                }
            }
        },
        "400": {
            "description": "Données invalides"
        }
    },
    "requestBody": {
        "description": "Données du rapport à créer",
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/Report"}
            }
        }
    },
    "tags": ["reports"]
}

# Documentation pour la régénération de rapport
report_regenerate_schema = {
    "operation_id": "report_regenerate",
    "responses": {
        "200": {
            "description": "Rapport régénéré avec succès",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Report"}
                }
            }
        },
        "404": {
            "description": "Rapport non trouvé"
        },
        "500": {
            "description": "Erreur lors de la génération"
        }
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "description": "ID du rapport à régénérer",
            "required": True,
            "schema": {"type": "integer"}
        }
    ],
    "tags": ["reports"]
} 