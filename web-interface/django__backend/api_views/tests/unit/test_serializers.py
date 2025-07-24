"""
Tests unitaires pour les sérialiseurs du module API Views.

Ce module teste la validation et la transformation des données
par les sérialiseurs du module api_views.
"""

import pytest
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError as DRFValidationError

from api_views.presentation.serializers import (
    BaseAPISerializer,
    DashboardRequestSerializer,
    DashboardWidgetSerializer,
    CustomDashboardSerializer,
    DashboardConfigurationSerializer,
    PaginatedResponseSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer
)


class TestBaseAPISerializer:
    """Tests pour le sérialiseur de base."""

    def test_base_serializer_init(self):
        """Test l'initialisation du sérialiseur de base."""
        serializer = BaseAPISerializer()
        assert hasattr(serializer, 'request_context')
        assert serializer.request_context == {}

    def test_base_serializer_with_context(self):
        """Test l'initialisation avec un contexte personnalisé."""
        context = {'test': 'value'}
        serializer = BaseAPISerializer(request_context=context)
        assert serializer.request_context == context

    def test_validate_uuid_field_valid(self):
        """Test la validation d'un UUID valide."""
        serializer = BaseAPISerializer()
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        result = serializer.validate_uuid_field(valid_uuid, "test_field")
        assert str(result) == valid_uuid

    def test_validate_uuid_field_invalid(self):
        """Test la validation d'un UUID invalide."""
        serializer = BaseAPISerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_uuid_field("invalid-uuid", "test_field")
        assert "doit être un UUID valide" in str(exc_info.value)

    def test_validate_ip_address_valid(self):
        """Test la validation d'une adresse IP valide."""
        serializer = BaseAPISerializer()
        valid_ip = "192.168.1.1"
        result = serializer.validate_ip_address(valid_ip)
        assert result == valid_ip

    def test_validate_ip_address_invalid(self):
        """Test la validation d'une adresse IP invalide."""
        serializer = BaseAPISerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_ip_address("invalid.ip.address")
        assert "Adresse IP IPv4 invalide" in str(exc_info.value)

    def test_validate_port_number_valid(self):
        """Test la validation d'un port valide."""
        serializer = BaseAPISerializer()
        valid_port = 8080
        result = serializer.validate_port_number(valid_port)
        assert result == valid_port

    def test_validate_port_number_invalid_range(self):
        """Test la validation d'un port hors plage."""
        serializer = BaseAPISerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_port_number(70000)
        assert "entre 1 et 65535" in str(exc_info.value)

    def test_validate_port_number_invalid_type(self):
        """Test la validation d'un port avec type invalide."""
        serializer = BaseAPISerializer()
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.validate_port_number("8080")
        assert "entre 1 et 65535" in str(exc_info.value)


class TestDashboardRequestSerializer:
    """Tests pour le sérialiseur de requête de dashboard."""

    def test_valid_dashboard_request(self, sample_dashboard_data):
        """Test une requête de dashboard valide."""
        serializer = DashboardRequestSerializer(data=sample_dashboard_data)
        assert serializer.is_valid()
        assert serializer.validated_data['dashboard_type'] == 'system-overview'
        assert serializer.validated_data['time_range'] == '24h'

    def test_dashboard_request_with_custom_time_range(self):
        """Test une requête avec plage de temps personnalisée."""
        now = datetime.now()
        start_date = now - timedelta(hours=2)
        end_date = now
        
        data = {
            'dashboard_type': 'network-status',
            'time_range': 'custom',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        serializer = DashboardRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_dashboard_request_custom_time_missing_dates(self):
        """Test une requête custom sans dates."""
        data = {
            'dashboard_type': 'network-status',
            'time_range': 'custom'
            # start_date et end_date manquantes
        }
        
        serializer = DashboardRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'start_date et end_date sont requis' in str(serializer.errors)

    def test_dashboard_request_invalid_date_range(self):
        """Test une requête avec plage de dates invalide."""
        now = datetime.now()
        start_date = now
        end_date = now - timedelta(hours=2)  # Fin avant début
        
        data = {
            'dashboard_type': 'network-status',
            'time_range': 'custom',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        serializer = DashboardRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'start_date doit être antérieure' in str(serializer.errors)

    def test_dashboard_request_invalid_type(self):
        """Test une requête avec type de dashboard invalide."""
        data = {
            'dashboard_type': 'invalid-type',
            'time_range': '24h'
        }
        
        serializer = DashboardRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'dashboard_type' in serializer.errors

    def test_dashboard_request_invalid_time_range(self):
        """Test une requête avec plage de temps invalide."""
        data = {
            'dashboard_type': 'system-overview',
            'time_range': 'invalid-range'
        }
        
        serializer = DashboardRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'time_range' in serializer.errors


class TestDashboardWidgetSerializer:
    """Tests pour le sérialiseur de widget de dashboard."""

    def test_valid_widget(self, sample_widget_data):
        """Test un widget valide."""
        serializer = DashboardWidgetSerializer(data=sample_widget_data)
        assert serializer.is_valid()
        validated = serializer.validated_data
        assert validated['id'] == 'widget-test-1'
        assert validated['type'] == 'alerts'
        assert validated['position'] == {'x': 0, 'y': 0}

    def test_widget_without_position(self, sample_widget_data):
        """Test un widget sans position."""
        data = sample_widget_data.copy()
        del data['position']
        
        serializer = DashboardWidgetSerializer(data=data)
        assert serializer.is_valid()

    def test_widget_invalid_position(self, sample_widget_data):
        """Test un widget avec position invalide."""
        data = sample_widget_data.copy()
        data['position'] = {'x': -1, 'y': 'invalid'}
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'position' in serializer.errors

    def test_widget_invalid_size(self, sample_widget_data):
        """Test un widget avec taille invalide."""
        data = sample_widget_data.copy()
        data['size'] = {'width': 0, 'height': -1}
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'size' in serializer.errors

    def test_widget_size_exceeds_limits(self, sample_widget_data):
        """Test un widget avec taille dépassant les limites."""
        data = sample_widget_data.copy()
        data['size'] = {'width': 15, 'height': 10}  # Dépasse les limites
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Largeur maximum: 12' in str(serializer.errors)

    def test_widget_invalid_type(self, sample_widget_data):
        """Test un widget avec type invalide."""
        data = sample_widget_data.copy()
        data['type'] = 'invalid-type'
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'type' in serializer.errors

    def test_widget_configuration_validation_alerts(self):
        """Test la validation de configuration pour widget alerts."""
        data = {
            'id': 'test-alerts',
            'type': 'alerts',
            'title': 'Test Alerts',
            'configuration': {
                'severities': ['critical', 'invalid-severity']
            }
        }
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Severity invalide' in str(serializer.errors)

    def test_widget_configuration_validation_devices(self):
        """Test la validation de configuration pour widget devices."""
        data = {
            'id': 'test-devices',
            'type': 'devices',
            'title': 'Test Devices',
            'configuration': {
                'device_types': ['router', 'invalid-type']
            }
        }
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Device type invalide' in str(serializer.errors)

    def test_widget_refresh_interval_validation(self, sample_widget_data):
        """Test la validation de l'intervalle de rafraîchissement."""
        data = sample_widget_data.copy()
        data['refresh_interval'] = 10  # Trop faible
        
        serializer = DashboardWidgetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'refresh_interval' in serializer.errors


class TestCustomDashboardSerializer:
    """Tests pour le sérialiseur de dashboard personnalisé."""

    def test_valid_custom_dashboard(self, sample_custom_dashboard):
        """Test un dashboard personnalisé valide."""
        serializer = CustomDashboardSerializer(data=sample_custom_dashboard)
        assert serializer.is_valid()
        validated = serializer.validated_data
        assert validated['name'] == 'Mon Dashboard Test'
        assert len(validated['widgets']) == 2

    def test_custom_dashboard_without_widgets(self, sample_custom_dashboard):
        """Test un dashboard sans widgets."""
        data = sample_custom_dashboard.copy()
        data['widgets'] = []
        
        serializer = CustomDashboardSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Au moins un widget est requis' in str(serializer.errors)

    def test_custom_dashboard_too_many_widgets(self, sample_custom_dashboard):
        """Test un dashboard avec trop de widgets."""
        data = sample_custom_dashboard.copy()
        # Créer 25 widgets (dépasse la limite de 20)
        widgets = []
        for i in range(25):
            widgets.append({
                'id': f'widget-{i}',
                'type': 'alerts',
                'title': f'Widget {i}'
            })
        data['widgets'] = widgets
        
        serializer = CustomDashboardSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Maximum 20 widgets' in str(serializer.errors)

    def test_custom_dashboard_duplicate_widget_ids(self, sample_custom_dashboard):
        """Test un dashboard avec des IDs de widgets dupliqués."""
        data = sample_custom_dashboard.copy()
        data['widgets'][1]['id'] = data['widgets'][0]['id']  # Dupliquer l'ID
        
        serializer = CustomDashboardSerializer(data=data)
        assert not serializer.is_valid()
        assert 'IDs de widgets doivent être uniques' in str(serializer.errors)

    def test_custom_dashboard_fixed_layout_validation(self, sample_custom_dashboard):
        """Test la validation du layout fixed."""
        data = sample_custom_dashboard.copy()
        data['layout'] = 'fixed'
        # Supprimer la position d'un widget
        del data['widgets'][0]['position']
        
        serializer = CustomDashboardSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Position requise pour tous les widgets' in str(serializer.errors)

    def test_custom_dashboard_shared_permission_validation(self, sample_custom_dashboard):
        """Test la validation des permissions pour dashboard partagé."""
        from django.contrib.auth.models import User
        from rest_framework.request import Request
        from django.test import RequestFactory
        
        # Créer un utilisateur non-staff
        user = User(is_staff=False)
        
        # Créer une requête mockée
        factory = RequestFactory()
        request = factory.post('/')
        request.user = user
        
        data = sample_custom_dashboard.copy()
        data['shared'] = True
        
        serializer = CustomDashboardSerializer(
            data=data,
            context={'request': request}
        )
        assert not serializer.is_valid()
        assert 'privilèges administrateur' in str(serializer.errors)


class TestPaginatedResponseSerializer:
    """Tests pour le sérialiseur de réponse paginée."""

    def test_valid_paginated_response(self):
        """Test une réponse paginée valide."""
        data = {
            'count': 100,
            'next': 'http://example.com/api/items/?page=3',
            'previous': 'http://example.com/api/items/?page=1',
            'page': 2,
            'page_size': 20,
            'total_pages': 5,
            'results': [{'id': 1, 'name': 'Item 1'}]
        }
        
        serializer = PaginatedResponseSerializer(data=data)
        assert serializer.is_valid()

    def test_paginated_response_with_nulls(self):
        """Test une réponse paginée avec valeurs nulles."""
        data = {
            'count': 10,
            'next': None,  # Dernière page
            'previous': None,  # Première page
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'results': []
        }
        
        serializer = PaginatedResponseSerializer(data=data)
        assert serializer.is_valid()


class TestErrorResponseSerializer:
    """Tests pour le sérialiseur de réponse d'erreur."""

    def test_valid_error_response(self):
        """Test une réponse d'erreur valide."""
        data = {
            'error': 'Validation failed',
            'error_code': 'VALIDATION_ERROR',
            'details': {'field': 'value is required'},
            'timestamp': datetime.now().isoformat(),
            'request_id': '123e4567-e89b-12d3-a456-426614174000'
        }
        
        serializer = ErrorResponseSerializer(data=data)
        assert serializer.is_valid()

    def test_error_response_invalid_code(self):
        """Test une réponse d'erreur avec code invalide."""
        data = {
            'error': 'Some error',
            'error_code': 'INVALID_CODE',
            'timestamp': datetime.now().isoformat()
        }
        
        serializer = ErrorResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Code d\'erreur invalide' in str(serializer.errors)

    def test_error_response_minimal(self):
        """Test une réponse d'erreur minimale."""
        data = {
            'error': 'Some error',
            'timestamp': datetime.now().isoformat()
        }
        
        serializer = ErrorResponseSerializer(data=data)
        assert serializer.is_valid()


class TestSuccessResponseSerializer:
    """Tests pour le sérialiseur de réponse de succès."""

    def test_valid_success_response(self):
        """Test une réponse de succès valide."""
        data = {
            'success': True,
            'message': 'Operation completed successfully',
            'data': {'result': 'success'},
            'timestamp': datetime.now().isoformat(),
            'request_id': '123e4567-e89b-12d3-a456-426614174000'
        }
        
        serializer = SuccessResponseSerializer(data=data)
        assert serializer.is_valid()

    def test_success_response_minimal(self):
        """Test une réponse de succès minimale."""
        data = {
            'message': 'Operation completed',
            'timestamp': datetime.now().isoformat()
        }
        
        serializer = SuccessResponseSerializer(data=data)
        assert serializer.is_valid()
        # success devrait être True par défaut
        assert serializer.validated_data['success'] is True


class TestDashboardConfigurationSerializer:
    """Tests pour le sérialiseur de configuration de dashboard."""

    def test_valid_dashboard_configuration(self):
        """Test une configuration de dashboard valide."""
        data = {
            'dashboard_type': 'user-dashboard',
            'configuration': {
                'widgets': [
                    {'id': 'w1', 'type': 'alerts'},
                    {'id': 'w2', 'type': 'devices'}
                ],
                'layout': 'grid',
                'refresh_interval': 300
            },
            'user_id': 123
        }
        
        serializer = DashboardConfigurationSerializer(data=data)
        assert serializer.is_valid()

    def test_dashboard_configuration_invalid_structure(self):
        """Test une configuration avec structure invalide."""
        data = {
            'dashboard_type': 'custom',
            'configuration': "invalid_json_structure",  # Devrait être un dict
            'user_id': 123
        }
        
        serializer = DashboardConfigurationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'dictionnaire' in str(serializer.errors)

    def test_dashboard_configuration_invalid_widgets(self):
        """Test une configuration avec widgets invalides."""
        data = {
            'dashboard_type': 'custom',
            'configuration': {
                'widgets': "should_be_list"  # Devrait être une liste
            }
        }
        
        serializer = DashboardConfigurationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Configuration.widgets doit être une liste' in str(serializer.errors) 