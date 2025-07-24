"""
Configuration des URLs pour l'API de reporting.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.report_views import ReportViewSet
from .views.scheduled_report_views import ScheduledReportViewSet
from .views.advanced_views import (
    VisualizationViewSet,
    AnalyticsViewSet,
    DataIntegrationViewSet,
    PerformanceViewSet
)

from .swagger import urlpatterns as swagger_urls

# Création des routeurs
router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'scheduled-reports', ScheduledReportViewSet, basename='scheduled-report')
router.register(r'visualizations', VisualizationViewSet, basename='visualization')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'data-integration', DataIntegrationViewSet, basename='data-integration')
router.register(r'performance', PerformanceViewSet, basename='performance')

# Import des vues unifiées
from .views.unified_reporting_views import (
    unified_dashboard,
    generate_unified_report,
    distribute_report,
    available_channels,
    test_distribution
)

# URLs de l'application
app_name = 'reporting'
urlpatterns = [
    path('', include(router.urls)),
    # URLs du service unifié de reporting
    path('unified/dashboard/', unified_dashboard, name='unified-dashboard'),
    path('unified/generate/', generate_unified_report, name='generate-unified-report'),
    path('unified/distribute/', distribute_report, name='distribute-report'),
    path('unified/channels/', available_channels, name='available-channels'),
    path('unified/test-distribution/', test_distribution, name='test-distribution'),
    # URLs de la documentation Swagger - intégrées dans la doc globale
    # path('docs/', include(swagger_urls)),
] 