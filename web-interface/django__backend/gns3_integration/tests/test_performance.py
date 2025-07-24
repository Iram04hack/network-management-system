"""
Tests de performance pour le module GNS3 Integration.
"""

import time
import unittest
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User

from ..application.server_service import ServerService
from ..domain.models.server import GNS3Server
from ..domain.models.project import GNS3Project
from ..domain.models.node import Node


class PerformanceTestCase(TestCase):
    """
    Tests de performance pour le module GNS3 Integration.
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

    def test_server_list_performance_real_data(self):
        """
        Teste les performances de la liste des serveurs avec des données réelles.
        """
        # Création de données de test réelles dans la base
        servers_data = []
        for i in range(50):  # Réduire à 50 pour des tests plus réalistes
            server_data = {
                'name': f'Test Server {i}',
                'host': f'192.168.1.{100+i}',
                'port': 3080,
                'protocol': 'http',
                'username': 'admin',
                'password': 'password',
                'verify_ssl': False,
                'is_local': i < 10  # 10 serveurs locaux, 40 distants
            }
            servers_data.append(server_data)

        # Mesure du temps d'exécution réel
        start_time = time.time()
        
        # Création des serveurs dans la base (simulation réaliste)
        created_servers = []
        for server_data in servers_data[:10]:  # Limiter à 10 pour éviter la surcharge
            response = self.client.post(
                reverse('gns3_integration:gns3-server-list'),
                server_data,
                content_type='application/json'
            )
            if response.status_code == 201:
                created_servers.append(response.data['id'])
        
        # Test de récupération de la liste
        response = self.client.get(reverse('gns3_integration:gns3-server-list'))
        end_time = time.time()

        # Vérifications
        execution_time = end_time - start_time
        self.assertLess(execution_time, 2.0, f"La requête a pris {execution_time} secondes, ce qui est trop long")
        self.assertEqual(response.status_code, 200)

        # Nettoyage
        for server_id in created_servers:
            self.client.delete(reverse('gns3_integration:gns3-server-detail', args=[server_id]))

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_all_projects')
    def test_project_list_performance(self, mock_get_all_projects):
        """
        Teste les performances de la liste des projets.
        """
        # Création de données de test
        projects = []
        for i in range(100):
            project = GNS3Project(
                id=str(i),
                name=f'Test Project {i}',
                server_id='1',
                status='opened',
                path=f'/projects/{i}',
                filename=f'project_{i}.gns3',
                auto_open=False,
                auto_close=True,
                scene_width=2000,
                scene_height=1000
            )
            projects.append(project)

        # Configuration du mock
        mock_get_all_projects.return_value = projects

        # Mesure du temps d'exécution
        start_time = time.time()
        response = self.client.get(reverse('gns3_integration:gns3-project-list'))
        end_time = time.time()

        # Vérifications
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.5, f"La requête a pris {execution_time} secondes, ce qui est trop long")
        self.assertEqual(response.status_code, 200)

    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_all_nodes')
    def test_node_list_performance(self, mock_get_all_nodes):
        """
        Teste les performances de la liste des nœuds.
        """
        # Création de données de test
        nodes = []
        for i in range(500):
            node = Node(
                id=str(i),
                name=f'Test Node {i}',
                project_id='1',
                node_type='vpcs',
                status='started',
                console_port=5000 + i,
                console_type='telnet',
                x=i * 10,
                y=i % 10 * 50
            )
            nodes.append(node)

        # Configuration du mock
        mock_get_all_nodes.return_value = nodes

        # Mesure du temps d'exécution
        start_time = time.time()
        response = self.client.get(reverse('gns3_integration:gns3-node-list'))
        end_time = time.time()

        # Vérifications
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0, f"La requête a pris {execution_time} secondes, ce qui est trop long")
        self.assertEqual(response.status_code, 200)

    @patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.get_node_console')
    @patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.get_node')
    def test_node_console_performance(self, mock_get_node, mock_get_node_console):
        """
        Teste les performances de la récupération de la console d'un nœud.
        """
        # Création de données de test
        node = Node(
            id='1',
            name='Test Node',
            project_id='1',
            node_type='vpcs',
            status='started',
            console_port=5000,
            console_type='telnet',
            x=100,
            y=100
        )

        # Configuration des mocks
        mock_get_node.return_value = node
        mock_get_node_console.return_value = {
            'console_type': 'telnet',
            'console_host': 'localhost',
            'console_port': 5000
        }

        # Mesure du temps d'exécution
        start_time = time.time()
        response = self.client.get(reverse('gns3_integration:gns3-node-console', args=['1']))
        end_time = time.time()

        # Vérifications
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.2, f"La requête a pris {execution_time} secondes, ce qui est trop long")
        self.assertEqual(response.status_code, 200)

    def test_server_create_update_delete_performance(self):
        """
        Teste les performances des opérations CRUD sur les serveurs.
        """
        # Données de test
        server_data = {
            'name': 'Performance Test Server',
            'host': 'localhost',
            'port': 3080,
            'protocol': 'http',
            'username': 'admin',
            'password': 'password',
            'verify_ssl': False,
            'is_local': True
        }

        # Test de création
        with patch('gns3_integration.application.server_service.ServerService.create_server') as mock_create:
            mock_create.return_value = GNS3Server(id='1', **server_data)
            
            start_time = time.time()
            response = self.client.post(
                reverse('gns3_integration:gns3-server-list'),
                server_data,
                content_type='application/json'
            )
            end_time = time.time()
            
            creation_time = end_time - start_time
            self.assertLess(creation_time, 0.3, f"La création a pris {creation_time} secondes, ce qui est trop long")
            self.assertEqual(response.status_code, 201)

        # Test de mise à jour
        updated_data = {**server_data, 'name': 'Updated Server'}
        with patch('gns3_integration.application.server_service.ServerService.update_server') as mock_update:
            mock_update.return_value = GNS3Server(id='1', **updated_data)
            
            start_time = time.time()
            response = self.client.put(
                reverse('gns3_integration:gns3-server-detail', args=['1']),
                updated_data,
                content_type='application/json'
            )
            end_time = time.time()
            
            update_time = end_time - start_time
            self.assertLess(update_time, 0.3, f"La mise à jour a pris {update_time} secondes, ce qui est trop long")
            self.assertEqual(response.status_code, 200)

        # Test de suppression
        with patch('gns3_integration.application.server_service.ServerService.delete_server') as mock_delete:
            mock_delete.return_value = None
            
            start_time = time.time()
            response = self.client.delete(reverse('gns3_integration:gns3-server-detail', args=['1']))
            end_time = time.time()
            
            delete_time = end_time - start_time
            self.assertLess(delete_time, 0.2, f"La suppression a pris {delete_time} secondes, ce qui est trop long")
            self.assertEqual(response.status_code, 204) 