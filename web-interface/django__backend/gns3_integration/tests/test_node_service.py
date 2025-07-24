"""
Tests unitaires pour le service de nœuds GNS3.
"""

import uuid
from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.contrib.auth.models import User

from ..domain.exceptions import (
    GNS3ResourceNotFoundError, GNS3ConnectionError, GNS3OperationError
)
from ..domain.models import Project, Node
from ..application.node_service import NodeService


class NodeServiceTestCase(TestCase):
    """Tests pour le service de nœuds GNS3."""
    
    def setUp(self):
        """Configuration initiale pour chaque test."""
        self.client_mock = mock.MagicMock()
        self.repository_mock = mock.MagicMock()
        self.service = NodeService(self.client_mock, self.repository_mock)
        
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
            status="open",
            path="/tmp/test_project",
            filename="test_project.gns3",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=self.user,
            description="Test project description"
        )
        
        # Création d'un nœud de test
        self.test_node_id = str(uuid.uuid4())
        self.test_node = Node(
            id=self.test_node_id,
            name="Test Node",
            project_id=self.test_project_id,
            node_type="vpcs",
            compute_id="local",
            console=5000,
            console_type="telnet",
            x=100,
            y=100,
            z=0,
            status="stopped",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=self.user
        )
    
    def test_list_nodes(self):
        """Test de la méthode list_nodes."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        expected_nodes = [self.test_node]
        self.repository_mock.list_nodes.return_value = expected_nodes
        
        # Appel de la méthode
        result = self.service.list_nodes(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.list_nodes.assert_called_once_with(self.test_project_id)
        self.assertEqual(result, expected_nodes)
    
    def test_list_nodes_project_not_found(self):
        """Test de la méthode list_nodes avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.list_nodes(self.test_project_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.list_nodes.assert_not_called()
    
    def test_get_node_success(self):
        """Test de la méthode get_node avec succès."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.repository_mock.get_node.return_value = self.test_node
        
        # Appel de la méthode
        result = self.service.get_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.assertEqual(result, self.test_node)
    
    def test_get_node_project_not_found(self):
        """Test de la méthode get_node avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.get_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_not_called()
    
    def test_get_node_node_not_found(self):
        """Test de la méthode get_node avec nœud non trouvé."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.repository_mock.get_node.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.get_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
    
    def test_create_node_success(self):
        """Test de la méthode create_node avec succès."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        template_id = str(uuid.uuid4())
        
        gns3_node_data = {
            "node_id": self.test_node_id,
            "name": "Test Node",
            "node_type": "vpcs",
            "compute_id": "local",
            "console": 5000,
            "console_type": "telnet",
            "x": 100,
            "y": 100,
            "z": 0,
            "status": "stopped"
        }
        self.client_mock.create_node.return_value = gns3_node_data
        self.repository_mock.save_node.return_value = self.test_node
        
        # Appel de la méthode
        result = self.service.create_node(
            project_id=self.test_project_id,
            template_id=template_id,
            name="Test Node",
            compute_id="local",
            x=100,
            y=100,
            created_by=self.user
        )
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.create_node.assert_called_once_with(
            project_id=self.test_project_id,
            template_id=template_id,
            name="Test Node",
            compute_id="local",
            x=100,
            y=100
        )
        self.repository_mock.save_node.assert_called_once()
        self.assertEqual(result, self.test_node)
    
    def test_create_node_project_not_found(self):
        """Test de la méthode create_node avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.create_node(
                project_id=self.test_project_id,
                template_id=str(uuid.uuid4()),
                name="Test Node"
            )
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.create_node.assert_not_called()
        self.repository_mock.save_node.assert_not_called()
    
    def test_create_node_closed_project(self):
        """Test de la méthode create_node avec projet fermé."""
        # Configuration des mocks
        closed_project = Project(
            id=self.test_project_id,
            name="Test Project",
            status="closed",
            path="/tmp/test_project",
            filename="test_project.gns3",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=self.user
        )
        self.repository_mock.get_project.return_value = closed_project
        template_id = str(uuid.uuid4())
        
        gns3_node_data = {
            "node_id": self.test_node_id,
            "name": "Test Node",
            "node_type": "vpcs",
            "compute_id": "local",
            "console": 5000,
            "console_type": "telnet",
            "x": 100,
            "y": 100,
            "z": 0,
            "status": "stopped"
        }
        self.client_mock.create_node.return_value = gns3_node_data
        self.repository_mock.save_node.return_value = self.test_node
        
        # Appel de la méthode
        result = self.service.create_node(
            project_id=self.test_project_id,
            template_id=template_id,
            name="Test Node"
        )
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.client_mock.open_project.assert_called_once_with(self.test_project_id)
        self.client_mock.create_node.assert_called_once()
        self.repository_mock.save_node.assert_called_once()
        self.assertEqual(result, self.test_node)
    
    def test_delete_node_success(self):
        """Test de la méthode delete_node avec succès."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.repository_mock.get_node.return_value = self.test_node
        self.client_mock.delete_node.return_value = True
        self.repository_mock.delete_node.return_value = True
        
        # Appel de la méthode
        result = self.service.delete_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.delete_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.repository_mock.delete_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.assertTrue(result)
    
    def test_delete_node_project_not_found(self):
        """Test de la méthode delete_node avec projet non trouvé."""
        # Configuration du mock
        self.repository_mock.get_project.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.delete_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_not_called()
        self.client_mock.delete_node.assert_not_called()
        self.repository_mock.delete_node.assert_not_called()
    
    def test_delete_node_node_not_found(self):
        """Test de la méthode delete_node avec nœud non trouvé."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.repository_mock.get_node.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.delete_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.delete_node.assert_not_called()
        self.repository_mock.delete_node.assert_not_called()
    
    def test_delete_node_operation_error(self):
        """Test de la méthode delete_node avec erreur d'opération."""
        # Configuration des mocks
        self.repository_mock.get_project.return_value = self.test_project
        self.repository_mock.get_node.return_value = self.test_node
        self.client_mock.delete_node.return_value = False
        
        # Vérification de l'exception
        with self.assertRaises(GNS3OperationError):
            self.service.delete_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_project.assert_called_once_with(self.test_project_id)
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.delete_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.repository_mock.delete_node.assert_not_called()
    
    def test_start_node_success(self):
        """Test de la méthode start_node avec succès."""
        # Configuration des mocks
        self.repository_mock.get_node.return_value = self.test_node
        gns3_node_data = {
            "node_id": self.test_node_id,
            "name": "Test Node",
            "node_type": "vpcs",
            "compute_id": "local",
            "console": 5000,
            "console_type": "telnet",
            "x": 100,
            "y": 100,
            "z": 0,
            "status": "started"  # Status changed to started
        }
        self.client_mock.start_node.return_value = gns3_node_data
        
        expected_node = Node(
            id=self.test_node_id,
            name="Test Node",
            project_id=self.test_project_id,
            node_type="vpcs",
            compute_id="local",
            console=5000,
            console_type="telnet",
            x=100,
            y=100,
            z=0,
            status="started",  # Status changed to started
            created_at=self.test_node.created_at,
            updated_at=self.test_node.updated_at,
            created_by=self.user
        )
        self.repository_mock.save_node.return_value = expected_node
        
        # Appel de la méthode
        result = self.service.start_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.start_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.repository_mock.save_node.assert_called_once()
        self.assertEqual(result.status, "started")
    
    def test_start_node_not_found(self):
        """Test de la méthode start_node avec nœud non trouvé."""
        # Configuration du mock
        self.repository_mock.get_node.return_value = None
        
        # Vérification de l'exception
        with self.assertRaises(GNS3ResourceNotFoundError):
            self.service.start_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.start_node.assert_not_called()
        self.repository_mock.save_node.assert_not_called()
    
    def test_stop_node_success(self):
        """Test de la méthode stop_node avec succès."""
        # Configuration des mocks
        running_node = Node(
            id=self.test_node_id,
            name="Test Node",
            project_id=self.test_project_id,
            node_type="vpcs",
            compute_id="local",
            console=5000,
            console_type="telnet",
            x=100,
            y=100,
            z=0,
            status="started",
            created_at=self.test_node.created_at,
            updated_at=self.test_node.updated_at,
            created_by=self.user
        )
        self.repository_mock.get_node.return_value = running_node
        
        gns3_node_data = {
            "node_id": self.test_node_id,
            "name": "Test Node",
            "node_type": "vpcs",
            "compute_id": "local",
            "console": 5000,
            "console_type": "telnet",
            "x": 100,
            "y": 100,
            "z": 0,
            "status": "stopped"  # Status changed to stopped
        }
        self.client_mock.stop_node.return_value = gns3_node_data
        self.repository_mock.save_node.return_value = self.test_node
        
        # Appel de la méthode
        result = self.service.stop_node(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.stop_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.repository_mock.save_node.assert_called_once()
        self.assertEqual(result.status, "stopped")
    
    def test_update_node_position_success(self):
        """Test de la méthode update_node_position avec succès."""
        # Configuration des mocks
        self.repository_mock.get_node.return_value = self.test_node
        
        gns3_node_data = {
            "node_id": self.test_node_id,
            "name": "Test Node",
            "node_type": "vpcs",
            "compute_id": "local",
            "console": 5000,
            "console_type": "telnet",
            "x": 200,  # Updated x
            "y": 300,  # Updated y
            "z": 10,   # Updated z
            "status": "stopped"
        }
        self.client_mock.update_node.return_value = gns3_node_data
        
        expected_node = Node(
            id=self.test_node_id,
            name="Test Node",
            project_id=self.test_project_id,
            node_type="vpcs",
            compute_id="local",
            console=5000,
            console_type="telnet",
            x=200,  # Updated x
            y=300,  # Updated y
            z=10,   # Updated z
            status="stopped",
            created_at=self.test_node.created_at,
            updated_at=self.test_node.updated_at,
            created_by=self.user
        )
        self.repository_mock.save_node.return_value = expected_node
        
        # Appel de la méthode
        result = self.service.update_node_position(
            project_id=self.test_project_id,
            node_id=self.test_node_id,
            x=200,
            y=300,
            z=10
        )
        
        # Vérifications
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.update_node.assert_called_once_with(
            project_id=self.test_project_id,
            node_id=self.test_node_id,
            x=200,
            y=300,
            z=10
        )
        self.repository_mock.save_node.assert_called_once()
        self.assertEqual(result.x, 200)
        self.assertEqual(result.y, 300)
        self.assertEqual(result.z, 10)
    
    def test_update_node_name_success(self):
        """Test de la méthode update_node_name avec succès."""
        # Configuration des mocks
        self.repository_mock.get_node.return_value = self.test_node
        
        gns3_node_data = {
            "node_id": self.test_node_id,
            "name": "Updated Node Name",  # Updated name
            "node_type": "vpcs",
            "compute_id": "local",
            "console": 5000,
            "console_type": "telnet",
            "x": 100,
            "y": 100,
            "z": 0,
            "status": "stopped"
        }
        self.client_mock.update_node.return_value = gns3_node_data
        
        expected_node = Node(
            id=self.test_node_id,
            name="Updated Node Name",  # Updated name
            project_id=self.test_project_id,
            node_type="vpcs",
            compute_id="local",
            console=5000,
            console_type="telnet",
            x=100,
            y=100,
            z=0,
            status="stopped",
            created_at=self.test_node.created_at,
            updated_at=self.test_node.updated_at,
            created_by=self.user
        )
        self.repository_mock.save_node.return_value = expected_node
        
        # Appel de la méthode
        result = self.service.update_node_name(
            project_id=self.test_project_id,
            node_id=self.test_node_id,
            name="Updated Node Name"
        )
        
        # Vérifications
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.update_node.assert_called_once_with(
            project_id=self.test_project_id,
            node_id=self.test_node_id,
            name="Updated Node Name"
        )
        self.repository_mock.save_node.assert_called_once()
        self.assertEqual(result.name, "Updated Node Name")
    
    def test_get_console_url_success(self):
        """Test de la méthode get_console_url avec succès."""
        # Configuration des mocks
        self.repository_mock.get_node.return_value = self.test_node
        expected_url = "http://localhost:5000"
        self.client_mock.get_console_url.return_value = expected_url
        
        # Appel de la méthode
        result = self.service.get_console_url(self.test_project_id, self.test_node_id)
        
        # Vérifications
        self.repository_mock.get_node.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.client_mock.get_console_url.assert_called_once_with(self.test_project_id, self.test_node_id)
        self.assertEqual(result, expected_url) 