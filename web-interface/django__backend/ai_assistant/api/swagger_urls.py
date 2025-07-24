"""
URLs pour la documentation Swagger/OpenAPI du module AI Assistant.
"""

from django.urls import path, include
from .docs import schema_view

# URLs de la documentation Swagger
urlpatterns = [
    # Interface Swagger interactive
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # Interface ReDoc (alternative plus moderne)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Schéma JSON brut (pour intégrations)
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # Schéma YAML brut (pour intégrations)
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
]