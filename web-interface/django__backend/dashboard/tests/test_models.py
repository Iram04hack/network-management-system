"""
Tests pour les modèles du module dashboard.

Tests pour les modèles UserDashboard, DashboardWidget et DashboardUsageStats.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
from django.utils import timezone

from dashboard.models import UserDashboardConfig, DashboardWidget, DashboardViewLog

pytestmark = pytest.mark.django_db


class TestUserDashboardConfig(TestCase):
    """Tests pour le modèle UserDashboardConfig."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.valid_layout = {
            'widgets': [
                {
                    'type': 'device_summary',
                    'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4},
                    'id': 'devices'
                },
                {
                    'type': 'alert_list',
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4},
                    'id': 'alerts'
                }
            ]
        }
    
    def test_create_dashboard_config_valid(self):
        """Test de création d'une configuration dashboard valide."""
        config = UserDashboardConfig.objects.create(
            user=self.user,
            theme='dark',
            layout='grid',
            refresh_interval=30
        )

        assert config.id is not None
        assert config.user == self.user
        assert config.theme == 'dark'
        assert config.layout == 'grid'
        assert config.refresh_interval == 30
        assert config.created_at is not None
        assert config.updated_at is not None
    
    def test_dashboard_config_validation_invalid_theme(self):
        """Test de validation avec thème invalide."""
        with pytest.raises(ValidationError):
            config = UserDashboardConfig(
                user=self.user,
                theme='invalid_theme_that_is_too_long_for_the_field',
                layout='grid',
                refresh_interval=30
            )
            config.full_clean()
    
    def test_dashboard_widget_creation(self):
        """Test de création d'un widget de dashboard."""
        config = UserDashboardConfig.objects.create(
            user=self.user,
            theme='light',
            layout='grid',
            refresh_interval=60
        )

        widget = DashboardWidget.objects.create(
            config=config,
            widget_type='system_health',
            position_x=0,
            position_y=0,
            width=6,
            height=4
        )

        assert widget.id is not None
        assert widget.config == config
        assert widget.widget_type == 'system_health'
        assert widget.position_x == 0
        assert widget.position_y == 0
    
    def test_refresh_interval_validation(self):
        """Test de validation de l'intervalle de rafraîchissement."""
        # Test avec un intervalle valide
        config = UserDashboardConfig(
            user=self.user,
            theme='light',
            layout='grid',
            refresh_interval=60
        )

        # Cela ne devrait pas lever d'exception
        config.full_clean()

        # Test avec un intervalle négatif (invalide)
        config.refresh_interval = -1

        with pytest.raises(ValidationError):
            config.full_clean()
    
    def test_unique_user_dashboard_config(self):
        """Test de contrainte unique pour la configuration utilisateur."""
        # Créer une première configuration
        config1 = UserDashboardConfig.objects.create(
            user=self.user,
            theme='light',
            layout='grid',
            refresh_interval=60
        )

        # Tenter de créer une seconde configuration pour le même utilisateur
        # Cela devrait échouer car OneToOneField
        with pytest.raises(Exception):  # IntegrityError ou ValidationError
            UserDashboardConfig.objects.create(
                user=self.user,
                theme='dark',
                layout='list',
                refresh_interval=30
            )
    
    def test_duplicate_dashboard(self):
        """Test de duplication de dashboard."""
        original = UserDashboard.objects.create(
            user=self.user,
            name='Dashboard Original',
            description='Description originale',
            layout_config=self.valid_layout,
            filters_config={'filter1': 'value1'}
        )
        
        # Créer un autre utilisateur
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Dupliquer pour l'autre utilisateur
        duplicate = original.duplicate_for_user(user2, 'Dashboard Dupliqué')
        
        assert duplicate.user == user2
        assert duplicate.name == 'Dashboard Dupliqué'
        assert duplicate.description == original.description
        assert duplicate.layout_config == original.layout_config
        assert duplicate.filters_config == original.filters_config
        assert duplicate.is_default is True  # Premier dashboard du nouvel utilisateur
    
    def test_get_widget_methods(self):
        """Test des méthodes de récupération des widgets."""
        dashboard = UserDashboard.objects.create(
            user=self.user,
            name='Dashboard Test',
            layout_config=self.valid_layout
        )
        
        assert dashboard.get_widget_count() == 2
        widget_types = dashboard.get_widget_types()
        assert len(widget_types) == 2
        assert 'device_summary' in widget_types
        assert 'alert_list' in widget_types


class TestDashboardWidget(TestCase):
    """Tests pour le modèle DashboardWidget."""
    
    def test_create_widget(self):
        """Test de création d'un widget."""
        widget = DashboardWidget.objects.create(
            name='Résumé Équipements',
            widget_type='device_summary',
            description='Widget affichant le résumé des équipements',
            default_config={'show_charts': True, 'limit': 10}
        )
        
        assert widget.id is not None
        assert widget.name == 'Résumé Équipements'
        assert widget.widget_type == 'device_summary'
        assert widget.is_active is True
        assert widget.default_config['show_charts'] is True
    
    def test_widget_str_representation(self):
        """Test de la représentation string du widget."""
        widget = DashboardWidget.objects.create(
            name='Test Widget',
            widget_type='alert_list'
        )
        
        expected_str = f"Liste des alertes - Test Widget"
        assert str(widget) == expected_str


class TestDashboardUsageStats(TestCase):
    """Tests pour le modèle DashboardUsageStats."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dashboard = UserDashboard.objects.create(
            user=self.user,
            name='Dashboard Test',
            layout_config={'widgets': []}
        )
    
    def test_create_usage_stats(self):
        """Test de création de statistiques d'utilisation."""
        today = date.today()
        
        stats = DashboardUsageStats.objects.create(
            dashboard=self.dashboard,
            access_date=today,
            view_count=5,
            avg_load_time=250.5,
            total_websocket_connections=3
        )
        
        assert stats.id is not None
        assert stats.dashboard == self.dashboard
        assert stats.access_date == today
        assert stats.view_count == 5
        assert stats.avg_load_time == 250.5
        assert stats.total_websocket_connections == 3
    
    def test_unique_dashboard_date_constraint(self):
        """Test de contrainte unique dashboard/date."""
        today = date.today()
        
        # Créer la première statistique
        DashboardUsageStats.objects.create(
            dashboard=self.dashboard,
            access_date=today,
            view_count=1
        )
        
        # Essayer de créer une seconde statistique pour le même jour
        with pytest.raises(Exception):  # Violation de contrainte unique
            DashboardUsageStats.objects.create(
                dashboard=self.dashboard,
                access_date=today,
                view_count=2
            )
    
    def test_stats_str_representation(self):
        """Test de la représentation string des statistiques."""
        today = date.today()
        
        stats = DashboardUsageStats.objects.create(
            dashboard=self.dashboard,
            access_date=today,
            view_count=10
        )
        
        expected_str = f"Dashboard Test - {today} (10 vues)"
        assert str(stats) == expected_str
    
    def test_get_or_create_stats(self):
        """Test de récupération ou création de statistiques."""
        today = date.today()
        
        # Première récupération (création)
        stats, created = DashboardUsageStats.objects.get_or_create(
            dashboard=self.dashboard,
            access_date=today,
            defaults={'view_count': 1}
        )
        
        assert created is True
        assert stats.view_count == 1
        
        # Seconde récupération (existant)
        stats2, created2 = DashboardUsageStats.objects.get_or_create(
            dashboard=self.dashboard,
            access_date=today,
            defaults={'view_count': 5}  # Ne sera pas utilisé
        )
        
        assert created2 is False
        assert stats2.id == stats.id
        assert stats2.view_count == 1  # Valeur originale conservée


class TestModelIntegration(TestCase):
    """Tests d'intégration entre les modèles."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cascade_delete_dashboard(self):
        """Test de suppression en cascade lors de la suppression d'un dashboard."""
        dashboard = UserDashboard.objects.create(
            user=self.user,
            name='Dashboard Test',
            layout_config={'widgets': []}
        )
        
        # Créer des statistiques
        stats = DashboardUsageStats.objects.create(
            dashboard=dashboard,
            access_date=date.today(),
            view_count=5
        )
        
        # Supprimer le dashboard
        dashboard_id = dashboard.id
        stats_id = stats.id
        dashboard.delete()
        
        # Vérifier que les statistiques sont supprimées aussi
        assert not UserDashboard.objects.filter(id=dashboard_id).exists()
        assert not DashboardUsageStats.objects.filter(id=stats_id).exists()
    
    def test_cascade_delete_user(self):
        """Test de suppression en cascade lors de la suppression d'un utilisateur."""
        dashboard = UserDashboard.objects.create(
            user=self.user,
            name='Dashboard Test',
            layout_config={'widgets': []}
        )
        
        stats = DashboardUsageStats.objects.create(
            dashboard=dashboard,
            access_date=date.today(),
            view_count=5
        )
        
        # Supprimer l'utilisateur
        user_id = self.user.id
        dashboard_id = dashboard.id
        stats_id = stats.id
        self.user.delete()
        
        # Vérifier que tout est supprimé
        assert not User.objects.filter(id=user_id).exists()
        assert not UserDashboard.objects.filter(id=dashboard_id).exists()
        assert not DashboardUsageStats.objects.filter(id=stats_id).exists()