"""
Configuration des URLs pour le projet NMS - Version simplifiée.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration Swagger/OpenAPI - Version simplifiée
schema_view = get_schema_view(
    openapi.Info(
        title="Network Management System (NMS) API",
        default_version='v1',
        description="""
        API complète pour le Network Management System (NMS)

        ## Modules disponibles:
        - **Monitoring** : Surveillance et alertes  
        - **Dashboard** : Tableaux de bord
        - **API Clients** : Gestion des clients API
        - **GNS3** : Intégration GNS3

        ## Authentification
        - Session Django pour l'interface web
        """,
        contact=openapi.Contact(name="NMS Support Team", email="admin@nms.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('api/monitoring/', include('monitoring.urls')),
        path('api/dashboard/', include('dashboard.api.urls')),
        path('api/clients/', include('api_clients.urls')),
        path('api/gns3/', include('gns3_integration.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/monitoring/', include('monitoring.urls')),
    path('api/dashboard/', include('dashboard.api.urls')),
    path('api/clients/', include('api_clients.urls')),
    path('api/gns3/', include('gns3_integration.urls')),
    
    # Vues web Django
    path('dashboard/', include('dashboard.urls')),

    # Documentation Swagger/OpenAPI
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]

# Servir les fichiers statiques
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
