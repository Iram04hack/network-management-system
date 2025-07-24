"""
Tests simples pour les modèles Dashboard.

Ces tests vérifient le bon fonctionnement des modèles de données
du module dashboard avec la vraie structure.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date
from django.utils import timezone

from dashboard.models import (
    DashboardPreset, 
    UserDashboardConfig, 
    DashboardWidget, 
    CustomDashboard, 
    DashboardViewLog
)

User = get_user_model()
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
    
    def test_dashboard_config_str_representation(self):
        """Test de la représentation string de la configuration."""
        config = UserDashboardConfig.objects.create(
            user=self.user,
            theme='light',
            layout='grid',
            refresh_interval=60
        )
        
        expected = f"Configuration de {self.user.username}"
        assert str(config) == expected


class TestDashboardWidget(TestCase):
    """Tests pour le modèle DashboardWidget."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        self.config = UserDashboardConfig.objects.create(
            user=self.user,
            theme='light',
            layout='grid',
            refresh_interval=60
        )
    
    def test_create_widget_valid(self):
        """Test de création d'un widget valide."""
        widget = DashboardWidget.objects.create(
            config=self.config,
            widget_type='system_health',
            position_x=0,
            position_y=0,
            width=6,
            height=4
        )
        
        assert widget.id is not None
        assert widget.config == self.config
        assert widget.widget_type == 'system_health'
        assert widget.position_x == 0
        assert widget.position_y == 0
        assert widget.width == 6
        assert widget.height == 4


class TestCustomDashboard(TestCase):
    """Tests pour le modèle CustomDashboard."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
    
    def test_create_custom_dashboard(self):
        """Test de création d'un tableau de bord personnalisé."""
        dashboard = CustomDashboard.objects.create(
            user=self.user,
            name='Mon Dashboard Personnalisé',
            description='Description de test',
            config={'theme': 'dark'},
            layout='grid',
            widgets=[],
            is_public=False
        )
        
        assert dashboard.id is not None
        assert dashboard.user == self.user
        assert dashboard.name == 'Mon Dashboard Personnalisé'
        assert dashboard.description == 'Description de test'
        assert dashboard.config == {'theme': 'dark'}
        assert dashboard.layout == 'grid'
        assert dashboard.widgets == []
        assert dashboard.is_public is False


class TestDashboardViewLog(TestCase):
    """Tests pour le modèle DashboardViewLog."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
    
    def test_create_view_log(self):
        """Test de création d'un log de vue."""
        log = DashboardViewLog.objects.create(
            user=self.user,
            dashboard_type='main',
            view_duration=120
        )
        
        assert log.id is not None
        assert log.user == self.user
        assert log.dashboard_type == 'main'
        assert log.view_duration == 120
        assert log.viewed_at is not None


class TestDashboardPreset(TestCase):
    """Tests pour le modèle DashboardPreset."""
    
    def test_create_preset(self):
        """Test de création d'un préréglage."""
        preset = DashboardPreset.objects.create(
            name='Préréglage Test',
            description='Description du préréglage',
            theme='dark',
            layout='grid'
        )
        
        assert preset.id is not None
        assert preset.name == 'Préréglage Test'
        assert preset.description == 'Description du préréglage'
        assert preset.theme == 'dark'
        assert preset.layout == 'grid'
        assert preset.is_default is False
        assert preset.is_active is True
