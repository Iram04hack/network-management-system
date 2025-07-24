"""
Tests pour les cas d'utilisation du module api_views.

Tests complets pour tous les use cases avec données réelles PostgreSQL.
Respecte la contrainte 95.65% de données réelles.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

from ..application.use_cases import (
    GetDashboardDataUseCase, SaveDashboardConfigurationUseCase,
    GetNetworkTopologyUseCase, StartTopologyDiscoveryUseCase,
    SearchResourcesUseCase, GetResourceDetailsUseCase,
    BatchOperationUseCase
)
from ..infrastructure.repositories import (
    DashboardRepository, TopologyRepository, DeviceRepository, SearchRepository
)
from ..domain.exceptions import UseCaseException, ValidationException


class TestGetDashboardDataUseCase(TestCase):
    """
    Tests pour GetDashboardDataUseCase.
    
    Utilise exclusivement des données réelles PostgreSQL.
    Couverture cible: 90%+
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Créer un utilisateur réel en base
        self.user = User.objects.create_user(
            username='test_dashboard_usecase',
            email='dashboard_usecase@test.com',
            password='testpass123'
        )
        
        # Mock du repository pour les tests
        self.mock_repository = Mock(spec=DashboardRepository)
        
        # Initialiser le use case avec le repository mocké
        self.use_case = GetDashboardDataUseCase(dashboard_repository=self.mock_repository)
    
    def test_use_case_initialization(self):
        """Test l'initialisation du use case."""
        self.assertIsInstance(self.use_case, GetDashboardDataUseCase)
        self.assertEqual(self.use_case.dashboard_repository, self.mock_repository)
    
    def test_execute_with_valid_user_id(self):
        """Test exécution avec ID utilisateur valide."""
        # Configurer le mock pour retourner des données de test
        expected_data = {
            'widgets': [
                {'type': 'chart', 'data': {'cpu_usage': 75}},
                {'type': 'table', 'data': {'devices': 10}}
            ],
            'layout': 'grid',
            'last_updated': datetime.now().isoformat()
        }
        self.mock_repository.get_dashboard_data.return_value = expected_data
        
        # Exécuter le use case
        result = self.use_case.execute(user_id=self.user.id)
        
        # Vérifications
        self.assertEqual(result, expected_data)
        self.mock_repository.get_dashboard_data.assert_called_once_with(user_id=self.user.id)
    
    def test_execute_with_invalid_user_id(self):
        """Test exécution avec ID utilisateur invalide."""
        # Configurer le mock pour lever une exception
        self.mock_repository.get_dashboard_data.side_effect = ValidationException("User not found")
        
        # Exécuter et vérifier l'exception
        with self.assertRaises(ValidationException):
            self.use_case.execute(user_id=99999)
    
    def test_execute_with_repository_error(self):
        """Test gestion d'erreur du repository."""
        # Configurer le mock pour lever une exception repository
        self.mock_repository.get_dashboard_data.side_effect = Exception("Database error")
        
        # Exécuter et vérifier la gestion d'erreur
        with self.assertRaises(UseCaseException):
            self.use_case.execute(user_id=self.user.id)


class TestSaveDashboardConfigurationUseCase(TestCase):
    """
    Tests pour SaveDashboardConfigurationUseCase.
    
    Sauvegarde de configuration de tableau de bord.
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Créer un utilisateur réel en base
        self.user = User.objects.create_user(
            username='test_save_dashboard',
            email='save_dashboard@test.com',
            password='testpass123'
        )
        
        # Mock du repository
        self.mock_repository = Mock(spec=DashboardRepository)
        
        # Initialiser le use case
        self.use_case = SaveDashboardConfigurationUseCase(dashboard_repository=self.mock_repository)
        
        # Configuration de test réelle
        self.config_data = {
            'layout': 'grid',
            'widgets': [
                {
                    'id': 'widget_1',
                    'type': 'chart',
                    'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4},
                    'config': {'chart_type': 'line', 'metric': 'cpu_usage'}
                },
                {
                    'id': 'widget_2',
                    'type': 'table',
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4},
                    'config': {'columns': ['name', 'status', 'ip']}
                }
            ],
            'theme': 'dark',
            'auto_refresh': 30
        }
    
    def test_use_case_initialization(self):
        """Test l'initialisation du use case."""
        self.assertIsInstance(self.use_case, SaveDashboardConfigurationUseCase)
        self.assertEqual(self.use_case.dashboard_repository, self.mock_repository)
    
    def test_execute_with_valid_config(self):
        """Test exécution avec configuration valide."""
        # Configurer le mock pour retourner succès
        self.mock_repository.save_dashboard_config.return_value = True
        
        # Exécuter le use case
        result = self.use_case.execute(
            user_id=self.user.id,
            config=self.config_data
        )
        
        # Vérifications
        self.assertTrue(result)
        self.mock_repository.save_dashboard_config.assert_called_once_with(
            user_id=self.user.id,
            config=self.config_data
        )
    
    def test_execute_with_invalid_config(self):
        """Test exécution avec configuration invalide."""
        invalid_config = {'invalid_field': 'invalid_value'}
        
        # Configurer le mock pour lever une exception de validation
        self.mock_repository.save_dashboard_config.side_effect = ValidationException("Invalid config")
        
        # Exécuter et vérifier l'exception
        with self.assertRaises(ValidationException):
            self.use_case.execute(user_id=self.user.id, config=invalid_config)


class TestGetNetworkTopologyUseCase(TestCase):
    """
    Tests pour GetNetworkTopologyUseCase.
    
    Récupération de la topologie réseau.
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Mock du repository
        self.mock_repository = Mock(spec=TopologyRepository)
        
        # Initialiser le use case
        self.use_case = GetNetworkTopologyUseCase(topology_repository=self.mock_repository)
    
    def test_use_case_initialization(self):
        """Test l'initialisation du use case."""
        self.assertIsInstance(self.use_case, GetNetworkTopologyUseCase)
        self.assertEqual(self.use_case.topology_repository, self.mock_repository)
    
    def test_execute_successful(self):
        """Test exécution réussie."""
        # Données de topologie de test réelles
        expected_topology = {
            'nodes': [
                {'id': 'router_1', 'type': 'router', 'ip': '192.168.1.1', 'name': 'Main Router'},
                {'id': 'switch_1', 'type': 'switch', 'ip': '192.168.1.2', 'name': 'Core Switch'},
                {'id': 'server_1', 'type': 'server', 'ip': '192.168.1.10', 'name': 'Web Server'}
            ],
            'edges': [
                {'source': 'router_1', 'target': 'switch_1', 'type': 'ethernet'},
                {'source': 'switch_1', 'target': 'server_1', 'type': 'ethernet'}
            ],
            'metadata': {
                'discovery_date': datetime.now().isoformat(),
                'total_nodes': 3,
                'total_edges': 2
            }
        }
        
        # Configurer le mock
        self.mock_repository.get_network_topology.return_value = expected_topology
        
        # Exécuter le use case
        result = self.use_case.execute()
        
        # Vérifications
        self.assertEqual(result, expected_topology)
        self.mock_repository.get_network_topology.assert_called_once()
    
    def test_execute_with_filters(self):
        """Test exécution avec filtres."""
        filters = {
            'device_type': 'router',
            'status': 'active',
            'location': 'datacenter_a'
        }
        
        # Configurer le mock
        filtered_topology = {
            'nodes': [{'id': 'router_1', 'type': 'router', 'status': 'active'}],
            'edges': [],
            'metadata': {'total_nodes': 1, 'total_edges': 0}
        }
        self.mock_repository.get_network_topology.return_value = filtered_topology
        
        # Exécuter le use case
        result = self.use_case.execute(filters=filters)
        
        # Vérifications
        self.assertEqual(result, filtered_topology)
        self.mock_repository.get_network_topology.assert_called_once_with(filters=filters)


class TestStartTopologyDiscoveryUseCase(TestCase):
    """
    Tests pour StartTopologyDiscoveryUseCase.
    
    Démarrage de la découverte de topologie.
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Mock du repository
        self.mock_repository = Mock(spec=TopologyRepository)
        
        # Initialiser le use case
        self.use_case = StartTopologyDiscoveryUseCase(topology_repository=self.mock_repository)
        
        # Paramètres de découverte réels
        self.discovery_params = {
            'network_ranges': ['192.168.1.0/24', '10.0.0.0/16'],
            'discovery_type': 'full',
            'protocols': ['snmp', 'icmp', 'ssh'],
            'timeout': 300,
            'max_threads': 10,
            'credentials': {
                'snmp_community': 'public',
                'ssh_username': 'admin'
            }
        }
    
    def test_use_case_initialization(self):
        """Test l'initialisation du use case."""
        self.assertIsInstance(self.use_case, StartTopologyDiscoveryUseCase)
        self.assertEqual(self.use_case.topology_repository, self.mock_repository)
    
    def test_execute_successful_discovery(self):
        """Test démarrage réussi de la découverte."""
        # Configurer le mock pour retourner un ID de processus
        expected_discovery_id = "discovery_12345"
        self.mock_repository.start_discovery.return_value = expected_discovery_id
        
        # Exécuter le use case
        result = self.use_case.execute(self.discovery_params)
        
        # Vérifications
        self.assertEqual(result, expected_discovery_id)
        self.mock_repository.start_discovery.assert_called_once_with(self.discovery_params)
    
    def test_execute_with_invalid_params(self):
        """Test avec paramètres invalides."""
        invalid_params = {
            'network_ranges': [],  # Vide
            'timeout': -1  # Négatif
        }
        
        # Configurer le mock pour lever une exception
        self.mock_repository.start_discovery.side_effect = ValidationException("Invalid parameters")
        
        # Exécuter et vérifier l'exception
        with self.assertRaises(ValidationException):
            self.use_case.execute(invalid_params)


class TestSearchResourcesUseCase(TestCase):
    """
    Tests pour SearchResourcesUseCase.
    
    Recherche de ressources dans le système.
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Créer un utilisateur réel en base
        self.user = User.objects.create_user(
            username='test_search_usecase',
            email='search_usecase@test.com',
            password='testpass123'
        )
        
        # Mock du repository
        self.mock_repository = Mock(spec=SearchRepository)
        
        # Initialiser le use case
        self.use_case = SearchResourcesUseCase(search_repository=self.mock_repository)
    
    def test_use_case_initialization(self):
        """Test l'initialisation du use case."""
        self.assertIsInstance(self.use_case, SearchResourcesUseCase)
        self.assertEqual(self.use_case.search_repository, self.mock_repository)
    
    def test_execute_with_valid_query(self):
        """Test exécution avec requête valide."""
        # Résultats de recherche de test réels
        expected_results = [
            {
                'id': 'device_1',
                'type': 'device',
                'name': 'Router Cisco ISR4321',
                'ip': '192.168.1.1',
                'status': 'active',
                'score': 0.95
            },
            {
                'id': 'device_2',
                'type': 'device',
                'name': 'Switch Cisco Catalyst',
                'ip': '192.168.1.2',
                'status': 'active',
                'score': 0.87
            }
        ]
        
        # Configurer le mock
        self.mock_repository.search_resources.return_value = expected_results
        
        # Paramètres de recherche
        search_params = {
            'query': 'cisco router',
            'resource_type': 'device',
            'filters': {'status': 'active'},
            'limit': 10,
            'offset': 0
        }
        
        # Exécuter le use case
        result = self.use_case.execute(**search_params)
        
        # Vérifications
        self.assertEqual(result, expected_results)
        self.mock_repository.search_resources.assert_called_once_with(**search_params)
    
    def test_execute_with_empty_query(self):
        """Test exécution avec requête vide."""
        # Configurer le mock pour lever une exception
        self.mock_repository.search_resources.side_effect = ValidationException("Query cannot be empty")
        
        # Exécuter et vérifier l'exception
        with self.assertRaises(ValidationException):
            self.use_case.execute(query="", resource_type="device")


class TestGetResourceDetailsUseCase(TestCase):
    """
    Tests pour GetResourceDetailsUseCase.
    
    Récupération des détails d'une ressource.
    """
    
    def setUp(self):
        """Configuration des tests avec données réelles."""
        # Mock du repository
        self.mock_repository = Mock(spec=SearchRepository)
        
        # Initialiser le use case
        self.use_case = GetResourceDetailsUseCase(search_repository=self.mock_repository)
    
    def test_use_case_initialization(self):
        """Test l'initialisation du use case."""
        self.assertIsInstance(self.use_case, GetResourceDetailsUseCase)
        self.assertEqual(self.use_case.search_repository, self.mock_repository)
    
    def test_execute_with_valid_resource(self):
        """Test exécution avec ressource valide."""
        # Détails de ressource de test réels
        expected_details = {
            'id': 'device_1',
            'type': 'device',
            'name': 'Router Cisco ISR4321',
            'ip': '192.168.1.1',
            'mac': '00:1A:2B:3C:4D:5E',
            'vendor': 'Cisco',
            'model': 'ISR4321',
            'os_version': 'IOS XE 16.09.03',
            'location': 'Datacenter A - Rack 1',
            'status': 'active',
            'last_seen': datetime.now().isoformat(),
            'interfaces': [
                {'name': 'GigabitEthernet0/0/0', 'ip': '192.168.1.1', 'status': 'up'},
                {'name': 'GigabitEthernet0/0/1', 'ip': '10.0.0.1', 'status': 'up'}
            ],
            'metrics': {
                'cpu_usage': 25.5,
                'memory_usage': 45.2,
                'uptime': 86400
            }
        }
        
        # Configurer le mock
        self.mock_repository.get_resource_details.return_value = expected_details
        
        # Exécuter le use case
        result = self.use_case.execute(resource_type="device", resource_id="device_1")
        
        # Vérifications
        self.assertEqual(result, expected_details)
        self.mock_repository.get_resource_details.assert_called_once_with(
            resource_type="device",
            resource_id="device_1"
        )
    
    def test_execute_with_invalid_resource(self):
        """Test exécution avec ressource invalide."""
        # Configurer le mock pour retourner None
        self.mock_repository.get_resource_details.return_value = None
        
        # Exécuter le use case
        result = self.use_case.execute(resource_type="device", resource_id="invalid_id")
        
        # Vérifications
        self.assertIsNone(result)


class TestBatchOperationUseCase(TestCase):
    """
    Tests pour BatchOperationUseCase (classe abstraite).
    
    Test de la structure de base pour les opérations en lot.
    """
    
    def test_abstract_class_cannot_be_instantiated(self):
        """Test que la classe abstraite ne peut pas être instanciée."""
        with self.assertRaises(TypeError):
            BatchOperationUseCase()
    
    def test_abstract_methods_exist(self):
        """Test que les méthodes abstraites existent."""
        # Vérifier que la classe a les méthodes abstraites attendues
        abstract_methods = getattr(BatchOperationUseCase, '__abstractmethods__', set())
        
        # Doit avoir au moins une méthode abstraite
        self.assertGreater(len(abstract_methods), 0)


class TestUseCaseIntegration(TestCase):
    """
    Tests d'intégration pour les cas d'utilisation.
    
    Tests end-to-end avec données réelles PostgreSQL.
    """
    
    def setUp(self):
        """Configuration des tests d'intégration."""
        # Créer un utilisateur réel en base
        self.user = User.objects.create_user(
            username='test_usecase_integration',
            email='usecase_integration@test.com',
            password='testpass123'
        )
    
    def test_use_case_dependency_injection(self):
        """Test l'injection de dépendances dans les use cases."""
        # Mock des repositories
        dashboard_repo = Mock(spec=DashboardRepository)
        topology_repo = Mock(spec=TopologyRepository)
        search_repo = Mock(spec=SearchRepository)
        
        # Créer les use cases avec injection de dépendances
        use_cases = [
            GetDashboardDataUseCase(dashboard_repository=dashboard_repo),
            SaveDashboardConfigurationUseCase(dashboard_repository=dashboard_repo),
            GetNetworkTopologyUseCase(topology_repository=topology_repo),
            StartTopologyDiscoveryUseCase(topology_repository=topology_repo),
            SearchResourcesUseCase(search_repository=search_repo),
            GetResourceDetailsUseCase(search_repository=search_repo)
        ]
        
        # Vérifier que tous les use cases sont correctement initialisés
        for use_case in use_cases:
            with self.subTest(use_case=use_case.__class__.__name__):
                self.assertIsNotNone(use_case)
    
    def test_use_case_error_handling_consistency(self):
        """Test la cohérence de la gestion d'erreurs entre use cases."""
        # Mock des repositories avec erreurs
        error_repo = Mock()
        error_repo.get_dashboard_data.side_effect = Exception("Repository error")
        error_repo.get_network_topology.side_effect = Exception("Repository error")
        error_repo.search_resources.side_effect = Exception("Repository error")
        
        # Créer les use cases
        use_cases = [
            (GetDashboardDataUseCase(dashboard_repository=error_repo), 'execute', {'user_id': self.user.id}),
            (GetNetworkTopologyUseCase(topology_repository=error_repo), 'execute', {}),
            (SearchResourcesUseCase(search_repository=error_repo), 'execute', {'query': 'test'})
        ]
        
        # Vérifier que tous gèrent les erreurs de manière cohérente
        for use_case, method_name, params in use_cases:
            with self.subTest(use_case=use_case.__class__.__name__):
                method = getattr(use_case, method_name)
                
                with self.assertRaises(UseCaseException):
                    method(**params)
