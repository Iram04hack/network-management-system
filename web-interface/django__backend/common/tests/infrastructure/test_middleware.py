"""
Tests unitaires pour le middleware de gestion des exceptions.
"""
from django.test import TestCase, RequestFactory
import json
from django.http import JsonResponse
from ...domain.exceptions import (
    ValidationException, NotFoundException, UnauthorizedException,
    PermissionException, ServiceUnavailableException, ConflictException,
    RateLimitedException, TimeoutException
)
from ...infrastructure.middleware import ExceptionHandlerMiddleware


class ExceptionHandlerMiddlewareTestCase(TestCase):
    """Tests pour le middleware de gestion des exceptions."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.factory = RequestFactory()
        self.middleware = ExceptionHandlerMiddleware(get_response=lambda req: None)
        self.request = self.factory.get('/api/test')
        
    def test_validation_exception(self):
        """Test de gestion d'une exception de validation."""
        # Créer l'exception
        exception = ValidationException(
            message="Données invalides", 
            details={"field": "username", "error": "Requis"}
        )
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 400)
        
        # Vérifier le contenu de la réponse
        content = json.loads(response.content)
        self.assertTrue(content['error'])
        self.assertEqual(content['code'], "validation_error")
        self.assertEqual(content['message'], "Données invalides")
        self.assertEqual(content['details'], {"field": "username", "error": "Requis"})
        
    def test_not_found_exception(self):
        """Test de gestion d'une exception de ressource non trouvée."""
        # Créer l'exception
        exception = NotFoundException(message="Ressource introuvable")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 404)
        
        # Vérifier le contenu de la réponse
        content = json.loads(response.content)
        self.assertEqual(content['message'], "Ressource introuvable")
        
    def test_unauthorized_exception(self):
        """Test de gestion d'une exception d'accès non autorisé."""
        # Créer l'exception
        exception = UnauthorizedException(message="Authentification requise")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 401)
        
    def test_permission_exception(self):
        """Test de gestion d'une exception de permission."""
        # Créer l'exception
        exception = PermissionException(message="Accès refusé")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 403)
        
    def test_service_unavailable_exception(self):
        """Test de gestion d'une exception de service indisponible."""
        # Créer l'exception
        exception = ServiceUnavailableException(message="Service temporairement indisponible")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 503)
        
    def test_conflict_exception(self):
        """Test de gestion d'une exception de conflit."""
        # Créer l'exception
        exception = ConflictException(message="Conflit de ressources")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 409)
        
    def test_rate_limited_exception(self):
        """Test de gestion d'une exception de limite de taux."""
        # Créer l'exception
        exception = RateLimitedException(message="Trop de requêtes")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 429)
        
    def test_timeout_exception(self):
        """Test de gestion d'une exception de délai d'attente."""
        # Créer l'exception
        exception = TimeoutException(message="Opération expirée")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 504)
        
    def test_generic_exception(self):
        """Test de gestion d'une exception générique non NMS."""
        # Créer une exception standard
        exception = ValueError("Erreur inattendue")
        
        # Exécuter le middleware
        response = self.middleware.process_exception(self.request, exception)
        
        # Vérifications
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 500)
        
        # Vérifier que les détails de l'erreur ne sont pas exposés
        content = json.loads(response.content)
        self.assertTrue(content['error'])
        self.assertEqual(content['code'], "server_error")
        self.assertEqual(content['message'], "Une erreur interne est survenue.")
        self.assertNotIn('details', content) 