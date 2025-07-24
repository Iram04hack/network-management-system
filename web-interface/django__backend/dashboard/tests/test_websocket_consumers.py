"""
Tests pour les consommateurs WebSocket du module dashboard.

Tests pour DashboardConsumer et TopologyConsumer.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from dashboard.consumers import DashboardConsumer, TopologyConsumer

pytestmark = pytest.mark.django_db


class TestDashboardConsumer(TestCase):
    """Tests pour le consumer WebSocket du dashboard."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.mark.asyncio
    async def test_consumer_connect_authenticated(self):
        """Test de connexion avec utilisateur authentifié."""
        # Mock des données de dashboard
        mock_dashboard_data = {
            'devices': {'total': 10, 'active': 8},
            'alerts': [],
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_dashboard_data
            
            # Créer le communicator avec un utilisateur authentifié
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            # Connecter
            connected, subprotocol = await communicator.connect()
            assert connected
            
            # Vérifier que les données initiales sont envoyées
            response = await communicator.receive_json_from()
            assert response['type'] == 'dashboard_update'
            assert response['data'] == mock_dashboard_data
            
            # Déconnecter
            await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_connect_anonymous(self):
        """Test de refus de connexion pour utilisateur anonyme."""
        # Créer le communicator avec un utilisateur anonyme
        communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
        communicator.scope["user"] = AnonymousUser()
        
        # La connexion doit être refusée
        connected, subprotocol = await communicator.connect()
        assert not connected
    
    @pytest.mark.asyncio
    async def test_consumer_receive_get_dashboard_command(self):
        """Test de réception de la commande get_dashboard."""
        mock_dashboard_data = {
            'devices': {'total': 5, 'active': 4},
            'alerts': [{'id': 1, 'message': 'Test alert'}],
            'timestamp': '2024-01-01T12:05:00Z'
        }
        
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_dashboard_data
            
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            await communicator.connect()
            
            # Ignorer le message initial
            await communicator.receive_json_from()
            
            # Envoyer la commande get_dashboard
            await communicator.send_json_to({
                'command': 'get_dashboard'
            })
            
            # Vérifier la réponse
            response = await communicator.receive_json_from()
            assert response['type'] == 'dashboard_update'
            assert response['data'] == mock_dashboard_data
            assert response['timestamp'] == mock_dashboard_data['timestamp']
            
            await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_receive_get_network_overview_command(self):
        """Test de réception de la commande get_network_overview."""
        mock_network_data = {
            'devices': {'total': 15, 'active': 12},
            'interfaces': {'total': 45, 'up': 40},
            'timestamp': '2024-01-01T12:05:00Z'
        }
        
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_dashboard:
            with patch.object(DashboardConsumer, '_get_network_data', new_callable=AsyncMock) as mock_get_network:
                mock_get_dashboard.return_value = {}
                mock_get_network.return_value = mock_network_data
                
                communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
                communicator.scope["user"] = self.user
                
                await communicator.connect()
                await communicator.receive_json_from()  # Message initial
                
                # Envoyer la commande get_network_overview
                await communicator.send_json_to({
                    'command': 'get_network_overview'
                })
                
                # Vérifier la réponse
                response = await communicator.receive_json_from()
                assert response['type'] == 'network_update'
                assert response['data'] == mock_network_data
                assert response['timestamp'] == mock_network_data['timestamp']
                
                await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_receive_get_health_metrics_command(self):
        """Test de réception de la commande get_health_metrics."""
        mock_health_data = {
            'system_health': 0.85,
            'network_health': 0.90,
            'security_health': 0.75
        }
        
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_dashboard:
            with patch.object(DashboardConsumer, '_get_health_metrics', new_callable=AsyncMock) as mock_get_health:
                mock_get_dashboard.return_value = {}
                mock_get_health.return_value = mock_health_data
                
                communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
                communicator.scope["user"] = self.user
                
                await communicator.connect()
                await communicator.receive_json_from()  # Message initial
                
                # Envoyer la commande get_health_metrics
                await communicator.send_json_to({
                    'command': 'get_health_metrics'
                })
                
                # Vérifier la réponse
                response = await communicator.receive_json_from()
                assert response['type'] == 'health_update'
                assert response['data'] == mock_health_data
                
                await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_set_update_interval_valid(self):
        """Test de modification de l'intervalle de mise à jour (valide)."""
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            await communicator.connect()
            await communicator.receive_json_from()  # Message initial
            
            # Envoyer la commande set_update_interval
            await communicator.send_json_to({
                'command': 'set_update_interval',
                'interval': 60
            })
            
            # Vérifier la réponse
            response = await communicator.receive_json_from()
            assert response['type'] == 'interval_updated'
            assert response['interval'] == 60
            
            await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_set_update_interval_invalid(self):
        """Test de modification de l'intervalle de mise à jour (invalide)."""
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            await communicator.connect()
            await communicator.receive_json_from()  # Message initial
            
            # Envoyer une commande avec intervalle invalide
            await communicator.send_json_to({
                'command': 'set_update_interval',
                'interval': 400  # Trop élevé
            })
            
            # Vérifier la réponse d'erreur
            response = await communicator.receive_json_from()
            assert response['type'] == 'error'
            assert 'Intervalle doit être entre 5 et 300' in response['message']
            
            await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_invalid_json(self):
        """Test de gestion d'un JSON invalide."""
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            await communicator.connect()
            await communicator.receive_json_from()  # Message initial
            
            # Envoyer un JSON invalide
            await communicator.send_to(text_data="invalid json")
            
            # Vérifier la réponse d'erreur
            response = await communicator.receive_json_from()
            assert response['type'] == 'error'
            assert 'Format JSON invalide' in response['message']
            
            await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_consumer_data_retrieval_error(self):
        """Test de gestion d'erreur lors de la récupération de données."""
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.side_effect = Exception("Database error")
            
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            await communicator.connect()
            
            # Vérifier que l'erreur est gérée
            response = await communicator.receive_json_from()
            assert response['type'] == 'error'
            assert 'Erreur lors du chargement des données initiales' in response['message']
            
            await communicator.disconnect()


class TestTopologyConsumer(TestCase):
    """Tests pour le consumer WebSocket de topologie."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.topology_id = 123
    
    @pytest.mark.asyncio
    async def test_topology_consumer_connect_authenticated(self):
        """Test de connexion avec utilisateur authentifié et topology_id."""
        mock_topology_data = {
            'topology_id': self.topology_id,
            'name': 'Test Topology',
            'nodes': [{'id': 1, 'name': 'Node1'}],
            'connections': []
        }
        
        with patch.object(TopologyConsumer, '_get_topology_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_topology_data
            
            # Créer le communicator avec topology_id dans l'URL
            communicator = WebsocketCommunicator(
                TopologyConsumer.as_asgi(), 
                f"/ws/topology/{self.topology_id}/"
            )
            communicator.scope["user"] = self.user
            communicator.scope['url_route'] = {
                'kwargs': {'topology_id': self.topology_id}
            }
            
            # Connecter
            connected, subprotocol = await communicator.connect()
            assert connected
            
            # Vérifier que les données initiales sont envoyées
            response = await communicator.receive_json_from()
            assert response['type'] == 'topology_update'
            assert response['data'] == mock_topology_data
            
            await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_topology_consumer_connect_anonymous(self):
        """Test de refus de connexion pour utilisateur anonyme."""
        communicator = WebsocketCommunicator(
            TopologyConsumer.as_asgi(), 
            f"/ws/topology/{self.topology_id}/"
        )
        communicator.scope["user"] = AnonymousUser()
        communicator.scope['url_route'] = {
            'kwargs': {'topology_id': self.topology_id}
        }
        
        # La connexion doit être refusée
        connected, subprotocol = await communicator.connect()
        assert not connected
    
    @pytest.mark.asyncio
    async def test_topology_consumer_connect_no_topology_id(self):
        """Test de refus de connexion sans topology_id."""
        communicator = WebsocketCommunicator(
            TopologyConsumer.as_asgi(), 
            "/ws/topology/"
        )
        communicator.scope["user"] = self.user
        communicator.scope['url_route'] = {
            'kwargs': {}  # Pas de topology_id
        }
        
        # La connexion doit être refusée
        connected, subprotocol = await communicator.connect()
        assert not connected
    
    @pytest.mark.asyncio
    async def test_topology_consumer_data_error(self):
        """Test de gestion d'erreur lors de la récupération de données de topologie."""
        with patch.object(TopologyConsumer, '_get_topology_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.side_effect = Exception("Topology not found")
            
            communicator = WebsocketCommunicator(
                TopologyConsumer.as_asgi(), 
                f"/ws/topology/{self.topology_id}/"
            )
            communicator.scope["user"] = self.user
            communicator.scope['url_route'] = {
                'kwargs': {'topology_id': self.topology_id}
            }
            
            await communicator.connect()
            
            # Vérifier que l'erreur est gérée
            response = await communicator.receive_json_from()
            assert response['type'] == 'error'
            assert 'Erreur lors du chargement de la topologie' in response['message']
            
            await communicator.disconnect()


class TestConsumerDataMethods(TestCase):
    """Tests pour les méthodes de récupération de données des consumers."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.mark.asyncio
    async def test_dashboard_consumer_get_dashboard_data(self):
        """Test de la méthode _get_dashboard_data du DashboardConsumer."""
        consumer = DashboardConsumer()
        consumer.scope = {"user": self.user}
        
        mock_data = {
            'devices': {'total': 10, 'active': 8},
            'alerts': [],
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        with patch('django__backend.dashboard.consumers.get_container') as mock_get_container:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = mock_data
            
            mock_container = Mock()
            mock_container.resolve.return_value = mock_use_case
            mock_get_container.return_value = mock_container
            
            result = await consumer._get_dashboard_data()
            
            assert result == mock_data
            mock_container.resolve.assert_called_once()
            mock_use_case.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dashboard_consumer_get_network_data(self):
        """Test de la méthode _get_network_data du DashboardConsumer."""
        consumer = DashboardConsumer()
        consumer.scope = {"user": self.user}
        
        mock_data = {
            'devices': {'total': 15, 'active': 12},
            'interfaces': {'total': 45, 'up': 40}
        }
        
        with patch('django__backend.dashboard.consumers.get_container') as mock_get_container:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = mock_data
            
            mock_container = Mock()
            mock_container.resolve.return_value = mock_use_case
            mock_get_container.return_value = mock_container
            
            result = await consumer._get_network_data()
            
            assert result == mock_data
            mock_container.resolve.assert_called_once()
            mock_use_case.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dashboard_consumer_get_health_metrics(self):
        """Test de la méthode _get_health_metrics du DashboardConsumer."""
        consumer = DashboardConsumer()
        consumer.scope = {"user": self.user}
        
        mock_data = {
            'system_health': 0.85,
            'network_health': 0.90,
            'security_health': 0.75
        }
        
        with patch('django__backend.dashboard.consumers.get_container') as mock_get_container:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = mock_data
            
            mock_container = Mock()
            mock_container.resolve.return_value = mock_use_case
            mock_get_container.return_value = mock_container
            
            result = await consumer._get_health_metrics()
            
            assert result == mock_data
            mock_container.resolve.assert_called_once()
            mock_use_case.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_topology_consumer_get_topology_data(self):
        """Test de la méthode _get_topology_data du TopologyConsumer."""
        topology_id = 123
        consumer = TopologyConsumer()
        consumer.scope = {"user": self.user}
        consumer.topology_id = topology_id
        
        mock_data = {
            'topology_id': topology_id,
            'name': 'Test Topology',
            'nodes': [],
            'connections': []
        }
        
        with patch('django__backend.dashboard.consumers.get_container') as mock_get_container:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = mock_data
            
            mock_container = Mock()
            mock_container.resolve.return_value = mock_use_case
            mock_get_container.return_value = mock_container
            
            result = await consumer._get_topology_data()
            
            assert result == mock_data
            mock_container.resolve.assert_called_once()
            mock_use_case.execute.assert_called_once_with(topology_id)
    
    @pytest.mark.asyncio
    async def test_data_method_error_handling(self):
        """Test de gestion d'erreur dans les méthodes de récupération de données."""
        consumer = DashboardConsumer()
        consumer.scope = {"user": self.user}
        
        with patch('django__backend.dashboard.consumers.get_container') as mock_get_container:
            mock_get_container.side_effect = Exception("Container error")
            
            result = await consumer._get_dashboard_data()
            
            assert 'error' in result
            assert result['error'] == "Container error"


class TestConsumerTaskManagement(TestCase):
    """Tests pour la gestion des tâches dans les consumers."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.mark.asyncio
    async def test_dashboard_consumer_task_cancellation_on_disconnect(self):
        """Test d'annulation de la tâche de mise à jour lors de la déconnexion."""
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
            communicator.scope["user"] = self.user
            
            await communicator.connect()
            await communicator.receive_json_from()  # Message initial
            
            # Vérifier que la tâche de mise à jour existe
            consumer = communicator.instance
            assert consumer.update_task is not None
            assert not consumer.update_task.cancelled()
            
            # Déconnecter
            await communicator.disconnect()
            
            # Vérifier que la tâche a été annulée
            assert consumer.update_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_topology_consumer_task_cancellation_on_disconnect(self):
        """Test d'annulation de la tâche de mise à jour de topologie lors de la déconnexion."""
        topology_id = 123
        
        with patch.object(TopologyConsumer, '_get_topology_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            communicator = WebsocketCommunicator(
                TopologyConsumer.as_asgi(), 
                f"/ws/topology/{topology_id}/"
            )
            communicator.scope["user"] = self.user
            communicator.scope['url_route'] = {
                'kwargs': {'topology_id': topology_id}
            }
            
            await communicator.connect()
            await communicator.receive_json_from()  # Message initial
            
            # Vérifier que la tâche de mise à jour existe
            consumer = communicator.instance
            assert consumer.update_task is not None
            assert not consumer.update_task.cancelled()
            
            # Déconnecter
            await communicator.disconnect()
            
            # Vérifier que la tâche a été annulée
            assert consumer.update_task.cancelled()


class TestConsumerGroupCommunication(TestCase):
    """Tests pour la communication de groupe dans les consumers."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.mark.asyncio
    async def test_dashboard_consumer_group_operations(self):
        """Test des opérations de groupe pour DashboardConsumer."""
        with patch.object(DashboardConsumer, '_get_dashboard_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            consumer = DashboardConsumer()
            consumer.scope = {"user": self.user}
            consumer.channel_layer = Mock()
            consumer.channel_name = "test.channel.name"
            consumer.group_name = "dashboard_updates"
            
            # Test de connexion (ajout au groupe)
            await consumer.connect()
            
            consumer.channel_layer.group_add.assert_called_once_with(
                "dashboard_updates",
                "test.channel.name"
            )
            
            # Test de déconnexion (suppression du groupe)
            await consumer.disconnect(1000)
            
            consumer.channel_layer.group_discard.assert_called_once_with(
                "dashboard_updates",
                "test.channel.name"
            )
    
    @pytest.mark.asyncio
    async def test_topology_consumer_group_operations(self):
        """Test des opérations de groupe pour TopologyConsumer."""
        topology_id = 123
        
        with patch.object(TopologyConsumer, '_get_topology_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = {}
            
            consumer = TopologyConsumer()
            consumer.scope = {
                "user": self.user,
                'url_route': {'kwargs': {'topology_id': topology_id}}
            }
            consumer.channel_layer = Mock()
            consumer.channel_name = "test.channel.name"
            consumer.topology_id = topology_id
            
            # Test de connexion (ajout au groupe)
            await consumer.connect()
            
            consumer.channel_layer.group_add.assert_called_once_with(
                f"topology_{topology_id}",
                "test.channel.name"
            )
            
            # Test de déconnexion (suppression du groupe)
            await consumer.disconnect(1000)
            
            consumer.channel_layer.group_discard.assert_called_once_with(
                f"topology_{topology_id}",
                "test.channel.name"
            )