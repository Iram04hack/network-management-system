import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from ...models import Server, Project
from ...serializers import ProjectSerializer
from unittest.mock import patch, MagicMock

class ProjectViewSetTestCase(APITestCase):
    """Tests pour les vues de projets GNS3."""
    
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
        
        # Création de projets de test
        self.project1 = Project.objects.create(
            name='Test Project 1',
            project_id='00000000-0000-0000-0000-000000000001',
            server=self.server,
            status='opened'
        )
        
        self.project2 = Project.objects.create(
            name='Test Project 2',
            project_id='00000000-0000-0000-0000-000000000002',
            server=self.server,
            status='closed'
        )
        
        # Configuration du client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # URLs pour les tests
        self.list_url = reverse('project-list')
        self.detail_url = reverse('project-detail', kwargs={'pk': self.project1.pk})
    
    def test_get_project_list(self):
        """Test de récupération de la liste des projets."""
        response = self.client.get(self.list_url)
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_get_project_detail(self):
        """Test de récupération des détails d'un projet."""
        response = self.client.get(self.detail_url)
        project = Project.objects.get(pk=self.project1.pk)
        serializer = ProjectSerializer(project)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_project(self):
        """Test de création d'un projet."""
        data = {
            'name': 'New Test Project',
            'project_id': '00000000-0000-0000-0000-000000000003',
            'server': self.server.id,
            'status': 'opened'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(Project.objects.get(name='New Test Project').project_id, 
                         '00000000-0000-0000-0000-000000000003')
    
    def test_update_project(self):
        """Test de mise à jour d'un projet."""
        data = {
            'name': 'Updated Project',
            'project_id': self.project1.project_id,
            'server': self.server.id,
            'status': 'closed'
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project1.refresh_from_db()
        self.assertEqual(self.project1.name, 'Updated Project')
        self.assertEqual(self.project1.status, 'closed')
    
    def test_delete_project(self):
        """Test de suppression d'un projet."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)
    
    @patch('gns3_integration.services.project_service.ProjectService.open_project')
    def test_open_project(self, mock_open_project):
        """Test de l'ouverture d'un projet."""
        # Configuration du mock
        mock_open_project.return_value = True
        
        # Appel de l'action personnalisée
        url = reverse('project-open', kwargs={'pk': self.project1.pk})
        response = self.client.post(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success', 'message': 'Project opened successfully'})
        mock_open_project.assert_called_once_with(self.project1.id)
    
    @patch('gns3_integration.services.project_service.ProjectService.close_project')
    def test_close_project(self, mock_close_project):
        """Test de la fermeture d'un projet."""
        # Configuration du mock
        mock_close_project.return_value = True
        
        # Appel de l'action personnalisée
        url = reverse('project-close', kwargs={'pk': self.project1.pk})
        response = self.client.post(url)
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success', 'message': 'Project closed successfully'})
        mock_close_project.assert_called_once_with(self.project1.id) 