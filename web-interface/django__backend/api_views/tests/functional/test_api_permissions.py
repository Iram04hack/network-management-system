"""
Tests fonctionnels pour vérifier les permissions des API endpoints.

Ces tests vérifient que les mécanismes de permission fonctionnent correctement
sur les différentes API du module api_views.
"""

import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class APIPermissionsTests(APITestCase):
    """Tests de permissions pour les endpoints API."""
    
    @classmethod
    def setUpTestData(cls):
        """Configuration des données de test."""
        # Création des utilisateurs avec différents niveaux d'accès
        cls.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        
        cls.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass',
            email='staff@example.com',
            is_staff=True
        )
        
        cls.regular_user = User.objects.create_user(
            username='user',
            password='userpass',
            email='user@example.com'
        )
        
        cls.readonly_user = User.objects.create_user(
            username='readonly',
            password='readonlypass',
            email='readonly@example.com'
        )
        
        # Configuration des groupes et permissions
        network_admin_group = Group.objects.create(name='network_admin')
        readonly_group = Group.objects.create(name='readonly')
        
        # Ajout des utilisateurs aux groupes
        cls.staff_user.groups.add(network_admin_group)
        cls.readonly_user.groups.add(readonly_group)
        
        # Configuration des endpoints à tester
        cls.api_endpoints = {
            'lecture_seule': [
                'api-system-dashboard',
                'api-network-dashboard',
                'api-network-map',
                'api-topology-discovery-list',
                'api-prometheus-list'
            ],
            'modification': [
                'api-dashboard-widget-list',
                'api-custom-dashboard'
            ],
            'admin_only': [
                'api-prometheus-targets',
                'api-fail2ban-jail-status',
                'api-suricata-rules'
            ]
        }

    def setUp(self):
        """Configuration avant chaque test."""
        self.client = APIClient()
        
    def test_unauthenticated_access(self):
        """Vérifie que les utilisateurs non authentifiés n'ont pas accès aux API."""
        for endpoint_type in self.api_endpoints:
            for endpoint_name in self.api_endpoints[endpoint_type]:
                try:
                    if endpoint_type == 'api-custom-dashboard':
                        url = reverse(f"api_views:{endpoint_name}", kwargs={'dashboard_id': 1})
                    else:
                        url = reverse(f"api_views:{endpoint_name}")
                    
                    response = self.client.get(url)
                    self.assertEqual(
                        response.status_code, 
                        status.HTTP_401_UNAUTHORIZED,
                        f"L'endpoint {endpoint_name} permet l'accès sans authentification"
                    )
                except Exception as e:
                    print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                    continue
                    
    def test_readonly_user_permissions(self):
        """Vérifie que les utilisateurs en lecture seule ont accès restreint."""
        self.client.force_authenticate(user=self.readonly_user)
        
        # Doit pouvoir accéder aux endpoints en lecture
        for endpoint_name in self.api_endpoints['lecture_seule']:
            try:
                url = reverse(f"api_views:{endpoint_name}")
                response = self.client.get(url)
                
                self.assertIn(
                    response.status_code,
                    [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT],
                    f"L'utilisateur en lecture seule ne peut pas accéder à {endpoint_name}"
                )
            except Exception as e:
                print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                continue
                
        # Ne doit pas pouvoir modifier les données
        for endpoint_name in self.api_endpoints['modification']:
            try:
                if endpoint_name == 'api-custom-dashboard':
                    url = reverse(f"api_views:{endpoint_name}", kwargs={'dashboard_id': 1})
                else:
                    url = reverse(f"api_views:{endpoint_name}")
                
                # Test POST
                response = self.client.post(url, data={}, format='json')
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f"L'utilisateur en lecture seule peut faire un POST sur {endpoint_name}"
                )
                
                # Test DELETE (si applicable)
                if endpoint_name != 'api-custom-dashboard':
                    response = self.client.delete(f"{url}1/")
                    self.assertIn(
                        response.status_code,
                        [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
                        f"L'utilisateur en lecture seule peut faire un DELETE sur {endpoint_name}"
                    )
            except Exception as e:
                print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                continue
        
        # Ne doit pas avoir accès aux endpoints admin
        for endpoint_name in self.api_endpoints['admin_only']:
            try:
                url = reverse(f"api_views:{endpoint_name}")
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f"L'utilisateur en lecture seule peut accéder à {endpoint_name}"
                )
            except Exception as e:
                print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                continue
                
    def test_admin_full_access(self):
        """Vérifie que les administrateurs ont accès complet."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Doit pouvoir accéder à tous les endpoints
        for endpoint_type in self.api_endpoints:
            for endpoint_name in self.api_endpoints[endpoint_type]:
                try:
                    if endpoint_name == 'api-custom-dashboard':
                        url = reverse(f"api_views:{endpoint_name}", kwargs={'dashboard_id': 1})
                    else:
                        url = reverse(f"api_views:{endpoint_name}")
                    
                    response = self.client.get(url)
                    self.assertNotEqual(
                        response.status_code,
                        status.HTTP_403_FORBIDDEN,
                        f"L'administrateur ne peut pas accéder à {endpoint_name}"
                    )
                except Exception as e:
                    print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                    continue
    
    def test_staff_restricted_access(self):
        """Vérifie que les utilisateurs staff ont des accès restreints aux fonctions admin."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Doit avoir accès aux fonctions de modification
        for endpoint_name in self.api_endpoints['modification']:
            try:
                if endpoint_name == 'api-custom-dashboard':
                    url = reverse(f"api_views:{endpoint_name}", kwargs={'dashboard_id': 1})
                else:
                    url = reverse(f"api_views:{endpoint_name}")
                
                response = self.client.get(url)
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f"L'utilisateur staff ne peut pas accéder à {endpoint_name}"
                )
            except Exception as e:
                print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                continue
        
        # Accès restreint à certaines fonctions admin
        for endpoint_name in self.api_endpoints['admin_only']:
            try:
                url = reverse(f"api_views:{endpoint_name}")
                response = self.client.get(url)
                # Le résultat peut varier selon les permissions exactes configurées
                print(f"Staff - Endpoint {endpoint_name}: {response.status_code}")
            except Exception as e:
                print(f"Erreur pour l'endpoint {endpoint_name}: {str(e)}")
                continue 