"""
Configuration des URLs minimaliste pour debug Swagger.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration Swagger minimale pour debug
schema_view = get_schema_view(
    openapi.Info(
        title="NMS API Debug",
        default_version='v1',
        description="Version minimaliste pour debug",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        # Tester un module à la fois
        # path('api/monitoring/', include('monitoring.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Documentation Swagger/OpenAPI
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

# Servir les fichiers statiques
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
