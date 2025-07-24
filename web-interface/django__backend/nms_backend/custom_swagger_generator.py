"""
Générateur Swagger personnalisé pour unifier automatiquement les tags basés sur les préfixes d'URL.
"""

from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg import openapi
from collections import OrderedDict


class UnifiedTagsOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    """
    Générateur Swagger personnalisé qui unifie automatiquement les tags
    basés sur les préfixes d'URL au lieu des noms d'app Django.
    """
    
    def __init__(self, info=None, *args, **kwargs):
        """
        Initialise le générateur avec les paramètres requis.
        """
        if info is None:
            # Utiliser une info par défaut si non fournie
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
    }
    
    def get_operation_keys(self, subpath, method, view):
        """
        Surcharge pour personnaliser la génération des tags basés sur l'URL.
        """
        try:
            # Obtenir les clés d'opération par défaut
            operation_keys = super().get_operation_keys(subpath, method, view)
            
            if operation_keys and len(operation_keys) >= 1:
                # Le tag est généralement le premier élément
                original_tag = operation_keys[0]
                
                # Construire le chemin complet
                # Note: subpath contient déjà le chemin complet dans certains cas
                full_path = subpath if subpath.startswith('/api/') else f'/api/{subpath}'
                unified_tag = self._get_unified_tag_for_path(full_path)
                
                if unified_tag:
                    # Remplacer le tag par défaut par le tag unifié
                    operation_keys = list(operation_keys)
                    operation_keys[0] = unified_tag
                    
            return operation_keys
        except Exception as e:
            # En cas d'erreur, retourner les clés par défaut
            return super().get_operation_keys(subpath, method, view)
    
    def _get_unified_tag_for_path(self, path):
        """
        Détermine le tag unifié basé sur le chemin de l'URL.
        """
        for url_prefix, unified_tag in self.URL_TAG_MAPPING.items():
            if path.startswith(url_prefix):
                return unified_tag
        
        # Fallback: essayer de déduire depuis le chemin
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'api':
            module_name = path_parts[1]
            return self._get_unified_tag_from_module(module_name)
        
        return None
    
    def _get_unified_tag_from_module(self, module_name):
        """
        Convertit un nom de module en tag unifié.
        """
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
        }
        
        return module_tag_mapping.get(module_name.lower())
    
    def get_schema(self, request=None, public=False):
        """
        Surcharge pour post-traiter le schéma et nettoyer les tags dupliqués.
        """
        try:
            schema = super().get_schema(request, public)
            
            # Post-traitement pour nettoyer et organiser les tags
            if schema and isinstance(schema, dict):
                schema = self._cleanup_and_organize_tags(schema)
            
            return schema
        except Exception as e:
            # En cas d'erreur, retourner le schéma par défaut
            return super().get_schema(request, public)
    
    def _cleanup_and_organize_tags(self, schema):
        """
        Nettoie et organise les tags dans le schéma Swagger final.
        """
        if not isinstance(schema, dict) or 'paths' not in schema:
            return schema
        
        # Collecter tous les tags utilisés et les mapper vers leurs versions unifiées
        used_tags = set()
        tag_mapping = {}
        
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
            'ai': 'AI Assistant'
        }
        reverse_mapping.update(additional_mappings)
        
        # Parcourir toutes les opérations pour collecter et mapper les tags
        for path, path_item in schema.get('paths', {}).items():
            for method, operation in path_item.items():
                if isinstance(operation, dict) and 'tags' in operation:
                    unified_tags = []
                    for tag in operation['tags']:
                        # Essayer de mapper le tag vers sa version unifiée
                        unified_tag = self._get_unified_tag_for_path(path)
                        if unified_tag:
                            unified_tags.append(unified_tag)
                            used_tags.add(unified_tag)
                            tag_mapping[tag] = unified_tag
                        else:
                            # Vérifier si c'est un tag en minuscules à unifier
                            if tag.lower() in reverse_mapping:
                                unified_tag = reverse_mapping[tag.lower()]
                                unified_tags.append(unified_tag)
                                used_tags.add(unified_tag)
                                tag_mapping[tag] = unified_tag
                            else:
                                # Garder le tag tel quel
                                unified_tags.append(tag)
                                used_tags.add(tag)
                                tag_mapping[tag] = tag
                    
                    # Remplacer les tags par leurs versions unifiées
                    operation['tags'] = list(set(unified_tags))  # Éliminer les doublons
        
        # Créer la liste des tags organisés
        organized_tags = self._create_organized_tags_list(used_tags)
        
        # Mettre à jour le schéma avec les tags organisés
        schema['tags'] = organized_tags
        
        return schema
    
    def _create_organized_tags_list(self, used_tags):
        """
        Crée une liste organisée des tags avec descriptions.
        """
        # Ordre préféré des tags
        tag_order = [
            'AI Assistant',
            'API Clients', 
            'API Views',
            'Dashboard',
            'GNS3 Integration',
            'Monitoring',
            'Network Management',
            'Reporting',
            'Security Management'
        ]
        
        # Descriptions des tags
        tag_descriptions = {
            'AI Assistant': 'Assistant intelligent et automation',
            'API Clients': 'Intégration avec services externes',
            'API Views': 'Vues métier sophistiquées', 
            'Dashboard': 'Tableaux de bord et visualisation',
            'GNS3 Integration': 'Interface complète avec GNS3',
            'Monitoring': 'Surveillance et métriques avancées',
            'Network Management': 'Gestion réseau et équipements',
            'Reporting': 'Système de génération de rapports',
            'Security Management': 'Système de sécurité avancé'
        }
        
        # Créer la liste organisée
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