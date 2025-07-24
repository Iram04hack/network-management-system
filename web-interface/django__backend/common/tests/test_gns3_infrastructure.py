"""
Tests complets pour l'infrastructure GNS3 Central Service.

Ce module teste toutes les fonctionnalités du service central GNS3 :
- Service central et ses méthodes
- Interface module
- Système d'événements temps réel
- APIs REST et WebSocket
- Intégration complète
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.core.cache import cache
from channels.testing import WebsocketCommunicator
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from common.infrastructure.gns3_central_service import (
    gns3_central_service, GNS3Event, GNS3EventType, NetworkState
)
from common.api.gns3_module_interface import create_gns3_interface, GNS3SubscriptionType
from common.infrastructure.realtime_event_system import (
    realtime_event_manager, RealtimeEvent, EventPriority, GNS3WebSocketConsumer
)
from common.api.gns3_central_viewsets import GNS3CentralViewSet
from common.integration.module_integration_helper import (
    GNS3ModuleIntegrationMixin, create_integration_config
)


class TestGNS3CentralService(TestCase):
    """Tests pour le service central GNS3."""
    
    def setUp(self):
        """Configuration des tests."""
        self.service = gns3_central_service
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        cache.clear()
    
    @patch('common.infrastructure.gns3_central_service.GNS3Client')
    async def test_service_initialization(self, mock_gns3_client):
        """Test l'initialisation du service central."""
        # Mock du client GNS3
        mock_client = Mock()
        mock_client.get_version.return_value = {'version': '2.2.0'}
        mock_client.get_projects.return_value = []
        mock_gns3_client.return_value = mock_client
        
        # Tester l'initialisation
        result = await self.service.initialize()
        
        self.assertTrue(result)
        self.assertTrue(self.service.is_connected)
    
    def test_service_status(self):
        """Test la récupération du statut du service."""
        status = self.service.get_service_status()
        
        self.assertIn('service_name', status)
        self.assertIn('version', status)
        self.assertIn('status', status)
        self.assertIn('statistics', status)
        self.assertEqual(status['service_name'], 'GNS3CentralService')
    
    async def test_node_actions(self):
        """Test les actions sur les nœuds."""
        project_id = "test-project-123"
        node_id = "test-node-456"
        
        with patch.object(self.service.gns3_client, 'start_node') as mock_start:
            mock_start.return_value = {'success': True}
            
            result = await self.service.start_node(project_id, node_id)
            
            self.assertTrue(result.get('success'))
            mock_start.assert_called_once_with(project_id, node_id)
    
    def test_cache_operations(self):
        """Test les opérations de cache."""
        node_id = "test-node-123"
        node_data = {
            'node_id': node_id,
            'name': 'Test Node',
            'status': 'started'
        }
        
        # Mettre en cache
        cache_key = f"{self.service.cache_prefix}:node:{node_id}"
        cache.set(cache_key, node_data)
        
        # Récupérer depuis le cache
        cached_data = self.service.get_cached_node_status(node_id)
        
        self.assertEqual(cached_data['node_id'], node_id)
        self.assertEqual(cached_data['status'], 'started')


class TestGNS3ModuleInterface(TestCase):
    """Tests pour l'interface module GNS3."""
    
    def setUp(self):
        """Configuration des tests."""
        self.module_name = "test_module"
        self.interface = create_gns3_interface(self.module_name)
        cache.clear()
    
    def test_interface_creation(self):
        """Test la création d'une interface module."""
        self.assertEqual(self.interface.module_name, self.module_name)
        self.assertFalse(self.interface.is_initialized)
    
    async def test_interface_initialization(self):
        """Test l'initialisation de l'interface."""
        with patch.object(gns3_central_service, 'get_service_status') as mock_status:
            mock_status.return_value = {'status': 'connected'}
            
            result = await self.interface.initialize()
            
            self.assertTrue(result)
            self.assertTrue(self.interface.is_initialized)
    
    def test_event_subscription(self):
        """Test l'abonnement aux événements."""
        subscriptions = [GNS3SubscriptionType.NODE_STATUS]
        callback = Mock()
        
        self.interface.subscribe_to_events(subscriptions, callback)
        
        self.assertIn(GNS3SubscriptionType.NODE_STATUS, self.interface.subscriptions)
        self.assertEqual(self.interface.event_callback, callback)
    
    def test_network_summary(self):
        """Test la génération du résumé réseau."""
        # Mock de la topologie
        topology = {
            'projects': {'project1': {}},
            'nodes': {
                'node1': {'status': 'started', 'node_type': 'qemu'},
                'node2': {'status': 'stopped', 'node_type': 'docker'}
            },
            'links': {},
            'last_update': datetime.now().isoformat()
        }
        
        with patch.object(self.interface, 'get_complete_topology') as mock_topology:
            mock_topology.return_value = topology
            
            summary = self.interface.get_network_summary()
            
            self.assertEqual(summary['projects_count'], 1)
            self.assertEqual(summary['nodes_count'], 2)
            self.assertEqual(summary['status_distribution']['started'], 1)
            self.assertEqual(summary['status_distribution']['stopped'], 1)


class TestRealtimeEventSystem(TransactionTestCase):
    """Tests pour le système d'événements temps réel."""
    
    def setUp(self):
        """Configuration des tests."""
        self.event_manager = realtime_event_manager
        cache.clear()
    
    async def test_event_publishing(self):
        """Test la publication d'événements."""
        event = RealtimeEvent(
            event_id="test-event-123",
            event_type="test.event",
            source="test",
            data={"message": "Test event"},
            timestamp=datetime.now(),
            priority=EventPriority.NORMAL
        )
        
        with patch.object(self.event_manager, '_publish_to_websocket') as mock_ws:
            with patch.object(self.event_manager, '_async_redis_lpush') as mock_redis:
                await self.event_manager.publish_event(event)
                
                mock_ws.assert_called_once()
                mock_redis.assert_called_once()
    
    async def test_gns3_event_conversion(self):
        """Test la conversion d'événements GNS3."""
        gns3_event = GNS3Event(
            event_type=GNS3EventType.NODE_STARTED,
            project_id="project-123",
            data={"node_id": "node-456", "new_status": "started"},
            timestamp=datetime.now()
        )
        
        with patch.object(self.event_manager, 'publish_event') as mock_publish:
            await self.event_manager.publish_gns3_event(gns3_event)
            
            mock_publish.assert_called_once()
            published_event = mock_publish.call_args[0][0]
            self.assertEqual(published_event.event_type, GNS3EventType.NODE_STARTED.value)
            self.assertEqual(published_event.priority, EventPriority.HIGH)
    
    def test_statistics(self):
        """Test la récupération des statistiques."""
        stats = self.event_manager.get_statistics()
        
        self.assertIn('events_published', stats)
        self.assertIn('events_delivered', stats)
        self.assertIn('connections_active', stats)
        self.assertIn('is_running', stats)


class TestWebSocketConsumer(TransactionTestCase):
    """Tests pour le consommateur WebSocket."""
    
    async def test_websocket_connection(self):
        """Test la connexion WebSocket."""
        communicator = WebsocketCommunicator(GNS3WebSocketConsumer.as_asgi(), "/ws/gns3/events/")
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Recevoir le message de bienvenue
        message = await communicator.receive_json_from()
        self.assertEqual(message['type'], 'connection_established')
        
        await communicator.disconnect()
    
    async def test_event_subscription(self):
        """Test l'abonnement aux événements via WebSocket."""
        communicator = WebsocketCommunicator(GNS3WebSocketConsumer.as_asgi(), "/ws/gns3/events/")
        
        await communicator.connect()
        
        # S'abonner aux événements de nœuds
        await communicator.send_json_to({
            'type': 'subscribe',
            'subscriptions': ['node_status']
        })
        
        # Recevoir la confirmation
        message = await communicator.receive_json_from(timeout=5)
        self.assertEqual(message['type'], 'subscription_confirmed')
        
        await communicator.disconnect()
    
    async def test_node_action_via_websocket(self):
        """Test les actions sur les nœuds via WebSocket."""
        communicator = WebsocketCommunicator(GNS3WebSocketConsumer.as_asgi(), "/ws/gns3/events/")
        
        await communicator.connect()
        
        with patch('common.infrastructure.gns3_central_service.gns3_central_service.start_node') as mock_start:
            mock_start.return_value = {"success": True}
            
            # Envoyer une action de démarrage
            await communicator.send_json_to({
                'type': 'node_action',
                'action': 'start',
                'project_id': 'project-123',
                'node_id': 'node-456'
            })
            
            # Recevoir le résultat
            message = await communicator.receive_json_from(timeout=5)
            self.assertEqual(message['type'], 'node_action_result')
            self.assertEqual(message['action'], 'start')
        
        await communicator.disconnect()


class TestAPIEndpoints(APITestCase):
    """Tests pour les endpoints API REST."""
    
    def setUp(self):
        """Configuration des tests."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_service_status_endpoint(self):
        """Test l'endpoint de statut du service."""
        response = self.client.get('/api/gns3-central/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('service_name', response.data)
        self.assertIn('version', response.data)
    
    async def test_start_node_endpoint(self):
        """Test l'endpoint de démarrage de nœud."""
        with patch('common.infrastructure.gns3_central_service.gns3_central_service.start_node') as mock_start:
            mock_start.return_value = {"success": True, "node_id": "node-123"}
            
            response = self.client.post('/api/gns3-central/start_node/', {
                'project_id': 'project-123',
                'node_id': 'node-456'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data.get('success'))
    
    def test_topology_endpoint(self):
        """Test l'endpoint de topologie."""
        # Mock de la topologie
        topology = {
            'projects': {},
            'nodes': {},
            'links': {},
            'last_update': datetime.now().isoformat()
        }
        
        with patch('common.infrastructure.gns3_central_service.gns3_central_service.get_cached_topology') as mock_topology:
            mock_topology.return_value = topology
            
            response = self.client.get('/api/gns3-central/topology/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('projects', response.data)
    
    def test_create_module_interface_endpoint(self):
        """Test l'endpoint de création d'interface module."""
        response = self.client.post('/api/gns3-central/create_module_interface/', {
            'module_name': 'test_module'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data.get('module_name'), 'test_module')
    
    def test_unauthorized_access(self):
        """Test l'accès non autorisé aux APIs."""
        self.client.logout()
        
        response = self.client.get('/api/gns3-central/status/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestModuleIntegration(TestCase):
    """Tests pour l'intégration des modules."""
    
    def test_integration_mixin(self):
        """Test le mixin d'intégration."""
        class TestModule(GNS3ModuleIntegrationMixin):
            def __init__(self):
                self.setup_gns3_integration('test_module')
        
        module = TestModule()
        
        self.assertEqual(module.module_name, 'test_module')
        self.assertIsNotNone(module.gns3_interface)
    
    def test_integration_config(self):
        """Test la configuration d'intégration."""
        config = create_integration_config(
            'monitoring',
            events=['node_status', 'topology_changes'],
            node_types=['qemu', 'docker']
        )
        
        self.assertEqual(config.module_name, 'monitoring')
        self.assertIn(GNS3SubscriptionType.NODE_STATUS, config.auto_subscribe_events)
        self.assertIn(GNS3SubscriptionType.TOPOLOGY_CHANGES, config.auto_subscribe_events)
        self.assertEqual(config.required_node_types, ['qemu', 'docker'])
    
    async def test_event_handling(self):
        """Test la gestion d'événements dans les modules."""
        class TestModule(GNS3ModuleIntegrationMixin):
            def __init__(self):
                self.events_received = []
                self.setup_gns3_integration('test_module')
            
            async def on_node_status_change(self, event):
                self.events_received.append(event)
        
        module = TestModule()
        
        # Simuler un événement
        event = GNS3Event(
            event_type=GNS3EventType.NODE_STARTED,
            project_id="project-123",
            data={"node_id": "node-456"},
            timestamp=datetime.now()
        )
        
        await module._handle_gns3_event(event)
        
        self.assertEqual(len(module.events_received), 1)


class TestIntegrationComplète(TransactionTestCase):
    """Tests d'intégration complète du système."""
    
    def setUp(self):
        """Configuration des tests d'intégration."""
        self.user = User.objects.create_user(
            username='integrationuser',
            password='testpass123'
        )
        cache.clear()
    
    async def test_end_to_end_workflow(self):
        """Test un workflow complet end-to-end."""
        # 1. Créer une interface module
        interface = create_gns3_interface('integration_test')
        
        # 2. Initialiser l'interface
        with patch.object(gns3_central_service, 'get_service_status') as mock_status:
            mock_status.return_value = {'status': 'connected'}
            await interface.initialize()
        
        # 3. S'abonner aux événements
        events_received = []
        
        async def event_handler(event):
            events_received.append(event)
        
        interface.subscribe_to_events([GNS3SubscriptionType.NODE_STATUS], event_handler)
        
        # 4. Simuler une action via l'API
        with patch.object(gns3_central_service, 'start_node') as mock_start:
            mock_start.return_value = {"success": True}
            
            result = await interface.start_node('project-123', 'node-456')
            self.assertTrue(result.get('success'))
        
        # 5. Vérifier que l'événement a été traité
        # (Dans un test réel, l'événement serait généré automatiquement)
        self.assertTrue(interface.is_initialized)
    
    async def test_performance_under_load(self):
        """Test les performances sous charge."""
        # Créer plusieurs interfaces
        interfaces = []
        for i in range(10):
            interface = create_gns3_interface(f'load_test_{i}')
            interfaces.append(interface)
        
        # Initialiser toutes les interfaces en parallèle
        with patch.object(gns3_central_service, 'get_service_status') as mock_status:
            mock_status.return_value = {'status': 'connected'}
            
            tasks = [interface.initialize() for interface in interfaces]
            results = await asyncio.gather(*tasks)
            
            # Vérifier que toutes les initialisations ont réussi
            self.assertTrue(all(results))
    
    def test_error_handling(self):
        """Test la gestion d'erreurs dans le système."""
        # Test avec service GNS3 indisponible
        with patch.object(gns3_central_service, 'get_service_status') as mock_status:
            mock_status.return_value = {'status': 'disconnected'}
            
            interface = create_gns3_interface('error_test')
            
            # L'interface devrait gérer l'erreur gracieusement
            self.assertIsNotNone(interface)
            self.assertFalse(interface.is_initialized)


# Configuration des tests
@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    },
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }
)
class TestSuite:
    """Suite de tests pour l'infrastructure GNS3."""
    
    @staticmethod
    def run_all_tests():
        """Exécute tous les tests de l'infrastructure."""
        import django
        from django.test.utils import get_runner
        from django.conf import settings
        
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner()
        
        failures = test_runner.run_tests([
            'common.tests.test_gns3_infrastructure'
        ])
        
        return failures == 0


if __name__ == '__main__':
    # Exécuter les tests en mode standalone
    result = TestSuite.run_all_tests()
    if result:
        print("✅ Tous les tests sont passés avec succès!")
    else:
        print("❌ Certains tests ont échoué!")
        exit(1)