"""
Tests pour le service de cache du module dashboard.

Tests pour DashboardCacheService, CacheWarmer et les décorateurs de cache.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core.cache import cache
from django.contrib.auth.models import User
from datetime import datetime

from dashboard.infrastructure.cache_service import (
    DashboardCacheService,
    CacheWarmer,
    cache_dashboard_data
)

pytestmark = pytest.mark.django_db


class TestDashboardCacheService(TestCase):
    """Tests pour le service de cache de dashboard."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.cache_service = DashboardCacheService()
        self.user_id = 123
        self.test_data = {
            'devices': {'total': 10, 'active': 8},
            'alerts': [],
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        # Nettoyer le cache avant chaque test
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        cache.clear()
    
    def test_set_and_get_dashboard_overview(self):
        """Test de mise en cache et récupération des données dashboard."""
        # Mise en cache
        success = self.cache_service.set_dashboard_overview(
            self.user_id, 
            self.test_data
        )
        assert success is True
        
        # Récupération depuis le cache
        cached_data = self.cache_service.get_dashboard_overview(self.user_id)
        
        assert cached_data is not None
        assert cached_data['data'] == self.test_data
        assert cached_data['user_id'] == self.user_id
        assert 'cached_at' in cached_data
    
    def test_get_dashboard_overview_cache_miss(self):
        """Test de cache miss pour les données dashboard."""
        # Tentative de récupération sans mise en cache préalable
        cached_data = self.cache_service.get_dashboard_overview(999)
        
        assert cached_data is None
        assert self.cache_service.cache_stats['misses'] == 1
        assert self.cache_service.cache_stats['hits'] == 0
    
    def test_set_and_get_widget_data(self):
        """Test de mise en cache et récupération des données de widget."""
        widget_type = 'device_summary'
        widget_config = {'limit': 10}
        widget_data = {'devices': [{'id': 1, 'name': 'Router1'}]}
        
        # Mise en cache
        success = self.cache_service.set_widget_data(
            widget_type,
            self.user_id,
            widget_data,
            widget_config
        )
        assert success is True
        
        # Récupération
        cached_data = self.cache_service.get_widget_data(
            widget_type,
            self.user_id,
            widget_config
        )
        
        assert cached_data is not None
        assert cached_data['data'] == widget_data
        assert cached_data['widget_type'] == widget_type
        assert cached_data['user_id'] == self.user_id
    
    def test_widget_data_different_configs(self):
        """Test que différentes configurations de widget créent des clés différentes."""
        widget_type = 'alert_list'
        config1 = {'limit': 5}
        config2 = {'limit': 10}
        data1 = {'alerts': ['alert1']}
        data2 = {'alerts': ['alert1', 'alert2']}
        
        # Mettre en cache avec les deux configurations
        self.cache_service.set_widget_data(widget_type, self.user_id, data1, config1)
        self.cache_service.set_widget_data(widget_type, self.user_id, data2, config2)
        
        # Récupérer les deux versions
        cached1 = self.cache_service.get_widget_data(widget_type, self.user_id, config1)
        cached2 = self.cache_service.get_widget_data(widget_type, self.user_id, config2)
        
        assert cached1['data'] == data1
        assert cached2['data'] == data2
    
    def test_invalidate_user_cache(self):
        """Test d'invalidation du cache utilisateur."""
        # Mettre en cache plusieurs éléments
        self.cache_service.set_dashboard_overview(self.user_id, self.test_data)
        self.cache_service.set_widget_data('device_summary', self.user_id, {'test': 'data'})
        
        # Vérifier que les données sont en cache
        assert self.cache_service.get_dashboard_overview(self.user_id) is not None
        assert self.cache_service.get_widget_data('device_summary', self.user_id) is not None
        
        # Invalider le cache utilisateur
        success = self.cache_service.invalidate_user_cache(self.user_id)
        assert success is True
        
        # Vérifier que le cache a été invalidé
        assert self.cache_service.get_dashboard_overview(self.user_id) is None
        assert self.cache_service.get_widget_data('device_summary', self.user_id) is None
    
    def test_cache_stats(self):
        """Test des statistiques de cache."""
        # État initial
        stats = self.cache_service.get_cache_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0
        
        # Générer des hits et misses
        self.cache_service.get_dashboard_overview(self.user_id)  # Miss
        self.cache_service.set_dashboard_overview(self.user_id, self.test_data)
        self.cache_service.get_dashboard_overview(self.user_id)  # Hit
        self.cache_service.get_dashboard_overview(self.user_id)  # Hit
        
        stats = self.cache_service.get_cache_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_operations'] == 3
        assert stats['hit_rate'] == 66.67  # 2/3 * 100
    
    def test_cache_key_generation(self):
        """Test de génération de clés de cache."""
        # Clés avec mêmes paramètres doivent être identiques
        key1 = self.cache_service._generate_cache_key('dashboard', 123, {'filter': 'value'})
        key2 = self.cache_service._generate_cache_key('dashboard', 123, {'filter': 'value'})
        assert key1 == key2
        
        # Clés avec paramètres différents doivent être différentes
        key3 = self.cache_service._generate_cache_key('dashboard', 123, {'filter': 'different'})
        assert key1 != key3
        
        # Clés avec utilisateurs différents doivent être différentes
        key4 = self.cache_service._generate_cache_key('dashboard', 456, {'filter': 'value'})
        assert key1 != key4
    
    def test_cache_with_filters(self):
        """Test de cache avec filtres."""
        filters1 = {'time_range': '24h', 'status': 'active'}
        filters2 = {'time_range': '1w', 'status': 'active'}
        
        # Mettre en cache avec différents filtres
        self.cache_service.set_dashboard_overview(self.user_id, self.test_data, filters1)
        
        # Récupérer avec les mêmes filtres
        cached_with_filters = self.cache_service.get_dashboard_overview(self.user_id, filters1)
        assert cached_with_filters is not None
        
        # Récupérer avec des filtres différents
        cached_different_filters = self.cache_service.get_dashboard_overview(self.user_id, filters2)
        assert cached_different_filters is None


class TestCacheDecorator(TestCase):
    """Tests pour le décorateur de cache."""
    
    def setUp(self):
        """Configuration des données de test."""
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        cache.clear()
    
    def test_cache_decorator_basic(self):
        """Test basique du décorateur de cache."""
        call_count = 0
        
        @cache_dashboard_data('test_cache', ttl=60)
        def test_function(self, user_id):
            nonlocal call_count
            call_count += 1
            return {'data': f'test_data_{call_count}', 'user_id': user_id}
        
        # Premier appel - doit exécuter la fonction
        result1 = test_function(None, user_id=123)
        assert call_count == 1
        assert result1['data'] == 'test_data_1'
        
        # Deuxième appel - doit utiliser le cache
        result2 = test_function(None, user_id=123)
        assert call_count == 1  # Pas d'exécution supplémentaire
        assert result2['data'] == 'test_data_1'  # Même résultat
    
    def test_cache_decorator_different_users(self):
        """Test du décorateur avec différents utilisateurs."""
        call_count = 0
        
        @cache_dashboard_data('test_cache')
        def test_function(self, user_id):
            nonlocal call_count
            call_count += 1
            return {'data': f'user_{user_id}_data_{call_count}'}
        
        # Appels avec différents utilisateurs
        result1 = test_function(None, user_id=123)
        result2 = test_function(None, user_id=456)
        
        assert call_count == 2  # Deux exécutions
        assert result1['data'] == 'user_123_data_1'
        assert result2['data'] == 'user_456_data_2'
        
        # Appels répétés - doivent utiliser le cache
        result3 = test_function(None, user_id=123)
        result4 = test_function(None, user_id=456)
        
        assert call_count == 2  # Pas d'exécutions supplémentaires
        assert result3 == result1
        assert result4 == result2
    
    def test_cache_decorator_no_user_id(self):
        """Test du décorateur sans user_id (pas de cache)."""
        call_count = 0
        
        @cache_dashboard_data('test_cache')
        def test_function():
            nonlocal call_count
            call_count += 1
            return {'data': f'no_cache_{call_count}'}
        
        # Tous les appels doivent exécuter la fonction
        result1 = test_function()
        result2 = test_function()
        
        assert call_count == 2
        assert result1['data'] == 'no_cache_1'
        assert result2['data'] == 'no_cache_2'


class TestCacheWarmer(TestCase):
    """Tests pour le service de préchauffage de cache."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.cache_warmer = CacheWarmer()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        cache.clear()
    
    @patch('django__backend.dashboard.infrastructure.cache_service.get_container')
    def test_warm_user_dashboard_cache(self, mock_get_container):
        """Test de préchauffage du cache utilisateur."""
        # Mock des use cases
        mock_dashboard_use_case = Mock()
        mock_network_use_case = Mock()
        mock_health_use_case = Mock()
        
        mock_dashboard_use_case.execute.return_value = {'dashboard': 'data'}
        mock_network_use_case.execute.return_value = {'network': 'data'}
        mock_health_use_case.execute.return_value = {'health': 'data'}
        
        mock_container = Mock()
        mock_container.resolve.side_effect = [
            mock_dashboard_use_case,
            mock_network_use_case,
            mock_health_use_case
        ]
        mock_get_container.return_value = mock_container
        
        # Préchauffer le cache
        success = self.cache_warmer.warm_user_dashboard_cache(self.user.id)
        
        assert success is True
        
        # Vérifier que les use cases ont été appelés
        assert mock_dashboard_use_case.execute.called
        assert mock_network_use_case.execute.called
        assert mock_health_use_case.execute.called
        
        # Vérifier que les données sont en cache
        cached_data = self.cache_warmer.cache_service.get_dashboard_overview(self.user.id)
        assert cached_data is not None
    
    @patch('django__backend.dashboard.infrastructure.cache_service.get_container')
    def test_warm_user_cache_error_handling(self, mock_get_container):
        """Test de gestion d'erreur lors du préchauffage."""
        # Mock qui lève une exception
        mock_get_container.side_effect = Exception("Container error")
        
        # Le préchauffage doit échouer gracieusement
        success = self.cache_warmer.warm_user_dashboard_cache(self.user.id)
        assert success is False
    
    @patch('django__backend.dashboard.infrastructure.cache_service.timezone')
    @patch('django__backend.dashboard.infrastructure.cache_service.User')
    def test_warm_all_active_users_cache(self, mock_user_model, mock_timezone):
        """Test de préchauffage pour tous les utilisateurs actifs."""
        # Mock des utilisateurs actifs
        mock_users = [
            Mock(id=1),
            Mock(id=2),
            Mock(id=3)
        ]
        mock_user_model.objects.filter.return_value = mock_users
        
        # Mock du temps
        mock_timezone.now.return_value = datetime.now()
        
        # Mock du préchauffage individuel
        with patch.object(self.cache_warmer, 'warm_user_dashboard_cache') as mock_warm:
            mock_warm.return_value = True
            
            # Préchauffer pour tous les utilisateurs
            warmed_count = self.cache_warmer.warm_all_active_users_cache()
            
            assert warmed_count == 3
            assert mock_warm.call_count == 3


class TestCacheIntegration(TestCase):
    """Tests d'intégration pour le système de cache."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.cache_service = DashboardCacheService()
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        cache.clear()
    
    def test_cache_invalidation_workflow(self):
        """Test du workflow d'invalidation de cache."""
        user_id = 123
        
        # Mettre plusieurs éléments en cache
        self.cache_service.set_dashboard_overview(user_id, {'test': 'data1'})
        self.cache_service.set_widget_data('device_summary', user_id, {'test': 'data2'})
        self.cache_service.set_widget_data('alert_list', user_id, {'test': 'data3'})
        
        # Vérifier que tout est en cache
        assert self.cache_service.get_dashboard_overview(user_id) is not None
        assert self.cache_service.get_widget_data('device_summary', user_id) is not None
        assert self.cache_service.get_widget_data('alert_list', user_id) is not None
        
        # Invalider le cache utilisateur
        self.cache_service.invalidate_user_cache(user_id)
        
        # Vérifier que tout est invalidé
        assert self.cache_service.get_dashboard_overview(user_id) is None
        assert self.cache_service.get_widget_data('device_summary', user_id) is None
        assert self.cache_service.get_widget_data('alert_list', user_id) is None
    
    def test_cache_performance_metrics(self):
        """Test des métriques de performance du cache."""
        user_id = 123
        
        # Générer une série d'opérations
        for i in range(5):
            self.cache_service.get_dashboard_overview(user_id)  # Miss
        
        self.cache_service.set_dashboard_overview(user_id, {'test': 'data'})
        
        for i in range(10):
            self.cache_service.get_dashboard_overview(user_id)  # Hit
        
        # Vérifier les statistiques
        stats = self.cache_service.get_cache_stats()
        assert stats['misses'] == 5
        assert stats['hits'] == 10
        assert stats['total_operations'] == 15
        assert stats['hit_rate'] == 66.67  # 10/15 * 100
    
    def test_multiple_users_cache_isolation(self):
        """Test d'isolation du cache entre utilisateurs."""
        user1_id = 123
        user2_id = 456
        
        data1 = {'user': 'user1_data'}
        data2 = {'user': 'user2_data'}
        
        # Mettre en cache pour les deux utilisateurs
        self.cache_service.set_dashboard_overview(user1_id, data1)
        self.cache_service.set_dashboard_overview(user2_id, data2)
        
        # Vérifier l'isolation
        cached1 = self.cache_service.get_dashboard_overview(user1_id)
        cached2 = self.cache_service.get_dashboard_overview(user2_id)
        
        assert cached1['data'] == data1
        assert cached2['data'] == data2
        
        # Invalider le cache d'un utilisateur
        self.cache_service.invalidate_user_cache(user1_id)
        
        # Vérifier que seul le cache de user1 est invalidé
        assert self.cache_service.get_dashboard_overview(user1_id) is None
        assert self.cache_service.get_dashboard_overview(user2_id) is not None