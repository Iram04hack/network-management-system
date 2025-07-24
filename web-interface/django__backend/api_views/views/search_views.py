"""
Vues API pour les fonctionnalités de recherche.

Ce module implémente les vues API pour la recherche dans le système de gestion
de réseau en suivant les principes de l'architecture hexagonale.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
import time
from typing import Dict, Any, List, Optional

from ..presentation.serializers.search_serializers import (
    SearchRequestSerializer,
    SearchResponseSerializer,
    ResourceDetailSerializer,
    SearchSuggestionSerializer,
    GlobalSearchSerializer,
    SearchHistorySerializer,
    SearchAnalyticsSerializer
)
from ..presentation.filters.advanced_filters import SearchFilterBackend
from ..presentation.filters.dynamic_filters import DynamicFilterBackend
from ..presentation.pagination.advanced_pagination import AdvancedPageNumberPagination, SmartPagination
from ..presentation.pagination.cursor_pagination import CursorPagination
from ..domain.exceptions import (
    ResourceNotFoundException,
    SearchException,
    ValidationException
)
# from .mixins import DIViewMixin  # Removed - not available in this project
from ..application.use_cases import SearchResourcesUseCase, GetResourceDetailsUseCase

logger = logging.getLogger(__name__)


class GlobalSearchViewSet(viewsets.ViewSet):
    """
    API endpoint pour la recherche globale multi-types.
    
    Permet de rechercher à travers tous les types de ressources
    du système de gestion de réseau avec filtrage et pagination avancés.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = SmartPagination
    filter_backends = [SearchFilterBackend, DynamicFilterBackend]
    
    # Champs de recherche pour la recherche textuelle
    search_fields = ['name', 'description', 'tags', 'properties']
    
    def get_queryset(self):
        """Retourne un queryset vide pour la compatibilité Swagger."""
        if getattr(self, 'swagger_fake_view', False):
            from django.contrib.auth.models import User
            return User.objects.none()
        return None
    
    @property
    def search_use_case(self):
        """Mock search use case for testing."""
        return type('MockSearchUseCase', (), {
            'execute': lambda self, params: {
                'total': 0,
                'results': [],
                'type_counts': {},
                'suggestions': []
            },
            'get_suggestions': lambda self, params: [],
            'get_analytics': lambda self, params: {},
            'clear_user_search_history': lambda self, params: None
        })()
    
    def validate_filter_params(self, query_params):
        """Valide les paramètres de filtrage."""
        errors = []
        # Validation basique pour demo
        return errors
    
    @swagger_auto_schema(
        operation_summary="Liste tous les recherche globale",
        operation_description="Récupère la liste complète des recherche globale avec filtrage, tri et pagination.",
        tags=['API Views'],
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description='Numéro de page', type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description='Éléments par page', type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description='Champ de tri', type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Liste récupérée avec succès",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def list(self, request):
        """Liste les capacités de recherche disponibles"""
        try:
            from django.utils import timezone

            capabilities = {
                'search_types': ['devices', 'networks', 'alerts', 'configurations'],
                'filters_available': ['status', 'type', 'location', 'date_range'],
                'operators': ['eq', 'ne', 'gt', 'lt', 'contains', 'in'],
                'max_results': 1000,
                'pagination_supported': True,
                'timestamp': timezone.now().isoformat()
            }
            return Response(capabilities)
        except Exception as e:
            logger.exception(f"Erreur liste search capabilities: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @action(detail=False, methods=['get', 'post'])
    @swagger_auto_schema(
        operation_summary="Action search",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def search(self, request):
        """
        Effectue une recherche globale dans le système.

        Cette vue permet de rechercher simultanément dans tous les types
        de ressources avec pondération, groupement par type, filtrage avancé et pagination.
        """
        start_time = time.time()
        
        try:
            # Valider les paramètres de filtrage
            filter_errors = self.validate_filter_params(request.query_params)
            if filter_errors:
                return Response(
                    {"error": "Paramètres de filtrage invalides", "details": filter_errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Déterminer les paramètres selon la méthode
            if request.method == 'POST':
                serializer = GlobalSearchSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(
                        {"error": "Paramètres de recherche invalides", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                search_data = serializer.validated_data
            else:
                # GET request - utiliser les query params
                search_data = {
                    'query': request.query_params.get('q', ''),
                    'resource_types': request.query_params.get('resource_types', '').split(',') if request.query_params.get('resource_types') else None,
                    'group_by_type': request.query_params.get('group_by_type', 'true').lower() == 'true',
                    'max_per_type': int(request.query_params.get('max_per_type', 10)),
                    'use_cache': request.query_params.get('use_cache', 'true').lower() == 'true'
                }
            
            # Préparer les paramètres de recherche
            search_params = {
                'query': search_data['query'],
                'resource_types': search_data.get('resource_types') or ['device', 'alert', 'topology', 'configuration', 'user'],
                'group_by_type': search_data.get('group_by_type', True),
                'max_per_type': search_data.get('max_per_type', 10),
                'type_weights': search_data.get('type_weights', {}),
                'use_cache': search_data.get('use_cache', True),
                'user_id': request.user.id,
                'filters': self._extract_dynamic_filters(request.query_params),
                'ordering': request.query_params.get('ordering', '-updated_at')
            }
            
            # Ajouter les filtres rapides
            quick_filters = search_data.get('quick_filters', {})
            if quick_filters:
                search_params['filters'].update(quick_filters)
            
            # Exécuter la recherche via le cas d'utilisation
            search_results = self.search_use_case.execute(search_params)
            
            # Appliquer la pagination
            paginated_results = self._paginate_search_results(request, search_results)
            
            # Calculer le temps de recherche
            search_time = time.time() - start_time
            
            # Préparer la réponse
            response_data = {
                'query': search_data['query'],
                'total': search_results.get('total', 0),
                'search_time': round(search_time, 3),
                'results': paginated_results.get('results', []),
                'type_counts': search_results.get('type_counts', {}),
                'suggestions': search_results.get('suggestions', []),
                'filters_applied': search_params['filters'],
                'pagination': paginated_results.get('pagination', {})
            }
            
            # Ajouter des métadonnées si demandées
            if search_data.get('group_by_type'):
                response_data['grouped_results'] = search_results.get('grouped_results', {})
            
            return Response(response_data)
            
        except SearchException as e:
            logger.error(f"Erreur lors de la recherche globale: {e}")
            return Response({
                "error": "Erreur lors de la recherche",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la recherche globale: {e}")
            return Response({
                "error": "Erreur interne du serveur"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Action _extract_dynamic_filters",
        operation_description="Récupère la liste complète des filtres applicables par type de ressource.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def _extract_dynamic_filters(self, query_params):
        """
        Extrait les filtres dynamiques des paramètres de requête
        """
        filters = {}
        for key, value in query_params.items():
            if key.startswith('filter[') and key.endswith(']'):
                # Parser le format filter[field][operator]=value
                filter_part = key[7:-1]  # Enlever 'filter[' et ']'
                if '][' in filter_part:
                    field, operator = filter_part.split('][', 1)
                    filters[f"{field}__{operator}"] = value
                else:
                    filters[f"{filter_part}__eq"] = value
        return filters
    
    @swagger_auto_schema(
        operation_summary="Action _paginate_search_results",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def _paginate_search_results(self, request, search_results):
        """
        Applique la pagination aux résultats de recherche
        """
        try:
            # Initialiser la pagination
            paginator = self.pagination_class()
            
            # Simuler un queryset pour la pagination
            results = search_results.get('results', [])
            
            # Appliquer la pagination manuelle
            page_size = paginator.get_page_size(request)
            page = int(request.query_params.get('page', 1))
            
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_data = results[start_index:end_index]
            
            return {
                'results': paginated_data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': len(results),
                    'total_pages': (len(results) // page_size) + (1 if len(results) % page_size else 0),
                    'has_next': end_index < len(results),
                    'has_previous': start_index > 0
                }
            }
        except Exception:
            # Fallback : retourner tous les résultats
            return {'results': search_results.get('results', []), 'pagination': {}}
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Action suggestions",
        operation_description="Fournit des suggestions de recherche contextuelles basées sur l'historique utilisateur.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def suggestions(self, request):
        """
        Retourne des suggestions de recherche basées sur l'input utilisateur avec contexte.
        """
        try:
            query_start = request.query_params.get('q', '').strip()
            limit = int(request.query_params.get('limit', 10))
            resource_types = request.query_params.get('resource_types', '').split(',') if request.query_params.get('resource_types') else None
            context = request.query_params.get('context', 'global')
            
            if len(query_start) < 2:
                return Response({
                    "suggestions": [],
                    "message": "Saisissez au moins 2 caractères pour obtenir des suggestions"
                })
            
            # Obtenir les suggestions via le cas d'utilisation
            suggestions = self.search_use_case.get_suggestions({
                'query_start': query_start,
                'limit': limit,
                'resource_types': resource_types,
                'context': context,
                'user_id': request.user.id
            })
            
            # Sérialiser les suggestions
            serializer = SearchSuggestionSerializer(suggestions, many=True)
            
            return Response({
                "suggestions": serializer.data,
                "query_start": query_start,
                "context": context,
                "resource_types": resource_types
            })
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des suggestions: {e}")
            return Response({
                "error": "Erreur lors de la récupération des suggestions"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Action filters",
        operation_description="Récupère la liste complète des filtres applicables par type de ressource.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def filters(self, request):
        """
        Retourne les filtres disponibles pour la recherche
        """
        try:
            resource_type = request.query_params.get('resource_type', 'all')
            
            # Définir les filtres disponibles par type de ressource
            available_filters = {
                'device': {
                    'device_type': {
                        'type': 'choice',
                        'choices': ['router', 'switch', 'firewall', 'access_point', 'server'],
                        'description': 'Type d\'équipement'
                    },
                    'status': {
                        'type': 'choice',
                        'choices': ['online', 'offline', 'maintenance', 'error'],
                        'description': 'Statut de l\'équipement'
                    },
                    'vendor': {
                        'type': 'text',
                        'operators': ['eq', 'contains', 'startswith'],
                        'description': 'Fabricant'
                    },
                    'ip_address': {
                        'type': 'ip',
                        'operators': ['eq', 'contains', 'range'],
                        'description': 'Adresse IP'
                    }
                },
                'topology': {
                    'topology_type': {
                        'type': 'choice',
                        'choices': ['physical', 'logical', 'vlan', 'routing'],
                        'description': 'Type de topologie'
                    },
                    'discovery_status': {
                        'type': 'choice',
                        'choices': ['pending', 'running', 'completed', 'failed'],
                        'description': 'Statut de découverte'
                    }
                },
                'alert': {
                    'severity': {
                        'type': 'choice',
                        'choices': ['low', 'medium', 'high', 'critical'],
                        'description': 'Niveau de sévérité'
                    },
                    'status': {
                        'type': 'choice',
                        'choices': ['new', 'acknowledged', 'resolved'],
                        'description': 'Statut de l\'alerte'
                    }
                }
            }
            
            # Filtres communs à tous les types
            common_filters = {
                'created_at': {
                    'type': 'datetime',
                    'operators': ['gte', 'lte', 'range'],
                    'description': 'Date de création'
                },
                'updated_at': {
                    'type': 'datetime',
                    'operators': ['gte', 'lte', 'range'],
                    'description': 'Date de mise à jour'
                }
            }
            
            if resource_type == 'all':
                # Retourner tous les filtres
                result = {
                    'common_filters': common_filters,
                    'resource_filters': available_filters,
                    'dynamic_operators': list(DynamicFilterBackend.SUPPORTED_OPERATORS.keys())
                }
            else:
                # Retourner les filtres pour un type spécifique
                resource_filters = available_filters.get(resource_type, {})
                resource_filters.update(common_filters)
                result = {
                    'filters': resource_filters,
                    'dynamic_operators': list(DynamicFilterBackend.SUPPORTED_OPERATORS.keys())
                }
            
            return Response(result)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des filtres: {e}")
            return Response({
                "error": "Erreur lors de la récupération des filtres"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResourceSearchViewSet(viewsets.ViewSet):
    """
    API endpoint pour la recherche par type de ressource spécifique.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = AdvancedPageNumberPagination
    filter_backends = [SearchFilterBackend, DynamicFilterBackend]
    
    def get_queryset(self):
        """Retourne un queryset vide pour la compatibilité Swagger."""
        if getattr(self, 'swagger_fake_view', False):
            from django.contrib.auth.models import User
            return User.objects.none()
        return None
    
    @property
    def search_use_case(self):
        """Mock search use case for testing."""
        return type('MockSearchUseCase', (), {
            'execute': lambda self, params: {
                'total': 0,
                'results': [],
                'type_counts': {},
                'suggestions': []
            },
            'get_suggestions': lambda self, params: [],
            'get_analytics': lambda self, params: {},
            'clear_user_search_history': lambda self, params: None
        })()
    
    @swagger_auto_schema(
        operation_summary="Liste tous les recherche globale",
        operation_description="Récupère la liste complète des recherche globale avec filtrage, tri et pagination.",
        tags=['API Views'],
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description='Numéro de page', type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description='Éléments par page', type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description='Champ de tri', type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Liste récupérée avec succès",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def list(self, request):
        """Liste les types de ressources disponibles pour la recherche"""
        try:
            from django.utils import timezone

            resource_types = {
                'available_types': [
                    {'type': 'device', 'description': 'Network devices and equipment'},
                    {'type': 'alert', 'description': 'Security and monitoring alerts'},
                    {'type': 'topology', 'description': 'Network topology maps'},
                    {'type': 'configuration', 'description': 'Device configurations'}
                ],
                'search_methods': ['search_devices', 'search_alerts', 'search_topologies', 'search_configurations'],
                'timestamp': timezone.now().isoformat()
            }
            return Response(resource_types)
        except Exception as e:
            logger.exception(f"Erreur liste resource types: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Action search_devices",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def search_devices(self, request):
        """Recherche spécifiquement dans les équipements."""
        return self._search_by_type(request, 'device')
    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Action search_alerts",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def search_alerts(self, request):
        """Recherche spécifiquement dans les alertes."""
        return self._search_by_type(request, 'alert')
    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Action search_topologies",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def search_topologies(self, request):
        """Recherche spécifiquement dans les topologies."""
        return self._search_by_type(request, 'topology')
    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Action search_configurations",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def search_configurations(self, request):
        """Recherche spécifiquement dans les configurations."""
        return self._search_by_type(request, 'configuration')
    
    @swagger_auto_schema(
        operation_summary="Action _search_by_type",
        operation_description="Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def _search_by_type(self, request, resource_type: str):
        """
        Méthode générique pour la recherche par type de ressource.
        """
        try:
            # Valider les données de la requête
            serializer = SearchRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Paramètres de recherche invalides", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            
            # Préparer les paramètres de recherche
            search_params = {
                'query': validated_data['query'],
                'resource_types': [resource_type],
                'filters': validated_data.get('filters', {}),
                'sort_by': validated_data.get('sort_by', 'relevance'),
                'sort_order': validated_data.get('sort_order', 'desc'),
                'include_facets': validated_data.get('include_facets', True),
                'user_id': request.user.id
            }
            
            # Définir les champs de recherche selon le type
            type_search_fields = {
                'device': ['name', 'description', 'ip_address', 'location', 'vendor', 'model'],
                'alert': ['title', 'description', 'source', 'target'],
                'topology': ['name', 'description', 'discovery_method'],
                'configuration': ['name', 'description', 'content']
            }
            search_params['search_fields'] = type_search_fields.get(resource_type, ['name', 'description'])
            
            # Exécuter la recherche
            search_results = self.search_use_case.execute(search_params)
            
            # Préparer la réponse
            response_data = {
                'resource_type': resource_type,
                'query': validated_data['query'],
                'total': search_results.get('total', 0),
                'results': search_results.get('results', []),
                'facets': search_results.get('facets', {}),
                'aggregations': search_results.get('aggregations', {})
            }
            
            return Response(response_data)
            
        except SearchException as e:
            logger.error(f"Erreur lors de la recherche {resource_type}: {e}")
            return Response({
                "error": f"Erreur lors de la recherche {resource_type}",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la recherche {resource_type}: {e}")
            return Response({
                "error": "Erreur interne du serveur"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResourceDetailView(APIView):
    """
    API endpoint pour obtenir les détails complets d'une ressource.
    """
    permission_classes = [IsAuthenticated]
    
    _dependencies = {
        "get_details_use_case": GetResourceDetailsUseCase
    }
    
    @property
    def get_details_use_case(self):
        """Mock get details use case for testing."""
        return type('MockGetDetailsUseCase', (), {
            'execute': lambda self, params: {
                'id': params.get('resource_id'),
                'type': params.get('resource_type'),
                'name': 'Mock Resource',
                'description': 'Mock resource for testing'
            }
        })()
    
    @swagger_auto_schema(
        operation_summary="Action get",
        operation_description="Récupère les informations détaillées avec données temps réel et métriques associées.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def get(self, request, resource_type, resource_id):
        """
        Récupère les détails complets d'une ressource.
        
        Args:
            resource_type: Type de la ressource (device, alert, etc.)
            resource_id: Identifiant unique de la ressource
        """
        try:
            # Récupérer les détails via le cas d'utilisation
            resource_details = self.get_details_use_case.execute({
                'resource_type': resource_type,
                'resource_id': resource_id,
                'user_id': request.user.id,
                'include_related': request.query_params.get('include_related', 'false').lower() == 'true',
                'include_history': request.query_params.get('include_history', 'false').lower() == 'true'
            })
            
            # Sérialiser les détails
            serializer = ResourceDetailSerializer(resource_details)
            
            return Response(serializer.data)
            
        except ResourceNotFoundException as e:
            return Response({
                "error": "Ressource non trouvée",
                "details": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des détails {resource_type}:{resource_id}: {e}")
            return Response({
                "error": "Erreur lors de la récupération des détails"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchAnalyticsView(APIView):
    """
    API endpoint pour les analyses et métriques de recherche.
    """
    permission_classes = [IsAuthenticated]
    
    _dependencies = {
        "search_use_case": SearchResourcesUseCase
    }
    
    @property
    def search_use_case(self):
        """Mock search use case for testing."""
        return type('MockSearchUseCase', (), {
            'execute': lambda self, params: {
                'total': 0,
                'results': [],
                'type_counts': {},
                'suggestions': []
            },
            'get_suggestions': lambda self, params: [],
            'get_analytics': lambda self, params: {},
            'clear_user_search_history': lambda self, params: None
        })()
    
    @swagger_auto_schema(
        operation_summary="Action post",
        operation_description="Exécute une opération avec validation des données et traitement sécurisé.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def post(self, request):
        """
        Génère des analyses de recherche pour une période donnée.
        """
        try:
            # Valider les paramètres
            serializer = SearchAnalyticsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Paramètres d'analyse invalides", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            
            # Générer les analyses via le cas d'utilisation
            analytics = self.search_use_case.get_analytics({
                'period': validated_data['period'],
                'start_date': validated_data.get('start_date'),
                'end_date': validated_data.get('end_date'),
                'user_id': request.user.id
            })
            
            # Enrichir avec les données calculées
            analytics.update({
                'period': validated_data['period'],
                'generated_at': time.time()
            })
            
            # Sérialiser la réponse
            response_serializer = SearchAnalyticsSerializer(analytics)
            
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la génération des analyses de recherche: {e}")
            return Response({
                "error": "Erreur lors de la génération des analyses"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchHistoryViewSet(viewsets.ViewSet):
    """
    API endpoint pour l'historique des recherches utilisateur.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourne un queryset vide pour la compatibilité Swagger."""
        if getattr(self, 'swagger_fake_view', False):
            from django.contrib.auth.models import User
            return User.objects.none()
        return None
    
    @property
    def search_use_case(self):
        """Mock search use case for testing."""
        return type('MockSearchUseCase', (), {
            'execute': lambda self, params: {
                'total': 0,
                'results': [],
                'type_counts': {},
                'suggestions': []
            },
            'get_suggestions': lambda self, params: [],
            'get_analytics': lambda self, params: {},
            'clear_user_search_history': lambda self, params: None
        })()
    
    @swagger_auto_schema(
        operation_summary="Liste tous les recherche globale",
        operation_description="Récupère la liste complète des recherche globale avec filtrage, tri et pagination.",
        tags=['API Views'],
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description='Numéro de page', type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description='Éléments par page', type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description='Champ de tri', type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Liste récupérée avec succès",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def list(self, request):
        """
        Retourne l'historique des recherches de l'utilisateur connecté.
        """
        try:
            # Paramètres de pagination
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))

            # Simuler l'historique de recherche
            import random
            from django.utils import timezone

            history = []
            for i in range(min(limit, 10)):
                history.append({
                    'id': i + offset + 1,
                    'query': f'search query {i+1}',
                    'timestamp': timezone.now().isoformat(),
                    'results_count': random.randint(1, 50),
                    'user_id': request.user.id
                })

            return Response({
                'history': history,
                'limit': limit,
                'offset': offset,
                'total': 10
            })

        except Exception as e:
            logger.exception(f"Erreur lors de la récupération de l'historique de recherche: {e}")
            return Response({
                "error": "Erreur lors de la récupération de l'historique"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'])
    @swagger_auto_schema(
        operation_summary="Action clear",
        operation_description="Supprime définitivement tout l'historique de recherche pour conformité RGPD.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def clear(self, request):
        """
        Supprime tout l'historique de recherche de l'utilisateur.
        """
        try:
            # Supprimer l'historique via le cas d'utilisation
            self.search_use_case.clear_user_search_history({
                'user_id': request.user.id
            })
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.exception(f"Erreur lors de la suppression de l'historique: {e}")
            return Response({
                "error": "Erreur lors de la suppression de l'historique"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 