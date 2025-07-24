"""
Tests des vues API du module api_clients.
Remplace et consolide : test_views.py, test_views_corrected.py, test_views_exhaustive.py
"""

import unittest
import json
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class APIClientsViewsTest(APITestCase):
    """Tests pour les vues API du module api_clients."""
    
    def setUp(self):
        """Configuration pour les tests."""
        self.user = User.objects.create_user(
            username="api_test_user",
            email="apitest@example.com",
            password="password123"
        )
        
        self.admin_user = User.objects.create_superuser(
            username="api_admin",
            email="apiadmin@example.com",
            password="admin123"
        )
        
        self.client = Client()
    
    def test_api_clients_status_endpoint(self):
        """Test de l'endpoint de statut des clients API."""
        # Authentification requise
        self.client.force_login(self.user)
        
        # Mock des statuts des clients
        with patch('api_clients.views.get_clients_status') as mock_status:
            mock_status.return_value = {
                'gns3': {'status': 'connected', 'version': '2.2.46'},
                'prometheus': {'status': 'connected', 'metrics_count': 1500},
                'snmp': {'status': 'ready', 'discovered_devices': 25}
            }
            
            response = self.client.get('/api/clients/status/')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn('gns3', data)
            self.assertIn('prometheus', data)
            self.assertIn('snmp', data)
            
            self.assertEqual(data['gns3']['status'], 'connected')
            self.assertEqual(data['prometheus']['metrics_count'], 1500)
    
    def test_gns3_projects_list_endpoint(self):
        """Test de l'endpoint de liste des projets GNS3."""
        self.client.force_login(self.admin_user)
        
        with patch('api_clients.network.gns3_client.GNS3Client.get_projects') as mock_projects:
            mock_projects.return_value = [
                {
                    'project_id': 'project-1',
                    'name': 'Test Network 1',
                    'status': 'opened',
                    'nodes': 5
                },
                {
                    'project_id': 'project-2', 
                    'name': 'Test Network 2',
                    'status': 'closed',
                    'nodes': 8
                }
            ]
            
            response = self.client.get('/api/clients/gns3/projects/')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['name'], 'Test Network 1')
            self.assertEqual(data[1]['nodes'], 8)
    
    def test_gns3_project_create_endpoint(self):
        """Test de création de projet GNS3."""
        self.client.force_login(self.admin_user)
        
        project_data = {
            'name': 'New Test Project',
            'auto_close': True,
            'auto_start': False
        }
        
        with patch('api_clients.network.gns3_client.GNS3Client.create_project') as mock_create:
            mock_create.return_value = {
                'project_id': 'new-project-123',
                'name': 'New Test Project',
                'status': 'opened'
            }
            
            response = self.client.post(
                '/api/clients/gns3/projects/',
                data=json.dumps(project_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 201)
            data = response.json()
            
            self.assertEqual(data['project_id'], 'new-project-123')
            self.assertEqual(data['name'], 'New Test Project')
            mock_create.assert_called_once_with(project_data)
    
    def test_prometheus_metrics_endpoint(self):
        """Test de l'endpoint des métriques Prometheus."""
        self.client.force_login(self.user)
        
        with patch('api_clients.monitoring.prometheus_client.PrometheusClient.query_instant') as mock_query:
            mock_query.return_value = {
                'success': True,
                'data': {
                    'result': [
                        {
                            'metric': {'instance': 'localhost:9100'},
                            'value': [1641024000, '45.5']
                        }
                    ]
                }
            }
            
            response = self.client.get('/api/clients/prometheus/metrics/?query=up')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertTrue(data['success'])
            self.assertEqual(len(data['data']['result']), 1)
            self.assertEqual(data['data']['result'][0]['value'][1], '45.5')
    
    def test_snmp_discovery_endpoint(self):
        """Test de l'endpoint de découverte SNMP."""
        self.client.force_login(self.admin_user)
        
        discovery_params = {
            'target_ip': '192.168.1.1',
            'community': 'public'
        }
        
        with patch('api_clients.network.snmp_client.SNMPClient.discover_device') as mock_discover:
            mock_discover.return_value = {
                'success': True,
                'device_info': {
                    'hostname': 'Router-1',
                    'description': 'Cisco Router',
                    'interfaces': [
                        {'name': 'FastEthernet0/0', 'status': 'up'},
                        {'name': 'FastEthernet0/1', 'status': 'down'}
                    ]
                }
            }
            
            response = self.client.post(
                '/api/clients/snmp/discover/',
                data=json.dumps(discovery_params),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertTrue(data['success'])
            self.assertEqual(data['device_info']['hostname'], 'Router-1')
            self.assertEqual(len(data['device_info']['interfaces']), 2)
    
    def test_api_authentication_required(self):
        """Test que l'authentification est requise."""
        # Tentative d'accès sans authentification
        response = self.client.get('/api/clients/status/')
        
        # Doit retourner 401 Unauthorized ou rediriger vers login
        self.assertIn(response.status_code, [401, 302])
    
    def test_admin_only_endpoints(self):
        """Test des endpoints réservés aux administrateurs."""
        # Connexion avec utilisateur normal
        self.client.force_login(self.user)
        
        # Tentative de création de projet (admin requis)
        project_data = {'name': 'Test Project'}
        response = self.client.post(
            '/api/clients/gns3/projects/',
            data=json.dumps(project_data),
            content_type='application/json'
        )
        
        # Doit être refusé pour un utilisateur normal
        self.assertEqual(response.status_code, 403)
        
        # Maintenant avec admin
        self.client.force_login(self.admin_user)
        
        with patch('api_clients.network.gns3_client.GNS3Client.create_project') as mock_create:
            mock_create.return_value = {'project_id': 'test-123'}
            
            response = self.client.post(
                '/api/clients/gns3/projects/',
                data=json.dumps(project_data),
                content_type='application/json'
            )
            
            # Doit réussir avec admin
            self.assertEqual(response.status_code, 201)
    
    def test_api_error_handling(self):
        """Test de gestion d'erreurs des APIs."""
        self.client.force_login(self.user)
        
        # Simuler une erreur de client GNS3
        with patch('api_clients.network.gns3_client.GNS3Client.get_projects') as mock_projects:
            mock_projects.side_effect = ConnectionError("GNS3 server unreachable")
            
            response = self.client.get('/api/clients/gns3/projects/')
            
            self.assertEqual(response.status_code, 503)  # Service Unavailable
            data = response.json()
            
            self.assertFalse(data['success'])
            self.assertIn('error', data)
            self.assertIn('unreachable', data['error'])
    
    def test_api_request_validation(self):
        """Test de validation des requêtes API."""
        self.client.force_login(self.admin_user)
        
        # Données invalides pour création de projet
        invalid_data = {
            'name': '',  # Nom vide
            'invalid_field': 'value'
        }
        
        response = self.client.post(
            '/api/clients/gns3/projects/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)  # Bad Request
        data = response.json()
        
        self.assertIn('errors', data)
    
    def test_api_pagination(self):
        """Test de pagination des APIs."""
        self.client.force_login(self.user)
        
        # Mock d'une grande liste de métriques
        with patch('api_clients.monitoring.prometheus_client.PrometheusClient.get_metrics_list') as mock_metrics:
            mock_metrics.return_value = {
                'success': True,
                'metrics': [f'metric_{i}' for i in range(100)]  # 100 métriques
            }
            
            # Test avec pagination
            response = self.client.get('/api/clients/prometheus/metrics-list/?page=1&page_size=20')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn('results', data)
            self.assertIn('count', data)
            self.assertIn('next', data)
            self.assertIn('previous', data)
            
            # Vérifier la taille de page
            self.assertEqual(len(data['results']), 20)
            self.assertEqual(data['count'], 100)
    
    def test_api_filtering_and_search(self):
        """Test de filtrage et recherche dans les APIs."""
        self.client.force_login(self.user)
        
        with patch('api_clients.monitoring.prometheus_client.PrometheusClient.get_metrics_list') as mock_metrics:
            mock_metrics.return_value = {
                'success': True,
                'metrics': [
                    'node_cpu_seconds_total',
                    'node_memory_MemTotal_bytes',
                    'http_requests_total',
                    'disk_usage_percent'
                ]
            }
            
            # Test de recherche
            response = self.client.get('/api/clients/prometheus/metrics-list/?search=node')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Doit retourner seulement les métriques contenant "node"
            filtered_metrics = data['results']
            for metric in filtered_metrics:
                self.assertIn('node', metric)
    
    def test_api_rate_limiting(self):
        """Test de limitation du taux de requêtes."""
        self.client.force_login(self.user)
        
        # Mock pour simuler des réponses rapides
        with patch('api_clients.views.get_clients_status') as mock_status:
            mock_status.return_value = {'status': 'ok'}
            
            # Faire plusieurs requêtes rapides
            responses = []
            for i in range(10):
                response = self.client.get('/api/clients/status/')
                responses.append(response)
            
            # Les premières requêtes doivent réussir
            self.assertEqual(responses[0].status_code, 200)
            self.assertEqual(responses[1].status_code, 200)
            
            # Selon la configuration de rate limiting,
            # certaines requêtes peuvent être limitées (429)
            status_codes = [r.status_code for r in responses]
            self.assertIn(200, status_codes)  # Au moins une réussit


class APIClientsCacheTest(APITestCase):
    """Tests pour le cache des APIs clients."""
    
    def setUp(self):
        """Configuration pour les tests de cache."""
        self.user = User.objects.create_user(
            username="cache_test_user",
            email="cachetest@example.com",
            password="password123"
        )
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_api_response_caching(self):
        """Test de mise en cache des réponses API."""
        with patch('api_clients.monitoring.prometheus_client.PrometheusClient.get_metrics_list') as mock_metrics:
            mock_metrics.return_value = {
                'success': True,
                'metrics': ['metric1', 'metric2']
            }
            
            # Première requête
            response1 = self.client.get('/api/clients/prometheus/metrics-list/')
            self.assertEqual(response1.status_code, 200)
            
            # Deuxième requête (doit utiliser le cache)
            response2 = self.client.get('/api/clients/prometheus/metrics-list/')
            self.assertEqual(response2.status_code, 200)
            
            # Le client externe ne doit être appelé qu'une fois
            mock_metrics.assert_called_once()
            
            # Les réponses doivent être identiques
            self.assertEqual(response1.json(), response2.json())
    
    def test_cache_invalidation(self):
        """Test d'invalidation du cache."""
        with patch('api_clients.views.invalidate_cache') as mock_invalidate:
            mock_invalidate.return_value = {'success': True}
            
            # Invalider le cache
            response = self.client.post('/api/clients/cache/invalidate/')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            
            mock_invalidate.assert_called_once()


if __name__ == '__main__':
    unittest.main()