import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from ...models import Server
from ...serializers import ServerSerializer
from unittest.mock import patch, MagicMock

class ServerViewSetTestCase(APITestCase):
    """Tests pour les vues de serveurs GNS3."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Création d'un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Création de serveurs de test
        self.server1 = Server.objects.create(
            name='Test Server 1',
            host='192.168.1.100',
            port=3080,
            user='admin',
            password='password',
            protocol='http'
        )
        
        self.server2 = Server.objects.create(
            name='Test Server 2',
            host='192.168.1.101',
            port=3080,
            user='admin',
            password='password',
            protocol='http'
        )
        
        # Configuration du client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # URLs pour les tests
        self.list_url = reverse('server-list')
        self.detail_url = reverse('server-detail', kwargs={'pk': self.server1.pk})
    
    def test_get_server_list(self):
        """Test de récupération de la liste des serveurs."""
        response = self.client.get(self.list_url)
        servers = Server.objects.all()
        serializer = ServerSerializer(servers, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_get_server_detail(self):
        """Test de récupération des détails d'un serveur."""
        response = self.client.get(self.detail_url)
        server = Server.objects.get(pk=self.server1.pk)
        serializer = ServerSerializer(server)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_server(self):
        """Test de création d'un serveur."""
        data = {
            'name': 'New Test Server',
            'host': '192.168.1.102',
            'port': 3080,
            'user': 'admin',
            'password': 'password',
            'protocol': 'http'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Server.objects.count(), 3)
        self.assertEqual(Server.objects.get(name='New Test Server').host, '192.168.1.102')
    
    def test_update_server(self):
        """Test de mise à jour d'un serveur."""
        data = {
            'name': 'Updated Server',
            'host': '192.168.1.100',
            'port': 3080,
            'user': 'admin',
            'password': 'newpassword',
            'protocol': 'http'
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.server1.refresh_from_db()
        self.assertEqual(self.server1.name, 'Updated Server')
        self.assertEqual(self.server1.password, 'newpassword')
    
    def test_delete_server(self):
        """Test de suppression d'un serveur."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Server.objects.count(), 1)
    
    @patch('gns3_integration.services.server_service.ServerService.check_connection')
    def test_check_connection(self, mock_check_connection):
        """Test de la vérification de connexion à un serveur."""
        # Configuration du mock
        mock_check_connection.return_value = True
        
        # Appel de l'action personnalisée
        url = reverse('server-check-connection', kwargs={'pk': self.server1.pk})
        response = self.client.post(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success', 'connected': True})
        mock_check_connection.assert_called_once_with(self.server1.id) 