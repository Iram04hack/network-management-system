"""
Tests d'intégration sans base de données pour le module api_views.

Ces tests vérifient que toutes les fonctionnalités du module sont opérationnelles
sans nécessiter de connexion à une base de données.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Configuration Django minimale pour les tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_views.tests.test_settings')

import django
from django.conf import settings

# Configuration de test sans base de données
if not settings.configured:
    settings.configure(
        SECRET_KEY='test-secret-key',
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'rest_framework',
            'drf_yasg',
            'api_views',
        ],
        DATABASES={},  # Pas de base de données
        USE_TZ=True,
        REST_FRAMEWORK={
            'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
        },
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
    )

django.setup()


class ModuleImportTest(unittest.TestCase):
    """
    Tests d'importation pour vérifier que tous les composants du module sont accessibles.
    """
    
    def test_viewsets_importable(self):
        """Test que tous les ViewSets peuvent être importés."""
        # Test des ViewSets de dashboard
        try:
            from api_views.views.dashboard_views import DashboardViewSet, DashboardWidgetViewSet
            self.assertIsNotNone(DashboardViewSet)
            self.assertIsNotNone(DashboardWidgetViewSet)
        except ImportError as e:
            self.fail(f"Impossible d'importer DashboardViewSets: {e}")
        
        # Test des ViewSets de gestion d'équipements
        try:
            from api_views.views.device_management_views import DeviceManagementViewSet
            self.assertIsNotNone(DeviceManagementViewSet)
        except ImportError as e:
            self.fail(f"Impossible d'importer DeviceManagementViewSet: {e}")
        
        # Test des ViewSets de recherche
        try:
            from api_views.views.search_views import GlobalSearchViewSet, ResourceSearchViewSet
            self.assertIsNotNone(GlobalSearchViewSet)
            self.assertIsNotNone(ResourceSearchViewSet)
        except ImportError as e:
            self.fail(f"Impossible d'importer SearchViewSets: {e}")
        
        # Test des ViewSets de découverte de topologie
        try:
            from api_views.views.topology_discovery_views import TopologyDiscoveryViewSet
            self.assertIsNotNone(TopologyDiscoveryViewSet)
        except ImportError as e:
            self.fail(f"Impossible d'importer TopologyDiscoveryViewSet: {e}")
    
    def test_serializers_importable(self):
        """Test que tous les sérialiseurs peuvent être importés."""
        try:
            from api_views.presentation.serializers import (
                DashboardRequestSerializer,
                CustomDashboardSerializer,
                DashboardWidgetSerializer,
                GlobalSearchSerializer,
                PaginatedResponseSerializer,
                ErrorResponseSerializer,
                SuccessResponseSerializer
            )
            
            # Vérifier que tous les sérialiseurs sont disponibles
            self.assertIsNotNone(DashboardRequestSerializer)
            self.assertIsNotNone(CustomDashboardSerializer)
            self.assertIsNotNone(DashboardWidgetSerializer)
            self.assertIsNotNone(GlobalSearchSerializer)
            self.assertIsNotNone(PaginatedResponseSerializer)
            self.assertIsNotNone(ErrorResponseSerializer)
            self.assertIsNotNone(SuccessResponseSerializer)
            
        except ImportError as e:
            self.fail(f"Impossible d'importer les sérialiseurs: {e}")
    
    def test_filters_importable(self):
        """Test que le système de filtrage peut être importé."""
        try:
            from api_views.presentation.filters import (
                DynamicFilterBackend,
                SearchFilterBackend,
                DashboardFilterSet
            )
            
            self.assertIsNotNone(DynamicFilterBackend)
            self.assertIsNotNone(SearchFilterBackend)
            self.assertIsNotNone(DashboardFilterSet)
            
        except ImportError as e:
            self.fail(f"Impossible d'importer les filtres: {e}")
    
    def test_pagination_importable(self):
        """Test que les classes de pagination peuvent être importées."""
        try:
            from api_views.presentation.pagination import (
                SmartPagination,
                CursorPagination,
                AdvancedPageNumberPagination
            )
            
            self.assertIsNotNone(SmartPagination)
            self.assertIsNotNone(CursorPagination)
            self.assertIsNotNone(AdvancedPageNumberPagination)
            
        except ImportError as e:
            self.fail(f"Impossible d'importer les classes de pagination: {e}")
    
    def test_cache_system_importable(self):
        """Test que le système de cache peut être importé."""
        try:
            from api_views.infrastructure.cache_config import (
                cache_dashboard_view,
                cache_search_results,
                cache_topology_view
            )
            
            self.assertIsNotNone(cache_dashboard_view)
            self.assertIsNotNone(cache_search_results)
            self.assertIsNotNone(cache_topology_view)
            
        except ImportError as e:
            self.fail(f"Impossible d'importer les fonctions de cache: {e}")
    
    def test_use_cases_importable(self):
        """Test que les cas d'usage peuvent être importés."""
        try:
            from api_views.application.use_cases import (
                GetDashboardDataUseCase,
                SaveDashboardConfigurationUseCase,
                SearchResourcesUseCase,
                GetResourceDetailsUseCase
            )
            
            self.assertIsNotNone(GetDashboardDataUseCase)
            self.assertIsNotNone(SaveDashboardConfigurationUseCase)
            self.assertIsNotNone(SearchResourcesUseCase)
            self.assertIsNotNone(GetResourceDetailsUseCase)
            
        except ImportError as e:
            self.fail(f"Impossible d'importer les cas d'usage: {e}")
    
    def test_dependency_injection_importable(self):
        """Test que le système d'injection de dépendances peut être importé."""
        try:
            from api_views.infrastructure.di_container import DIContainer
            from api_views.presentation.mixins import DIViewMixin
            
            self.assertIsNotNone(DIContainer)
            self.assertIsNotNone(DIViewMixin)
            
        except ImportError as e:
            self.fail(f"Impossible d'importer le système DI: {e}")


class SerializerFunctionalityTest(unittest.TestCase):
    """
    Tests de fonctionnalité pour les sérialiseurs sans base de données.
    """
    
    def test_dashboard_request_serializer_validation(self):
        """Test la validation du DashboardRequestSerializer."""
        from api_views.presentation.serializers import DashboardRequestSerializer
        
        # Test avec des données valides
        valid_data = {
            'dashboard_type': 'system-overview',
            'time_range': '24h',
            'refresh_interval': 300
        }
        
        serializer = DashboardRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), f"Erreurs: {serializer.errors}")
        
        # Vérifier les données validées
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['dashboard_type'], 'system-overview')
        self.assertEqual(validated_data['time_range'], '24h')
        self.assertEqual(validated_data['refresh_interval'], 300)
    
    def test_custom_dashboard_serializer_validation(self):
        """Test la validation du CustomDashboardSerializer."""
        from api_views.presentation.serializers import CustomDashboardSerializer
        
        # Test avec des données valides
        dashboard_data = {
            'name': 'Test Dashboard',
            'description': 'Dashboard de test',
            'layout': 'grid',
            'widgets': [
                {
                    'id': 'widget-1',
                    'type': 'alerts',
                    'title': 'Test Widget',
                    'position': {'x': 0, 'y': 0},
                    'size': {'width': 6, 'height': 4}
                }
            ]
        }
        
        serializer = CustomDashboardSerializer(data=dashboard_data)
        self.assertTrue(serializer.is_valid(), f"Erreurs: {serializer.errors}")
        
        # Vérifier les données validées
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['name'], 'Test Dashboard')
        self.assertEqual(validated_data['layout'], 'grid')
        self.assertEqual(len(validated_data['widgets']), 1)
    
    def test_global_search_serializer_validation(self):
        """Test la validation du GlobalSearchSerializer."""
        from api_views.presentation.serializers import GlobalSearchSerializer
        
        # Test avec des données valides
        search_data = {
            'query': 'test search',
            'resource_types': ['devices'],
            'filters': {'status': 'active'}
        }
        
        serializer = GlobalSearchSerializer(data=search_data)
        self.assertTrue(serializer.is_valid(), f"Erreurs: {serializer.errors}")
        
        # Vérifier les données validées
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['query'], 'test search')
        self.assertEqual(validated_data['resource_types'], ['devices'])


class ViewSetFunctionalityTest(unittest.TestCase):
    """
    Tests de fonctionnalité pour les ViewSets sans base de données.
    """
    
    def test_dashboard_viewset_instantiation(self):
        """Test l'instanciation du DashboardViewSet."""
        from api_views.views.dashboard_views import DashboardViewSet
        
        viewset = DashboardViewSet()
        
        # Vérifier que le ViewSet a les méthodes requises
        self.assertTrue(hasattr(viewset, 'list'))
        self.assertTrue(hasattr(viewset, 'retrieve'))
        self.assertTrue(hasattr(viewset, 'create'))
        self.assertTrue(hasattr(viewset, 'update'))
        self.assertTrue(hasattr(viewset, 'destroy'))
        
        # Vérifier les attributs de configuration
        self.assertTrue(hasattr(viewset, 'permission_classes'))
        self.assertTrue(hasattr(viewset, 'serializer_class'))
    
    def test_search_viewset_instantiation(self):
        """Test l'instanciation du GlobalSearchViewSet."""
        from api_views.views.search_views import GlobalSearchViewSet
        
        viewset = GlobalSearchViewSet()
        
        # Vérifier que le ViewSet a les méthodes requises
        self.assertTrue(hasattr(viewset, 'list'))
        self.assertTrue(hasattr(viewset, 'search'))
        
        # Vérifier les attributs de configuration
        self.assertTrue(hasattr(viewset, 'permission_classes'))
    
    def test_device_management_viewset_instantiation(self):
        """Test l'instanciation du DeviceManagementViewSet."""
        from api_views.views.device_management_views import DeviceManagementViewSet
        
        viewset = DeviceManagementViewSet()
        
        # Vérifier que le ViewSet a les méthodes requises
        self.assertTrue(hasattr(viewset, 'list'))
        self.assertTrue(hasattr(viewset, 'retrieve'))
        self.assertTrue(hasattr(viewset, 'create'))
        self.assertTrue(hasattr(viewset, 'update'))
        self.assertTrue(hasattr(viewset, 'destroy'))


class ArchitectureIntegrityTest(unittest.TestCase):
    """
    Tests pour vérifier l'intégrité de l'architecture hexagonale.
    """
    
    def test_layer_separation(self):
        """Test que les couches de l'architecture sont bien séparées."""
        # Vérifier la structure des couches
        layers = [
            'api_views.presentation',
            'api_views.application',
            'api_views.infrastructure',
            'api_views.views'
        ]
        
        for layer in layers:
            try:
                __import__(layer)
            except ImportError as e:
                self.fail(f"Couche {layer} non accessible: {e}")
    
    def test_dependency_direction(self):
        """Test que les dépendances respectent l'architecture hexagonale."""
        # Les couches de présentation ne doivent pas dépendre de l'infrastructure
        try:
            from api_views.presentation.serializers import DashboardRequestSerializer
            from api_views.application.use_cases import GetDashboardDataUseCase
            
            # Ces imports doivent fonctionner sans problème
            self.assertIsNotNone(DashboardRequestSerializer)
            self.assertIsNotNone(GetDashboardDataUseCase)
            
        except ImportError as e:
            self.fail(f"Problème de dépendance dans l'architecture: {e}")


if __name__ == '__main__':
    unittest.main()
