"""
Générateur automatique de documentation Swagger pour le module api_clients.

Ce module utilise l'introspection pour générer automatiquement la documentation
sans nécessiter de remplissage manuel des métadonnées Swagger.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
import inspect
import json
from typing import Dict, Any, List, Optional


class AutoSwaggerGenerator:
    """Générateur automatique de documentation Swagger."""
    
    def __init__(self):
        self.auto_schemas = {}
    
    def introspect_view_function(self, view_func):
        """
        Analyse automatiquement une fonction de vue pour générer la documentation Swagger.
        
        Args:
            view_func: Fonction de vue à analyser
            
        Returns:
            dict: Configuration Swagger automatiquement générée
        """
        # Extraire le nom et la docstring
        func_name = view_func.__name__
        docstring = view_func.__doc__ or f"Endpoint {func_name}"
        
        # Extraire la première ligne comme résumé
        doc_lines = docstring.strip().split('\n')
        summary = doc_lines[0].strip()
        description = '\n'.join(doc_lines[1:]).strip() if len(doc_lines) > 1 else summary
        
        # Déterminer la méthode HTTP basée sur le nom de la fonction
        method = self._infer_http_method(func_name)
        
        # Déterminer les paramètres automatiquement
        parameters = self._extract_parameters(view_func)
        
        # Déterminer les réponses basées sur le type de vue
        responses = self._generate_responses(func_name)
        
        # Déterminer le body de requête si nécessaire
        request_body = self._extract_request_body(view_func, method)
        
        return {
            'method': method,
            'operation_description': description,
            'operation_summary': summary,
            'parameters': parameters,
            'responses': responses,
            'request_body': request_body,
            'tags': self._extract_tags(func_name)
        }
    
    def _infer_http_method(self, func_name: str) -> str:
        """Détermine la méthode HTTP basée sur le nom de la fonction."""
        if 'create' in func_name.lower() or func_name.startswith('post_'):
            return 'post'
        elif 'update' in func_name.lower() or func_name.startswith('put_'):
            return 'put'
        elif 'delete' in func_name.lower() or func_name.startswith('delete_'):
            return 'delete'
        else:
            return 'get'
    
    def _extract_parameters(self, view_func) -> List[Dict]:
        """Extrait les paramètres automatiquement de la fonction."""
        sig = inspect.signature(view_func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['request', 'self']:
                continue
                
            # Paramètre de path
            param_config = {
                'name': param_name,
                'in': 'path',
                'required': param.default == inspect.Parameter.empty,
                'description': f'Paramètre {param_name}',
                'schema': {'type': 'string'}
            }
            
            # Inférer le type basé sur le nom
            if 'id' in param_name.lower():
                param_config['schema'] = {'type': 'string', 'format': 'uuid'}
            elif 'port' in param_name.lower():
                param_config['schema'] = {'type': 'integer'}
            elif 'count' in param_name.lower() or 'size' in param_name.lower():
                param_config['schema'] = {'type': 'integer'}
                
            parameters.append(param_config)
        
        return parameters
    
    def _generate_responses(self, func_name: str) -> Dict:
        """Génère les réponses automatiquement basées sur le type de fonction."""
        responses = {
            '200': {
                'description': 'Opération réussie',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'success': {'type': 'boolean'},
                                'data': {'type': 'object'},
                                'message': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            '400': {
                'description': 'Requête invalide',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'details': {'type': 'object'}
                            }
                        }
                    }
                }
            },
            '500': {
                'description': 'Erreur serveur interne',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
        
        # Réponses spécifiques basées sur le type d'opération
        if 'create' in func_name.lower():
            responses['201'] = {
                'description': 'Ressource créée avec succès',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'created_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            }
        elif 'delete' in func_name.lower():
            responses['204'] = {'description': 'Ressource supprimée avec succès'}
        elif 'health' in func_name.lower() or 'status' in func_name.lower():
            responses['503'] = {
                'description': 'Service non disponible',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'service': {'type': 'string'},
                                'status': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        
        return responses
    
    def _extract_request_body(self, view_func, method: str) -> Optional[Dict]:
        """Extrait le corps de requête automatiquement."""
        if method in ['post', 'put', 'patch']:
            # Corps générique pour les méthodes qui modifient des données
            return {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'description': 'Données à traiter'
                                }
                            }
                        }
                    }
                }
            }
        return None
    
    def _extract_tags(self, func_name: str) -> List[str]:
        """Extrait les tags automatiquement basés sur le nom de la fonction."""
        if 'network' in func_name.lower() or 'gns3' in func_name.lower() or 'snmp' in func_name.lower():
            return ['Clients Réseau']
        elif 'monitoring' in func_name.lower() or 'prometheus' in func_name.lower() or 'grafana' in func_name.lower():
            return ['Clients Monitoring']
        elif 'infrastructure' in func_name.lower() or 'haproxy' in func_name.lower():
            return ['Clients Infrastructure']
        elif 'security' in func_name.lower() or 'fail2ban' in func_name.lower() or 'suricata' in func_name.lower():
            return ['Clients Sécurité']
        elif 'health' in func_name.lower() or 'status' in func_name.lower():
            return ['Santé & Monitoring']
        else:
            return ['API Clients']


def auto_swagger_schema(**kwargs):
    """
    Décorateur pour générer automatiquement la documentation Swagger.
    
    Usage:
        @auto_swagger_schema()
        @api_view(['GET'])
        def my_view(request):
            pass
    """
    def decorator(view_func):
        # Configuration minimale automatique
        auto_config = {
            'operation_description': view_func.__doc__ or f"Endpoint {view_func.__name__}",
            'operation_summary': (view_func.__doc__ or f"Endpoint {view_func.__name__}").split('\n')[0].strip(),
            'tags': ['API Clients']
        }
        
        # Fusionner avec les kwargs fournis
        final_config = {**auto_config, **kwargs}
        
        # Appliquer le décorateur swagger_auto_schema de drf-yasg
        return swagger_auto_schema(**final_config)(view_func)
    
    return decorator


def generate_client_schema(client_name: str, operations: List[str]) -> Dict:
    """
    Génère automatiquement le schéma Swagger pour un client API.
    
    Args:
        client_name: Nom du client (ex: 'GNS3Client')
        operations: Liste des opérations supportées
        
    Returns:
        dict: Schéma Swagger généré
    """
    schema = {
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string',
                'example': client_name,
                'description': f'Nom du client {client_name}'
            },
            'status': {
                'type': 'string',
                'enum': ['available', 'unavailable', 'error'],
                'description': 'Statut de disponibilité du client'
            },
            'operations': {
                'type': 'array',
                'items': {'type': 'string'},
                'example': operations,
                'description': 'Liste des opérations supportées'
            }
        }
    }
    
    return schema


# Schémas prédéfinis pour les réponses communes
COMMON_SCHEMAS = {
    'SuccessResponse': {
        'type': 'object',
        'properties': {
            'success': {'type': 'boolean', 'example': True},
            'message': {'type': 'string', 'example': 'Opération réussie'},
            'data': {'type': 'object'}
        }
    },
    'ErrorResponse': {
        'type': 'object',
        'properties': {
            'error': {'type': 'string', 'example': 'Erreur lors de l\'opération'},
            'details': {'type': 'object'},
            'timestamp': {'type': 'string', 'format': 'date-time'}
        }
    },
    'HealthStatus': {
        'type': 'object',
        'properties': {
            'service': {'type': 'string'},
            'status': {'type': 'string', 'enum': ['healthy', 'unhealthy', 'degraded']},
            'checks': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'status': {'type': 'boolean'},
                        'message': {'type': 'string'}
                    }
                }
            },
            'timestamp': {'type': 'string', 'format': 'date-time'}
        }
    }
}