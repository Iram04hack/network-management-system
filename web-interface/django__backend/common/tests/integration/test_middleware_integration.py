"""
Tests d'intégration pour les middlewares du module Common.

Ces tests valident le bon fonctionnement des middlewares dans un
environnement Django complet, notamment:
- L'ajout des en-têtes de sécurité
- La conversion des exceptions en réponses JSON
- L'enregistrement des actions utilisateur
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views import View
from django.test.utils import override_settings

from common.domain.exceptions import (
    NotFoundException, ValidationException, PermissionException, NMSException
)
from common.infrastructure.middleware import (
    SecurityHeadersMiddleware, ExceptionHandlerMiddleware, AuditMiddleware
)
from common.infrastructure.models import AuditLogEntry


# Vues de test pour les middlewares
class TestExceptionView(View):
    """Vue qui lève différents types d'exceptions pour tester le middleware."""
    
    def get(self, request, exception_type):
        """Lève différents types d'exceptions selon le paramètre."""
        if exception_type == 'not_found':
            raise NotFoundException(message="Ressource introuvable", details={"resource_id": "123"})
        elif exception_type == 'validation':
            raise ValidationException(message="Données invalides", details={"field": "username"})
        elif exception_type == 'permission':
            raise PermissionException(message="Accès refusé")
        elif exception_type == 'generic':
            raise NMSException(message="Erreur générique")
        elif exception_type == 'standard':
            raise ValueError("Erreur Python standard")
        return HttpResponse("Cette réponse ne devrait jamais être retournée")


class TestAuditView(View):
    """Vue pour tester le middleware d'audit."""
    
    def post(self, request):
        """Méthode POST pour déclencher l'audit."""
        return JsonResponse({"success": True})
    
    def put(self, request):
        """Méthode PUT pour déclencher l'audit."""
        return JsonResponse({"success": True})
    
    def delete(self, request):
        """Méthode DELETE pour déclencher l'audit."""
        return JsonResponse({"success": True})
    
    def get(self, request):
        """Méthode GET qui ne devrait pas déclencher d'audit."""
        return JsonResponse({"success": True})


# URLs de test
urlpatterns = [
    path('exceptions/<str:exception_type>/', TestExceptionView.as_view(), name='test_exceptions'),
    path('audit/', TestAuditView.as_view(), name='test_audit'),
]


@override_settings(ROOT_URLCONF=__name__)
class TestSecurityHeadersMiddleware(TestCase):
    """
    Tests pour le SecurityHeadersMiddleware.
    
    Vérifie que les en-têtes de sécurité sont correctement ajoutés
    aux réponses HTTP.
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_security_headers_added(self):
        """Vérifie que les en-têtes de sécurité standard sont ajoutés."""
        response = self.client.get('/audit/')
        
        # Vérifie les en-têtes de base
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
    
    @override_settings(DEBUG=False)
    def test_production_security_headers(self):
        """Vérifie que les en-têtes supplémentaires sont ajoutés en production."""
        response = self.client.get('/audit/')
        
        # Vérifie les en-têtes de base
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        
        # Vérifie les en-têtes de production
        self.assertIn('Strict-Transport-Security', response)
        self.assertIn('Content-Security-Policy', response)


@override_settings(ROOT_URLCONF=__name__)
class TestExceptionHandlerMiddleware(TestCase):
    """
    Tests pour le ExceptionHandlerMiddleware.
    
    Vérifie que les exceptions sont correctement converties en réponses
    JSON avec les codes HTTP appropriés.
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_not_found_exception(self):
        """Vérifie que NotFoundException est convertie en réponse 404."""
        response = self.client.get('/exceptions/not_found/')
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['error'])
        self.assertEqual(data['code'], 'not_found')
        self.assertEqual(data['message'], 'Ressource introuvable')
        self.assertEqual(data['type'], 'NotFoundException')
        self.assertIn('resource_id', data['details'])
    
    def test_validation_exception(self):
        """Vérifie que ValidationException est convertie en réponse 400."""
        response = self.client.get('/exceptions/validation/')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['error'])
        self.assertEqual(data['code'], 'validation_error')
        self.assertEqual(data['message'], 'Données invalides')
        self.assertIn('details', data)
    
    def test_permission_exception(self):
        """Vérifie que PermissionException est convertie en réponse 403."""
        response = self.client.get('/exceptions/permission/')
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['error'])
        self.assertEqual(data['code'], 'permission_denied')
        self.assertEqual(data['message'], 'Accès refusé')
    
    def test_generic_nms_exception(self):
        """Vérifie que NMSException est convertie en réponse 500."""
        response = self.client.get('/exceptions/generic/')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['error'])
        self.assertEqual(data['code'], 'error')
        self.assertEqual(data['message'], 'Erreur générique')
    
    def test_standard_python_exception(self):
        """Vérifie que les exceptions Python standards sont gérées."""
        response = self.client.get('/exceptions/standard/')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['error'])
        self.assertEqual(data['code'], 'server_error')
        self.assertEqual(data['message'], "Une erreur inattendue s'est produite.")


@override_settings(ROOT_URLCONF=__name__)
class TestAuditMiddleware(TestCase):
    """
    Tests pour le AuditMiddleware.
    
    Vérifie que les actions importantes des utilisateurs sont correctement
    journalisées dans la base de données.
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='password123'
        )
        self.client.force_login(self.user)
        
        # S'assurer qu'il n'y a pas d'entrées d'audit au début
        AuditLogEntry.objects.all().delete()
    
    def test_post_request_is_audited(self):
        """Vérifie que les requêtes POST sont auditées."""
        self.client.post('/audit/', {"test": "data"})
        
        # Vérifie qu'une entrée d'audit a été créée
        self.assertEqual(AuditLogEntry.objects.count(), 1)
        
        audit_entry = AuditLogEntry.objects.first()
        self.assertEqual(audit_entry.action, 'create')
        self.assertEqual(audit_entry.user, self.user)
        self.assertEqual(audit_entry.object_type, 'TestAuditView')
        self.assertIn('method', audit_entry.details)
        self.assertEqual(audit_entry.details['method'], 'POST')
    
    def test_put_request_is_audited(self):
        """Vérifie que les requêtes PUT sont auditées."""
        self.client.put('/audit/', data={"test": "data"}, content_type='application/json')
        
        # Vérifie qu'une entrée d'audit a été créée
        self.assertEqual(AuditLogEntry.objects.count(), 1)
        
        audit_entry = AuditLogEntry.objects.first()
        self.assertEqual(audit_entry.action, 'update')
        self.assertEqual(audit_entry.user, self.user)
    
    def test_delete_request_is_audited(self):
        """Vérifie que les requêtes DELETE sont auditées."""
        self.client.delete('/audit/')
        
        # Vérifie qu'une entrée d'audit a été créée
        self.assertEqual(AuditLogEntry.objects.count(), 1)
        
        audit_entry = AuditLogEntry.objects.first()
        self.assertEqual(audit_entry.action, 'delete')
        self.assertEqual(audit_entry.user, self.user)
    
    def test_get_request_not_audited(self):
        """Vérifie que les requêtes GET ne sont pas auditées."""
        self.client.get('/audit/')
        
        # Vérifie qu'aucune entrée d'audit n'a été créée
        self.assertEqual(AuditLogEntry.objects.count(), 0)
    
    def test_anonymous_request_not_audited(self):
        """Vérifie que les requêtes anonymes ne sont pas auditées."""
        # Se déconnecter
        self.client.logout()
        
        # Faire une requête POST anonyme
        self.client.post('/audit/', {"test": "data"})
        
        # Vérifie qu'aucune entrée d'audit n'a été créée
        self.assertEqual(AuditLogEntry.objects.count(), 0)


class TestMiddlewareChain(TestCase):
    """
    Tests pour la chaîne complète de middlewares.
    
    Vérifie que les middlewares fonctionnent correctement ensemble
    dans une chaîne de traitement.
    """
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='password123'
        )
    
    def test_full_middleware_chain(self):
        """
        Teste la chaîne complète de middlewares.
        
        Simule une requête qui traverse tous les middlewares:
        1. Le middleware d'audit enregistre l'action
        2. Une exception est levée et capturée par le middleware d'exceptions
        3. Le middleware de sécurité ajoute des en-têtes à la réponse
        """
        # Créer une chaîne de middlewares manuellement
        def get_response(request):
            raise NotFoundException(message="Test d'intégration")
        
        # Ordre: sécurité -> audit -> exceptions
        exception_middleware = ExceptionHandlerMiddleware(get_response)
        audit_middleware = AuditMiddleware(exception_middleware)
        security_middleware = SecurityHeadersMiddleware(audit_middleware)
        
        # Créer une requête POST authentifiée
        request = self.factory.post('/test-integration/')
        request.user = self.user
        
        # Simuler l'attribut .data de DRF pour le middleware d'audit
        request.data = {"test": "integration"}
        
        # Exécuter la chaîne de middlewares
        response = security_middleware(request)
        
        # Vérifier que l'exception a été correctement gérée
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Vérifier que les en-têtes de sécurité sont présents
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        
        # Vérifier que l'action a été auditée
        self.assertEqual(AuditLogEntry.objects.count(), 1)
        
        audit_entry = AuditLogEntry.objects.first()
        self.assertEqual(audit_entry.user, self.user)
        self.assertEqual(audit_entry.action, 'create')  # POST -> create 