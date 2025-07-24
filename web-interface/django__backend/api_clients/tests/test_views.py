"""
Tests pour les vues de l'application api_clients.

Ce module contient les tests pour les vues de l'application api_clients.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from api_clients.container import APIClientContainer


class SwaggerJSONViewTests(TestCase):
    """
    Tests pour la vue SwaggerJSONView.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.api_client = APIClient()
        self.example_swagger_doc = {
            'openapi': '3.0.0',
            'info': {
                'title': 'Example API',
                'version': '1.0.0',
                'description': "API d'exemple pour les tests"
            },
            'paths': {
                '/example': {
                    'get': {
                        'summary': 'Récupère un exemple',
                        'responses': {
                            '200': {
                                'description': 'Succès',
                                'content': {
                                    'application/json': {
                                        'schema': {
                                            'type': 'object',
                                            'properties': {
                                                'id': {'type': 'integer'},
                                                'name': {'type': 'string'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    @patch.object(APIClientContainer, 'get_client')
    def test_swagger_json_view_success(self, mock_get_client):
        """
        Teste que la vue SwaggerJSONView retourne correctement le document Swagger.
        """
        # Configuration du mock
        mock_client = MagicMock()
        mock_client.get_swagger_doc.return_value = self.example_swagger_doc
        mock_get_client.return_value = mock_client
        
        # Appel de la vue
        url = reverse('api_clients_swagger_json', kwargs={'client_name': 'example'})
        response = self.api_client.get(url)
        
        # Vérification des résultats
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.example_swagger_doc)
        mock_get_client.assert_called_once_with('example')
        mock_client.get_swagger_doc.assert_called_once()
    
    @patch.object(APIClientContainer, 'get_client')
    def test_swagger_json_view_client_not_found(self, mock_get_client):
        """
        Teste que la vue SwaggerJSONView retourne une erreur 404 si le client n'existe pas.
        """
        # Configuration du mock
        mock_get_client.return_value = None
        
        # Appel de la vue
        url = reverse('api_clients_swagger_json', kwargs={'client_name': 'nonexistent'})
        response = self.api_client.get(url)
        
        # Vérification des résultats
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Client API nonexistent non trouvé'})
        mock_get_client.assert_called_once_with('nonexistent')


class ClientsHealthViewTests(TestCase):
    """
    Tests pour la vue ClientsHealthView.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.api_client = APIClient()
    
    @patch.object(APIClientContainer, 'get_all_clients')
    def test_clients_health_view_success(self, mock_get_all_clients):
        """
        Teste que la vue ClientsHealthView retourne correctement l'état de santé des clients.
        """
        # Configuration du mock
        mock_example_client = MagicMock()
        mock_example_client.check_health.return_value = True
        mock_network_client = MagicMock()
        mock_network_client.check_health.return_value = True
        mock_get_all_clients.return_value = {
            'example': mock_example_client,
            'network': mock_network_client
        }
        
        # Appel de la vue
        url = reverse('api_clients_health')
        response = self.api_client.get(url)
        
        # Vérification des résultats
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'healthy',
            'clients': {
                'example': {
                    'status': 'healthy',
                    'message': 'OK'
                },
                'network': {
                    'status': 'healthy',
                    'message': 'OK'
                }
            }
        })
        mock_get_all_clients.assert_called_once()
        mock_example_client.check_health.assert_called_once()
        mock_network_client.check_health.assert_called_once()
    
    @patch.object(APIClientContainer, 'get_all_clients')
    def test_clients_health_view_with_unhealthy_client(self, mock_get_all_clients):
        """
        Teste que la vue ClientsHealthView retourne correctement l'état de santé des clients
        lorsqu'un client est en mauvaise santé.
        """
        # Configuration du mock
        mock_example_client = MagicMock()
        mock_example_client.check_health.return_value = True
        mock_network_client = MagicMock()
        mock_network_client.check_health.return_value = False
        mock_get_all_clients.return_value = {
            'example': mock_example_client,
            'network': mock_network_client
        }
        
        # Appel de la vue
        url = reverse('api_clients_health')
        response = self.api_client.get(url)
        
        # Vérification des résultats
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'unhealthy',
            'clients': {
                'example': {
                    'status': 'healthy',
                    'message': 'OK'
                },
                'network': {
                    'status': 'unhealthy',
                    'message': 'Service indisponible'
                }
            }
        })
        mock_get_all_clients.assert_called_once()
        mock_example_client.check_health.assert_called_once()
        mock_network_client.check_health.assert_called_once() 