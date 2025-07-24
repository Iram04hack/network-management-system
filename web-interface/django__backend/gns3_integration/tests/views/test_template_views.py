import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from ...models import Server, Template
from ...serializers import TemplateSerializer
from unittest.mock import patch, MagicMock

class TemplateViewSetTestCase(APITestCase):
    """Tests pour les vues de templates GNS3."""
    
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
        
        # Création de templates de test
        self.template1 = Template.objects.create(
            name='Test Template 1',
            template_id='00000000-0000-0000-0000-000000000001',
            template_type='qemu',
            server=self.server,
            image='ubuntu-20.04.qcow2',
            console_type='vnc'
        )
        
        self.template2 = Template.objects.create(
            name='Test Template 2',
            template_id='00000000-0000-0000-0000-000000000002',
            template_type='docker',
            server=self.server,
            image='ubuntu:latest',
            console_type='telnet'
        )
        
        # Configuration du client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # URLs pour les tests
        self.list_url = reverse('template-list')
        self.detail_url = reverse('template-detail', kwargs={'pk': self.template1.pk})
    
    def test_get_template_list(self):
        """Test de récupération de la liste des templates."""
        response = self.client.get(self.list_url)
        templates = Template.objects.all()
        serializer = TemplateSerializer(templates, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_get_template_detail(self):
        """Test de récupération des détails d'un template."""
        response = self.client.get(self.detail_url)
        template = Template.objects.get(pk=self.template1.pk)
        serializer = TemplateSerializer(template)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_template(self):
        """Test de création d'un template."""
        data = {
            'name': 'New Test Template',
            'template_id': '00000000-0000-0000-0000-000000000003',
            'template_type': 'vpcs',
            'server': self.server.id,
            'image': '',
            'console_type': 'telnet'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Template.objects.count(), 3)
        self.assertEqual(Template.objects.get(name='New Test Template').template_id, 
                         '00000000-0000-0000-0000-000000000003')
    
    def test_update_template(self):
        """Test de mise à jour d'un template."""
        data = {
            'name': 'Updated Template',
            'template_id': self.template1.template_id,
            'template_type': self.template1.template_type,
            'server': self.server.id,
            'image': 'ubuntu-22.04.qcow2',
            'console_type': 'vnc'
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.template1.refresh_from_db()
        self.assertEqual(self.template1.name, 'Updated Template')
        self.assertEqual(self.template1.image, 'ubuntu-22.04.qcow2')
    
    def test_delete_template(self):
        """Test de suppression d'un template."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Template.objects.count(), 1)
    
    @patch('gns3_integration.services.template_service.TemplateService.sync_templates')
    def test_sync_templates(self, mock_sync_templates):
        """Test de la synchronisation des templates."""
        # Configuration du mock
        mock_sync_templates.return_value = 2
        
        # Appel de l'action personnalisée
        url = reverse('template-sync', kwargs={'pk': self.server.pk})
        response = self.client.post(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success', 'templates_synced': 2})
        mock_sync_templates.assert_called_once_with(self.server.id)