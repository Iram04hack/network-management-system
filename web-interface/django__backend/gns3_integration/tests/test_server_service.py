"""
Tests pour le service de serveur GNS3.
"""

import unittest
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from ..application.server_service import ServerService
from ..domain.exceptions import GNS3ConnectionError, GNS3ServerError
from ..domain.models.server import GNS3Server


class ServerServiceTestCase(TestCase):
    """
    Tests pour le service de serveur GNS3.
    """

    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.server_service = ServerService()
        self.mock_server_data = {
            'id': '1',
            'name': 'Test Server',
            'host': 'localhost',
            'port': 3080,
            'protocol': 'http',
            'username': 'admin',
            'password': 'password',
            'verify_ssl': False,
            'is_local': True
        }
        self.mock_server = GNS3Server(**self.mock_server_data)

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_all_servers')
    def test_get_all_servers(self, mock_get_all_servers):
        """
        Teste la récupération de tous les serveurs.
        """
        # Configuration du mock
        mock_get_all_servers.return_value = [self.mock_server]

        # Appel de la méthode à tester
        servers = self.server_service.get_all_servers()

        # Vérifications
        mock_get_all_servers.assert_called_once()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0].id, self.mock_server.id)
        self.assertEqual(servers[0].name, self.mock_server.name)

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_get_server_success(self, mock_get_server):
        """
        Teste la récupération d'un serveur spécifique avec succès.
        """
        # Configuration du mock
        mock_get_server.return_value = self.mock_server

        # Appel de la méthode à tester
        server = self.server_service.get_server('1')

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        self.assertEqual(server.id, self.mock_server.id)
        self.assertEqual(server.name, self.mock_server.name)

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_get_server_not_found(self, mock_get_server):
        """
        Teste la récupération d'un serveur inexistant.
        """
        # Configuration du mock
        mock_get_server.side_effect = ObjectDoesNotExist()

        # Vérification que l'exception est bien levée
        with self.assertRaises(ObjectDoesNotExist):
            self.server_service.get_server('999')

        # Vérifications
        mock_get_server.assert_called_once_with('999')

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_server')
    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    def test_create_server_success(self, mock_test_connection, mock_create_server):
        """
        Teste la création d'un serveur avec succès.
        """
        # Configuration des mocks
        mock_test_connection.return_value = True
        mock_create_server.return_value = self.mock_server

        # Appel de la méthode à tester
        server = self.server_service.create_server(self.mock_server_data)

        # Vérifications
        mock_test_connection.assert_called_once()
        mock_create_server.assert_called_once()
        self.assertEqual(server.id, self.mock_server.id)
        self.assertEqual(server.name, self.mock_server.name)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    def test_create_server_connection_error(self, mock_test_connection):
        """
        Teste la création d'un serveur avec erreur de connexion.
        """
        # Configuration du mock
        mock_test_connection.return_value = False

        # Vérification que l'exception est bien levée
        with self.assertRaises(GNS3ConnectionError):
            self.server_service.create_server(self.mock_server_data)

        # Vérifications
        mock_test_connection.assert_called_once()

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.update_server')
    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_update_server_success(self, mock_get_server, mock_test_connection, mock_update_server):
        """
        Teste la mise à jour d'un serveur avec succès.
        """
        # Configuration des mocks
        mock_get_server.return_value = self.mock_server
        mock_test_connection.return_value = True
        updated_server = GNS3Server(**{**self.mock_server_data, 'name': 'Updated Server'})
        mock_update_server.return_value = updated_server

        # Appel de la méthode à tester
        server = self.server_service.update_server('1', {'name': 'Updated Server'})

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        mock_test_connection.assert_called_once()
        mock_update_server.assert_called_once()
        self.assertEqual(server.id, updated_server.id)
        self.assertEqual(server.name, 'Updated Server')

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.delete_server')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_delete_server_success(self, mock_get_server, mock_delete_server):
        """
        Teste la suppression d'un serveur avec succès.
        """
        # Configuration des mocks
        mock_get_server.return_value = self.mock_server
        mock_delete_server.return_value = None

        # Appel de la méthode à tester
        self.server_service.delete_server('1')

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        mock_delete_server.assert_called_once_with('1')

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_test_connection_success(self, mock_get_server, mock_test_connection):
        """
        Teste la vérification de la connexion avec succès.
        """
        # Configuration des mocks
        mock_get_server.return_value = self.mock_server
        mock_test_connection.return_value = True

        # Appel de la méthode à tester
        result = self.server_service.test_connection('1')

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        mock_test_connection.assert_called_once()
        self.assertTrue(result)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_test_connection_failure(self, mock_get_server, mock_test_connection):
        """
        Teste la vérification de la connexion avec échec.
        """
        # Configuration des mocks
        mock_get_server.return_value = self.mock_server
        mock_test_connection.return_value = False

        # Appel de la méthode à tester
        result = self.server_service.test_connection('1')

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        mock_test_connection.assert_called_once()
        self.assertFalse(result)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.get_server_stats')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_get_server_stats_success(self, mock_get_server, mock_get_server_stats):
        """
        Teste la récupération des statistiques du serveur avec succès.
        """
        # Configuration des mocks
        mock_get_server.return_value = self.mock_server
        mock_stats = {
            'cpu_usage_percent': 25.5,
            'memory_usage_percent': 60.2,
            'disk_usage_percent': 45.8,
            'uptime': 3600
        }
        mock_get_server_stats.return_value = mock_stats

        # Appel de la méthode à tester
        stats = self.server_service.get_server_stats('1')

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        mock_get_server_stats.assert_called_once()
        self.assertEqual(stats, mock_stats)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.get_server_stats')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_get_server_stats_error(self, mock_get_server, mock_get_server_stats):
        """
        Teste la récupération des statistiques du serveur avec erreur.
        """
        # Configuration des mocks
        mock_get_server.return_value = self.mock_server
        mock_get_server_stats.side_effect = GNS3ServerError("Erreur lors de la récupération des statistiques")

        # Vérification que l'exception est bien levée
        with self.assertRaises(GNS3ServerError):
            self.server_service.get_server_stats('1')

        # Vérifications
        mock_get_server.assert_called_once_with('1')
        mock_get_server_stats.assert_called_once() 