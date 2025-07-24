"""
Tests d'intégration pour le module GNS3 Integration.
"""

import unittest
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from rest_framework import status

from ..application.server_service import ServerService
from ..application.project_service import ProjectService
from ..application.node_service import NodeService
from ..domain.models.server import GNS3Server
from ..domain.models.project import GNS3Project
from ..domain.models.node import GNS3Node
from ..domain.exceptions import GNS3ConnectionError, GNS3ServerError


class IntegrationTestCase(TestCase):
    """
    Tests d'intégration pour le module GNS3 Integration.
    """

    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client.login(username='admin', password='password')
        
        self.server_service = ServerService()
        self.project_service = ProjectService()
        self.node_service = NodeService()
        
        # Données de test
        self.server_data = {
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
        
        self.project_data = {
            'id': '1',
            'name': 'Test Project',
            'server_id': '1',
            'status': 'opened',
            'path': '/projects/1',
            'filename': 'project_1.gns3',
            'auto_open': False,
            'auto_close': True,
            'scene_width': 2000,
            'scene_height': 1000
        }
        
        self.node_data = {
            'id': '1',
            'name': 'Test Node',
            'project_id': '1',
            'node_type': 'vpcs',
            'status': 'started',
            'console': 5000,
            'console_type': 'telnet',
            'x': 100,
            'y': 100
        }

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_all_servers')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_all_projects')
    def test_server_project_integration(self, mock_get_all_projects, mock_get_all_servers):
        """
        Teste l'intégration entre les serveurs et les projets.
        """
        # Configuration des mocks
        server = GNS3Server(**self.server_data)
        project = GNS3Project(**self.project_data)
        
        mock_get_all_servers.return_value = [server]
        mock_get_all_projects.return_value = [project]
        
        # Test de récupération des serveurs
        response = self.client.get(reverse('gns3_integration:gns3-server-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test de récupération des projets
        response = self.client.get(reverse('gns3_integration:gns3-project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Vérification que le projet est associé au bon serveur
        self.assertEqual(response.data[0]['server_id'], server.id)

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_project')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_all_nodes')
    def test_project_node_integration(self, mock_get_all_nodes, mock_get_project):
        """
        Teste l'intégration entre les projets et les nœuds.
        """
        # Configuration des mocks
        project = GNS3Project(**self.project_data)
        node = GNS3Node(**self.node_data)
        
        mock_get_project.return_value = project
        mock_get_all_nodes.return_value = [node]
        
        # Test de récupération du projet
        response = self.client.get(reverse('gns3_integration:gns3-project-detail', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test de récupération des nœuds du projet
        response = self.client.get(reverse('gns3_integration:gns3-project-nodes', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Vérification que le nœud est associé au bon projet
        self.assertEqual(response.data[0]['project_id'], project.id)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_server')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_project')
    def test_server_project_creation_flow(self, mock_create_project, mock_create_server, mock_test_connection):
        """
        Teste le flux complet de création d'un serveur puis d'un projet.
        """
        # Configuration des mocks
        server = GNS3Server(**self.server_data)
        project = GNS3Project(**self.project_data)
        
        mock_test_connection.return_value = True
        mock_create_server.return_value = server
        mock_create_project.return_value = project
        
        # Création du serveur
        response = self.client.post(
            reverse('gns3_integration:gns3-server-list'),
            self.server_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Création du projet
        response = self.client.post(
            reverse('gns3_integration:gns3-project-list'),
            self.project_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérification que le projet est bien associé au serveur
        self.assertEqual(response.data['server_id'], server.id)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.start_node')
    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.stop_node')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_node')
    def test_node_start_stop_flow(self, mock_get_node, mock_stop_node, mock_start_node):
        """
        Teste le flux de démarrage et d'arrêt d'un nœud.
        """
        # Configuration des mocks
        node = GNS3Node(**self.node_data)
        started_node = GNS3Node(**{**self.node_data, 'status': 'started'})
        stopped_node = GNS3Node(**{**self.node_data, 'status': 'stopped'})
        
        mock_get_node.return_value = node
        mock_start_node.return_value = started_node
        mock_stop_node.return_value = stopped_node
        
        # Démarrage du nœud
        response = self.client.post(reverse('gns3_integration:gns3-node-start', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'started')
        
        # Arrêt du nœud
        response = self.client.post(reverse('gns3_integration:gns3-node-stop', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'stopped')

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.get_node_console')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_node')
    def test_node_console_integration(self, mock_get_node, mock_get_node_console):
        """
        Teste l'intégration de la console d'un nœud.
        """
        # Configuration des mocks
        node = GNS3Node(**self.node_data)
        console_data = {
            'console_type': 'telnet',
            'console_host': 'localhost',
            'console_port': 5000
        }
        
        mock_get_node.return_value = node
        mock_get_node_console.return_value = console_data
        
        # Récupération des informations de console
        response = self.client.get(reverse('gns3_integration:gns3-node-console', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['console_type'], 'telnet')
        self.assertEqual(response.data['console_port'], 5000)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_error_handling(self, mock_get_server, mock_test_connection):
        """
        Teste la gestion des erreurs.
        """
        # Configuration des mocks
        server = GNS3Server(**self.server_data)
        
        mock_get_server.return_value = server
        mock_test_connection.side_effect = GNS3ConnectionError("Impossible de se connecter au serveur")
        
        # Test de connexion au serveur
        response = self.client.get(reverse('gns3_integration:gns3-server-test-connection', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Erreur de connexion', response.data['error'])

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.get_server_stats')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_server')
    def test_server_stats_integration(self, mock_get_server, mock_get_server_stats):
        """
        Teste l'intégration des statistiques du serveur.
        """
        # Configuration des mocks
        server = GNS3Server(**self.server_data)
        stats_data = {
            'cpu_usage_percent': 25.5,
            'memory_usage_percent': 60.2,
            'disk_usage_percent': 45.8,
            'uptime': 3600
        }
        
        mock_get_server.return_value = server
        mock_get_server_stats.return_value = stats_data
        
        # Récupération des statistiques du serveur
        response = self.client.get(reverse('gns3_integration:gns3-server-stats', args=['1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cpu_usage_percent'], 25.5)
        self.assertEqual(response.data['memory_usage_percent'], 60.2) 