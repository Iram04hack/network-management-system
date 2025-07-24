"""
Tests unitaires pour le service de projet GNS3.
"""

import uuid
from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.contrib.auth.models import User

from ..domain.exceptions import (
    GNS3ResourceNotFoundError, GNS3ConnectionError, GNS3OperationError
)
from ..domain.models import Project
from ..application.project_app_service import ProjectService


class ProjectServiceTestCase(TestCase):
    """Tests pour le service de projet GNS3."""
    
    def setUp(self):
        """Configuration initiale pour chaque test."""
        self.client_mock = mock.MagicMock()
        self.repository_mock = mock.MagicMock()
        self.service = ProjectService(self.client_mock, self.repository_mock)
        
        # Création d'un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Création d'un projet de test
        self.test_project_id = str(uuid.uuid4())
        self.test_project = Project(
            id=self.test_project_id,
            name="Test Project",
            status="closed",
            path="/tmp/test_project",
            filename="test_project.gns3",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=self.user,
            description="Test project description"
        )
    
    def test_list_projects(self):
        """Test de la méthode list_projects."""
        # Configuration du mock
        expected_projects = [self.test_project]
        self.repository_mock.list_projects.return_value = expected_projects
        
        # Appel de la méthode
        result = self.service.list_projects()
        
        # Vérifications
        self.repository_mock.list_projects.assert_called_once()
        self.assertEqual(result, expected_projects)
    
    def test_get_project_success(self):
        """Test de la méthode get_project avec succès."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = self.test_project
        
        # Appel de la méthode
        result = self.service.get_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.assertEqual(result, self.test_project)
    
    def test_get_project_not_found(self):
        """Test de la méthode get_project avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.get_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
    
    def test_create_project_success(self):
        """Test de la méthode create_project avec succès."""
        # Configuration des mocks
        gns3_project_data = {
            "project_id": self.test_project_id,
            "name": "Test Project",
            "status": "closed",
            "path": "/tmp/test_project",
            "filename": "test_project.gns3"
        }
        self.client_mock.create_project.return_value = gns3_project_data
        self.repository_mock.save_project.return_value = self.test_project
        
        # Appel de la méthode
        result = self.service.create_project(
            name="Test Project",
            description="Test project description", 
            created_by=self.user
        )
        
        # Vérifications
        self.client_mock.create_project.assert_called_once_with(
            "Test Project", "Test project description"
        )
        self.repository_mock.save_project.assert_called_once()
        self.assertEqual(result, self.test_project)
    
    def test_create_project_connection_error(self):
        """Test de la méthode create_project avec erreur de connexion."""
        # Configuration du mock
        self.client_mock.create_project.side_effect = GNS3ConnectionError("Connection error")
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ConnectionError):
            self.service.create_project("Test Project", "Test description")
        
        # Vérifications
        self.client_mock.create_project.assert_called_once()
        self.repository_mock.save_project.assert_not_called()
    
    def test_delete_project_success(self):
        """Test de la méthode delete_project avec succès."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.client_mock.delete_project.return_value = True
        self.repository_mock.delete_project.return_value = True
        
        # Appel de la méthode
        result = self.service.delete_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.delete_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.delete_project.assert_called_once_with(self.test_project_id)
        self.assertTrue(result)
    
    def test_delete_project_not_found(self):
        """Test de la méthode delete_project avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.delete_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.delete_project.assert_not_called()
        self.repository_mock.delete_project.assert_not_called()
    
    def test_delete_project_operation_error(self):
        """Test de la méthode delete_project avec erreur d'opération."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.client_mock.delete_project.return_value = False
        
        # Vérification de l'exception
        with self.assertRaises(GNS3OperationError):
            self.service.delete_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.delete_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.delete_project.assert_not_called()
    
    def test_open_project_success(self):
        """Test de la méthode open_project avec succès."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        gns3_project_data = {
            "project_id": self.test_project_id,
            "name": "Test Project",
            "status": "open",
            "path": "/tmp/test_project",
            "filename": "test_project.gns3"
        }
        self.client_mock.open_project.return_value = gns3_project_data
        
        expected_project = Project(
            id=self.test_project_id,
            name="Test Project",
            status="open",  # Status changed to open
            path="/tmp/test_project",
            filename="test_project.gns3",
            created_at=self.test_project.created_at,
            updated_at=self.test_project.updated_at,
            created_by=self.user,
            description="Test project description"
        )
        self.repository_mock.save_project.return_value = expected_project
        
        # Appel de la méthode
        result = self.service.open_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.open_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.save_project.assert_called_once()
        self.assertEqual(result.status, "open")
    
    def test_open_project_not_found(self):
        """Test de la méthode open_project avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.open_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.open_project.assert_not_called()
        self.repository_mock.save_project.assert_not_called()
    
    def test_close_project_success(self):
        """Test de la méthode close_project avec succès."""
        # Configuration des mocks
        open_project = Project(
            id=self.test_project_id,
            name="Test Project",
            status="open",
            path="/tmp/test_project",
            filename="test_project.gns3",
            created_at=self.test_project.created_at,
            updated_at=self.test_project.updated_at,
            created_by=self.user,
            description="Test project description"
        )
        self.repository_mock.get_project.return_value = open_project
        
        gns3_project_data = {
            "project_id": self.test_project_id,
            "name": "Test Project",
            "status": "closed",
            "path": "/tmp/test_project",
            "filename": "test_project.gns3"
        }
        self.client_mock.close_project.return_value = gns3_project_data
        self.repository_mock.save_project.return_value = self.test_project
        
        # Appel de la méthode
        result = self.service.close_project(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.close_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.save_project.assert_called_once()
        self.assertEqual(result.status, "closed")
    
    def test_sync_project_success(self):
        """Test de la méthode sync_project avec succès."""
        # Configuration des mocks
        gns3_project_data = {
            "project_id": self.test_project_id,
            "name": "Updated Project Name",
            "status": "closed",
            "path": "/tmp/test_project",
            "filename": "test_project.gns3"
        }
        self.client_mock.get_project.return_value = gns3_project_data
        self.repository_mock.get_project.return_value = self.test_project
        
        expected_project = Project(
            id=self.test_project_id,
            name="Updated Project Name",  # Name updated
            status="closed",
            path="/tmp/test_project",
            filename="test_project.gns3",
            created_at=self.test_project.created_at,
            updated_at=self.test_project.updated_at,
            created_by=self.user,
            description="Test project description"
        )
        self.repository_mock.save_project.return_value = expected_project
        
        # Appel de la méthode
        result = self.service.sync_project(self.test_project_id)
        
        # Vérifications
        self.client_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.save_project.assert_called_once()
        self.assertEqual(result.name, "Updated Project Name")
    
    def test_sync_project_not_in_repository(self):
        """Test de la méthode sync_project avec projet non trouvé dans le repository."""
        # Configuration des mocks
        gns3_project_data = {
            "project_id": self.test_project_id,
            "name": "Test Project",
            "status": "closed",
            "path": "/tmp/test_project",
            "filename": "test_project.gns3"
        }
        self.client_mock.get_project.return_value = gns3_project_data
        self.repository_mock.get_project.return_value = None
        self.repository_mock.save_project.return_value = self.test_project
        
        # Appel de la méthode
        result = self.service.sync_project(self.test_project_id)
        
        # Vérifications
        self.client_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.save_project.assert_called_once()
        self.assertIsNotNone(result)
    
    def test_create_snapshot_success(self):
        """Test de la méthode create_snapshot avec succès."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        snapshot_id = str(uuid.uuid4())
        snapshot_name = "Test Snapshot"
        gns3_snapshot_data = {
            "snapshot_id": snapshot_id,
            "name": snapshot_name,
            "created_at": "2023-07-01T12:00:00Z",
            "project_id": self.test_project_id
        }
        self.client_mock.create_snapshot.return_value = gns3_snapshot_data
        
        # Appel de la méthode
        result = self.service.create_snapshot(
            project_id=self.test_project_id,
            name=snapshot_name,
            created_by=self.user
        )
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.create_snapshot.assert_called_once_with(self.test_project_id, snapshot_name)
        self.repository_mock.save_snapshot.assert_called_once_with(
            project_id=self.test_project_id,
            snapshot_id=snapshot_id,
            snapshot_name=snapshot_name
        )
        self.assertEqual(result, gns3_snapshot_data)
    
    def test_restore_snapshot_success(self):
        """Test de la méthode restore_snapshot avec succès."""
        # Configuration des mocks
        snapshot_id = str(uuid.uuid4())
        self.client_mock.restore_snapshot.return_value = True
        
        # Appel de la méthode
        result = self.service.restore_snapshot(self.test_project_id, snapshot_id)
        
        # Vérifications
        self.client_mock.restore_snapshot.assert_called_once_with(self.test_project_id, snapshot_id)
        self.assertTrue(result) 