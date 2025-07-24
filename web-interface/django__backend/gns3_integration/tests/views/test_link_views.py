import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from ...models import Server, Project, Node, Link
from ...serializers import LinkSerializer
from unittest.mock import patch, MagicMock

class LinkViewSetTestCase(APITestCase):
    """Tests pour les vues de liens GNS3."""
    
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
            status='started',
            project=self.project,
            console_port=5001,
            x=200,
            y=200
        )
        
        # Création de liens de test
        self.link1 = Link.objects.create(
            link_id='00000000-0000-0000-0000-000000000001',
            project=self.project,
            source_node=self.node1,
            source_port=0,
            destination_node=self.node2,
            destination_port=0
        )
        
        self.link2 = Link.objects.create(
            link_id='00000000-0000-0000-0000-000000000002',
            project=self.project,
            source_node=self.node2,
            source_port=1,
            destination_node=self.node1,
            destination_port=1
        )
        
        # Configuration du client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # URLs pour les tests
        self.list_url = reverse('link-list')
        self.detail_url = reverse('link-detail', kwargs={'pk': self.link1.pk})
    
    def test_get_link_list(self):
        """Test de récupération de la liste des liens."""
        response = self.client.get(self.list_url)
        links = Link.objects.all()
        serializer = LinkSerializer(links, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_get_link_detail(self):
        """Test de récupération des détails d'un lien."""
        response = self.client.get(self.detail_url)
        link = Link.objects.get(pk=self.link1.pk)
        serializer = LinkSerializer(link)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_link(self):
        """Test de création d'un lien."""
        data = {
            'link_id': '00000000-0000-0000-0000-000000000003',
            'project': self.project.id,
            'source_node': self.node1.id,
            'source_port': 2,
            'destination_node': self.node2.id,
            'destination_port': 2
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Link.objects.count(), 3)
        self.assertEqual(Link.objects.get(link_id='00000000-0000-0000-0000-000000000003').source_port, 2)
    
    def test_update_link(self):
        """Test de mise à jour d'un lien."""
        data = {
            'link_id': self.link1.link_id,
            'project': self.project.id,
            'source_node': self.node1.id,
            'source_port': 3,
            'destination_node': self.node2.id,
            'destination_port': 3
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.link1.refresh_from_db()
        self.assertEqual(self.link1.source_port, 3)
        self.assertEqual(self.link1.destination_port, 3)
    
    def test_delete_link(self):
        """Test de suppression d'un lien."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Link.objects.count(), 1) 