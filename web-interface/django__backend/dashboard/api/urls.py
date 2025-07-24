"""
Configuration des URLs pour l'API du module Dashboard.

Ce fichier définit les routes API pour accéder aux fonctionnalités
du tableau de bord.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import controllers
from .viewsets import (
    UserDashboardConfigViewSet,
    DashboardWidgetViewSet,
    DashboardPresetViewSet,
    CustomDashboardViewSet
)

# Router pour les ViewSets CRUD
router = DefaultRouter()
router.register(r'configs', UserDashboardConfigViewSet, basename='dashboard-config')
router.register(r'widgets', DashboardWidgetViewSet, basename='dashboard-widget')
router.register(r'presets', DashboardPresetViewSet, basename='dashboard-preset')
router.register(r'custom', CustomDashboardViewSet, basename='custom-dashboard')

# Préfixe d'URL pour toutes les routes de ce fichier: /api/dashboard/
urlpatterns = [
    # Routes CRUD pour les ViewSets (avec toutes les opérations CRUD)
    path('', include(router.urls)),

    # Route de test sans authentification
    path('test/status/', controllers.test_dashboard_status, name='test_dashboard_status'),

    # Routes pour les données du tableau de bord (lecture seule)
    path('data/', controllers.DashboardDataView.as_view(), name='dashboard_data'),
    path('config/', controllers.UserDashboardConfigView.as_view(), name='dashboard_config'),

    # Routes pour les données réseau (lecture seule)
    path('network/overview/', controllers.NetworkOverviewView.as_view(), name='network_overview'),
    path('network/health/', controllers.SystemHealthView.as_view(), name='system_health'),
    path('network/device/<int:device_id>/metrics/', controllers.DeviceMetricsView.as_view(), name='device_metrics'),

    # Routes pour les données de topologie (lecture seule)
    path('topology/list/', controllers.TopologyListView.as_view(), name='topology_list'),
    path('topology/data/', controllers.TopologyDataView.as_view(), name='topology_data'),
]