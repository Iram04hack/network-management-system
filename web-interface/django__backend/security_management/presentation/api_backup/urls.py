"""
Configuration des URLs pour l'API REST du module security_management.

Ce fichier définit les routes de l'API REST pour le module security_management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SecurityRuleViewSet, SecurityAlertViewSet


# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'rules', SecurityRuleViewSet, basename='security-rule')
router.register(r'alerts', SecurityAlertViewSet, basename='security-alert')

# Définir les patterns d'URL
urlpatterns = [
    path('', include(router.urls)),
] 