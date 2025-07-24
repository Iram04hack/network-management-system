"""
Tests unitaires pour la hiérarchie d'exceptions du module Common.

Ces tests valident le bon fonctionnement de la hiérarchie d'exceptions
définie dans le module domain/exceptions.py, notamment:
- L'initialisation avec valeurs par défaut
- L'initialisation avec valeurs personnalisées
- L'héritage correct entre les différentes classes d'exceptions
- La représentation sous forme de chaîne des exceptions
"""
import unittest

from common.domain.exceptions import (
    NMSException, ServiceException, ValidationException, PermissionException,
    ResourceException, NetworkException, SecurityException, MonitoringException,
    QoSException, NotFoundException, ServiceUnavailableException, InvalidInputException,
    MissingRequiredFieldException, DeviceConnectionException
)


class TestExceptionHierarchy(unittest.TestCase):
    """
    Tests unitaires pour la hiérarchie d'exceptions.
    
    Vérifie que les relations d'héritage entre les classes d'exceptions
    sont correctement définies et que l'instance de chaque exception est
    également une instance de ses classes parentes.
    """
    
    def test_inheritance_relationships(self):
        """Teste les relations d'héritage entre les classes d'exceptions."""
        # Exceptions de base
        self.assertTrue(issubclass(ServiceException, NMSException))
        self.assertTrue(issubclass(ValidationException, NMSException))
        self.assertTrue(issubclass(PermissionException, NMSException))
        self.assertTrue(issubclass(ResourceException, NMSException))
        self.assertTrue(issubclass(NetworkException, NMSException))
        self.assertTrue(issubclass(SecurityException, NMSException))
        self.assertTrue(issubclass(MonitoringException, NMSException))
        self.assertTrue(issubclass(QoSException, NMSException))
        
        # Exceptions spécifiques
        self.assertTrue(issubclass(NotFoundException, ResourceException))
        self.assertTrue(issubclass(ServiceUnavailableException, ServiceException))
        self.assertTrue(issubclass(InvalidInputException, ValidationException))
        self.assertTrue(issubclass(DeviceConnectionException, NetworkException))
    
    def test_instance_inheritance(self):
        """Teste que les instances d'exceptions spécifiques sont aussi des instances des classes parentes."""
        # Exceptions de base
        self.assertIsInstance(ServiceException(), NMSException)
        self.assertIsInstance(ValidationException(), NMSException)
        
        # Exceptions spécifiques
        not_found = NotFoundException()
        self.assertIsInstance(not_found, ResourceException)
        self.assertIsInstance(not_found, NMSException)
        
        invalid_input = InvalidInputException()
        self.assertIsInstance(invalid_input, ValidationException)
        self.assertIsInstance(invalid_input, NMSException)
        
        device_connection = DeviceConnectionException()
        self.assertIsInstance(device_connection, NetworkException)
        self.assertIsInstance(device_connection, NMSException)


class TestNMSExceptionBase(unittest.TestCase):
    """
    Tests unitaires pour la classe de base NMSException.
    
    Vérifie que l'initialisation, les valeurs par défaut et les
    représentations sous forme de chaîne fonctionnent correctement.
    """
    
    def test_default_values(self):
        """Teste les valeurs par défaut."""
        exc = NMSException()
        self.assertEqual(exc.message, "Une erreur inattendue s'est produite.")
        self.assertEqual(exc.code, "error")
        self.assertEqual(exc.details, {})
    
    def test_custom_values(self):
        """Teste l'initialisation avec des valeurs personnalisées."""
        message = "Message personnalisé"
        code = "custom_code"
        details = {"key": "value"}
        
        exc = NMSException(message=message, code=code, details=details)
        self.assertEqual(exc.message, message)
        self.assertEqual(exc.code, code)
        self.assertEqual(exc.details, details)
    
    def test_str_representation(self):
        """Teste la représentation sous forme de chaîne."""
        # Sans détails
        exc = NMSException(message="Test", code="test_code")
        self.assertEqual(str(exc), "Test [Code: test_code]")
        
        # Avec détails
        exc = NMSException(message="Test", code="test_code", details={"key": "value"})
        self.assertEqual(str(exc), "Test [Code: test_code, Details: {'key': 'value'}]")


class TestServiceExceptions(unittest.TestCase):
    """
    Tests pour les exceptions liées aux services externes.
    
    Vérifie que les exceptions spécifiques aux services ont les bonnes
    valeurs par défaut et peuvent être personnalisées.
    """
    
    def test_service_exception_defaults(self):
        """Teste les valeurs par défaut de ServiceException."""
        exc = ServiceException()
        self.assertEqual(exc.message, "Erreur lors de l'interaction avec un service.")
        self.assertEqual(exc.code, "service_error")
    
    def test_service_unavailable_defaults(self):
        """Teste les valeurs par défaut de ServiceUnavailableException."""
        exc = ServiceUnavailableException()
        self.assertEqual(exc.message, "Le service est actuellement indisponible.")
        self.assertEqual(exc.code, "service_unavailable")
    
    def test_custom_service_exception(self):
        """Teste la personnalisation des exceptions de service."""
        message = "Service XYZ indisponible"
        code = "xyz_unavailable"
        details = {"service": "xyz", "retry_after": 30}
        
        exc = ServiceUnavailableException(message=message, code=code, details=details)
        self.assertEqual(exc.message, message)
        self.assertEqual(exc.code, code)
        self.assertEqual(exc.details, details)


class TestValidationExceptions(unittest.TestCase):
    """
    Tests pour les exceptions liées à la validation.
    
    Vérifie que les exceptions de validation ont les bonnes valeurs par défaut
    et peuvent stocker des informations spécifiques à la validation.
    """
    
    def test_validation_exception_defaults(self):
        """Teste les valeurs par défaut de ValidationException."""
        exc = ValidationException()
        self.assertEqual(exc.message, "Erreur de validation.")
        self.assertEqual(exc.code, "validation_error")
    
    def test_invalid_input_exception(self):
        """Teste les valeurs par défaut de InvalidInputException."""
        exc = InvalidInputException()
        self.assertEqual(exc.message, "Les données d'entrée sont invalides.")
        self.assertEqual(exc.code, "invalid_input")
    
    def test_missing_required_field(self):
        """Teste les valeurs par défaut de MissingRequiredFieldException."""
        exc = MissingRequiredFieldException()
        self.assertEqual(exc.message, "Un champ requis est manquant.")
        self.assertEqual(exc.code, "missing_required_field")
    
    def test_validation_with_field_details(self):
        """Teste la personnalisation avec des détails de champ."""
        details = {
            "fields": {
                "username": ["Ce champ est requis."],
                "email": ["Format d'email invalide."]
            }
        }
        
        exc = ValidationException(
            message="Erreurs de validation du formulaire",
            details=details
        )
        self.assertEqual(exc.message, "Erreurs de validation du formulaire")
        self.assertEqual(exc.details, details)


class TestResourceExceptions(unittest.TestCase):
    """
    Tests pour les exceptions liées aux ressources.
    
    Vérifie que les exceptions de ressources fonctionnent correctement,
    en particulier NotFoundException qui est fréquemment utilisée.
    """
    
    def test_not_found_exception_defaults(self):
        """Teste les valeurs par défaut de NotFoundException."""
        exc = NotFoundException()
        self.assertEqual(exc.message, "La ressource demandée n'a pas été trouvée.")
        self.assertEqual(exc.code, "not_found")
    
    def test_not_found_with_resource_id(self):
        """Teste NotFoundException avec un ID de ressource."""
        resource_id = "123"
        resource_type = "User"
        
        exc = NotFoundException(
            message=f"{resource_type} #{resource_id} non trouvé",
            details={"resource_id": resource_id, "resource_type": resource_type}
        )
        
        self.assertEqual(exc.message, "User #123 non trouvé")
        self.assertEqual(exc.details["resource_id"], "123")
        self.assertEqual(exc.details["resource_type"], "User")


if __name__ == '__main__':
    unittest.main() 