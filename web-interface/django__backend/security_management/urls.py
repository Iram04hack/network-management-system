"""
Configuration des URLs pour le module security_management.

Ce module définit les points d'entrée URL pour le module security_management.
"""

from django.urls import path, include

urlpatterns = [
    # API complète avec toutes les fonctionnalités avancées
    path('', include('security_management.api.urls')),
]
