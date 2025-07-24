"""
Configuration des URLs pour l'API du module plugins.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PluginViewSet
from ..swagger_schema import swagger_urls

# Création du routeur pour les endpoints de l'API REST
router = DefaultRouter()
router.register(r'plugins', PluginViewSet, basename='plugin')

# Assemblage des URLs de l'API et de la documentation
urlpatterns = [
    # Endpoints de l'API REST
    path('', include(router.urls)),
    
    # Documentation Swagger
    *swagger_urls,
] 