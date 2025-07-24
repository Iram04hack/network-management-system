"""
Tests d'intégration pour la gestion de la qualité de service (QoS).
Ce fichier contient des tests d'intégration pour vérifier le fonctionnement de la gestion QoS.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from qos_management.models import QoSPolicy, TrafficClass, TrafficClassifier, InterfaceQoSPolicy
from network_management.models import NetworkDevice, NetworkInterface
from api_clients.traffic_control_client import TrafficControlClient

pytestmark = [pytest.mark.django_db, pytest.mark.qos, pytest.mark.integration]


@pytest.fixture
def api_client():
    """Fixture pour créer un client API."""
    client = APIClient()
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def test_user():
    """Fixture pour créer un utilisateur de test."""
    return User.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="password456"
    )


@pytest.fixture
def test_device(test_user):
    """Fixture pour créer un équipement réseau de test."""
    device = NetworkDevice.objects.create(
        name="Router de Test",
        hostname="test-router.local",
        ip_address="192.168.1.1",
        device_type="router",
        os="cisco_ios",
        created_by=test_user
    )
    return device


@pytest.fixture
def test_interface(test_device):
    """Fixture pour créer une interface réseau de test."""
    interface = NetworkInterface.objects.create(
        device=test_device,
        name="GigabitEthernet0/0",
        mac_address="00:11:22:33:44:55",
        ip_address="192.168.1.1",
        status="up"
    )
    return interface


@pytest.fixture
def test_qos_policy():
    """Fixture pour créer une politique QoS de test."""
    policy = QoSPolicy.objects.create(
        name="Politique QoS de Test",
        description="Politique pour tester l'intégration QoS",
        is_active=True
    )
    return policy


@pytest.fixture
def test_traffic_classes(test_qos_policy):
    """Fixture pour créer des classes de trafic de test."""
    classes = [
        TrafficClass.objects.create(
            policy=test_qos_policy,
            name="Voix",
            description="Trafic voix prioritaire",
            dscp="ef",
            priority=10,
            min_bandwidth=10000,
            max_bandwidth=20000
        ),
        TrafficClass.objects.create(
            policy=test_qos_policy,
            name="Vidéo",
            description="Trafic vidéo",
            dscp="af41",
            priority=8,
            min_bandwidth=20000,
            max_bandwidth=50000
        ),
        TrafficClass.objects.create(
            policy=test_qos_policy,
            name="Web",
            description="Trafic web standard",
            dscp="af21",
            priority=5,
            min_bandwidth=10000,
            max_bandwidth=100000
        )
    ]
    
    # Créer des classificateurs pour chaque classe
    TrafficClassifier.objects.create(
        traffic_class=classes[0],
        name="SIP",
        protocol="udp",
        destination_port_start=5060,
        destination_port_end=5061,
        dscp_marking="ef"
    )
    
    TrafficClassifier.objects.create(
        traffic_class=classes[1],
        name="RTP",
        protocol="udp",
        destination_port_start=16384,
        destination_port_end=32767,
        dscp_marking="af41"
    )
    
    TrafficClassifier.objects.create(
        traffic_class=classes[2],
        name="HTTP/HTTPS",
        protocol="tcp",
        destination_port_start=80,
        destination_port_end=443,
        dscp_marking="af21"
    )
    
    return classes


class TestQoSIntegration:
    """Tests d'intégration pour la gestion QoS."""
    
    def test_list_policies(self, api_client, test_qos_policy):
        """Test de récupération de la liste des politiques QoS."""
        response = api_client.get("/api/qos/policies/")
        
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert any(policy["name"] == test_qos_policy.name for policy in response.data)
    
    def test_get_traffic_classes(self, api_client, test_qos_policy, test_traffic_classes):
        """Test de récupération des classes de trafic d'une politique."""
        response = api_client.get(f"/api/qos/policies/{test_qos_policy.id}/traffic_classes/")
        
        assert response.status_code == 200
        assert len(response.data) == 3
        class_names = [tc["name"] for tc in response.data]
        assert "Voix" in class_names
        assert "Vidéo" in class_names
        assert "Web" in class_names
    
    @patch('api_clients.traffic_control_client.TrafficControlClient.test_connection')
    @patch('api_clients.traffic_control_client.TrafficControlClient.set_traffic_prioritization')
    @patch('api_clients.traffic_control_client.TrafficControlClient.add_traffic_filter')
    def test_apply_policy_to_interface(self, mock_add_filter, mock_set_prio, mock_test_connection, 
                                      api_client, test_qos_policy, test_interface, test_traffic_classes):
        """Test d'application d'une politique QoS à une interface."""
        # Configuration des mocks
        mock_test_connection.return_value = True
        mock_set_prio.return_value = True
        mock_add_filter.return_value = True
        
        # Appel de l'API pour appliquer la politique
        response = api_client.post(
            f"/api/qos/policies/{test_qos_policy.id}/apply_to_interface/",
            {
                "interface_id": test_interface.id,
                "direction": "egress"
            }
        )
        
        assert response.status_code == 201
        assert response.data["interface"] == test_interface.id
        assert response.data["policy"] == test_qos_policy.id
        assert response.data["direction"] == "egress"
        
        # Vérifier que les appels aux méthodes Traffic Control ont été effectués
        mock_test_connection.assert_called_once()
        mock_set_prio.assert_called_once()
        assert mock_add_filter.call_count >= 3  # Au moins un appel pour chaque classe
    
    def test_toggle_policy_status(self, api_client, test_qos_policy, test_interface):
        """Test de l'activation/désactivation d'une politique sur une interface."""
        # Créer une application de politique
        interface_policy = InterfaceQoSPolicy.objects.create(
            interface=test_interface,
            policy=test_qos_policy,
            direction="egress",
            is_active=True
        )
        
        # Désactiver la politique
        response = api_client.post(f"/api/qos/interface_policies/{interface_policy.id}/toggle_status/")
        
        assert response.status_code == 200
        assert response.data["is_active"] is False
        
        # Réactiver la politique
        response = api_client.post(f"/api/qos/interface_policies/{interface_policy.id}/toggle_status/")
        
        assert response.status_code == 200
        assert response.data["is_active"] is True
    
    def test_remove_policy_from_interface(self, api_client, test_qos_policy, test_interface):
        """Test de suppression d'une politique d'une interface."""
        # Créer une application de politique
        interface_policy = InterfaceQoSPolicy.objects.create(
            interface=test_interface,
            policy=test_qos_policy,
            direction="egress",
            is_active=True
        )
        
        # Supprimer la politique
        response = api_client.delete(f"/api/qos/interface_policies/{interface_policy.id}/remove/")
        
        assert response.status_code == 204
        
        # Vérifier que la politique a été supprimée
        assert not InterfaceQoSPolicy.objects.filter(id=interface_policy.id).exists()
    
    def test_qos_visualization(self, api_client, test_qos_policy, test_traffic_classes):
        """Test de visualisation des politiques QoS."""
        response = api_client.get(f"/api/qos/visualization/{test_qos_policy.id}/")
        
        assert response.status_code == 200
        assert "policy" in response.data
        assert "traffic_classes" in response.data
        assert len(response.data["traffic_classes"]) == 3
        assert "traffic_data" in response.data
    
    def test_qos_configurer(self, api_client):
        """Test de l'assistant de configuration QoS."""
        response = api_client.get("/api/qos/configurer/", {
            "traffic_type": "mixed",
            "network_size": "medium"
        })
        
        assert response.status_code == 200
        assert "recommendations" in response.data
        assert len(response.data["recommendations"]) > 0


@pytest.mark.skipif(not pytest.has_traffic_control(), reason="Traffic Control non disponible")
class TestRealQoSIntegration:
    """Tests d'intégration avec l'outil Traffic Control réel."""
    
    def test_real_traffic_control_connection(self):
        """Test de la connexion à l'outil Traffic Control réel."""
        tc_client = TrafficControlClient(sudo_required=False)  # Ne pas utiliser sudo pour les tests
        
        # Tester la connexion
        assert tc_client.test_connection() is True
    
    def test_real_traffic_control_commands(self):
        """Test des commandes Traffic Control réelles (lecture seule)."""
        tc_client = TrafficControlClient(sudo_required=False)
        
        # Lister les interfaces (commande en lecture seule)
        interfaces = tc_client.list_interfaces()
        assert len(interfaces) > 0
        
        # Obtenir les statistiques (commande en lecture seule)
        stats = tc_client.get_interface_stats(interfaces[0])
        assert stats is not None 