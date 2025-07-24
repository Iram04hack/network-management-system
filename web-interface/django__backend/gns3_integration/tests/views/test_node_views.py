import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from ...models import Server, Project, Node
from ...serializers import NodeSerializer
from unittest.mock import patch, MagicMock

class NodeViewSetTestCase(APITestCase):
    """Tests pour les vues de nœuds GNS3."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Création d'un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Création d'un serveur et d'un projet de test
        self.server = Server.objects.create(
            name='Test Server',
            host='192.168.1.100',
            port=3080,
            user='admin',
            password='password',
            protocol='http'
        )
        
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
        
        # Configuration du client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # URLs pour les tests
        self.list_url = reverse('node-list')
        self.detail_url = reverse('node-detail', kwargs={'pk': self.node1.pk})
    
    def test_get_node_list(self):
        """Test de récupération de la liste des nœuds."""
        response = self.client.get(self.list_url)
        nodes = Node.objects.all()
        serializer = NodeSerializer(nodes, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_get_node_detail(self):
        """Test de récupération des détails d'un nœud."""
        response = self.client.get(self.detail_url)
        node = Node.objects.get(pk=self.node1.pk)
        serializer = NodeSerializer(node)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_node(self):
        """Test de création d'un nœud."""
        data = {
            'name': 'New Test Node',
            'node_id': '00000000-0000-0000-0000-000000000003',
            'node_type': 'vpcs',
            'status': 'stopped',
            'project': self.project.id,
            'console_port': 5002,
            'x': 300,
            'y': 300
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Node.objects.count(), 3)
        self.assertEqual(Node.objects.get(name='New Test Node').node_id, 
                         '00000000-0000-0000-0000-000000000003')
    
    def test_update_node(self):
        """Test de mise à jour d'un nœud."""
        data = {
            'name': 'Updated Node',
            'node_id': self.node1.node_id,
            'node_type': self.node1.node_type,
            'status': 'stopped',
            'project': self.project.id,
            'console_port': self.node1.console_port,
            'x': 150,
            'y': 150
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.node1.refresh_from_db()
        self.assertEqual(self.node1.name, 'Updated Node')
        self.assertEqual(self.node1.status, 'stopped')
        self.assertEqual(self.node1.x, 150)
        self.assertEqual(self.node1.y, 150)
    
    def test_delete_node(self):
        """Test de suppression d'un nœud."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Node.objects.count(), 1)
    
    @patch('gns3_integration.services.node_service.NodeService.start_node')
    def test_start_node(self, mock_start_node):
        """Test du démarrage d'un nœud."""
        # Configuration du mock
        mock_start_node.return_value = True
        
        # Appel de l'action personnalisée
        url = reverse('node-start', kwargs={'pk': self.node1.pk})
        response = self.client.post(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success', 'message': 'Node started successfully'})
        mock_start_node.assert_called_once_with(self.node1.id)
    
    @patch('gns3_integration.services.node_service.NodeService.stop_node')
    def test_stop_node(self, mock_stop_node):
        """Test de l'arrêt d'un nœud."""
        # Configuration du mock
        mock_stop_node.return_value = True
        
        # Appel de l'action personnalisée
        url = reverse('node-stop', kwargs={'pk': self.node1.pk})
        response = self.client.post(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success', 'message': 'Node stopped successfully'})
        mock_stop_node.assert_called_once_with(self.node1.id)
    
    @patch('gns3_integration.services.node_service.NodeService.get_console_url')
    def test_get_console_url(self, mock_get_console_url):
        """Test de l'obtention de l'URL de console d'un nœud."""
        # Configuration du mock
        mock_get_console_url.return_value = 'http://192.168.1.100:5000'
        
        # Appel de l'action personnalisée
        url = reverse('node-console', kwargs={'pk': self.node1.pk})
        response = self.client.get(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'console_url': 'http://192.168.1.100:5000'})
        mock_get_console_url.assert_called_once_with(self.node1.id) 