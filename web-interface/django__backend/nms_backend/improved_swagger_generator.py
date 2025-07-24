"""
Générateur Swagger amélioré qui ajoute automatiquement des descriptions 
pour les paramètres request_body basées sur les serializers.
"""

from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg import openapi
from rest_framework import serializers
import inspect


class ImprovedSwaggerGenerator(OpenAPISchemaGenerator):
    """
    Générateur Swagger amélioré qui:
    1. Unifie les tags basés sur les préfixes d'URL
    2. Améliore les descriptions des request_body
    3. Ajoute des descriptions automatiques pour les paramètres 'data'
    """
    
    def __init__(self, info=None, *args, **kwargs):
        """Initialise le générateur avec les paramètres requis."""
        if info is None:
            info = openapi.Info(
                title="Network Management System API",
                default_version='v1.0',
                description="API du système de gestion réseau"
            )
        super().__init__(info, *args, **kwargs)
    
    # Mapping des préfixes d'URL vers les tags unifiés
    URL_TAG_MAPPING = {
        '/api/reporting/': 'Reporting',
        '/api/monitoring/': 'Monitoring', 
        '/api/security/': 'Security Management',
        '/api/network/': 'Network Management',
        '/api/views/': 'API Views',
        '/api/dashboard/': 'Dashboard',
        '/api/clients/': 'API Clients',
        '/api/gns3/': 'GNS3 Integration',
        '/api/ai/': 'AI Assistant',
        '/api/common/': 'Common - Infrastructure',
        '/api/qos/': 'QoS Management',
    }
    
    def get_operation_keys(self, subpath, method, view):
        """Surcharge pour personnaliser la génération des tags basés sur l'URL."""
        try:
            operation_keys = super().get_operation_keys(subpath, method, view)
            
            if operation_keys and len(operation_keys) >= 1:
                full_path = subpath if subpath.startswith('/api/') else f'/api/{subpath}'
                unified_tag = self._get_unified_tag_for_path(full_path)
                
                if unified_tag:
                    operation_keys = list(operation_keys)
                    operation_keys[0] = unified_tag
                    
            return operation_keys
        except Exception as e:
            return super().get_operation_keys(subpath, method, view)
    
    def _get_unified_tag_for_path(self, path):
        """Détermine le tag unifié basé sur le chemin de l'URL."""
        for url_prefix, unified_tag in self.URL_TAG_MAPPING.items():
            if path.startswith(url_prefix):
                return unified_tag
        
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'api':
            module_name = path_parts[1]
            return self._get_unified_tag_from_module(module_name)
        
        return None
    
    def _get_unified_tag_from_module(self, module_name):
        """Convertit un nom de module en tag unifié."""
        module_tag_mapping = {
            'reporting': 'Reporting',
            'monitoring': 'Monitoring',
            'security': 'Security Management',
            'security_management': 'Security Management',
            'network': 'Network Management',
            'network_management': 'Network Management',
            'views': 'API Views',
            'api_views': 'API Views',
            'dashboard': 'Dashboard',
            'clients': 'API Clients',
            'api_clients': 'API Clients',
            'gns3': 'GNS3 Integration',
            'gns3_integration': 'GNS3 Integration',
            'ai': 'AI Assistant',
            'ai_assistant': 'AI Assistant',
            'common': 'Common - Infrastructure',
            'qos': 'QoS Management',
            'qos_management': 'QoS Management',
        }
        
        return module_tag_mapping.get(module_name.lower())
    
    def get_schema(self, request=None, public=False):
        """Surcharge pour post-traiter le schéma et améliorer les descriptions."""
        try:
            schema = super().get_schema(request, public)
            
            if schema and isinstance(schema, dict):
                # Validation et nettoyage du schéma avant traitement
                schema = self._validate_and_clean_schema(schema)
                schema = self._improve_request_body_descriptions(schema)
                schema = self._cleanup_and_organize_tags(schema)
            
            return schema
        except Exception as e:
            # En cas d'erreur, créer un schéma basique plutôt que d'échouer complètement
            print(f"⚠️ Erreur lors de la génération du schéma Swagger : {e}")
            print("🔄 Basculement vers le schéma de secours...")
            return self._create_fallback_schema()
    
    def _validate_and_clean_schema(self, schema):
        """Valide et nettoie le schéma pour éviter les problèmes de sérialisation."""
        if not isinstance(schema, dict):
            return schema
        
        # Nettoyer récursivement le schéma pour éliminer les références de serializers
        return self._recursive_clean(schema)
    
    def _recursive_clean(self, obj):
        """Nettoie récursivement les objets pour éliminer les références problématiques."""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                try:
                    # Vérifier si la valeur est sérialisable
                    import json
                    json.dumps(value, default=str)
                    cleaned[key] = self._recursive_clean(value)
                except (TypeError, ValueError):
                    # Si la valeur n'est pas sérialisable, créer une représentation simple
                    if hasattr(value, '__class__'):
                        if 'Serializer' in value.__class__.__name__:
                            # Remplacer les références de serializers par une description
                            cleaned[key] = {
                                'type': 'object',
                                'description': f'Données {value.__class__.__name__.replace("Serializer", "")}'
                            }
                        else:
                            cleaned[key] = str(value)
                    else:
                        cleaned[key] = str(value)
            return cleaned
        elif isinstance(obj, list):
            return [self._recursive_clean(item) for item in obj]
        else:
            return obj
    
    def _improve_request_body_descriptions(self, schema):
        """Améliore les descriptions des request_body basées sur les serializers."""
        if not isinstance(schema, dict) or 'paths' not in schema:
            return schema
        
        for path, path_item in schema.get('paths', {}).items():
            for method, operation in path_item.items():
                if isinstance(operation, dict):
                    # Améliorer les descriptions des paramètres
                    self._improve_parameters_descriptions(operation)
                    
                    # Améliorer les descriptions des request_body
                    self._improve_request_body_description(operation)
                    
                    # Améliorer les descriptions des réponses
                    self._improve_responses_descriptions(operation)
        
        return schema
    
    def _improve_parameters_descriptions(self, operation):
        """Améliore les descriptions des paramètres."""
        parameters = operation.get('parameters', [])
        for param in parameters:
            if param.get('name') == 'data' and not param.get('description'):
                # Améliorer la description du paramètre 'data' générique
                operation_summary = operation.get('summary', '')
                if 'create' in operation_summary.lower() or 'créer' in operation_summary.lower():
                    param['description'] = "Données pour créer l'entité"
                elif 'update' in operation_summary.lower() or 'mettre à jour' in operation_summary.lower():
                    param['description'] = "Données pour mettre à jour l'entité"
                else:
                    param['description'] = "Données de l'entité"
    
    def _improve_request_body_description(self, operation):
        """Améliore la description du request_body."""
        request_body = operation.get('requestBody')
        if request_body and isinstance(request_body, dict):
            content = request_body.get('content', {})
            for media_type, media_content in content.items():
                if media_type == 'application/json' and not request_body.get('description'):
                    # Générer une description basée sur l'opération
                    operation_summary = operation.get('summary', '')
                    if 'create' in operation_summary.lower() or 'créer' in operation_summary.lower():
                        request_body['description'] = "Données JSON pour créer l'entité"
                    elif 'update' in operation_summary.lower() or 'mettre à jour' in operation_summary.lower():
                        request_body['description'] = "Données JSON pour mettre à jour l'entité"
                    else:
                        request_body['description'] = "Données JSON de l'entité"
    
    def _improve_responses_descriptions(self, operation):
        """Améliore les descriptions des réponses."""
        responses = operation.get('responses', {})
        for status_code, response in responses.items():
            if isinstance(response, dict) and not response.get('description'):
                # Ajouter des descriptions par défaut basées sur le code de statut
                status_descriptions = {
                    '200': 'Opération réussie',
                    '201': 'Entité créée avec succès',
                    '204': 'Opération réussie sans contenu',
                    '400': 'Données invalides',
                    '401': 'Non authentifié',
                    '403': 'Accès interdit',
                    '404': 'Entité non trouvée',
                    '500': 'Erreur serveur interne'
                }
                
                if status_code in status_descriptions:
                    response['description'] = status_descriptions[status_code]
    
    def _cleanup_and_organize_tags(self, schema):
        """Nettoie et organise les tags dans le schéma Swagger final."""
        if not isinstance(schema, dict) or 'paths' not in schema:
            return schema
        
        used_tags = set()
        
        # Créer un mapping inversé pour identifier les tags à unifier
        reverse_mapping = {}
        for prefix, unified_tag in self.URL_TAG_MAPPING.items():
            reverse_mapping[unified_tag.lower()] = unified_tag
        
        # Ajouter des mappings supplémentaires pour les tags en minuscules
        additional_mappings = {
            'reporting': 'Reporting',
            'monitoring': 'Monitoring',
            'security': 'Security Management',
            'network': 'Network Management',
            'views': 'API Views',
            'dashboard': 'Dashboard',
            'clients': 'API Clients',
            'gns3': 'GNS3 Integration',
            'ai': 'AI Assistant',
            'common': 'Common - Infrastructure',
            'qos': 'QoS Management'
        }
        reverse_mapping.update(additional_mappings)
        
        # Mapping complet pour tous les tags non-unifiés identifiés
        comprehensive_tag_mapping = {
            'ai assistant - intégration gns3': 'AI Assistant',
            'ai assistant - intègration gns3': 'AI Assistant',
            'dashboard - gestion docker': 'Dashboard',
            'dashboard unifié': 'Dashboard',
            'monitoring - configuration': 'Monitoring',
            'monitoring - services spécialisés': 'Monitoring',
            'monitoring - service unifié': 'Monitoring',
            'monitoring - tests': 'Monitoring',
            'qos management unifié': 'QoS Management',
            'reporting unifié': 'Reporting',
            'security alerts': 'Security Management',
            'security analysis': 'Security Management',
            'security dashboard': 'Security Management',
            'security events': 'Security Management',
            'security metrics': 'Security Management',
            'security rules': 'Security Management',
            'security status': 'Security Management',
            'security vulnerabilities': 'Security Management',
            'statut des nœuds': 'Monitoring',
            'sécurité': 'Security Management',
            'sécurité management': 'Security Management',
        }
        reverse_mapping.update(comprehensive_tag_mapping)
        
        # Parcourir toutes les opérations pour collecter et mapper les tags
        for path, path_item in schema.get('paths', {}).items():
            for method, operation in path_item.items():
                if isinstance(operation, dict) and 'tags' in operation:
                    unified_tags = []
                    for tag in operation['tags']:
                        # Première priorité : mapping basé sur l'URL
                        unified_tag = self._get_unified_tag_for_path(path)
                        if unified_tag:
                            unified_tags.append(unified_tag)
                            used_tags.add(unified_tag)
                        else:
                            # Deuxième priorité : mapping du tag exact (case-insensitive)
                            tag_lower = tag.lower()
                            if tag_lower in reverse_mapping:
                                unified_tag = reverse_mapping[tag_lower]
                                unified_tags.append(unified_tag)
                                used_tags.add(unified_tag)
                            else:
                                # Troisième priorité : recherche de correspondance partielle
                                found_match = False
                                for pattern, target_tag in reverse_mapping.items():
                                    if pattern in tag_lower or tag_lower in pattern:
                                        unified_tags.append(target_tag)
                                        used_tags.add(target_tag)
                                        found_match = True
                                        break
                                
                                if not found_match:
                                    unified_tags.append(tag)
                                    used_tags.add(tag)
                    
                    operation['tags'] = list(set(unified_tags))
        
        # Créer la liste des tags organisés
        organized_tags = self._create_organized_tags_list(used_tags)
        schema['tags'] = organized_tags
        
        return schema
    
    def _create_organized_tags_list(self, used_tags):
        """Crée une liste organisée des tags avec descriptions."""
        tag_order = [
            'AI Assistant',
            'API Clients', 
            'API Views',
            'Common - Infrastructure',
            'Dashboard',
            'GNS3 Integration',
            'Monitoring',
            'Network Management',
            'QoS Management',
            'Reporting',
            'Security Management'
        ]
        
        tag_descriptions = {
            'AI Assistant': 'Assistant intelligent et automation',
            'API Clients': 'Intégration avec services externes',
            'API Views': 'Vues métier sophistiquées', 
            'Common - Infrastructure': 'Services d\'infrastructure centralisés',
            'Dashboard': 'Tableaux de bord et visualisation',
            'GNS3 Integration': 'Interface complète avec GNS3',
            'Monitoring': 'Surveillance et métriques avancées',
            'Network Management': 'Gestion réseau et équipements',
            'QoS Management': 'Gestion avancée de la Qualité de Service',
            'Reporting': 'Système de génération de rapports',
            'Security Management': 'Système de sécurité avancé'
        }
        
        organized_tags = []
        
        # Ajouter les tags dans l'ordre préféré s'ils sont utilisés
        for tag_name in tag_order:
            if tag_name in used_tags:
                organized_tags.append({
                    'name': tag_name,
                    'description': tag_descriptions.get(tag_name, f'APIs pour {tag_name}')
                })
        
        # Ajouter les tags non prévus à la fin
        for tag_name in sorted(used_tags):
            if tag_name not in tag_order:
                organized_tags.append({
                    'name': tag_name,
                    'description': f'APIs pour {tag_name}'
                })
        
        return organized_tags
    
    def _create_fallback_schema(self):
        """Crée un schéma Swagger basique en cas d'erreur."""
        return {
            "openapi": "3.0.2",
            "info": {
                "title": "Network Management System API",
                "version": "v1.0",
                "description": "API du système de gestion réseau (Mode dégradé - Erreur de génération)"
            },
            "paths": {
                "/api/": {
                    "get": {
                        "operationId": "api_root",
                        "description": "Point d'entrée de l'API",
                        "responses": {
                            "200": {
                                "description": "Informations sur l'API"
                            }
                        },
                        "tags": ["API Root"]
                    }
                }
            },
            "tags": [
                {"name": "API Root", "description": "Point d'entrée de l'API"}
            ]
        }
    
    def get_paths(self, request=None, public=False):
        """Surcharge pour gérer les erreurs de façon granulaire."""
        paths = {}
        
        for path, method, callback in self.get_paths_and_endpoints():
            try:
                # Traiter chaque endpoint individuellement
                if not self.should_include_endpoint(path, method, callback, request):
                    continue
                    
                operation = self.get_operation(path, method, callback, request)
                if operation:
                    if path not in paths:
                        paths[path] = {}
                    paths[path][method.lower()] = operation
                    
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres endpoints
                print(f"Erreur pour l'endpoint {method} {path}: {e}")
                # Créer une entrée basique pour cet endpoint
                if path not in paths:
                    paths[path] = {}
                paths[path][method.lower()] = {
                    "operationId": f"{method.lower()}_{path.replace('/', '_').strip('_')}",
                    "description": f"Endpoint {method} {path} (Erreur de génération)",
                    "responses": {"200": {"description": "Réponse"}},
                    "tags": ["Erreur de génération"]
                }
                
        return paths