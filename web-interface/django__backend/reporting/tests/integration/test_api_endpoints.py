"""
Tests d'intégration pour les endpoints API du module reporting.

Ces tests vérifient que les endpoints API fonctionnent correctement
et interagissent avec les couches sous-jacentes comme prévu.
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from reporting.models import Report, ReportTemplate, ScheduledReport


@pytest.mark.django_db
class TestReportAPIEndpoints(TestCase):
    """Tests pour les endpoints API des rapports."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer un client API
        self.client = Client()
        
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Authentifier le client
        self.client.force_login(self.user)
        
        # Créer un rapport dans la base de données
        self.report = Report.objects.create(
            title="Test Report",
            description="Test description",
            report_type="network",
            created_by=self.user,
            status="draft",
            content={"data": "test"}
        )
        
        # Créer un template de rapport
        self.template = ReportTemplate.objects.create(
            name="Test Template",
            description="Test description",
            template_type="network_status",
            created_by=self.user,
            content={"sections": []},
            is_active=True
        )
    
    def test_list_reports(self):
        """Teste la récupération de la liste des rapports."""
        # Appeler l'endpoint
        response = self.client.get(reverse('reporting:report-list'))
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Vérifier que notre rapport est dans la liste
        report_ids = [r['id'] for r in data]
        self.assertIn(self.report.id, report_ids)
    
    def test_get_report_detail(self):
        """Teste la récupération des détails d'un rapport."""
        # Appeler l'endpoint
        response = self.client.get(
            reverse('reporting:report-detail', args=[self.report.id])
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertEqual(data['id'], self.report.id)
        self.assertEqual(data['title'], "Test Report")
        self.assertEqual(data['report_type'], "network")
    
    def test_create_report(self):
        """Teste la création d'un rapport via l'API."""
        # Données pour le nouveau rapport
        new_report_data = {
            'title': "API Created Report",
            'description': "Created via API",
            'report_type': "security",
            'content': {"api_data": "test"}
        }
        
        # Appeler l'endpoint
        response = self.client.post(
            reverse('reporting:report-list'),
            data=json.dumps(new_report_data),
            content_type='application/json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['title'], "API Created Report")
        self.assertEqual(data['report_type'], "security")
        
        # Vérifier que le rapport a été créé dans la base de données
        self.assertTrue(
            Report.objects.filter(title="API Created Report").exists()
        )
    
    def test_update_report(self):
        """Teste la mise à jour d'un rapport via l'API."""
        # Données pour la mise à jour
        update_data = {
            'title': "Updated Report",
            'status': "processing"
        }
        
        # Appeler l'endpoint
        response = self.client.patch(
            reverse('reporting:report-detail', args=[self.report.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertEqual(data['title'], "Updated Report")
        self.assertEqual(data['status'], "processing")
        
        # Vérifier que les modifications sont dans la base de données
        updated_report = Report.objects.get(pk=self.report.id)
        self.assertEqual(updated_report.title, "Updated Report")
        self.assertEqual(updated_report.status, "processing")
    
    def test_delete_report(self):
        """Teste la suppression d'un rapport via l'API."""
        # Appeler l'endpoint
        response = self.client.delete(
            reverse('reporting:report-detail', args=[self.report.id])
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que le rapport a été supprimé de la base de données
        self.assertFalse(
            Report.objects.filter(pk=self.report.id).exists()
        )


@pytest.mark.django_db
class TestReportTemplateAPIEndpoints(TestCase):
    """Tests pour les endpoints API des templates de rapport."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer un client API
        self.client = Client()
        
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Authentifier le client
        self.client.force_login(self.user)
        
        # Créer un template de rapport
        self.template = ReportTemplate.objects.create(
            name="Test Template",
            description="Test description",
            template_type="network_status",
            created_by=self.user,
            content={"sections": []},
            is_active=True
        )
    
    def test_list_templates(self):
        """Teste la récupération de la liste des templates."""
        # Appeler l'endpoint
        response = self.client.get(reverse('reporting:template-list'))
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Vérifier que notre template est dans la liste
        template_ids = [t['id'] for t in data]
        self.assertIn(self.template.id, template_ids)
    
    def test_get_template_detail(self):
        """Teste la récupération des détails d'un template."""
        # Appeler l'endpoint
        response = self.client.get(
            reverse('reporting:template-detail', args=[self.template.id])
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertEqual(data['id'], self.template.id)
        self.assertEqual(data['name'], "Test Template")
        self.assertEqual(data['template_type'], "network_status")
    
    def test_create_template(self):
        """Teste la création d'un template via l'API."""
        # Données pour le nouveau template
        new_template_data = {
            'name': "API Created Template",
            'description': "Created via API",
            'template_type': "security_audit",
            'content': {"sections": [{"title": "API Section"}]},
            'is_active': True
        }
        
        # Appeler l'endpoint
        response = self.client.post(
            reverse('reporting:template-list'),
            data=json.dumps(new_template_data),
            content_type='application/json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['name'], "API Created Template")
        
        # Vérifier que le template a été créé dans la base de données
        self.assertTrue(
            ReportTemplate.objects.filter(name="API Created Template").exists()
        )


@pytest.mark.django_db
class TestScheduledReportAPIEndpoints(TestCase):
    """Tests pour les endpoints API des rapports planifiés."""
    
    def setUp(self):
        """Initialise les données de test."""
        # Créer un client API
        self.client = Client()
        
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Authentifier le client
        self.client.force_login(self.user)
        
        # Créer un rapport pour associer à la planification
        self.report = Report.objects.create(
            title="Test Report",
            description="Test description",
            report_type="network",
            created_by=self.user,
            status="completed"
        )
        
        # Créer un rapport planifié
        self.scheduled = ScheduledReport.objects.create(
            report=self.report,
            frequency="weekly",
            is_active=True
        )
        self.scheduled.recipients.add(self.user)
    
    def test_list_scheduled_reports(self):
        """Teste la récupération de la liste des rapports planifiés."""
        # Appeler l'endpoint
        response = self.client.get(reverse('reporting:scheduled-list'))
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Vérifier que notre planification est dans la liste
        schedule_ids = [s['id'] for s in data]
        self.assertIn(self.scheduled.id, schedule_ids)
    
    def test_get_scheduled_report_detail(self):
        """Teste la récupération des détails d'un rapport planifié."""
        # Appeler l'endpoint
        response = self.client.get(
            reverse('reporting:scheduled-detail', args=[self.scheduled.id])
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertEqual(data['id'], self.scheduled.id)
        self.assertEqual(data['report_id'], self.report.id)
        self.assertEqual(data['frequency'], "weekly")
        self.assertTrue(data['is_active'])
        
        # Vérifier les destinataires
        self.assertIn(self.user.id, data['recipients'])
    
    def test_create_scheduled_report(self):
        """Teste la création d'un rapport planifié via l'API."""
        # Créer un autre rapport pour la planification
        report2 = Report.objects.create(
            title="Second Report",
            description="Another report",
            report_type="security",
            created_by=self.user,
            status="completed"
        )
        
        # Données pour la nouvelle planification
        new_schedule_data = {
            'report_id': report2.id,
            'frequency': "monthly",
            'is_active': True,
            'recipients': [self.user.id],
            'format': "pdf"
        }
        
        # Appeler l'endpoint
        response = self.client.post(
            reverse('reporting:scheduled-list'),
            data=json.dumps(new_schedule_data),
            content_type='application/json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier le contenu de la réponse
        data = response.json()
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['report_id'], report2.id)
        self.assertEqual(data['frequency'], "monthly")
        
        # Vérifier que la planification a été créée dans la base de données
        self.assertTrue(
            ScheduledReport.objects.filter(report=report2).exists()
        ) 