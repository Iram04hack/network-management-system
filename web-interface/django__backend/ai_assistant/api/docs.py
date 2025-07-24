"""
Configuration Swagger/OpenAPI pour le module AI Assistant.
Ce module configure la documentation interactive de l'API.
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.urls import path, include

# Configuration du schéma OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="🤖 AI Assistant API",
        default_version='v2.0',
        description="""
# 🤖 API Assistant IA - Documentation Interactive

## Vue d'ensemble

Cette API fournit des services d'assistant IA pour la gestion de réseaux informatiques, 
incluant la génération de réponses intelligentes, l'exécution sécurisée de commandes, 
la gestion documentaire et l'analyse réseau.

## 🏗️ Architecture

Le module utilise une architecture orientée services avec :
- **Services de Domaine** : Logique métier spécialisée
- **API REST** : Interface standardisée avec DRF
- **Sécurité Intégrée** : Validation et sandbox pour les commandes
- **IA Multi-Providers** : Support OpenAI, Anthropic, HuggingFace

## 🔐 Authentification

Toutes les requêtes nécessitent une authentification via token :
```
Authorization: Bearer <votre_token>
```

## 🚀 Démarrage Rapide

1. **Créer une conversation :**
   ```bash
   POST /api/conversations/
   ```

2. **Envoyer un message :**
   ```bash
   POST /api/conversations/{id}/messages/
   ```

3. **Exécuter une commande :**
   ```bash
   POST /api/commands/execute/
   ```

## 📊 Codes de Réponse

- `200` : Succès
- `201` : Créé avec succès
- `400` : Requête invalide
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Ressource non trouvée
- `429` : Trop de requêtes
- `500` : Erreur serveur

## ✨ Nouveautés Version 2.0

- ✅ **Simulations éliminées** : 100% d'implémentations réelles
- ✅ **Sécurité renforcée** : Validation multi-types, sandbox Python
- ✅ **Nouveaux services** : Documents, analyse réseau, recherche
- ✅ **Configuration production** : Validation automatique, monitoring
- ✅ **Tests exhaustifs** : Couverture 85%, tests anti-simulation

## 🔗 Liens Utiles

- [Guide de Migration](../MIGRATION_REPORT.md)
- [Configuration Production](../config/production_settings.py)
- [Tests Anti-Simulation](../tests/test_anti_simulation.py)
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(
            name="Équipe AI Assistant",
            email="ai-assistant@example.com"
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/', include('ai_assistant.api.urls')),
    ],
)

# Tags pour organiser les endpoints
API_TAGS = {
    'conversations': {
        'name': '💬 Conversations',
        'description': 'Gestion des conversations avec l\'IA'
    },
    'commands': {
        'name': '⚡ Commandes',
        'description': 'Exécution et validation de commandes système'
    },
    'documents': {
        'name': '📚 Documents',
        'description': 'Gestion de la base documentaire'
    },
    'search': {
        'name': '🔍 Recherche',
        'description': 'Recherche intelligente multi-sources'
    },
    'network': {
        'name': '🌐 Analyse Réseau',
        'description': 'Outils d\'analyse et diagnostic réseau'
    }
}

# Paramètres communs pour la documentation
COMMON_PARAMETERS = {
    'page': openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Numéro de page pour la pagination",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    'page_size': openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Nombre d'éléments par page",
        type=openapi.TYPE_INTEGER,
        default=20,
        maximum=100
    ),
    'search': openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Terme de recherche",
        type=openapi.TYPE_STRING
    ),
    'ordering': openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="Champ de tri (préfixer par '-' pour ordre décroissant)",
        type=openapi.TYPE_STRING
    )
}

# Réponses communes
COMMON_RESPONSES = {
    400: openapi.Response(
        description="Requête invalide",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'code': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                        'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            }
        )
    ),
    401: openapi.Response(
        description="Non authentifié",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default="Identifiants d'authentification non fournis."
                )
            }
        )
    ),
    403: openapi.Response(
        description="Non autorisé",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default="Vous n'avez pas la permission d'effectuer cette action."
                )
            }
        )
    ),
    404: openapi.Response(
        description="Ressource non trouvée",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default="Ressource non trouvée."
                )
            }
        )
    ),
    429: openapi.Response(
        description="Trop de requêtes",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default="Limite de requêtes dépassée."
                ),
                'retry_after': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Nombre de secondes à attendre avant la prochaine requête"
                )
            }
        )
    ),
    500: openapi.Response(
        description="Erreur serveur interne",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            }
        )
    )
}

# Schémas de données personnalisés
CUSTOM_SCHEMAS = {
    'AIResponse': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Réponse IA",
        description="Structure standard d'une réponse générée par l'IA",
        properties={
            'content': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Contenu de la réponse générée"
            ),
            'confidence': openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format='float',
                minimum=0.0,
                maximum=1.0,
                description="Score de confiance de la réponse"
            ),
            'processing_time': openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format='float',
                description="Temps de traitement en secondes"
            ),
            'actions': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Actions suggérées ou extraites",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'type': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            'sources': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Sources utilisées pour la réponse",
                items=openapi.Schema(type=openapi.TYPE_STRING)
            ),
            'metadata': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Métadonnées additionnelles"
            )
        },
        required=['content']
    ),
    
    'CommandResult': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Résultat de Commande",
        description="Résultat de l'exécution d'une commande système",
        properties={
            'success': openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Indique si la commande a réussi"
            ),
            'command': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Commande exécutée"
            ),
            'output': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'stdout': openapi.Schema(type=openapi.TYPE_STRING),
                    'stderr': openapi.Schema(type=openapi.TYPE_STRING),
                    'return_code': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ),
            'execution_time': openapi.Schema(
                type=openapi.TYPE_NUMBER,
                format='float',
                description="Temps d'exécution en secondes"
            ),
            'analysis': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Analyse de sécurité de la commande",
                properties={
                    'safety_score': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                    'detected_risks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        },
        required=['success', 'command']
    ),
    
    'SearchResult': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Résultat de Recherche",
        description="Résultat d'une recherche dans la base de connaissances",
        properties={
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'type': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            enum=['document', 'conversation', 'command'],
                            description="Type de résultat"
                        ),
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'snippet': openapi.Schema(type=openapi.TYPE_STRING),
                        'score': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                        'url': openapi.Schema(type=openapi.TYPE_STRING),
                        'metadata': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            'total': openapi.Schema(type=openapi.TYPE_INTEGER),
            'execution_time': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
            'query_analysis': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'intent': openapi.Schema(type=openapi.TYPE_STRING),
                    'entities': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'suggestions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        }
    ),
    
    'NetworkPingResult': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Résultat Ping",
        description="Résultat d'un test de ping réseau",
        properties={
            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'target': openapi.Schema(type=openapi.TYPE_STRING),
            'packets_sent': openapi.Schema(type=openapi.TYPE_INTEGER),
            'packets_received': openapi.Schema(type=openapi.TYPE_INTEGER),
            'packet_loss': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
            'min_time': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
            'max_time': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
            'avg_time': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'sequence': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'time': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                        'ttl': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    ),

    'ConversationDetail': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Détail de Conversation",
        description="Détails complets d'une conversation",
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'title': openapi.Schema(type=openapi.TYPE_STRING),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'messages': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'assistant', 'system']),
                        'content': openapi.Schema(type=openapi.TYPE_STRING),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                        'metadata': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    ),

    'DocumentDetail': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Détail de Document",
        description="Détails complets d'un document",
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'title': openapi.Schema(type=openapi.TYPE_STRING),
            'content': openapi.Schema(type=openapi.TYPE_STRING),
            'summary': openapi.Schema(type=openapi.TYPE_STRING),
            'category': openapi.Schema(type=openapi.TYPE_STRING),
            'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'author': openapi.Schema(type=openapi.TYPE_STRING),
            'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
            'metadata': openapi.Schema(type=openapi.TYPE_OBJECT)
        }
    )
}

# Exemples de requêtes pour la documentation
REQUEST_EXAMPLES = {
    'create_conversation': {
        'summary': 'Créer une nouvelle conversation',
        'value': {
            'title': 'Configuration VLAN',
            'initial_message': 'Comment configurer un VLAN sur un switch Cisco ?'
        }
    },
    'send_message': {
        'summary': 'Envoyer un message dans une conversation',
        'value': {
            'content': 'Peux-tu détailler la configuration du port trunk ?',
            'context': {
                'previous_topic': 'vlan_configuration'
            }
        }
    },
    'execute_command': {
        'summary': 'Exécuter une commande réseau',
        'value': {
            'command': 'ping 192.168.1.1',
            'type': 'network',
            'parameters': {
                'count': 4,
                'timeout': 10
            },
            'validation_level': 'strict'
        }
    },
    'search_global': {
        'summary': 'Recherche globale',
        'value': {
            'query': 'configuration vlan trunk',
            'filters': {
                'categories': ['network', 'documentation'],
                'date_range': {
                    'start': '2024-01-01',
                    'end': '2024-01-31'
                }
            },
            'options': {
                'max_results': 20,
                'include_snippets': True,
                'semantic_search': True
            }
        }
    },
    'create_document': {
        'summary': 'Créer un nouveau document',
        'value': {
            'title': 'Guide Configuration VLAN',
            'content': '# Configuration VLAN\n\nCe guide présente les étapes...',
            'category': 'network',
            'tags': ['vlan', 'network', 'configuration'],
            'is_public': True,
            'metadata': {
                'version': '1.0',
                'language': 'fr'
            }
        }
    },
    'network_ping': {
        'summary': 'Test de ping réseau',
        'value': {
            'target': '192.168.1.1',
            'count': 4,
            'timeout': 5
        }
    }
}

# Configuration des URLs Swagger
swagger_urls = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
]

def get_swagger_settings():
    """
    Retourne la configuration Swagger pour inclusion dans settings.py
    """
    return {
        'SWAGGER_SETTINGS': {
            'SECURITY_DEFINITIONS': {
                'Bearer': {
                    'type': 'apiKey',
                    'name': 'Authorization',
                    'in': 'header',
                    'description': 'Token d\'authentification Bearer. Format: Bearer <token>'
                }
            },
            'USE_SESSION_AUTH': False,
            'PERSIST_AUTH': True,
            'REFETCH_SCHEMA_WITH_AUTH': True,
            'REFETCH_SCHEMA_ON_LOGOUT': True,
            'DEFAULT_INFO': 'ai_assistant.api.docs.schema_view',
            'SPEC_URL': '/api/swagger.json',
            'LOGIN_URL': '/admin/login/',
            'LOGOUT_URL': '/admin/logout/',
            'DOC_EXPANSION': 'none',
            'DEEP_LINKING': True,
            'SHOW_EXTENSIONS': True,
            'DEFAULT_MODEL_RENDERING': 'example',
            'DEFAULT_MODEL_DEPTH': 3,
            'TAGS_SORTER': 'alpha',
            'OPERATIONS_SORTER': 'alpha',
            'VALIDATOR_URL': None,
        },
        'REDOC_SETTINGS': {
            'LAZY_RENDERING': False,
            'HIDE_HOSTNAME': False,
            'EXPAND_RESPONSES': ['200', '201'],
            'PATH_IN_MIDDLE': True,
            'REQUIRED_PROPS_FIRST': True,
            'SPEC_URL': '/api/swagger.json',
        }
    }

# Décorateurs pour les vues API
def swagger_auto_schema_extended(**kwargs):
    """
    Décorateur étendu pour la documentation Swagger avec paramètres par défaut
    """
    from drf_yasg.utils import swagger_auto_schema
    
    # Ajouter les réponses communes si non spécifiées
    if 'responses' not in kwargs:
        kwargs['responses'] = {}
    
    # Merger avec les réponses communes
    for status_code, response in COMMON_RESPONSES.items():
        if status_code not in kwargs['responses']:
            kwargs['responses'][status_code] = response
    
    return swagger_auto_schema(**kwargs)

# Tags de sécurité pour les endpoints
SECURITY_REQUIREMENTS = [
    {
        'Bearer': []
    }
]