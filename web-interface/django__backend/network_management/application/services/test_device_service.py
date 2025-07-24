"""
Tests unitaires pour le service DeviceService.
"""

import unittest
from unittest.mock import MagicMock, patch

from network_management.application.services.device_service import DeviceService
from network_management.domain.entities import NetworkDevice
from network_management.domain.exceptions import EntityNotFoundException, ValidationException


class TestDeviceService(unittest.TestCase):
    """
    Tests unitaires pour le service DeviceService.
    """

    def setUp(self):
        """
        Initialisation avant chaque test.
        """
        self.repository = MagicMock()
        self.service = DeviceService(self.repository)
        
        # Créer un appareil de test
        self.test_device = NetworkDevice(
            id=1,
            name="Test Router",
            ip_address="192.168.1.1",
            device_type="router",
            vendor="Cisco",
            status="active"
        )

    def test_get_device_success(self):
        """
        Test de récupération d'un appareil avec succès.
        """
        # Configurer le mock
        self.repository.get_by_id.return_value = self.test_device
        
        # Appeler la méthode à tester
        result = self.service.get_device(1)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once_with(1)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Test Router")
        self.assertEqual(result.ip_address, "192.168.1.1")

    def test_get_device_not_found(self):
        """
        Test de récupération d'un appareil qui n'existe pas.
        """
        # Configurer le mock
        self.repository.get_by_id.return_value = None
        
        # Vérifier que l'exception est levée
        with self.assertRaises(EntityNotFoundException):
            self.service.get_device(999)
        
        # Vérifier que la méthode du repository a été appelée
        self.repository.get_by_id.assert_called_once_with(999)

    def test_get_all_devices(self):
        """
        Test de récupération de tous les appareils.
        """
        # Configurer le mock
        self.repository.get_all.return_value = [self.test_device]
        
        # Appeler la méthode à tester
        result = self.service.get_all_devices()
        
        # Vérifier les résultats
        self.repository.get_all.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "Test Router")

    def test_create_device_success(self):
        """
        Test de création d'un appareil avec succès.
        """
        # Données pour la création
        device_data = {
            "name": "New Router",
            "ip_address": "192.168.2.1",
            "device_type": "router",
            "vendor": "Juniper",
            "status": "active"
        }
        
        # Créer un appareil de retour avec ID
        new_device = NetworkDevice(id=2, **device_data)
        
        # Configurer le mock
        self.repository.create.return_value = new_device
        
        # Appeler la méthode à tester
        result = self.service.create_device(device_data)
        
        # Vérifier les résultats
        self.repository.create.assert_called_once()
        self.assertEqual(result.id, 2)
        self.assertEqual(result.name, "New Router")
        self.assertEqual(result.ip_address, "192.168.2.1")

    def test_create_device_validation_error(self):
        """
        Test de création d'un appareil avec des données invalides.
        """
        # Données invalides (manque le nom)
        invalid_data = {
            "ip_address": "192.168.2.1",
            "device_type": "router",
            "vendor": "Juniper"
        }
        
        # Vérifier que l'exception est levée
        with self.assertRaises(ValidationException):
            self.service.create_device(invalid_data)
        
        # Vérifier que la méthode du repository n'a pas été appelée
        self.repository.create.assert_not_called()

    def test_update_device_success(self):
        """
        Test de mise à jour d'un appareil avec succès.
        """
        # Données pour la mise à jour
        update_data = {
            "name": "Updated Router",
            "status": "maintenance"
        }
        
        # Configurer le mock pour get_by_id
        self.repository.get_by_id.return_value = self.test_device
        
        # Configurer le mock pour update
        updated_device = NetworkDevice(
            id=1,
            name="Updated Router",
            ip_address="192.168.1.1",
            device_type="router",
            vendor="Cisco",
            status="maintenance"
        )
        self.repository.update.return_value = updated_device
        
        # Appeler la méthode à tester
        result = self.service.update_device(1, update_data)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once_with(1)
        self.repository.update.assert_called_once()
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Updated Router")
        self.assertEqual(result.status, "maintenance")

    def test_update_device_not_found(self):
        """
        Test de mise à jour d'un appareil qui n'existe pas.
        """
        # Configurer le mock
        self.repository.get_by_id.return_value = None
        
        # Vérifier que l'exception est levée
        with self.assertRaises(EntityNotFoundException):
            self.service.update_device(999, {"name": "Updated"})
        
        # Vérifier que la méthode du repository a été appelée
        self.repository.get_by_id.assert_called_once_with(999)
        self.repository.update.assert_not_called()

    def test_delete_device_success(self):
        """
        Test de suppression d'un appareil avec succès.
        """
        # Configurer le mock pour get_by_id
        self.repository.get_by_id.return_value = self.test_device
        
        # Configurer le mock pour delete
        self.repository.delete.return_value = True
        
        # Appeler la méthode à tester
        result = self.service.delete_device(1)
        
        # Vérifier les résultats
        self.repository.get_by_id.assert_called_once_with(1)
        self.repository.delete.assert_called_once_with(1)
        self.assertTrue(result)

    def test_delete_device_not_found(self):
        """
        Test de suppression d'un appareil qui n'existe pas.
        """
        # Configurer le mock
        self.repository.get_by_id.return_value = None
        
        # Vérifier que l'exception est levée
        with self.assertRaises(EntityNotFoundException):
            self.service.delete_device(999)
        
        # Vérifier que la méthode du repository a été appelée
        self.repository.get_by_id.assert_called_once_with(999)
        self.repository.delete.assert_not_called()

    def test_search_devices(self):
        """
        Test de recherche d'appareils.
        """
        # Configurer le mock
        self.repository.search.return_value = [self.test_device]
        
        # Appeler la méthode à tester
        result = self.service.search_devices("Router")
        
        # Vérifier les résultats
        self.repository.search.assert_called_once_with("Router")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "Test Router")


if __name__ == '__main__':
    unittest.main() 