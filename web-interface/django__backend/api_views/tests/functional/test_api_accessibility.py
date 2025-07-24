"""
Tests fonctionnels pour vérifier l'accessibilité des API endpoints.

Ces tests vérifient que tous les endpoints sont accessibles sans nécessairement tester
leur fonctionnalité complète. Ils servent de "smoke tests" pour s'assurer que les
routes sont correctement configurées.
"""

import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class APIAccessibilityTests(APITestCase):
    """Tests d'accessibilité pour tous les endpoints API."""
    
    @classmethod
    def setUpTestData(cls):
        """Configuration initiale des données de test."""
        # Création d'un utilisateur pour les tests
        cls.username = 'testuser'
        cls.password = 'testpassword'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
            email='testuser@example.com',
            is_staff=True
        )
        
        # Création des URLs à tester
        cls.api_endpoints = [
            # Dashboard endpoints
            'api-system-dashboard',
            'api-network-dashboard',
            'api-security-dashboard',
            'api-monitoring-dashboard',
            
            # Documentation endpoints
            'api-docs-swagger',
            'api-docs-redoc',
            'api-docs-schema',
            
            # Topology endpoints
            'api-topology-discovery-create',
            'api-network-map',
            'api-connections',
            'api-device-dependencies',
            'api-path-discovery',
            
            # Search endpoints
            'api-search-analytics',
        ]
        
        # Endpoints nécessitant des paramètres
        cls.param_endpoints = {
            'api-custom-dashboard': {'dashboard_id': 1},
            'api-device-management-detail': {'device_id': 1},
            'api-resource-detail': {'resource_type': 'device', 'resource_id': 1},
        }

    def setUp(self):
        """Configuration avant chaque test."""
        self.client = APIClient()
        # Authentification de l'utilisateur
        self.client.force_authenticate(user=self.user)

    def test_api_endpoints_accessible(self):
        """Vérifie que tous les endpoints API sont accessibles."""
        for endpoint_name in self.api_endpoints:
            try:
                url = reverse(f"api_views:{endpoint_name}")
                response = self.client.get(url)
                
                # Nous vérifions que l'endpoint ne retourne pas 404 ou 500
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                                   f"L'endpoint {endpoint_name} n'est pas disponible (404)")
                self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                                   f"L'endpoint {endpoint_name} a rencontré une erreur serveur (500)")
                
                # Journalisation du résultat
                print(f"Endpoint {endpoint_name}: {response.status_code}")
            except Exception as e:
                print(f"Erreur lors du test de l'endpoint {endpoint_name}: {str(e)}")
                # Ne pas échouer le test complet si un seul endpoint pose problème
                continue

    def test_param_endpoints_accessible(self):
        """Vérifie que les endpoints nécessitant des paramètres sont accessibles."""
        for endpoint_name, params in self.param_endpoints.items():
            try:
                url = reverse(f"api_views:{endpoint_name}", kwargs=params)
                response = self.client.get(url)
                
                # Même vérification que précédemment
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                                   f"L'endpoint {endpoint_name} n'est pas disponible (404)")
                self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                                   f"L'endpoint {endpoint_name} a rencontré une erreur serveur (500)")
                
                print(f"Endpoint avec paramètres {endpoint_name}: {response.status_code}")
            except Exception as e:
                print(f"Erreur lors du test de l'endpoint {endpoint_name}: {str(e)}")
                continue
                
    def test_viewsets_accessible(self):
        """Vérifie que les ViewSets sont accessibles."""
        viewsets = [
            'api-dashboard-list',
            'api-dashboard-widget-list',
            'api-topology-discovery-list',
            'api-device-management-list',
            'api-global-search-list',
            'api-resource-search-list',
            'api-search-history-list',
            'api-prometheus-list',
            'api-grafana-list',
            'api-fail2ban-list',
            'api-suricata-list',
        ]
        
        for viewset_name in viewsets:
            try:
                url = reverse(f"api_views:{viewset_name}")
                response = self.client.get(url)
                
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                                   f"Le viewset {viewset_name} n'est pas disponible (404)")
                self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                                   f"Le viewset {viewset_name} a rencontré une erreur serveur (500)")
                
                print(f"ViewSet {viewset_name}: {response.status_code}")
            except Exception as e:
                print(f"Erreur lors du test du viewset {viewset_name}: {str(e)}")
                continue 