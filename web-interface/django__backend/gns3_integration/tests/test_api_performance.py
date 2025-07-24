"""
Tests de performance pour l'API REST GNS3.

Ce module contient des tests de performance pour mesurer les temps de réponse
des différentes vues de l'API REST GNS3.
"""
import time
import json
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from ..models import Server, Project, Node, Link, Template
from unittest.mock import patch, MagicMock

class GNS3APIPerformanceTestCase(APITestCase):
    """Tests de performance pour l'API REST GNS3."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Création d'un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Création d'un serveur de test
        self.server = Server.objects.create(
            name='Test Server',
            host='192.168.1.100',
            port=3080,
            user='admin',
            password='password',
            protocol='http'
        )
        
        # Création d'un projet de test
        self.project = Project.objects.create(
            name='Test Project',
            project_id='00000000-0000-0000-0000-000000000001',
            server=self.server,
            status='opened'
        )
        
        # Création de nœuds de test
        self.node1 = Node.objects.create(
            name='Test Node 1',
            node_id='00000000-0000-0000-0000-000000000001',
            node_type='vpcs',
            status='started',
            project=self.project,
            console_port=5000,
            x=100,
            y=100
        )
        
        self.node2 = Node.objects.create(
            name='Test Node 2',
            node_id='00000000-0000-0000-0000-000000000002',
            node_type='qemu',
            status='stopped',
            project=self.project,
            console_port=5001,
            x=200,
            y=200
        )
        
        # Création d'un lien de test
        self.link = Link.objects.create(
            link_id='00000000-0000-0000-0000-000000000001',
            project=self.project,
            source_node=self.node1,
            source_port=0,
            destination_node=self.node2,
            destination_port=0
        )
        
        # Création d'un template de test
        self.template = Template.objects.create(
            name='Test Template',
            template_id='00000000-0000-0000-0000-000000000001',
            template_type='qemu',
            server=self.server,
            image='ubuntu-20.04.qcow2',
            console_type='vnc'
        )
        
        # Configuration du client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def measure_response_time(self, url, method='get', data=None):
        """Mesure le temps de réponse d'une requête API."""
        start_time = time.time()
        
        if method == 'get':
            response = self.client.get(url)
        elif method == 'post':
            response = self.client.post(url, data, format='json')
        elif method == 'put':
            response = self.client.put(url, data, format='json')
        elif method == 'delete':
            response = self.client.delete(url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return response, response_time
    
    def test_server_list_performance(self):
        """Test de performance pour la liste des serveurs."""
        url = reverse('server-list')
        response, response_time = self.measure_response_time(url)
        
        self.assertEqual(response.status_code, 200)
        print(f"Temps de réponse pour la liste des serveurs: {response_time:.4f} secondes")
        
        # Vérification que le temps de réponse est acceptable (< 0.5 secondes)
        self.assertLess(response_time, 0.5)
    
    def test_project_list_performance(self):
        """Test de performance pour la liste des projets."""
        url = reverse('project-list')
        response, response_time = self.measure_response_time(url)
        
        self.assertEqual(response.status_code, 200)
        print(f"Temps de réponse pour la liste des projets: {response_time:.4f} secondes")
        
        # Vérification que le temps de réponse est acceptable (< 0.5 secondes)
        self.assertLess(response_time, 0.5)
    
    def test_node_list_performance(self):
        """Test de performance pour la liste des nœuds."""
        url = reverse('node-list')
        response, response_time = self.measure_response_time(url)
        
        self.assertEqual(response.status_code, 200)
        print(f"Temps de réponse pour la liste des nœuds: {response_time:.4f} secondes")
        
        # Vérification que le temps de réponse est acceptable (< 0.5 secondes)
        self.assertLess(response_time, 0.5)
    
    def test_link_list_performance(self):
        """Test de performance pour la liste des liens."""
        url = reverse('link-list')
        response, response_time = self.measure_response_time(url)
        
        self.assertEqual(response.status_code, 200)
        print(f"Temps de réponse pour la liste des liens: {response_time:.4f} secondes")
        
        # Vérification que le temps de réponse est acceptable (< 0.5 secondes)
        self.assertLess(response_time, 0.5)
    
    def test_template_list_performance(self):
        """Test de performance pour la liste des templates."""
        url = reverse('template-list')
        response, response_time = self.measure_response_time(url)
        
        self.assertEqual(response.status_code, 200)
        print(f"Temps de réponse pour la liste des templates: {response_time:.4f} secondes")
        
        # Vérification que le temps de réponse est acceptable (< 0.5 secondes)
        self.assertLess(response_time, 0.5)
    
    @patch('gns3_integration.services.node_service.NodeService.start_node')
    def test_node_start_performance(self, mock_start_node):
        """Test de performance pour le démarrage d'un nœud."""
        mock_start_node.return_value = True
        
        url = reverse('node-start', kwargs={'pk': self.node1.pk})
        response, response_time = self.measure_response_time(url, method='post')
        
        self.assertEqual(response.status_code, 200)
        print(f"Temps de réponse pour le démarrage d'un nœud: {response_time:.4f} secondes")
        
        # Vérification que le temps de réponse est acceptable (< 1 seconde)
        self.assertLess(response_time, 1.0)