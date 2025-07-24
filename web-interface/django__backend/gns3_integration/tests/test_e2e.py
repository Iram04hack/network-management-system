"""
Tests end-to-end pour le module GNS3 Integration.
"""

import unittest
from unittest.mock import patch, MagicMock

from django.test import TestCase, LiveServerTestCase
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from rest_framework import status

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from ..application.server_service import ServerService
from ..application.project_service import ProjectService
from ..application.node_service import NodeService
from ..domain.models.server import GNS3Server
from ..domain.models.project import GNS3Project
from ..domain.models.node import Node
from ..domain.exceptions import GNS3ConnectionError, GNS3ServerError


class E2ETestCase(LiveServerTestCase):
    """
    Tests end-to-end pour le module GNS3 Integration.
    """

    @classmethod
    def setUpClass(cls):
        """
        Configuration initiale pour les tests.
        """
        super().setUpClass()
        try:
            # Configuration du navigateur headless pour les tests
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            cls.browser = webdriver.Chrome(options=options)
            cls.browser.implicitly_wait(10)
        except Exception as e:
            print(f"Erreur lors de la configuration du navigateur: {e}")
            cls.browser = None

    @classmethod
    def tearDownClass(cls):
        """
        Nettoyage après les tests.
        """
        if cls.browser:
            cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        """
        Configuration initiale pour chaque test.
        """
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client.login(username='admin', password='password')
        
        # Services
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

    @unittest.skipIf(False, "Test nécessitant un navigateur et un environnement graphique - activé pour tests")
    def test_server_management_ui(self):
        """
        Teste l'interface utilisateur de gestion des serveurs.
        """
        if not self.browser:
            self.skipTest("Navigateur non disponible")
            
        # Connexion à l'application
        self.browser.get(f"{self.live_server_url}/admin/login/")
        username_input = self.browser.find_element(By.NAME, "username")
        password_input = self.browser.find_element(By.NAME, "password")
        username_input.send_keys("admin")
        password_input.send_keys("password")
        self.browser.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        # Navigation vers la page de gestion des serveurs GNS3
        self.browser.get(f"{self.live_server_url}/gns3/servers/")
        
        # Vérification que la page est chargée correctement
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "server-list"))
            )
            # Vérification de la présence du bouton d'ajout
            add_button = self.browser.find_element(By.ID, "add-server-button")
            self.assertTrue(add_button.is_displayed())
            
            # Clic sur le bouton d'ajout pour ouvrir le formulaire
            add_button.click()
            
            # Attente du chargement du formulaire
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "server-form"))
            )
            
            # Remplissage du formulaire
            self.browser.find_element(By.ID, "id_name").send_keys("E2E Test Server")
            self.browser.find_element(By.ID, "id_host").send_keys("localhost")
            self.browser.find_element(By.ID, "id_port").send_keys("3080")
            self.browser.find_element(By.ID, "id_username").send_keys("admin")
            self.browser.find_element(By.ID, "id_password").send_keys("password")
            
            # Soumission du formulaire
            self.browser.find_element(By.ID, "submit-button").click()
            
            # Attente de la redirection vers la liste des serveurs
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "server-list"))
            )
            
            # Vérification que le serveur a été ajouté
            server_items = self.browser.find_elements(By.CSS_SELECTOR, ".server-item")
            self.assertTrue(any("E2E Test Server" in item.text for item in server_items))
            
        except TimeoutException:
            self.fail("La page n'a pas été chargée correctement")

    @unittest.skipIf(False, "Test nécessitant un serveur GNS3 réel - activé pour tests")
    def test_complete_workflow(self):
        """
        Teste un flux de travail complet avec un serveur GNS3 réel.
        
        Note: Ce test nécessite un serveur GNS3 réel et est désactivé par défaut.
        Pour l'activer, remplacer skipIf(True, ...) par skipIf(False, ...).
        """
        # Création d'un serveur
        response = self.client.post(
            reverse('gns3_integration:gns3-server-list'),
            {
                'name': 'Real GNS3 Server',
                'host': 'localhost',
                'port': 3080,
                'protocol': 'http',
                'username': '',
                'password': '',
                'verify_ssl': False,
                'is_local': True
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        server_id = response.data['id']
        
        # Création d'un projet
        response = self.client.post(
            reverse('gns3_integration:gns3-project-list'),
            {
                'name': 'E2E Test Project',
                'server_id': server_id
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data['id']
        
        # Création d'un nœud VPCS
        response = self.client.post(
            reverse('gns3_integration:gns3-node-list'),
            {
                'name': 'PC1',
                'project_id': project_id,
                'node_type': 'vpcs',
                'x': 100,
                'y': 100
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        node1_id = response.data['id']
        
        # Création d'un deuxième nœud VPCS
        response = self.client.post(
            reverse('gns3_integration:gns3-node-list'),
            {
                'name': 'PC2',
                'project_id': project_id,
                'node_type': 'vpcs',
                'x': 300,
                'y': 100
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        node2_id = response.data['id']
        
        # Création d'un lien entre les deux nœuds
        response = self.client.post(
            reverse('gns3_integration:gns3-link-list'),
            {
                'project_id': project_id,
                'node_a_id': node1_id,
                'port_a_id': 0,
                'node_b_id': node2_id,
                'port_b_id': 0
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        link_id = response.data['id']
        
        # Démarrage des nœuds
        response = self.client.post(reverse('gns3_integration:gns3-node-start', args=[node1_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.post(reverse('gns3_integration:gns3-node-start', args=[node2_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Récupération des informations de console
        response = self.client.get(reverse('gns3_integration:gns3-node-console', args=[node1_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Arrêt des nœuds
        response = self.client.post(reverse('gns3_integration:gns3-node-stop', args=[node1_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.post(reverse('gns3_integration:gns3-node-stop', args=[node2_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Suppression du lien
        response = self.client.delete(reverse('gns3_integration:gns3-link-detail', args=[link_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Suppression des nœuds
        response = self.client.delete(reverse('gns3_integration:gns3-node-detail', args=[node1_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        response = self.client.delete(reverse('gns3_integration:gns3-node-detail', args=[node2_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Suppression du projet
        response = self.client.delete(reverse('gns3_integration:gns3-project-detail', args=[project_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Suppression du serveur
        response = self.client.delete(reverse('gns3_integration:gns3-server-detail', args=[server_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_api_workflow_with_mocks(self):
        """
        Teste un flux de travail complet avec des mocks.
        """
        # Configuration des patchs pour les appels externes
        with patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.test_connection', return_value=True), \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_server') as mock_create_server, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_project') as mock_create_project, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_node') as mock_create_node, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.create_link') as mock_create_link, \
             patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.start_node') as mock_start_node, \
             patch('gns3_integration.infrastructure.gns3_client_impl.GNS3ClientImpl.stop_node') as mock_stop_node, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.delete_link') as mock_delete_link, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.delete_node') as mock_delete_node, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.delete_project') as mock_delete_project, \
             patch('gns3_integration.infrastructure.gns3_repository_impl.GNS3RepositoryImpl.delete_server') as mock_delete_server:
            
            # Configuration des retours des mocks
            server = GNS3Server(**self.server_data)
            project = GNS3Project(**self.project_data)
            node1 = Node(**{**self.node_data, 'id': '1', 'name': 'PC1'})
            node2 = Node(**{**self.node_data, 'id': '2', 'name': 'PC2'})
            
            mock_create_server.return_value = server
            mock_create_project.return_value = project
            mock_create_node.side_effect = [node1, node2]
            mock_create_link.return_value = {'id': '1', 'node_a_id': '1', 'node_b_id': '2'}
            mock_start_node.side_effect = [
                {**node1.__dict__, 'status': 'started'},
                {**node2.__dict__, 'status': 'started'}
            ]
            mock_stop_node.side_effect = [
                {**node1.__dict__, 'status': 'stopped'},
                {**node2.__dict__, 'status': 'stopped'}
            ]
            
            # Création d'un serveur
            response = self.client.post(
                reverse('gns3_integration:gns3-server-list'),
                self.server_data,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Création d'un projet
            response = self.client.post(
                reverse('gns3_integration:gns3-project-list'),
                self.project_data,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Création d'un nœud VPCS
            response = self.client.post(
                reverse('gns3_integration:gns3-node-list'),
                {
                    'name': 'PC1',
                    'project_id': '1',
                    'node_type': 'vpcs',
                    'x': 100,
                    'y': 100
                },
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Création d'un deuxième nœud VPCS
            response = self.client.post(
                reverse('gns3_integration:gns3-node-list'),
                {
                    'name': 'PC2',
                    'project_id': '1',
                    'node_type': 'vpcs',
                    'x': 300,
                    'y': 100
                },
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Création d'un lien entre les deux nœuds
            response = self.client.post(
                reverse('gns3_integration:gns3-link-list'),
                {
                    'project_id': '1',
                    'node_a_id': '1',
                    'port_a_id': 0,
                    'node_b_id': '2',
                    'port_b_id': 0
                },
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Démarrage des nœuds
            response = self.client.post(reverse('gns3_integration:gns3-node-start', args=['1']))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response = self.client.post(reverse('gns3_integration:gns3-node-start', args=['2']))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Arrêt des nœuds
            response = self.client.post(reverse('gns3_integration:gns3-node-stop', args=['1']))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response = self.client.post(reverse('gns3_integration:gns3-node-stop', args=['2']))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Suppression du lien
            response = self.client.delete(reverse('gns3_integration:gns3-link-detail', args=['1']))
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # Suppression des nœuds
            response = self.client.delete(reverse('gns3_integration:gns3-node-detail', args=['1']))
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            response = self.client.delete(reverse('gns3_integration:gns3-node-detail', args=['2']))
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # Suppression du projet
            response = self.client.delete(reverse('gns3_integration:gns3-project-detail', args=['1']))
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # Suppression du serveur
            response = self.client.delete(reverse('gns3_integration:gns3-server-detail', args=['1']))
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # Vérification des appels aux mocks
            mock_create_server.assert_called_once()
            mock_create_project.assert_called_once()
            self.assertEqual(mock_create_node.call_count, 2)
            mock_create_link.assert_called_once()
            self.assertEqual(mock_start_node.call_count, 2)
            self.assertEqual(mock_stop_node.call_count, 2)
            mock_delete_link.assert_called_once()
            self.assertEqual(mock_delete_node.call_count, 2)
            mock_delete_project.assert_called_once()
            mock_delete_server.assert_called_once()