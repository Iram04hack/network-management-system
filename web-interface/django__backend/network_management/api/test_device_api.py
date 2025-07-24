"""
Tests d'intégration pour l'API des équipements réseau.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User

from network_management.infrastructure.models import NetworkDevice


class DeviceAPITestCase(APITestCase):
    """
    Tests d'intégration pour l'API des équipements réseau.
    """

    def setUp(self):
        """
        Initialisation avant chaque test.
        """
        # Créer un utilisateur pour l'authentification
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        
        # Créer un client API
        self.client = APIClient()
        self.client.login(username=self.username, password=self.password)
        
        # Créer des équipements de test
        self.device1 = NetworkDevice.objects.create(
            name="Router-1",
            ip_address="192.168.1.1",
            device_type="router",
            vendor="Cisco",
            status="active"
        )
        
        self.device2 = NetworkDevice.objects.create(
            name="Switch-1",
            ip_address="192.168.1.2",
            device_type="switch",
            vendor="Juniper",
            status="active"
        )
        
        # URLs pour les tests
        self.list_url = reverse('network-devices-list')
        self.detail_url = reverse('network-devices-detail', args=[self.device1.id])

    def test_get_device_list(self):
        """
        Test de récupération de la liste des équipements.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], "Router-1")
        self.assertEqual(response.data[1]['name'], "Switch-1")

    def test_get_device_detail(self):
        """
        Test de récupération des détails d'un équipement.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Router-1")
        self.assertEqual(response.data['ip_address'], "192.168.1.1")
        self.assertEqual(response.data['device_type'], "router")

    def test_create_device(self):
        """
        Test de création d'un équipement.
        """
        data = {
            "name": "Firewall-1",
            "ip_address": "192.168.1.3",
            "device_type": "firewall",
            "vendor": "Palo Alto",
            "status": "active"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Firewall-1")
        self.assertEqual(response.data['ip_address'], "192.168.1.3")
        
        # Vérifier que l'équipement a bien été créé en base de données
        self.assertEqual(NetworkDevice.objects.count(), 3)
        device = NetworkDevice.objects.get(name="Firewall-1")
        self.assertEqual(device.ip_address, "192.168.1.3")
        self.assertEqual(device.device_type, "firewall")

    def test_update_device(self):
        """
        Test de mise à jour d'un équipement.
        """
        data = {
            "name": "Router-1-Updated",
            "status": "maintenance"
        }
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Router-1-Updated")
        self.assertEqual(response.data['status'], "maintenance")
        
        # Vérifier que l'équipement a bien été mis à jour en base de données
        device = NetworkDevice.objects.get(id=self.device1.id)
        self.assertEqual(device.name, "Router-1-Updated")
        self.assertEqual(device.status, "maintenance")

    def test_delete_device(self):
        """
        Test de suppression d'un équipement.
        """
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que l'équipement a bien été supprimé en base de données
        self.assertEqual(NetworkDevice.objects.count(), 1)
        with self.assertRaises(NetworkDevice.DoesNotExist):
            NetworkDevice.objects.get(id=self.device1.id)

    def test_search_devices(self):
        """
        Test de recherche d'équipements.
        """
        url = f"{self.list_url}?query=Router"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Router-1")
        
        url = f"{self.list_url}?query=Juniper"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Switch-1")

    def test_get_device_interfaces(self):
        """
        Test de récupération des interfaces d'un équipement.
        """
        url = reverse('network-devices-interfaces', args=[self.device1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Pas d'interfaces créées pour le moment

    def test_get_device_configurations(self):
        """
        Test de récupération des configurations d'un équipement.
        """
        url = reverse('network-devices-configurations', args=[self.device1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Pas de configurations créées pour le moment 