"""
Tests unitaires pour les corrections de la Phase 1 du Dashboard.

Ce fichier teste toutes les corrections apportées dans la Phase 1 :
- Corrections sync/async dans controllers.py
- Activation du module dans urls.py
- Correction des imports dans di_container.py
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.http import JsonResponse

from dashboard.api.controllers import (
    DashboardDataView,
    UserDashboardConfigView,
    NetworkOverviewView,
    TopologyDataView,
    TopologyListView,
    system_health,
    device_metrics
)
from dashboard.di_container import container


class TestPhase1SyncAsyncCorrections(TestCase):
    """
    Tests pour vérifier que les corrections sync/async fonctionnent correctement.
    """
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('dashboard.di_container.container.get_service')
    def test_dashboard_data_view_sync_async_correction(self, mock_get_service):
        """Test que DashboardDataView gère correctement les appels asynchrones."""
        # Mock du service dashboard
        mock_service = Mock()
        mock_service.get_dashboard_overview = AsyncMock(return_value=Mock(
            widgets=[],
            metrics={},
            last_updated=None,
            user_preferences={}
        ))
        mock_get_service.return_value = mock_service
        
        # Créer une requête
        request = self.factory.get('/api/dashboard/data/')
        request.user = self.user
        
        # Tester la vue
        view = DashboardDataView()
        response = view.get(request)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le service asynchrone a été appelé
        mock_service.get_dashboard_overview.assert_called_once_with(self.user.id)
    
    @patch('dashboard.di_container.container.get_service')
    def test_network_overview_view_sync_async_correction(self, mock_get_service):
        """Test que NetworkOverviewView gère correctement les appels asynchrones."""
        # Mock du service network
        mock_service = Mock()
        mock_service.get_network_overview = AsyncMock(return_value=Mock(
            devices=[],
            links=[],
            statistics={},
            alerts=[]
        ))
        mock_get_service.return_value = mock_service
        
        # Créer une requête
        request = self.factory.get('/api/dashboard/network/overview/')
        request.user = self.user
        
        # Tester la vue
        view = NetworkOverviewView()
        response = view.get(request)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le service asynchrone a été appelé
        mock_service.get_network_overview.assert_called_once()


class TestPhase1URLActivation(TestCase):
    """
    Tests pour vérifier que l'activation des URLs fonctionne correctement.
    """
    
    def test_dashboard_urls_are_accessible(self):
        """Test que les URLs du dashboard sont accessibles."""
        # Tester que l'URL principale du dashboard est accessible
        try:
            from django.urls import reverse
            # Ces URLs devraient maintenant être accessibles
            dashboard_data_url = reverse('dashboard:dashboard_data')
            self.assertTrue(dashboard_data_url.startswith('/api/dashboard/'))
        except Exception as e:
            # Si les URLs ne sont pas trouvées, le test échoue
            self.fail(f"Les URLs du dashboard ne sont pas accessibles: {e}")


class TestPhase1DIContainerImports(TestCase):
    """
    Tests pour vérifier que les imports du DI Container fonctionnent correctement.
    """
    
    def test_di_container_imports_successfully(self):
        """Test que le DI Container importe toutes les classes nécessaires."""
        try:
            from dashboard.di_container import container
            self.assertIsNotNone(container)
        except ImportError as e:
            self.fail(f"Erreur d'import du DI Container: {e}")
    
    def test_di_container_services_initialization(self):
        """Test que les services du DI Container s'initialisent correctement."""
        try:
            # Tester l'initialisation des services
            container.init_resources()
            
            # Vérifier que les services principaux sont disponibles
            required_services = [
                'cache_service',
                'monitoring_adapter',
                'network_adapter',
                'dashboard_service',
                'network_overview_service',
                'topology_service'
            ]
            
            for service_name in required_services:
                service = container.get_service(service_name)
                self.assertIsNotNone(service, f"Service {service_name} non trouvé")
                
        except Exception as e:
            self.fail(f"Erreur lors de l'initialisation des services: {e}")
    
    def test_infrastructure_classes_import_correctly(self):
        """Test que toutes les classes d'infrastructure s'importent correctement."""
        try:
            from dashboard.infrastructure.cache_service import RedisCacheService
            from dashboard.infrastructure.monitoring_adapter import MonitoringAdapter
            from dashboard.infrastructure.network_adapter import NetworkAdapter
            from dashboard.infrastructure.services import (
                DashboardDataServiceImpl,
                NetworkOverviewServiceImpl,
                TopologyVisualizationServiceImpl
            )
            
            # Vérifier que les classes peuvent être instanciées
            self.assertTrue(callable(RedisCacheService))
            self.assertTrue(callable(MonitoringAdapter))
            self.assertTrue(callable(NetworkAdapter))
            self.assertTrue(callable(DashboardDataServiceImpl))
            self.assertTrue(callable(NetworkOverviewServiceImpl))
            self.assertTrue(callable(TopologyVisualizationServiceImpl))
            
        except ImportError as e:
            self.fail(f"Erreur d'import des classes d'infrastructure: {e}")


class TestPhase1Integration(TestCase):
    """
    Tests d'intégration pour vérifier que toutes les corrections fonctionnent ensemble.
    """
    
    def setUp(self):
        """Configuration des tests d'intégration."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
    
    @patch('dashboard.di_container.container.get_service')
    def test_full_dashboard_workflow(self, mock_get_service):
        """Test du workflow complet du dashboard."""
        # Mock des services
        mock_dashboard_service = Mock()
        mock_dashboard_service.get_dashboard_overview = AsyncMock(return_value=Mock(
            widgets=[{"type": "test", "data": {}}],
            metrics={"cpu": 50},
            last_updated=None,
            user_preferences={}
        ))
        
        mock_network_service = Mock()
        mock_network_service.get_network_overview = AsyncMock(return_value=Mock(
            devices=[],
            links=[],
            statistics={},
            alerts=[]
        ))
        
        def mock_get_service_side_effect(service_name):
            if service_name == 'dashboard_service':
                return mock_dashboard_service
            elif service_name == 'network_overview_service':
                return mock_network_service
            return Mock()
        
        mock_get_service.side_effect = mock_get_service_side_effect
        
        # Test 1: Récupération des données dashboard
        request = self.factory.get('/api/dashboard/data/')
        request.user = self.user
        
        view = DashboardDataView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        
        # Test 2: Récupération des données réseau
        request = self.factory.get('/api/dashboard/network/overview/')
        request.user = self.user
        
        view = NetworkOverviewView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que tous les services ont été appelés
        mock_dashboard_service.get_dashboard_overview.assert_called()
        mock_network_service.get_network_overview.assert_called()
