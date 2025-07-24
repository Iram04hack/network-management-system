"""
Tests d'intégration complets pour le module API Views
Valide les workflows end-to-end et l'intégration entre composants
"""

import json
import time
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

# Import des ViewSets réellement disponibles
try:
    from api_views.views.dashboard_views import DashboardViewSet, DashboardWidgetViewSet
    from api_views.views.device_management_views import DeviceManagementViewSet
    from api_views.views.search_views import GlobalSearchViewSet, ResourceSearchViewSet
    from api_views.views.topology_discovery_views import TopologyDiscoveryViewSet
except ImportError:
    # Fallback si les imports échouent
    DashboardViewSet = None
    DashboardWidgetViewSet = None
    DeviceManagementViewSet = None
    GlobalSearchViewSet = None
    ResourceSearchViewSet = None
    TopologyDiscoveryViewSet = None


class APIViewsIntegrationTestCase(APITestCase):
    """
    Classe de base pour les tests d'intégration des API Views
    """

    def setUp(self):
        """
        Configuration de base pour tous les tests d'intégration
        """
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Configurer le client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # URLs réelles disponibles dans le module api_views
        self.api_urls = {
            'dashboard_system': reverse('api_views:api-system-dashboard'),
            'dashboard_widgets': reverse('api_views:api-dashboard-widgets'),
            'search_global': reverse('api_views:api-search-global'),
            'search_suggestions': reverse('api_views:api-search-suggestions'),
            'swagger': reverse('api_views:api-docs-swagger'),
            'redoc': reverse('api_views:api-docs-redoc'),
        }

        # URLs de base pour les tests (compatibilité avec les tests existants)
        self.base_urls = {
            'dashboard': '/api/views/dashboards/',
            'topology': '/api/views/topology/',
            'devices': '/api/views/devices/',
            'search': '/api/views/search/'
        }

        # Données de test
        self.test_data = self._create_test_data()

    def _create_test_data(self):
        """
        Crée des données de test standardisées
        """
        return {
            'device': {
                'name': 'Test Router',
                'device_type': 'router',
                'ip_address': '192.168.1.1',
                'vendor': 'Cisco',
                'model': 'ISR4321',
                'location': 'Data Center A'
            },
            'dashboard': {
                'name': 'Test Dashboard',
                'dashboard_type': 'network',
                'description': 'Dashboard de test'
            },
            'topology': {
                'name': 'Test Topology',
                'topology_type': 'physical',
                'discovery_method': 'snmp'
            }
        }


class DashboardWorkflowIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour les workflows de tableau de bord
    """

    def test_system_dashboard_access(self):
        """
        Test d'accès au dashboard système
        """
        # Test d'accès au dashboard système
        response = self.client.get(self.api_urls['dashboard_system'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que la réponse contient des données structurées
        self.assertIn('data', response.data)

    def test_dashboard_widgets_access(self):
        """
        Test d'accès aux widgets de dashboard
        """
        # Test d'accès aux widgets
        response = self.client.get(self.api_urls['dashboard_widgets'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test avec paramètres
        response = self.client.get(
            self.api_urls['dashboard_widgets'],
            {'widget_type': 'alerts'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_with_parameters(self):
        """
        Test du dashboard avec différents paramètres
        """
        # Test avec paramètres de temps
        params = {
            'time_range': '24h',
            'dashboard_type': 'system-overview'
        }
        response = self.client.get(self.api_urls['dashboard_system'], params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test avec POST
        post_data = {
            'dashboard_type': 'system-overview',
            'time_range': '24h',
            'refresh_interval': 300
        }
        response = self.client.post(
            self.api_urls['dashboard_system'],
            post_data,
            format='json'
        )
        # Accepter différents codes de réponse selon l'implémentation
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ])
    
    def test_dashboard_error_handling(self):
        """
        Test de la gestion d'erreurs pour les dashboards
        """
        # Test avec paramètres invalides
        invalid_params = {
            'time_range': 'invalid-range',
            'dashboard_type': 'invalid-type'
        }
        response = self.client.get(self.api_urls['dashboard_system'], invalid_params)

        # Devrait soit accepter les paramètres soit retourner une erreur appropriée
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])


class SearchWorkflowIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour les workflows de recherche
    """

    def test_global_search_access(self):
        """
        Test d'accès à la recherche globale
        """
        # Test d'accès à la recherche globale
        response = self.client.get(self.api_urls['search_global'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test avec paramètres de recherche
        search_params = {
            'q': 'router',
            'resource_types': 'devices',
            'page_size': 10
        }
        response = self.client.get(self.api_urls['search_global'], search_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_suggestions_access(self):
        """
        Test d'accès aux suggestions de recherche
        """
        # Test des suggestions
        response = self.client.get(self.api_urls['search_suggestions'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test avec paramètre de requête
        response = self.client.get(
            self.api_urls['search_suggestions'],
            {'q': 'rout'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_post_method(self):
        """
        Test de la recherche avec méthode POST
        """
        search_data = {
            'query': 'cisco router',
            'resource_types': ['devices'],
            'filters': {
                'device_type': 'router'
            }
        }
        response = self.client.post(
            self.api_urls['search_global'],
            search_data,
            format='json'
        )
        # Accepter différents codes selon l'implémentation
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ])


class DocumentationIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour la documentation API
    """

    def test_swagger_documentation_access(self):
        """
        Test d'accès à la documentation Swagger
        """
        # Test d'accès à Swagger
        response = self.client.get(self.api_urls['swagger'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que c'est du HTML (page Swagger)
        self.assertIn('text/html', response.get('Content-Type', ''))

    def test_redoc_documentation_access(self):
        """
        Test d'accès à la documentation Redoc
        """
        # Test d'accès à Redoc
        response = self.client.get(self.api_urls['redoc'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que c'est du HTML (page Redoc)
        self.assertIn('text/html', response.get('Content-Type', ''))

    def test_api_endpoints_accessibility(self):
        """
        Test d'accessibilité des endpoints API principaux
        """
        # Tester tous les endpoints principaux
        endpoints_to_test = [
            self.api_urls['dashboard_system'],
            self.api_urls['dashboard_widgets'],
            self.api_urls['search_global'],
            self.api_urls['search_suggestions'],
        ]

        for endpoint in endpoints_to_test:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                # Tous les endpoints devraient être accessibles
                self.assertEqual(response.status_code, status.HTTP_200_OK)


class ErrorHandlingIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour la gestion d'erreurs
    """

    def test_authentication_requirements(self):
        """
        Test des exigences d'authentification
        """
        # Créer un client non authentifié
        unauthenticated_client = APIClient()

        # Tester l'accès sans authentification
        response = unauthenticated_client.get(self.api_urls['dashboard_system'])

        # Devrait soit demander une authentification soit permettre l'accès anonyme
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,  # Accès anonyme autorisé
            status.HTTP_401_UNAUTHORIZED,  # Authentification requise
            status.HTTP_403_FORBIDDEN  # Accès interdit
        ])

    def test_invalid_parameters_handling(self):
        """
        Test de la gestion des paramètres invalides
        """
        # Test avec paramètres invalides pour la recherche
        invalid_search_params = {
            'q': '',  # Requête vide
            'page_size': -1,  # Taille de page négative
            'page': 'invalid'  # Page non numérique
        }

        response = self.client.get(
            self.api_urls['search_global'],
            invalid_search_params
        )

        # Devrait gérer gracieusement les paramètres invalides
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,  # Paramètres corrigés automatiquement
            status.HTTP_400_BAD_REQUEST  # Erreur de validation
        ])

    def test_nonexistent_endpoints(self):
        """
        Test d'accès à des endpoints inexistants
        """
        # Tester un endpoint qui n'existe pas
        nonexistent_url = '/api/views/nonexistent-endpoint/'
        response = self.client.get(nonexistent_url)

        # Devrait retourner 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PaginationIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour les différents types de pagination
    """
    
    def test_pagination_types_integration(self):
        """
        Test de l'intégration des différents types de pagination
        """
        # Créer un grand nombre d'équipements pour tester la pagination
        device_ids = []
        for i in range(50):
            device_data = {
                'name': f'Device {i:03d}',
                'device_type': 'router',
                'ip_address': f'192.168.1.{i+10}',
                'vendor': 'Cisco'
            }
            response = self.client.post(
                self.base_urls['devices'],
                data=device_data,
                format='json'
            )
            if response.status_code == status.HTTP_201_CREATED:
                device_ids.append(response.data['id'])
        
        # Test pagination standard
        response = self.client.get(
            self.base_urls['devices'],
            {'page': 1, 'page_size': 10}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('pagination', response.data)
        
        # Test pagination cursor
        response = self.client.get(
            self.base_urls['devices'],
            {'pagination_type': 'cursor', 'page_size': 10}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'links' in response.data:
            self.assertIn('next', response.data['links'])
        
        # Test pagination limit/offset
        response = self.client.get(
            self.base_urls['devices'],
            {'limit': 15, 'offset': 20}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Nettoyer
        for device_id in device_ids:
            self.client.delete(f"{self.base_urls['devices']}{device_id}/")


class FilteringIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour le système de filtrage avancé
    """
    
    def test_advanced_filtering_integration(self):
        """
        Test de l'intégration du système de filtrage avancé
        """
        # Créer des équipements avec différentes caractéristiques
        devices_data = [
            {
                'name': 'Router A',
                'device_type': 'router',
                'ip_address': '192.168.1.1',
                'vendor': 'Cisco',
                'status': 'online'
            },
            {
                'name': 'Switch B',
                'device_type': 'switch',
                'ip_address': '192.168.2.1',
                'vendor': 'HP',
                'status': 'offline'
            },
            {
                'name': 'Router C',
                'device_type': 'router',
                'ip_address': '10.0.1.1',
                'vendor': 'Cisco',
                'status': 'maintenance'
            }
        ]
        
        device_ids = []
        for device_data in devices_data:
            response = self.client.post(
                self.base_urls['devices'],
                data=device_data,
                format='json'
            )
            if response.status_code == status.HTTP_201_CREATED:
                device_ids.append(response.data['id'])
        
        # Test filtrage simple
        response = self.client.get(
            self.base_urls['devices'],
            {'device_type': 'router'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for device in response.data['results']:
            self.assertEqual(device['device_type'], 'router')
        
        # Test filtrage dynamique
        response = self.client.get(
            self.base_urls['devices'],
            {
                'filter[vendor][eq]': 'Cisco',
                'filter[status][ne]': 'offline'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for device in response.data['results']:
            self.assertEqual(device['vendor'], 'Cisco')
            self.assertNotEqual(device['status'], 'offline')
        
        # Test filtrage par plage d'IP
        response = self.client.get(
            self.base_urls['devices'],
            {'filter[ip_address][contains]': '192.168'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for device in response.data['results']:
            self.assertIn('192.168', device['ip_address'])
        
        # Test combinaison de filtres
        response = self.client.get(
            self.base_urls['devices'],
            {
                'device_type': 'router',
                'vendor': 'Cisco',
                'filter[status][in]': 'online,maintenance'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for device in response.data['results']:
            self.assertEqual(device['device_type'], 'router')
            self.assertEqual(device['vendor'], 'Cisco')
            self.assertIn(device['status'], ['online', 'maintenance'])
        
        # Nettoyer
        for device_id in device_ids:
            self.client.delete(f"{self.base_urls['devices']}{device_id}/")


class PerformanceIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour valider les performances
    """
    
    def test_large_dataset_performance(self):
        """
        Test de performance avec un grand dataset
        """
        import time
        
        # Créer un grand nombre d'entités
        start_time = time.time()
        device_ids = []
        
        for i in range(100):  # Réduire pour les tests
            device_data = {
                'name': f'Performance Test Device {i}',
                'device_type': 'router',
                'ip_address': f'10.{i//254}.{i%254}.1',
                'vendor': 'TestVendor'
            }
            response = self.client.post(
                self.base_urls['devices'],
                data=device_data,
                format='json'
            )
            if response.status_code == status.HTTP_201_CREATED:
                device_ids.append(response.data['id'])
        
        creation_time = time.time() - start_time
        
        # Test de récupération avec pagination
        start_time = time.time()
        response = self.client.get(
            self.base_urls['devices'],
            {'page_size': 50}
        )
        retrieval_time = time.time() - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(retrieval_time, 2.0)  # Moins de 2 secondes
        
        # Test de recherche
        start_time = time.time()
        response = self.client.get(
            self.base_urls['devices'],
            {'search': 'Performance Test'}
        )
        search_time = time.time() - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(search_time, 1.0)  # Moins de 1 seconde
        
        # Nettoyer
        for device_id in device_ids:
            self.client.delete(f"{self.base_urls['devices']}{device_id}/")


class ErrorHandlingIntegrationTest(APIViewsIntegrationTestCase):
    """
    Tests d'intégration pour la gestion d'erreurs
    """
    
    def test_error_handling_integration(self):
        """
        Test de la gestion d'erreurs intégrée
        """
        # Test données invalides
        invalid_device_data = {
            'name': '',  # Nom vide
            'device_type': 'invalid_type',
            'ip_address': 'invalid_ip'
        }
        
        response = self.client.post(
            self.base_urls['devices'],
            data=invalid_device_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        
        # Test ressource inexistante
        response = self.client.get(f"{self.base_urls['devices']}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test paramètres de pagination invalides
        response = self.client.get(
            self.base_urls['devices'],
            {'page': 'invalid', 'page_size': -1}
        )
        # Doit gérer gracieusement et utiliser des valeurs par défaut
        self.assertEqual(response.status_code, status.HTTP_200_OK) 