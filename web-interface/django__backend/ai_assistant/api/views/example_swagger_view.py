"""
Exemple de vue avec documentation Swagger complète.
Ce fichier montre comment bien documenter les endpoints API avec Swagger.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..docs import (
    CUSTOM_SCHEMAS, 
    REQUEST_EXAMPLES, 
    COMMON_RESPONSES,
    swagger_auto_schema_extended
)
from ..serializers.conversation_serializers import ConversationSerializer, MessageSerializer


class ConversationListView(APIView):
    """
    Vue pour lister et créer des conversations.
    """
    
    @swagger_auto_schema(
        operation_summary="Lister les conversations",
        operation_description="Récupère la liste paginée des conversations de l'utilisateur connecté",
        tags=['💬 Conversations'],
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Recherche dans les titres de conversations",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Numéro de page",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Nombre d'éléments par page",
                type=openapi.TYPE_INTEGER,
                default=20,
                maximum=100
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des conversations",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                                    'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                                    'message_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'last_message_preview': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                ),
                examples={
                    'application/json': {
                        'count': 25,
                        'next': 'http://api/conversations/?page=2',
                        'previous': None,
                        'results': [
                            {
                                'id': 1,
                                'title': 'Configuration VLAN',
                                'created_at': '2024-01-15T10:30:00Z',
                                'updated_at': '2024-01-15T11:15:00Z',
                                'message_count': 5,
                                'last_message_preview': 'Voici la configuration recommandée...'
                            }
                        ]
                    }
                }
            ),
            **COMMON_RESPONSES
        }
    )
    def get(self, request):
        """Liste les conversations de l'utilisateur."""
        # Implémentation de la méthode
        return Response({'message': 'Liste des conversations'})
    
    @swagger_auto_schema(
        operation_summary="Créer une nouvelle conversation",
        operation_description="Crée une nouvelle conversation avec un message initial optionnel",
        tags=['💬 Conversations'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title'],
            properties={
                'title': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Titre de la conversation",
                    max_length=200,
                    min_length=1
                ),
                'initial_message': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Message initial optionnel",
                    max_length=4000
                )
            },
            example=REQUEST_EXAMPLES['create_conversation']['value']
        ),
        responses={
            201: openapi.Response(
                description="Conversation créée avec succès",
                schema=CUSTOM_SCHEMAS['ConversationDetail'],
                examples={
                    'application/json': {
                        'id': 2,
                        'title': 'Nouvelle conversation',
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:00:00Z',
                        'user_id': 1,
                        'messages': [
                            {
                                'id': 1,
                                'role': 'user',
                                'content': 'Comment configurer un VLAN ?',
                                'timestamp': '2024-01-15T12:00:00Z',
                                'metadata': {}
                            }
                        ]
                    }
                }
            ),
            **COMMON_RESPONSES
        }
    )
    def post(self, request):
        """Crée une nouvelle conversation."""
        # Implémentation de la méthode
        return Response({'message': 'Conversation créée'}, status=status.HTTP_201_CREATED)


class MessageView(APIView):
    """
    Vue pour envoyer des messages dans une conversation.
    """
    
    @swagger_auto_schema_extended(
        operation_summary="Envoyer un message",
        operation_description="""
        Envoie un message à l'assistant IA dans une conversation existante.
        
        ### Fonctionnalités:
        - **IA Multi-Providers**: Support OpenAI, Anthropic, HuggingFace
        - **Contexte Intelligent**: Utilise l'historique de conversation
        - **Actions Automatiques**: Peut exécuter des commandes si demandé
        - **Base de Connaissances**: Enrichit les réponses avec la documentation
        
        ### Nouveautés v2.0:
        - ✅ **0% Simulation**: Toutes les réponses sont générées par de vraies IA
        - ✅ **Sécurité Renforcée**: Validation stricte des actions
        - ✅ **Performance Optimisée**: Cache intelligent et timeouts configurables
        """,
        tags=['💬 Conversations'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Contenu du message à envoyer",
                    max_length=4000,
                    min_length=1
                ),
                'context': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Contexte supplémentaire pour la requête",
                    properties={
                        'previous_topic': openapi.Schema(type=openapi.TYPE_STRING),
                        'priority': openapi.Schema(type=openapi.TYPE_STRING, enum=['low', 'normal', 'high']),
                        'expected_format': openapi.Schema(type=openapi.TYPE_STRING, enum=['text', 'command', 'config'])
                    }
                ),
                'options': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Options de traitement",
                    properties={
                        'include_actions': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'use_knowledge_base': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'max_response_length': openapi.Schema(type=openapi.TYPE_INTEGER, default=1000),
                        'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', minimum=0.0, maximum=2.0)
                    }
                )
            },
            example=REQUEST_EXAMPLES['send_message']['value']
        ),
        responses={
            200: openapi.Response(
                description="Message traité avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_message': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'role': openapi.Schema(type=openapi.TYPE_STRING, default='user'),
                                'content': openapi.Schema(type=openapi.TYPE_STRING),
                                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime')
                            }
                        ),
                        'assistant_response': openapi.Schema(
                            allOf=[
                                CUSTOM_SCHEMAS['AIResponse'],
                                openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'role': openapi.Schema(type=openapi.TYPE_STRING, default='assistant'),
                                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='datetime')
                                    }
                                )
                            ]
                        )
                    }
                ),
                examples={
                    'application/json': {
                        'user_message': {
                            'id': 3,
                            'role': 'user',
                            'content': 'Peux-tu détailler la configuration du trunk ?',
                            'timestamp': '2024-01-15T11:00:00Z'
                        },
                        'assistant_response': {
                            'id': 4,
                            'role': 'assistant',
                            'content': 'Pour configurer un port trunk sur un switch Cisco...',
                            'timestamp': '2024-01-15T11:01:00Z',
                            'confidence': 0.92,
                            'processing_time': 1.2,
                            'actions': [
                                {
                                    'type': 'command_suggestion',
                                    'data': {
                                        'command': 'switchport mode trunk',
                                        'description': 'Configure le port en mode trunk'
                                    }
                                }
                            ],
                            'sources': ['cisco_switching_guide.md'],
                            'metadata': {
                                'model_used': 'gpt-4',
                                'tokens_used': 150,
                                'knowledge_base_hits': 3
                            }
                        }
                    }
                }
            )
        }
    )
    def post(self, request, conversation_id):
        """Envoie un message dans une conversation."""
        # Implémentation de la méthode
        return Response({'message': 'Message envoyé'})


class CommandExecutionView(APIView):
    """
    Vue pour l'exécution sécurisée de commandes.
    """
    
    @swagger_auto_schema(
        operation_summary="Exécuter une commande",
        operation_description="""
        Exécute une commande système avec validation de sécurité intégrée.
        
        ### Types de commandes supportés:
        - **network**: ping, traceroute, nslookup, netstat
        - **system**: ps, top, df, free, uname
        - **sql**: Requêtes SELECT (lecture seule)
        - **python**: Code Python dans un sandbox sécurisé
        
        ### Sécurité:
        - ✅ **Validation IA**: Analyse de la commande avant exécution
        - ✅ **Liste Blanche**: Seules les commandes autorisées sont exécutées
        - ✅ **Sandbox**: Isolation complète pour Python
        - ✅ **Timeouts**: Limites de temps d'exécution
        - ✅ **Logs de Sécurité**: Toutes les commandes sont enregistrées
        """,
        tags=['⚡ Commandes'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['command', 'type'],
            properties={
                'command': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Commande à exécuter",
                    max_length=1000,
                    example='ping 192.168.1.1'
                ),
                'type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['network', 'system', 'sql', 'python'],
                    description="Type de commande",
                    example='network'
                ),
                'parameters': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Paramètres supplémentaires",
                    properties={
                        'timeout': openapi.Schema(type=openapi.TYPE_INTEGER, default=30),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Pour ping/traceroute"),
                        'max_output_size': openapi.Schema(type=openapi.TYPE_INTEGER, default=1048576)
                    }
                ),
                'validation_level': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['strict', 'normal', 'permissive'],
                    default='normal',
                    description="Niveau de validation de sécurité"
                )
            },
            example=REQUEST_EXAMPLES['execute_command']['value']
        ),
        responses={
            200: openapi.Response(
                description="Commande exécutée avec succès",
                schema=CUSTOM_SCHEMAS['CommandResult'],
                examples={
                    'application/json': {
                        'success': True,
                        'command': 'ping 192.168.1.1',
                        'command_id': 'cmd_123456',
                        'execution_time': 2.5,
                        'output': {
                            'stdout': 'PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data...',
                            'stderr': '',
                            'return_code': 0
                        },
                        'analysis': {
                            'safety_score': 0.98,
                            'detected_risks': [],
                            'recommendations': ['Commande réseau standard, aucun risque détecté']
                        },
                        'metadata': {
                            'executed_at': '2024-01-15T12:00:00Z',
                            'executor': 'network_service',
                            'user_id': 1,
                            'validation_passed': True
                        }
                    }
                }
            ),
            403: openapi.Response(
                description="Commande non autorisée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, default='FORBIDDEN_COMMAND'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'safety_analysis': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'safety_score': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                        'detected_risks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                        'blocked_reason': openapi.Schema(type=openapi.TYPE_STRING)
                                    }
                                )
                            }
                        )
                    }
                ),
                examples={
                    'application/json': {
                        'error': {
                            'code': 'FORBIDDEN_COMMAND',
                            'message': 'Commande bloquée pour des raisons de sécurité',
                            'safety_analysis': {
                                'safety_score': 0.15,
                                'detected_risks': ['destructive_operation', 'system_modification'],
                                'blocked_reason': 'Commande potentiellement destructive détectée'
                            }
                        }
                    }
                }
            )
        }
    )
    def post(self, request):
        """Exécute une commande avec validation de sécurité."""
        # Implémentation de la méthode
        return Response({'message': 'Commande exécutée'})


# Exemple d'utilisation du décorateur étendu
class SearchView(APIView):
    """Vue de recherche avec décorateur étendu."""
    
    @swagger_auto_schema_extended(
        operation_summary="Recherche globale",
        operation_description="Effectue une recherche intelligente dans tous les contenus",
        tags=['🔍 Recherche'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['query'],
            properties={
                'query': openapi.Schema(type=openapi.TYPE_STRING, min_length=1),
                'filters': openapi.Schema(type=openapi.TYPE_OBJECT),
                'options': openapi.Schema(type=openapi.TYPE_OBJECT)
            },
            example=REQUEST_EXAMPLES['search_global']['value']
        ),
        responses={
            200: openapi.Response(
                description="Résultats de recherche",
                schema=CUSTOM_SCHEMAS['SearchResult']
            )
            # Les réponses communes (400, 401, 403, etc.) sont ajoutées automatiquement
        }
    )
    def post(self, request):
        """Effectue une recherche globale."""
        return Response({'message': 'Recherche effectuée'})